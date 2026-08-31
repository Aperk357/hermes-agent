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

This module is a derivative work: the pipeline shape, the bounded multi-pass
resolve, the section-pointer and section-index forms, and the generated-file
banner all follow gstack's ``scripts/gen-skill-docs.ts``,
``scripts/discover-skills.ts`` and ``scripts/resolvers/*.ts``. gstack is MIT
licensed, which permits this on condition that its notice travels with the
derived code:

    MIT License

    Copyright (c) 2026 Garry Tan

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to permit
    persons to whom the Software is furnished to do so, subject to the
    following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

from agent.skill_utils import EXCLUDED_SKILL_DIRS

# Directories that never contain templates. Imported rather than re-listed:
# a hand-copy of this set is exactly the duplication-drift this module exists
# to prevent, and it had already drifted once (``_shared`` was added to the
# scanner's set but not to the copy here). ``agent.skill_utils`` imports on
# bare stdlib, so the CI gate still needs no dependency install.
SKIP_DIRS = EXCLUDED_SKILL_DIRS

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


# Closing fence, deliberately matching ``agent.skill_utils.parse_frontmatter``'s
# ``re.search(r"\n---\s*\n", ...)``. The two MUST agree: if the renderer decides
# a template has no frontmatter where the runtime sees one, the generated header
# is written above the ``---`` fence, the runtime then finds no frontmatter, and
# the skill silently loses the name and description that drive its discovery.
# ``[ \t]*`` rather than the runtime's ``\s*``: the tolerance that matters is
# trailing spaces/tabs and a fence at EOF, while ``\s*`` would also swallow the
# blank line after the fence and shift every generated body. ``\Z`` accepts a
# template whose closing fence has no final newline — the runtime rejects that,
# so normalising it here repairs the file instead of shipping a nameless skill.
_FRONTMATTER_CLOSE_RE = re.compile(r"\n---[ \t]*(?:\r?\n|\Z)")

# A frontmatter line is a key, a list item, a comment, an indented
# continuation, or blank. Used to reject a block that is really body prose.
_FRONTMATTER_LINE_RE = re.compile(
    r"^(?:[ \t]|#|-\s|[A-Za-z_][A-Za-z0-9_.\-]*\s*:|\.\.\.|---)|^\s*$"
)


def split_frontmatter(text: str) -> tuple[str, str]:
    """Split *text* into ``(frontmatter_block, body)``.

    The frontmatter block includes both ``---`` fences and the trailing
    newline.  Returns ``("", text)`` when there is no frontmatter, so callers
    can treat the two cases uniformly.

    Tolerances match the runtime parser exactly — a bare ``---`` prefix (not
    only ``---\n``) and a closing fence with trailing whitespace or at EOF.
    """
    if not text.startswith("---"):
        return "", text
    match = _FRONTMATTER_CLOSE_RE.search(text, 3)
    if match is None:
        return "", text
    cut = match.end()
    block = text[:cut]
    if not block.endswith("\n"):
        block += "\n"
    return block, text[cut:]


def _assert_frontmatter_is_plausible(frontmatter: str, tmpl_path: Path) -> None:
    """Reject a "frontmatter" block that is really body prose.

    A template whose opening fence is never properly closed lets the closing
    regex latch onto a ``---`` horizontal rule further down, swallowing real
    body text into the frontmatter — where ``_strip_build_only_keys`` can then
    delete lines from it. Both this renderer and the runtime would misread such
    a file identically, so catch it at build time instead.
    """
    inner = frontmatter.split("\n", 1)[1] if "\n" in frontmatter else ""
    for number, line in enumerate(inner.splitlines(), start=2):
        if line.strip() in ("---", "..."):
            break
        if not _FRONTMATTER_LINE_RE.match(line):
            raise TemplateError(
                f"{tmpl_path.name}:{number}: {line.strip()!r} is not a "
                "frontmatter line. The opening '---' is probably never closed, "
                "so a '---' later in the body was mistaken for the closing "
                "fence. Close the frontmatter."
            )


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
    if not isinstance(data, dict):
        raise TemplateError(f"{path}: expected a JSON object at the top level")
    sections = data.get("sections")
    if not isinstance(sections, list):
        raise TemplateError(f"{path}: expected a top-level 'sections' array")
    seen_ids: set = set()
    for entry in sections:
        if not isinstance(entry, dict):
            raise TemplateError(
                f"{path}: every entry in 'sections' must be an object, got "
                f"{type(entry).__name__}"
            )
        for key in ("id", "file", "trigger"):
            if key in entry and not isinstance(entry[key], str):
                raise TemplateError(
                    f"{path}: section {entry.get('id', '?')!r} has a "
                    f"non-string {key!r}"
                )
        missing = [k for k in ("id", "file", "trigger") if not entry.get(k)]
        if missing:
            raise TemplateError(
                f"{path}: section {entry.get('id', '?')!r} is missing "
                f"{', '.join(missing)}"
            )
        file_name = str(entry["file"])
        if "/" in file_name or "\\" in file_name or file_name.startswith("."):
            raise TemplateError(
                f"{path}: section {entry['id']!r} has file {file_name!r} — "
                "must be a bare file name inside sections/, since it is "
                "rendered into a path the agent is told to load"
            )
        if entry["id"] in seen_ids:
            raise TemplateError(
                f"{path}: duplicate section id {entry['id']!r}. Only the first "
                "is ever pointed at, so the reachability check cannot see that "
                "the second is stranded."
            )
        seen_ids.add(entry["id"])
        for key in ("id", "file", "trigger"):
            if "{{" in str(entry.get(key, "")):
                raise TemplateError(
                    f"{path}: section {entry['id']!r} has {key!r} containing "
                    "'{{'. Manifest text is rendered into the skill and would "
                    "be re-scanned as a placeholder."
                )
        target = skill_dir / "sections" / file_name
        # The body may itself be generated from <file>.tmpl, which has not been
        # rendered yet on a skill's first build — either satisfies the pointer.
        if not target.is_file() and not target.with_name(f"{file_name}.tmpl").is_file():
            raise TemplateError(
                f"{path}: section {entry['id']!r} points at sections/{file_name}, "
                "which does not exist. A STOP pointer to a missing file is a "
                "step that silently stops happening."
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
        # A '|' would end the cell and a newline would end the row.
        trigger = " ".join(entry["trigger"].split()).replace("|", "\\|")
        lines.append(f"| {trigger} | `sections/{entry['file']}` |")
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
        if not arg.startswith("skip="):
            raise TemplateError(
                f"{ctx.rel(ctx.tmpl_path)}: {{{{INVOKE_SKILL}}}} got unknown "
                f"argument {arg!r}; the only supported form is "
                "skip=Section A,Section B"
            )
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


# ``{{name}}`` / ``{{ NAME }}`` — shaped like a placeholder but not matched by
# PLACEHOLDER_RE, so it would sail through both the unknown-placeholder guard
# and the leftover check and ship verbatim. Deliberately narrow: the token must
# be a bare identifier with nothing but whitespace inside the braces, so shell
# and awk constructs like ``{{ print $1 }}`` and prose like ``{{ not a token }}``
# do not match.
NEAR_MISS_RE = re.compile(r"\{\{\s*([A-Za-z][A-Za-z0-9_]*)(?::[^}\n]*)?\s*\}\}")


def _assert_no_near_miss_placeholders(text: str, ctx: "TemplateContext") -> None:
    for match in NEAR_MISS_RE.finditer(text):
        name = match.group(1)
        inner = match.group(0)[2:-2]
        spaced = inner != inner.strip()
        if name in RESOLVERS and not spaced:
            # Correctly spelled: a real token, left to the leftover check
            # below, which reports it with the right diagnosis.
            continue
        if name.upper() in RESOLVERS:
            raise TemplateError(
                f"{ctx.rel(ctx.tmpl_path)}: {match.group(0)!r} looks like a "
                f"placeholder but does not match one. Placeholder names are "
                f"upper-case with no spaces inside the braces — did you mean "
                f"{{{{{name.upper()}}}}}?"
            )


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
    _assert_no_near_miss_placeholders(rendered, ctx)

    remaining = PLACEHOLDER_RE.findall(rendered)
    if remaining:
        raise TemplateError(
            f"{ctx.rel(ctx.tmpl_path)}: placeholders still unresolved after "
            f"{MAX_PASSES} passes — either a snippet includes itself, or the "
            f"include chain is deeper than {MAX_PASSES}. Still unresolved: "
            f"{', '.join(sorted(set(remaining)))}"
        )
    return rendered


def read_template(tmpl_path: Path) -> str:
    """Read a template, dropping a UTF-8 BOM.

    A BOM sits in front of the opening ``---`` and hides the frontmatter from
    both this renderer and the runtime, so strip it rather than ship a skill
    with no name.
    """
    return tmpl_path.read_text(encoding="utf-8").lstrip("\ufeff")


def build_context(tmpl_path: Path, root: Path) -> TemplateContext:
    """Derive a context from a template path and its frontmatter."""
    text = read_template(tmpl_path)
    frontmatter, _ = split_frontmatter(text)
    skill_dir = tmpl_path.parent
    # A section template lives at <skill>/sections/<name>.md.tmpl, so its
    # skill is the grandparent.  Sections must resolve with their parent
    # skill's context — the name a {{SECTION}} pointer prints has to be the
    # skill the agent can actually load, not the string "sections".
    if skill_dir.name == "sections":
        skill_dir = skill_dir.parent
    # A section template's own `name:` must not win: every {{SECTION}} pointer
    # and {{SKILL_NAME}} it renders has to name the skill the agent can load.
    if tmpl_path.parent.name == "sections":
        name = skill_dir.name
    else:
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
    text = read_template(tmpl_path)
    frontmatter, body = split_frontmatter(text)
    if frontmatter:
        _assert_frontmatter_is_plausible(frontmatter, tmpl_path)
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
    # Render everything before writing anything: a failure on the tenth
    # template must not leave the first nine rewritten on disk.
    rendered: List[tuple] = [
        (tmpl_path, render_template(tmpl_path, root))
        for tmpl_path in discover_templates(root)
    ]
    results: List[RenderResult] = []
    for tmpl_path, content in rendered:
        output_path = output_path_for(tmpl_path)
        try:
            # Universal newlines on purpose: a Windows checkout under
            # core.autocrlf=true holds CRLF on disk, and comparing raw bytes
            # would report permanent false drift there. .gitattributes pins LF
            # for these paths so CRLF never enters the repository itself.
            existing = output_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            existing = None
        changed = existing != content
        if write and changed:
            # newline="\n" pins LF on every platform: a bare open(..., "w") on
            # Windows emits CRLF, which would then be what gets committed.
            with open(output_path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
        results.append(RenderResult(tmpl_path, output_path, content, changed))
    return results


#: Substring identifying a file this renderer produced.
GENERATED_MARKER = "AUTO-GENERATED from"


def find_orphaned_generated(root: Path) -> List[Path]:
    """Generated files whose template no longer exists.

    ``check_templates`` is driven by discovered templates, so deleting a
    ``.tmpl`` quietly un-gates the file it used to produce: nothing compares it
    to anything, while it still carries the "do not edit directly" banner and
    points at a template that is gone. Catch that separately.
    """
    orphans: List[Path] = []
    for path in _walk(root):
        is_generated_name = path.name == "SKILL.md" or (
            path.parent.name == "sections" and path.name.endswith(".md")
        )
        if not is_generated_name:
            continue
        if path.with_name(f"{path.name}.tmpl").is_file():
            continue
        try:
            head = path.read_text(encoding="utf-8", errors="replace")[:4096]
        except OSError:
            continue
        if GENERATED_MARKER in head:
            orphans.append(path)
    return sorted(orphans, key=lambda p: p.as_posix())


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
        orphans = find_orphaned_generated(root)
        if results or orphans:
            for result in results:
                print(f"  out of date: {result.output_path.relative_to(root.parent)}")
            for orphan in orphans:
                print(f"  orphaned:    {orphan.relative_to(root.parent)}")
            if results:
                print("\nRun 'hermes skills render' and commit the result.")
            if orphans:
                print(
                    "\nOrphaned files are marked auto-generated but their template "
                    "is gone. Restore the template, or remove the banner and own "
                    "the file by hand."
                )
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
