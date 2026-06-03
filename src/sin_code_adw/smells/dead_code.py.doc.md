# smells/dead_code.py

Detect unreachable code and unused top-level definitions.

## What it does

Two checks per file:

1. **Unreachable code**: statements after a `return` / `raise` /
   `break` / `continue` in the same block (and not inside a separate
   `if` branch that could still execute).
2. **Unused definitions**: top-level functions/classes not referenced
   from any other file in the project (and not starting with `_`).

## Dependencies

- `report.py` — `DebtReport`

## Public API

| Symbol | Purpose |
|--------|---------|
| `detect(file_path, tree, all_files)` | Return `DebtReport`s for both checks |
| `_find_unreachable(node)` | Lines of unreachable code in a function |
| `_top_level_names(tree)` | Top-level defined names |
| `_names_used_in_project(file_path, all_files)` | Names referenced from other files |

## Known caveats

- "Unused" only catches top-level public names; private (`_*`) and
  `__init__.py` exports are intentionally ignored.
- The cross-file reference scan uses `ast.Name.id` (any reference,
  not just imports), so a name that happens to share a name in
  another file will mask an unused one.
- Unreachable-code detection is naive: it does not understand
  `if False:` or type-guarded code.
