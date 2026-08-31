"""``hermes skills render`` — regenerate ``SKILL.md`` files from templates.

A skill that shares prose with other skills is authored as ``SKILL.md.tmpl``
with ``{{PLACEHOLDER}}`` tokens; this command expands them and writes the
``SKILL.md`` that ships. Both files are committed.

``--check`` renders to memory and reports drift without writing, which is the
CI gate: an edit to a generated ``SKILL.md`` that skips the template would
otherwise be silently reverted by the next person who runs the renderer.

See ``tools/skill_template.py`` for the placeholder set.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from hermes_cli.colors import Colors, color


def _default_root() -> Path:
    """The repo's ``skills/`` directory.

    ``hermes_cli`` lives next to ``skills/`` in a source checkout, which is
    the only place templates exist — an installed wheel ships the generated
    files, not the templates.
    """
    return Path(__file__).resolve().parent.parent / "skills"


def render_command(args) -> None:
    """Entry point for ``hermes skills render``."""
    from tools.skill_template import TemplateError, check_templates, render_all

    root_arg: Optional[str] = getattr(args, "root", None)
    root = Path(root_arg).expanduser().resolve() if root_arg else _default_root()

    if not root.is_dir():
        print(color(f"No such directory: {root}", Colors.RED))
        sys.exit(1)

    check_only = bool(getattr(args, "check", False))

    try:
        results = check_templates(root) if check_only else render_all(root)
    except TemplateError as exc:
        print(color(f"Template error: {exc}", Colors.RED))
        sys.exit(1)

    if check_only:
        if results:
            print(
                color(
                    f"{len(results)} generated file(s) out of date:", Colors.RED
                )
            )
            for result in results:
                print(f"  {result.output_path.relative_to(root.parent)}")
            print()
            print("Run 'hermes skills render' and commit the result.")
            sys.exit(1)
        print(color("All generated SKILL.md files are up to date.", Colors.GREEN))
        return

    changed = [r for r in results if r.changed]
    for result in changed:
        print(f"  {color('rendered', Colors.GREEN)} {result.output_path.relative_to(root.parent)}")

    if not results:
        print("No SKILL.md.tmpl templates found.")
        return
    if not changed:
        print(
            color(
                f"{len(results)} template(s) already up to date.", Colors.GREEN
            )
        )
        return
    print()
    print(f"Rendered {len(changed)} of {len(results)} template(s).")
