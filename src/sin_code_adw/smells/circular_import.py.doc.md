# smells/circular_import.py

Detect direct A↔B import cycles between two files.

## What it does

A *naive* cycle detector: for each file `F` in the project, look at
every other file `G` that imports a name matching `F`'s module, and
check whether `F` in turn imports `G`. If both are true, report a
circular import.

## Dependencies

- `report.py` — `DebtReport`

## Public API

| Symbol | Purpose |
|--------|---------|
| `detect(file_path, tree, all_files)` | Return `DebtReport`s for circular imports involving `file_path` |
| `_extract_imports(tree)` | AST helper: list of imported module names |
| `_module_name(file_path)` | Dotted module name from path (uses `Path.stem`) |

## Known caveats

- Only direct 2-file cycles (A↔B) are detected, not longer chains
  (A→B→C→A).
- `_module_name` uses just `file_path.stem` (the file name without
  extension), so two files with the same name in different
  directories are treated as the same module.
- The inner loop is O(N²) over project files; a future rewrite should
  pre-build an import index.
