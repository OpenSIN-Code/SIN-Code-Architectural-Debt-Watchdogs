# smells/long_file.py

Detect files that exceed a line-count threshold.

## What it does

If a file's line count exceeds `thresholds["file_lines"]` (default
500), emits a single `DebtReport` with severity `low` and
`metric="file_lines"`. No additional checks.

## Dependencies

- `report.py` — `DebtReport`

## Public API

| Symbol | Purpose |
|--------|---------|
| `detect(file_path, line_count, thresholds)` | Run the check |

## Known caveats

- Line count is whatever the caller supplies (the analyzer uses
  `len(source.splitlines())`); blank lines and comments are
  counted. A future refinement could weight by logical lines.
- Severity is `low`; tune the `DebtScorer.WEIGHTS` if you want
  long files to count more.
