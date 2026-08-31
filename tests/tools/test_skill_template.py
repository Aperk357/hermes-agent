"""Tests for the SKILL.md template renderer (``tools.skill_template``).

These assert the contract the renderer offers skill authors — what a
placeholder expands to, and which mistakes fail the build loudly rather than
shipping a half-rendered SKILL.md — plus the freshness invariant that keeps
the committed files honest.
"""

import json
from pathlib import Path

import pytest

from tools.skill_template import (
    GENERATED_HEADER,
    MAX_PASSES,
    TemplateError,
    build_context,
    check_templates,
    discover_templates,
    render_all,
    render_template,
    render_text,
    split_frontmatter,
)


# ── Fixtures ───────────────────────────────────────────────────────────────


def write(path: Path, text: str) -> Path:
    """Write *text* to *path* with LF endings, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


@pytest.fixture
def skills_root(tmp_path: Path) -> Path:
    """A miniature skills/ tree with one shared snippet and one tier."""
    root = tmp_path / "skills"
    write(root / "_shared" / "snippets" / "greeting.md", "Hello from the snippet.\n")
    write(root / "_shared" / "snippets" / "farewell.md", "Goodbye.\n")
    write(
        root / "_shared" / "preamble" / "manifest.json",
        json.dumps({"tiers": {"basic": ["greeting", "farewell"]}}),
    )
    return root


def make_skill(root: Path, name: str, body: str, frontmatter: str = "") -> Path:
    """Create ``<root>/cat/<name>/SKILL.md.tmpl`` and return its path."""
    fm = f"---\nname: {name}\n{frontmatter}---\n"
    return write(root / "cat" / name / "SKILL.md.tmpl", f"{fm}\n{body}")


# ── Frontmatter ────────────────────────────────────────────────────────────


class TestSplitFrontmatter:
    def test_splits_fenced_block_from_body(self):
        fm, body = split_frontmatter("---\nname: a\n---\n\n# Title\n")
        assert fm == "---\nname: a\n---\n"
        assert body == "\n# Title\n"

    def test_no_frontmatter_returns_whole_text_as_body(self):
        fm, body = split_frontmatter("# Title\n")
        assert fm == ""
        assert body == "# Title\n"

    def test_unterminated_frontmatter_is_not_treated_as_frontmatter(self):
        # A stray leading '---' must not swallow the document.
        fm, body = split_frontmatter("---\nname: a\n# Title\n")
        assert fm == ""
        assert body == "---\nname: a\n# Title\n"


# ── Snippets ───────────────────────────────────────────────────────────────


class TestSnippet:
    def test_inlines_shared_text(self, skills_root):
        tmpl = make_skill(skills_root, "s", "Intro.\n\n{{SNIPPET:greeting}}\n")
        out = render_template(tmpl, skills_root)
        assert "Hello from the snippet." in out
        assert "{{" not in out

    def test_trailing_newlines_are_trimmed_so_callers_control_spacing(
        self, skills_root
    ):
        # A snippet dropped inside a fenced block must not inject a blank line
        # the author did not write.
        write(skills_root / "_shared" / "snippets" / "code.md", "echo hi\n\n\n")
        tmpl = make_skill(skills_root, "s", "```bash\n{{SNIPPET:code}}\necho bye\n```\n")
        out = render_template(tmpl, skills_root)
        assert "```bash\necho hi\necho bye\n```" in out

    def test_same_snippet_twice_expands_both_times(self, skills_root):
        tmpl = make_skill(skills_root, "s", "{{SNIPPET:greeting}}\n\n{{SNIPPET:greeting}}\n")
        out = render_template(tmpl, skills_root)
        assert out.count("Hello from the snippet.") == 2

    def test_unknown_snippet_fails_and_lists_what_exists(self, skills_root):
        tmpl = make_skill(skills_root, "s", "{{SNIPPET:nope}}\n")
        with pytest.raises(TemplateError) as exc:
            render_template(tmpl, skills_root)
        assert "nope" in str(exc.value)
        assert "greeting" in str(exc.value)

    def test_snippet_id_cannot_escape_the_snippets_directory(self, skills_root):
        tmpl = make_skill(skills_root, "s", "{{SNIPPET:../../etc/passwd}}\n")
        with pytest.raises(TemplateError, match="invalid snippet id"):
            render_template(tmpl, skills_root)

    def test_bare_snippet_without_id_is_rejected(self, skills_root):
        tmpl = make_skill(skills_root, "s", "{{SNIPPET}}\n")
        with pytest.raises(TemplateError, match="needs an id"):
            render_template(tmpl, skills_root)


# ── Preamble tiers ─────────────────────────────────────────────────────────


class TestPreamble:
    def test_tier_expands_to_its_snippets_in_order(self, skills_root):
        tmpl = make_skill(
            skills_root, "s", "{{PREAMBLE}}\n", frontmatter="preamble-tier: basic\n"
        )
        out = render_template(tmpl, skills_root)
        assert out.index("Hello from the snippet.") < out.index("Goodbye.")

    def test_tier_can_be_named_inline(self, skills_root):
        tmpl = make_skill(skills_root, "s", "{{PREAMBLE:basic}}\n")
        assert "Goodbye." in render_template(tmpl, skills_root)

    def test_preamble_without_a_tier_is_rejected(self, skills_root):
        tmpl = make_skill(skills_root, "s", "{{PREAMBLE}}\n")
        with pytest.raises(TemplateError, match="needs a tier"):
            render_template(tmpl, skills_root)

    def test_unknown_tier_names_the_known_ones(self, skills_root):
        tmpl = make_skill(
            skills_root, "s", "{{PREAMBLE}}\n", frontmatter="preamble-tier: ghost\n"
        )
        with pytest.raises(TemplateError) as exc:
            render_template(tmpl, skills_root)
        assert "ghost" in str(exc.value)
        assert "basic" in str(exc.value)

    def test_build_only_keys_are_stripped_from_the_shipped_file(self, skills_root):
        tmpl = make_skill(
            skills_root, "s", "{{PREAMBLE}}\n", frontmatter="preamble-tier: basic\n"
        )
        out = render_template(tmpl, skills_root)
        # The runtime never reads preamble-tier; leaving it in would imply it does.
        assert "preamble-tier" not in out
        assert "name: s" in out


# ── Sections ───────────────────────────────────────────────────────────────


def add_sections(skill_dir: Path, entries) -> None:
    write(
        skill_dir / "sections" / "manifest.json",
        json.dumps({"skill": skill_dir.name, "sections": entries}),
    )


class TestSections:
    def test_pointer_names_the_skill_and_file_the_agent_must_load(self, skills_root):
        tmpl = make_skill(skills_root, "carved", "{{SECTION:triage}}\n")
        add_sections(
            tmpl.parent,
            [{"id": "triage", "file": "triage.md", "trigger": "starting triage"}],
        )
        out = render_template(tmpl, skills_root)
        assert 'skill_view("carved", file_path="sections/triage.md")' in out
        assert "starting triage" in out
        assert "STOP" in out

    def test_pointer_does_not_inline_the_section_body(self, skills_root):
        # The whole point of a carve: the body stays out of the prompt.
        tmpl = make_skill(skills_root, "carved", "{{SECTION:triage}}\n")
        add_sections(
            tmpl.parent,
            [{"id": "triage", "file": "triage.md", "trigger": "starting triage"}],
        )
        write(tmpl.parent / "sections" / "triage.md", "SECRET BODY TEXT\n")
        assert "SECRET BODY TEXT" not in render_template(tmpl, skills_root)

    def test_index_renders_a_row_per_section(self, skills_root):
        tmpl = make_skill(skills_root, "carved", "{{SECTION_INDEX}}\n")
        add_sections(
            tmpl.parent,
            [
                {"id": "a", "file": "a.md", "trigger": "doing a"},
                {"id": "b", "file": "b.md", "trigger": "doing b"},
            ],
        )
        out = render_template(tmpl, skills_root)
        assert "| doing a | `sections/a.md` |" in out
        assert "| doing b | `sections/b.md` |" in out

    def test_unknown_section_id_names_the_known_ones(self, skills_root):
        tmpl = make_skill(skills_root, "carved", "{{SECTION:ghost}}\n")
        add_sections(
            tmpl.parent, [{"id": "real", "file": "real.md", "trigger": "later"}]
        )
        with pytest.raises(TemplateError) as exc:
            render_template(tmpl, skills_root)
        assert "ghost" in str(exc.value)
        assert "real" in str(exc.value)

    def test_manifest_entry_missing_a_field_is_rejected(self, skills_root):
        tmpl = make_skill(skills_root, "carved", "{{SECTION:a}}\n")
        add_sections(tmpl.parent, [{"id": "a", "file": "a.md"}])  # no trigger
        with pytest.raises(TemplateError, match="trigger"):
            render_template(tmpl, skills_root)

    def test_declared_section_nothing_points_at_is_rejected(self, skills_root):
        # A section the skill never references is a step that silently stops
        # happening — the agent is never told to load it.
        tmpl = make_skill(skills_root, "carved", "{{SECTION:used}}\n")
        add_sections(
            tmpl.parent,
            [
                {"id": "used", "file": "used.md", "trigger": "always"},
                {"id": "stranded", "file": "stranded.md", "trigger": "never"},
            ],
        )
        with pytest.raises(TemplateError) as exc:
            render_template(tmpl, skills_root)
        message = str(exc.value)
        assert "stranded" in message
        # The referenced one is not the problem and must not be reported.
        assert "declares stranded" in message

    def test_section_index_alone_counts_as_pointing_at_every_section(
        self, skills_root
    ):
        # The index table names them all, so a skill that ships only an index
        # has still routed the agent to each section.
        tmpl = make_skill(skills_root, "carved", "{{SECTION_INDEX}}\n")
        add_sections(
            tmpl.parent,
            [
                {"id": "a", "file": "a.md", "trigger": "doing a"},
                {"id": "b", "file": "b.md", "trigger": "doing b"},
            ],
        )
        assert "sections/b.md" in render_template(tmpl, skills_root)

    def test_orphan_check_does_not_apply_to_section_templates(self, skills_root):
        # A section renders one step; it is not expected to point at siblings.
        make_skill(skills_root, "carved", "{{SECTION:a}}\n")
        skill_dir = skills_root / "cat" / "carved"
        add_sections(skill_dir, [{"id": "a", "file": "a.md", "trigger": "doing a"}])
        section_tmpl = write(skill_dir / "sections" / "a.md.tmpl", "Step body.\n")
        assert "Step body." in render_template(section_tmpl, skills_root)

    def test_section_without_a_manifest_is_rejected(self, skills_root):
        tmpl = make_skill(skills_root, "carved", "{{SECTION:a}}\n")
        with pytest.raises(TemplateError, match="manifest.json is missing"):
            render_template(tmpl, skills_root)

    def test_section_template_resolves_with_its_parent_skills_name(self, skills_root):
        # A section file is rendered separately; it must still print the
        # parent skill's name, not the string "sections".
        make_skill(skills_root, "carved", "body\n")
        section_tmpl = write(
            skills_root / "cat" / "carved" / "sections" / "step.md.tmpl",
            "Owned by {{SKILL_NAME}}.\n",
        )
        ctx = build_context(section_tmpl, skills_root)
        assert ctx.skill_name == "carved"
        assert "Owned by carved." in render_template(section_tmpl, skills_root)


# ── Composition ────────────────────────────────────────────────────────────


class TestInvokeSkill:
    def test_emits_a_loadable_reference_with_skips(self, skills_root):
        tmpl = make_skill(skills_root, "s", "{{INVOKE_SKILL:other}}\n")
        out = render_template(tmpl, skills_root)
        assert 'skill_view("other")' in out
        assert "- Setup" in out

    def test_extra_skips_are_appended(self, skills_root):
        tmpl = make_skill(skills_root, "s", "{{INVOKE_SKILL:other:skip=Voice,Tone}}\n")
        out = render_template(tmpl, skills_root)
        assert "- Voice" in out
        assert "- Tone" in out
        assert "- Setup" in out

    def test_missing_target_is_rejected(self, skills_root):
        tmpl = make_skill(skills_root, "s", "{{INVOKE_SKILL}}\n")
        with pytest.raises(TemplateError, match="needs a skill"):
            render_template(tmpl, skills_root)


# ── Resolution rules ───────────────────────────────────────────────────────


class TestResolution:
    def test_nested_placeholders_are_expanded(self, skills_root):
        # A tier expands to snippets; a snippet may itself pull in another.
        write(
            skills_root / "_shared" / "snippets" / "outer.md",
            "outer -> {{SNIPPET:greeting}}\n",
        )
        tmpl = make_skill(skills_root, "s", "{{SNIPPET:outer}}\n")
        assert "outer -> Hello from the snippet." in render_template(tmpl, skills_root)

    def test_deep_nesting_that_does_resolve_is_accepted(self, skills_root):
        # Running out of passes is not itself the failure — holding an
        # unresolved token is. A chain that fully expands must be allowed.
        depth = MAX_PASSES - 1
        for i in range(depth):
            nxt = f"{{{{SNIPPET:link{i + 1}}}}}" if i + 1 < depth else "bottom"
            write(skills_root / "_shared" / "snippets" / f"link{i}.md", f"{i} {nxt}\n")
        tmpl = make_skill(skills_root, "s", "{{SNIPPET:link0}}\n")
        assert "bottom" in render_template(tmpl, skills_root)

    def test_self_referential_snippet_fails_instead_of_hanging(self, skills_root):
        write(
            skills_root / "_shared" / "snippets" / "loop.md", "loop {{SNIPPET:loop}}\n"
        )
        tmpl = make_skill(skills_root, "s", "{{SNIPPET:loop}}\n")
        with pytest.raises(TemplateError, match=f"after {MAX_PASSES} passes"):
            render_template(tmpl, skills_root)

    def test_unknown_placeholder_is_rejected(self, skills_root):
        tmpl = make_skill(skills_root, "s", "{{NOT_A_THING}}\n")
        with pytest.raises(TemplateError, match="unknown placeholder"):
            render_template(tmpl, skills_root)

    def test_shell_expansions_are_not_mistaken_for_placeholders(self, skills_root):
        # Skills are full of ${VAR} and $(cmd); only {{SCREAMING_SNAKE}} is ours.
        body = '```bash\nX=${HOME:-/tmp}\nY=$(date) # {{ not a token }}\n```\n'
        tmpl = make_skill(skills_root, "s", body)
        out = render_template(tmpl, skills_root)
        assert "${HOME:-/tmp}" in out
        assert "{{ not a token }}" in out

    def test_placeholders_resolve_inside_frontmatter(self, skills_root):
        tmpl = make_skill(
            skills_root, "s", "body\n", frontmatter="description: For {{SKILL_NAME}}.\n"
        )
        assert "description: For s." in render_template(tmpl, skills_root)


# ── Output shape ───────────────────────────────────────────────────────────


class TestOutput:
    def test_generated_header_sits_under_the_frontmatter(self, skills_root):
        tmpl = make_skill(skills_root, "s", "# Title\n")
        out = render_template(tmpl, skills_root)
        fm, body = split_frontmatter(out)
        assert fm.startswith("---\n")
        assert body.startswith(GENERATED_HEADER.format(source="SKILL.md.tmpl"))
        # Frontmatter must still parse: the header goes after it, never inside.
        assert "AUTO-GENERATED" not in fm

    def test_output_ends_with_exactly_one_newline(self, skills_root):
        tmpl = make_skill(skills_root, "s", "# Title")
        out = render_template(tmpl, skills_root)
        assert out.endswith("\n")
        assert not out.endswith("\n\n")

    def test_template_without_frontmatter_still_gets_a_header(self, skills_root):
        tmpl = write(skills_root / "cat" / "bare" / "SKILL.md.tmpl", "# Bare\n")
        out = render_template(tmpl, skills_root)
        assert "AUTO-GENERATED" in out
        assert "# Bare" in out


# ── Discovery and freshness ────────────────────────────────────────────────


class TestRenderAll:
    def test_discovers_skill_and_section_templates_only(self, skills_root):
        make_skill(skills_root, "a", "body\n")
        write(skills_root / "cat" / "a" / "sections" / "one.md.tmpl", "section\n")
        write(skills_root / "cat" / "a" / "references" / "notes.md", "not a template\n")
        found = {p.name for p in discover_templates(skills_root)}
        assert found == {"SKILL.md.tmpl", "one.md.tmpl"}

    def test_discovery_is_sorted_so_ci_does_not_flap(self, skills_root):
        for name in ("z", "a", "m"):
            make_skill(skills_root, name, "body\n")
        paths = [p.as_posix() for p in discover_templates(skills_root)]
        assert paths == sorted(paths)

    def test_ignores_vendored_directories(self, skills_root):
        write(skills_root / "node_modules" / "pkg" / "SKILL.md.tmpl", "---\nname: x\n---\n")
        assert discover_templates(skills_root) == []

    def test_writes_the_generated_file_next_to_its_template(self, skills_root):
        tmpl = make_skill(skills_root, "a", "# A\n")
        results = render_all(skills_root)
        assert [r.output_path for r in results] == [tmpl.parent / "SKILL.md"]
        assert "# A" in (tmpl.parent / "SKILL.md").read_text(encoding="utf-8")

    def test_second_render_reports_no_change(self, skills_root):
        make_skill(skills_root, "a", "# A\n")
        render_all(skills_root)
        assert all(not r.changed for r in render_all(skills_root))

    def test_check_reports_drift_without_writing(self, skills_root):
        tmpl = make_skill(skills_root, "a", "# A\n")
        render_all(skills_root)
        generated = tmpl.parent / "SKILL.md"
        write(generated, "# hand-edited, bypassing the template\n")

        stale = check_templates(skills_root)

        assert [r.output_path for r in stale] == [generated]
        # --check must not repair the file; that is the author's job.
        assert "hand-edited" in generated.read_text(encoding="utf-8")

    def test_check_passes_once_regenerated(self, skills_root):
        make_skill(skills_root, "a", "# A\n")
        render_all(skills_root)
        assert check_templates(skills_root) == []

    def test_render_text_is_usable_standalone(self, skills_root):
        tmpl = make_skill(skills_root, "a", "body\n")
        ctx = build_context(tmpl, skills_root)
        assert render_text("say {{SNIPPET:farewell}}", ctx) == "say Goodbye."


# ── The committed tree ─────────────────────────────────────────────────────

REPO_SKILLS = Path(__file__).resolve().parents[2] / "skills"


def snippet_usage_counts(root: Path) -> dict:
    """Map each shared snippet id -> how many skill templates pull it in.

    Counts both reference styles: a direct ``{{SNIPPET:id}}`` and membership in
    the tier a template names via ``preamble-tier`` + ``{{PREAMBLE}}``.
    """
    tiers = json.loads(
        (root / "_shared" / "preamble" / "manifest.json").read_text(encoding="utf-8")
    )["tiers"]
    counts = {p.stem: 0 for p in (root / "_shared" / "snippets").glob("*.md")}

    for tmpl in discover_templates(root):
        text = tmpl.read_text(encoding="utf-8")
        used = {sid for sid in counts if f"{{{{SNIPPET:{sid}}}}}" in text}
        if "{{PREAMBLE" in text:
            tier = build_context(tmpl, root).preamble_tier
            used.update(tiers.get(tier, []))
        for sid in used:
            counts[sid] += 1
    return counts


class TestRepoSkills:
    """Guards on the real skills/ tree — the CI gate's in-process twin."""

    def test_every_generated_skill_md_matches_its_template(self):
        stale = check_templates(REPO_SKILLS)
        assert not stale, (
            "Generated SKILL.md files are out of date: "
            + ", ".join(str(r.output_path) for r in stale)
            + ". Run 'hermes skills render'."
        )

    def test_templated_skills_carry_the_generated_header(self):
        for tmpl in discover_templates(REPO_SKILLS):
            generated = tmpl.with_suffix("")
            assert generated.is_file(), f"{tmpl} has no generated output"
            assert "AUTO-GENERATED" in generated.read_text(encoding="utf-8")

    def test_shared_snippets_are_used_by_more_than_one_skill(self):
        """A snippet used once is indirection, not deduplication."""
        assert snippet_usage_counts(REPO_SKILLS), "expected some templated skills"
        for sid, count in sorted(snippet_usage_counts(REPO_SKILLS).items()):
            assert count >= 2, (
                f"snippet '{sid}' is referenced by {count} skill(s) — a snippet "
                "used once is indirection, so inline it instead"
            )

    def test_snippet_usage_counts_sees_both_reference_styles(self):
        # Guards the helper above: the four GitHub skills reach these snippets
        # two different ways (two via {{PREAMBLE}}, two via {{SNIPPET:...}}),
        # so a counter that understood only one style would still pass the
        # >= 2 assertion while missing half the usages.
        counts = snippet_usage_counts(REPO_SKILLS)
        assert counts["github-auth-detect"] == 4
        assert counts["github-owner-repo"] == 4
