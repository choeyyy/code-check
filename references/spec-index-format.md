# spec-index.md Format

The `spec-index.md` file declares the mapping between rule documents and code files. It lives in the project root directory and is maintained by the user.

---

## Format

A Markdown table with at minimum two columns:

| Column | Description |
|--------|-------------|
| Rule Document | Relative path from project root to the rule/spec document |
| Code Patterns | Glob pattern(s) matching associated code files, relative to project root. Multiple patterns separated by `, ` |

The table header names are flexible — Orchestrator SHALL parse any two-column Markdown table where the first column contains a file path ending in a document extension (`.md`, `.txt`, `.yaml`, etc.) and the second column contains glob patterns.

---

## Path Conventions

- All paths use project root as base (no leading `/` or drive letter)
- Forward slashes for path separators (cross-platform)
- Glob patterns follow standard syntax: `*` (single segment), `**` (recursive), `?` (single char)
- Multiple patterns in one cell separated by `, `

---

## Example Structure

```markdown
| Rule Document | Code Patterns |
|---------------|---------------|
| docs/rules/feature-a.md | src/feature-a/**/*.go, src/shared/feature-a-*.go |
| docs/rules/feature-b.md | src/feature-b/**/*.ts |
| specs/algorithm.md | lib/algo/*.py |
```

---

## First-Run Generation

When `/check-rules` runs and no `spec-index.md` exists:

1. Orchestrator scans the project directory structure
2. Identifies candidate rule documents (files in directories named `docs/`, `specs/`, `rules/`, or files matching `*rule*`, `*spec*` patterns)
3. Attempts to infer code file associations based on naming conventions and directory structure
4. Generates a draft `spec-index.md` and presents it to the user for confirmation
5. User confirms or edits → saved as `spec-index.md`
6. This run ends here (no checking performed on first-run generation)

---

## Validation Rules

Orchestrator SHALL validate the parsed spec-index:

- Each rule document path must resolve to an existing file
- Glob patterns must match at least one existing file (warn if zero matches)
- Duplicate rule document entries are rejected (each document appears once)
