"""Render ``SKILL.md`` files from ``SKILL.md.tmpl`` templates.

Skills accumulate boilerplate.  Four of the ``skills/github/*`` skills each
carried their own copy of the same twenty-line auth-resolution shell block,
and the copies had already drifted apart — one grew an ``echo`` line, another
moved the owner/repo extraction somewhere else.  Nobody edits four files when
they fix one bug.

This module is the fix: shared prose lives in exactly one place and is
composed into each skill at build time.

Pipeline::

    read SKILL.md.tmpl -> expand {{PLACEHOLDER}} tokens -> write SKILL.md

The generated ``SKILL.md`` is committed, so nothing has to run at install or
at agent time — the runtime keeps reading plain markdown exactly as before.
``check_templates()`` backs a CI gate that fails when a committed file drifts
from its template, which is what keeps "generated" honest.

Placeholders
------------

``{{SNIPPET:id}}``
    Inline ``skills/_shared/snippets/<id>.md``.  The core mechanism.

``{{PREAMBLE}}``
    Inline the ordered snippet list for the template's ``preamble-tier``,
    read from ``skills/_shared/preamble/manifest.json``.  A tier is just a
    named bundle of snippets, so a skill opts into a whole shared header
    with one frontmatter key.

``{{SECTION:id}}``
    Emit a STOP-Read pointer to ``sections/<file>`` for a carved skill.  The
    section body stays out of the prompt until the step actually applies —
    progressive disclosure, the same idea as the existing ``references/``
    convention but for steps the agent must execute rather than background
    material.

``{{SECTION_INDEX}}``
    Render the situation -> section table from the skill's section manifest.

``{{INVOKE_SKILL:name[:skip=A,B]}}``
    Emit prose telling the agent to read another skill and follow it, minus
    the sections the calling skill has already handled.

``{{SKILL_NAME}}``
    The skill's directory name.

Adapted from the ``SKILL.md.tmpl`` / ``sections/`` / ``{{PREAMBLE}}`` build
system in garrytan/gstack, reduced to the parts that earn their keep here.
gstack renders per-host and per-model because each of its skills boots a
standalone ``claude -p`` process; Hermes loads skills into a live session, so
the host/model/telemetry layers are dropped and the section carve — which
decides how much text enters the prompt — carries the weight.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

# Directories that never contain templates.  Mirrors the spirit of
# ``agent.skill_utils.EXCLUDED_SKILL_DIRS`` without importing it — this module
# is build tooling and must stay importable with no agent dependencies.
SKIP_DIRS = frozenset(
    (
        ".git",
        ".github",
        ".hub",
        ".archive",
        ".venv",
        "venv",
        "node_modules",
        "site-packages",
        "__pycache__",
        ".tox",
        ".nox",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    )
)

#: Name of the build-only directory holding shared snippets and the tier map.
SHARED_DIR_NAME = "_shared"

#: Frontmatter keys consumed by the renderer and stripped from the output.
#: They configure the build; leaving them in the shipped file would imply the
#: runtime reads them, and it does not.
BUILD_ONLY_KEYS = ("preamble-tier",)

GENERATED_HEADER = (
    "<!-- AUTO-GENERATED from {source} — do not edit directly. -->\n"
    "<!-- Edit the template, then run: hermes skills render -->"
)

# ``{{NAME}}`` or ``{{NAME:arg[:arg...]}}``.  Names are SCREAMING_SNAKE so a
# placeholder can never collide with ordinary prose or a shell ``${VAR}``.
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*(?::[^}\n]*)?)\}\}")

# A resolver may emit text containing further placeholders — a snippet can
# use {{SNIPPET:...}}, and {{PREAMBLE}} expands to a list of them.  ``re.sub``
# does not rescan what it inserted, so resolution loops until the text stops
# changing.  Bounded so a snippet that (directly or through a cycle) emits its
# own placeholder fails loudly instead of hanging the build.
MAX_PASSES = 6


class TemplateError(Exception):
    """A template could not be rendered."""


@dataclass
class TemplateContext:
    """Everything a resolver is allowed to know about the file being rendered."""

    skill_name: str
    skill_dir: Path
    tmpl_path: Path
    root: Path
    preamble_tier: Optional[str] = None
    #: Section ids referenced by {{SECTION:id}} during this render, in order.
    #: Lets the caller assert that every declared section is actually used.
    used_sections: List[str] = field(default_factory=list)

    @property
    def shared_dir(self) -> Path:
        return self.root / SHARED_DIR_NAME

    def rel(self, path: Path) -> str:
        """Repo-relative path for error messages, with forward slashes."""
        try:
            return path.relative_to(self.root.parent).as_posix()
        except ValueError:
            return path.as_posix()


Resolver = Callable[[TemplateContext, Sequence[str]], str]


# ── Frontmatter ────────────────────────────────────────────────────────────


def split_frontmatter(text: str) -> tuple[str, str]:
    """Split *text* into ``(frontmatter_block, body)``.

    The frontmatter block includes both ``---`` fences and the trailing
    newline.  Returns ``("", text)`` when there is no frontmatter, so callers
    can treat the two cases uniformly.
    """
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 3)
    if end == -1:
        return "", text
    cut = end + len("\n---\n")
    return text[:cut], text[cut:]


def _frontmatter_value(frontmatter: str, key: str) -> Optional[str]:
    """Read a scalar ``key: value`` from *frontmatter*.

    Deliberately regex-based rather than a YAML parse: the renderer needs two
    scalars and must not depend on, or be broken by, anything else in the
    block.  The frontmatter is copied through verbatim regardless.
    """
    match = re.search(rf"^{re.escape(key)}:[ \t]*(.+?)[ \t]*$", frontmatter, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip("'\"")


def _strip_build_only_keys(frontmatter: str) -> str:
    """Drop build-only keys so they never reach the shipped file."""
    for key in BUILD_ONLY_KEYS:
        frontmatter = re.sub(
            rf"^{re.escape(key)}:[ \t]*.*\n", "", frontmatter, flags=re.MULTILINE
        )
    return frontmatter


# ── Shared snippets ────────────────────────────────────────────────────────


def _read_snippet(ctx: TemplateContext, snippet_id: str) -> str:
    if "/" in snippet_id or "\\" in snippet_id or snippet_id.startswith("."):
        raise TemplateError(
            f"{ctx.rel(ctx.tmpl_path)}: invalid snippet id {snippet_id!r} — "
            "ids are bare names, e.g. {{SNIPPET:github-auth}}"
        )
    path = ctx.shared_dir / "snippets" / f"{snippet_id}.md"
    if not path.is_file():
        available = sorted(
            p.stem for p in (ctx.shared_dir / "snippets").glob("*.md")
        )
        raise TemplateError(
            f"{ctx.rel(ctx.tmpl_path)}: no shared snippet {snippet_id!r} "
            f"({ctx.rel(path)} does not exist). Available: "
            f"{', '.join(available) or 'none'}"
        )
    return path.read_text(encoding="utf-8").strip("\n")


def resolve_snippet(ctx: TemplateContext, args: Sequence[str]) -> str:
    if not args or not args[0]:
        raise TemplateError(
            f"{ctx.rel(ctx.tmpl_path)}: {{{{SNIPPET}}}} needs an id, "
            "e.g. {{SNIPPET:github-auth}}"
        )
    return _read_snippet(ctx, args[0])


def load_preamble_manifest(shared_dir: Path) -> Dict[str, List[str]]:
    """Load the tier -> snippet-ids map, or ``{}`` when there is none."""
    path = shared_dir / "preamble" / "manifest.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TemplateError(f"{path}: invalid JSON — {exc}") from exc
    tiers = data.get("tiers")
    if not isinstance(tiers, dict):
        raise TemplateError(f"{path}: expected a top-level 'tiers' object")
    return {str(k): list(v) for k, v in tiers.items()}


def resolve_preamble(ctx: TemplateContext, args: Sequence[str]) -> str:
    """Inline the snippets bundled under the template's ``preamble-tier``."""
    tier = args[0] if args and args[0] else ctx.preamble_tier
    if not tier:
        raise TemplateError(
            f"{ctx.rel(ctx.tmpl_path)}: {{{{PREAMBLE}}}} needs a tier — add "
            "'preamble-tier: <name>' to the template frontmatter or write "
            "{{PREAMBLE:<name>}}"
        )
    tiers = load_preamble_manifest(ctx.shared_dir)
    if tier not in tiers:
        raise TemplateError(
            f"{ctx.rel(ctx.tmpl_path)}: unknown preamble tier {tier!r}. "
            f"Known tiers: {', '.join(sorted(tiers)) or 'none'} "
            f"(see {SHARED_DIR_NAME}/preamble/manifest.json)"
        )
    parts = [_read_snippet(ctx, sid) for sid in tiers[tier]]
    return "\n\n".join(p for p in parts if p.strip())


# ── Sections ───────────────────────────────────────────────────────────────


def load_section_manifest(skill_dir: Path) -> List[dict]:
    """Load ``sections/manifest.json`` for a carved skill.

    The manifest is a passive registry: ids, file names, and human-readable
    trigger text.  It records *where* a section lives and *when* it applies;
    the skill body remains the only thing that decides control flow.
    """
    path = skill_dir / "sections" / "manifest.json"
    if not path.is_file():
        raise TemplateError(
            f"{skill_dir.name}: {{{{SECTION}}}} used but "
            f"{path.parent.name}/manifest.json is missing"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TemplateError(f"{path}: invalid JSON — {exc}") from exc
    sections = data.get("sections")
    if not isinstance(sections, list):
        raise TemplateError(f"{path}: expected a top-level 'sections' array")
    for entry in sections:
        missing = [k for k in ("id", "file", "trigger") if not entry.get(k)]
        if missing:
            raise TemplateError(
                f"{path}: section {entry.get('id', '?')!r} is missing "
                f"{', '.join(missing)}"
            )
    return sections


def _find_section(ctx: TemplateContext, section_id: str) -> dict:
    sections = load_section_manifest(ctx.skill_dir)
    for entry in sections:
        if entry["id"] == section_id:
            return entry
    known = ", ".join(s["id"] for s in sections) or "none"
    raise TemplateError(
        f"{ctx.rel(ctx.tmpl_path)}: no section {section_id!r} in "
        f"sections/manifest.json (known: {known})"
    )


def resolve_section(ctx: TemplateContext, args: Sequence[str]) -> str:
    """Emit a STOP-Read pointer instead of the section body.

    The pointer names ``skill_view``'s exact arguments so the agent does not
    have to guess how to reach the file, and says outright that working from
    memory is not an option — a summary in the skeleton would otherwise be
    treated as a substitute for the real thing.
    """
    if not args or not args[0]:
        raise TemplateError(
            f"{ctx.rel(ctx.tmpl_path)}: {{{{SECTION}}}} needs an id, "
            "e.g. {{SECTION:triage}}"
        )
    entry = _find_section(ctx, args[0])
    ctx.used_sections.append(entry["id"])
    return (
        f"> **STOP.** Before {entry['trigger']}, load this step's instructions:\n"
        f"> `skill_view(\"{ctx.skill_name}\", file_path=\"sections/{entry['file']}\")`\n"
        "> Execute it in full. Do not work from the summary above — that file "
        "is the source of truth for this step."
    )


def resolve_section_index(ctx: TemplateContext, args: Sequence[str]) -> str:
    """Render the situation -> section table from the manifest."""
    sections = load_section_manifest(ctx.skill_dir)
    # The table names every section, so a skill that ships only an index has
    # still pointed the agent at all of them.
    ctx.used_sections.extend(entry["id"] for entry in sections)
    lines = [
        "| When | Load this section |",
        "|------|-------------------|",
    ]
    for entry in sections:
        lines.append(f"| {entry['trigger']} | `sections/{entry['file']}` |")
    return "\n".join(lines)


# ── Composition ────────────────────────────────────────────────────────────

#: Sections a called skill re-states that its caller has already covered.
#: Reading them twice wastes context and, worse, restarts setup the caller
#: already did.
DEFAULT_INVOKE_SKIPS = (
    "Requirements",
    "Setup",
)


def resolve_invoke_skill(ctx: TemplateContext, args: Sequence[str]) -> str:
    """Emit prose that hands control to another skill and comes back."""
    if not args or not args[0]:
        raise TemplateError(
            f"{ctx.rel(ctx.tmpl_path)}: {{{{INVOKE_SKILL}}}} needs a skill "
            "name, e.g. {{INVOKE_SKILL:github-auth}}"
        )
    target = args[0]
    extra: List[str] = []
    for arg in args[1:]:
        if arg.startswith("skip="):
            extra.extend(s.strip() for s in arg[len("skip=") :].split(",") if s.strip())
    skips = list(DEFAULT_INVOKE_SKIPS) + extra
    skip_lines = "\n".join(f"- {s}" for s in skips)
    return (
        f'Load the `{target}` skill with `skill_view("{target}")` and follow it '
        "top to bottom.\n\n"
        f"**If it will not load:** say \"Could not load {target} — continuing "
        "without it.\" and carry on; do not stop.\n\n"
        "Skip these sections — this skill has already handled them:\n"
        f"{skip_lines}\n\n"
        "Execute every other section at full depth, then continue below."
    )


RESOLVERS: Dict[str, Resolver] = {
    "SNIPPET": resolve_snippet,
    "PREAMBLE": resolve_preamble,
    "SECTION": resolve_section,
    "SECTION_INDEX": resolve_section_index,
    "INVOKE_SKILL": resolve_invoke_skill,
    "SKILL_NAME": lambda ctx, args: ctx.skill_name,
}


# ── Rendering ──────────────────────────────────────────────────────────────


def render_text(text: str, ctx: TemplateContext) -> str:
    """Expand every placeholder in *text* until the result stops changing."""

    def one_pass(chunk: str) -> str:
        def substitute(match: re.Match) -> str:
            name, _, arg_blob = match.group(1).partition(":")
            resolver = RESOLVERS.get(name)
            if resolver is None:
                raise TemplateError(
                    f"{ctx.rel(ctx.tmpl_path)}: unknown placeholder "
                    f"{{{{{name}}}}}. Known: {', '.join(sorted(RESOLVERS))}"
                )
            args = arg_blob.split(":") if arg_blob else []
            return resolver(ctx, args)

        return PLACEHOLDER_RE.sub(substitute, chunk)

    rendered = text
    for _ in range(MAX_PASSES):
        nxt = one_pass(rendered)
        if nxt == rendered:
            break
        rendered = nxt

    # Judge by what is left, not by whether the loop ran out: text that needed
    # every pass but did resolve is fine, while a self-referential snippet
    # keeps re-emitting its own token and is still holding one here.
    remaining = PLACEHOLDER_RE.findall(rendered)
    if remaining:
        raise TemplateError(
            f"{ctx.rel(ctx.tmpl_path)}: placeholders still expanding after "
            f"{MAX_PASSES} passes — a snippet probably includes itself. "
            f"Still unresolved: {', '.join(sorted(set(remaining)))}"
        )
    return rendered


def build_context(tmpl_path: Path, root: Path) -> TemplateContext:
    """Derive a context from a template path and its frontmatter."""
    text = tmpl_path.read_text(encoding="utf-8")
    frontmatter, _ = split_frontmatter(text)
    skill_dir = tmpl_path.parent
    # A section template lives at <skill>/sections/<name>.md.tmpl, so its
    # skill is the grandparent.  Sections must resolve with their parent
    # skill's context — the name a {{SECTION}} pointer prints has to be the
    # skill the agent can actually load, not the string "sections".
    if skill_dir.name == "sections":
        skill_dir = skill_dir.parent
    name = _frontmatter_value(frontmatter, "name") or skill_dir.name
    return TemplateContext(
        skill_name=name,
        skill_dir=skill_dir,
        tmpl_path=tmpl_path,
        root=root,
        preamble_tier=_frontmatter_value(frontmatter, "preamble-tier"),
    )


def _assert_every_section_is_reachable(ctx: TemplateContext) -> None:
    """Fail when a skill declares a section nothing points at.

    A section the SKILL.md never references is a file the agent will never be
    told to load — the step silently stops happening. Cheaper to catch at
    build time than to notice missing behaviour in a transcript.
    """
    if not (ctx.skill_dir / "sections" / "manifest.json").is_file():
        return
    declared = [entry["id"] for entry in load_section_manifest(ctx.skill_dir)]
    orphans = [sid for sid in declared if sid not in ctx.used_sections]
    if orphans:
        raise TemplateError(
            f"{ctx.rel(ctx.tmpl_path)}: sections/manifest.json declares "
            f"{', '.join(orphans)} but nothing points there. Add "
            f"{{{{SECTION:{orphans[0]}}}}} (or {{{{SECTION_INDEX}}}}) to the "
            "template, or drop the entry."
        )


def render_template(tmpl_path: Path, root: Path) -> str:
    """Render one template to its final file content."""
    ctx = build_context(tmpl_path, root)
    text = tmpl_path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    header = GENERATED_HEADER.format(source=tmpl_path.name)
    rendered_body = render_text(body, ctx)
    if frontmatter:
        frontmatter = render_text(frontmatter, ctx)
        frontmatter = _strip_build_only_keys(frontmatter)
        content = f"{frontmatter}{header}\n\n{rendered_body.lstrip(chr(10))}"
    else:
        content = f"{header}\n\n{rendered_body.lstrip(chr(10))}"
    if not content.endswith("\n"):
        content += "\n"
    # Only a skill's own SKILL.md.tmpl owns the pointers; a section template
    # renders one step and is not expected to reference its siblings.
    if tmpl_path.name == "SKILL.md.tmpl":
        _assert_every_section_is_reachable(ctx)
    return content


# ── Discovery ──────────────────────────────────────────────────────────────


def _walk(root: Path):
    """Yield files under *root*, pruning directories that never hold skills."""
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name)
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name not in SKIP_DIRS:
                    stack.append(entry)
            else:
                yield entry


def discover_templates(root: Path) -> List[Path]:
    """Find every ``SKILL.md.tmpl`` and ``sections/*.md.tmpl`` under *root*.

    Sorted so a freshness check never flaps on filesystem iteration order.
    """
    found = [
        path
        for path in _walk(root)
        if path.name == "SKILL.md.tmpl"
        or (path.parent.name == "sections" and path.name.endswith(".md.tmpl"))
    ]
    return sorted(found, key=lambda p: p.as_posix())


def output_path_for(tmpl_path: Path) -> Path:
    """The generated file a template writes to (``.tmpl`` stripped)."""
    return tmpl_path.with_suffix("")


@dataclass
class RenderResult:
    """One template's outcome."""

    tmpl_path: Path
    output_path: Path
    content: str
    changed: bool


def render_all(root: Path, *, write: bool = True) -> List[RenderResult]:
    """Render every template under *root*.

    With ``write=False`` nothing touches disk — that is the freshness check,
    which needs the comparison but not the side effect.
    """
    results: List[RenderResult] = []
    for tmpl_path in discover_templates(root):
        content = render_template(tmpl_path, root)
        output_path = output_path_for(tmpl_path)
        try:
            existing = output_path.read_text(encoding="utf-8")
        except OSError:
            existing = None
        changed = existing != content
        if write and changed:
            # newline="\n" pins LF on every platform: a Windows checkout would
            # otherwise write CRLF and fail the freshness check in CI forever.
            with open(output_path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
        results.append(RenderResult(tmpl_path, output_path, content, changed))
    return results


def check_templates(root: Path) -> List[RenderResult]:
    """Return the results whose committed file has drifted from its template."""
    return [r for r in render_all(root, write=False) if r.changed]


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Zero-dependency entry point: ``python -m tools.skill_template [--check]``.

    ``hermes skills render`` is the command contributors use. This exists so
    the CI freshness gate can run the renderer without booting the CLI (and
    its dependency chain) just to compare two strings.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m tools.skill_template",
        description="Render SKILL.md files from SKILL.md.tmpl templates.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing (exit 1 if any generated file is stale)",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Skills directory to render (default: the repo's skills/)",
    )
    args = parser.parse_args(argv)

    root = (
        Path(args.root).expanduser().resolve()
        if args.root
        else Path(__file__).resolve().parent.parent / "skills"
    )
    if not root.is_dir():
        print(f"No such directory: {root}")
        return 1

    try:
        results = check_templates(root) if args.check else render_all(root)
    except TemplateError as exc:
        print(f"Template error: {exc}")
        return 1

    if args.check:
        if results:
            print(f"{len(results)} generated file(s) out of date:")
            for result in results:
                print(f"  {result.output_path.relative_to(root.parent)}")
            print("\nRun 'hermes skills render' and commit the result.")
            return 1
        print("All generated SKILL.md files are up to date.")
        return 0

    changed = [r for r in results if r.changed]
    for result in changed:
        print(f"  rendered {result.output_path.relative_to(root.parent)}")
    print(f"Rendered {len(changed)} of {len(results)} template(s).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
