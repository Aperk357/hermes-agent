# Shared skill template assets

Build-time inputs for `hermes skills render`. Nothing here is a skill, and the
agent never loads this directory — the renderer inlines these files into each
skill's generated `SKILL.md`, which is what ships.

```
_shared/
  snippets/<id>.md          prose or code shared by several skills
  preamble/manifest.json    named bundles of snippets ("tiers")
```

## Why this exists

Four of the `skills/github/*` skills each carried their own copy of the same
twenty-line auth-resolution block. The copies had already drifted — one grew a
debug `echo`, another moved the owner/repo extraction to a different section.
A bug fixed in one copy stayed broken in the other three, because nobody edits
four files when they fix one.

Shared text now lives here once. A skill pulls it in with a placeholder, and
CI fails if a generated `SKILL.md` no longer matches its template.

## Using a snippet

In `SKILL.md.tmpl`:

```markdown
### Setup

{{SNIPPET:github-auth-detect}}
```

Or pull in a whole bundle by naming its tier in the frontmatter:

```markdown
---
name: github-issues
preamble-tier: github-api
---

### Setup

{{PREAMBLE}}
```

Then run `hermes skills render`.

## Adding a snippet

1. Write `snippets/<id>.md`. It is inlined verbatim — store exactly the text
   that should appear. Shared *shell* is stored without code fences so each
   skill can drop it into a fence alongside its own lines; shared *prose* is
   stored as-is. Either way the snippet never carries the heading above it.
   That is how four skills share one block and still read in their own voice.
2. Reference it from at least two skills. A snippet used once is just
   indirection; leave that text in the skill.
3. Run `hermes skills render` and commit both the snippet and every
   regenerated `SKILL.md`.

Add a tier only when the same *set* of snippets recurs. One skill wanting a
subset is a reason to call `{{SNIPPET:...}}` directly, not to fork a tier.

See `website/docs/contributing/skill-templates.md` for the full placeholder
reference.
