# False-Positive Patterns

Reviewers and confidence judges MUST NOT report findings that match these patterns. If a finding falls into any of these categories, drop it silently.

---

## 1. Pre-existing Issues

Problems that exist in unchanged code and were not introduced by this diff.

Even if the changed code calls into a buggy pre-existing function, that is not a finding against this change unless the change made it worse.

**Examples:**
- A function the diff calls has a bug, but the function itself was not modified → not a finding
- An existing API endpoint lacks rate limiting; the diff adds a new route using the same pattern → not a finding against the new route

## 2. Issues a Linter, Typechecker, or Compiler Would Catch

Assume CI runs linters, type checks, and compilation. Do not report:

- Missing imports or unused imports
- Type errors that the compiler/typechecker would reject
- Formatting, whitespace, or indentation issues
- Syntax errors

**Examples:**
- "Missing import for `useState`" — the build will fail and the author will see it
- "Inconsistent indentation on line 47" — the formatter handles this

## 3. Pedantic Nitpicks a Senior Engineer Wouldn't Flag

Minor style preferences that have no impact on correctness, readability, or maintainability.

**Examples:**
- "Prefer `const` over `let` here" when the variable is never reassigned (a linter catches this)
- "Consider renaming `data` to `userData`" when the scope is 3 lines and the meaning is obvious from context

## 4. General Quality Issues Not Called Out in REVIEW.md

Vague quality suggestions that aren't tied to a concrete problem in the diff.

**Examples:**
- "Consider adding more unit tests" when the project has no testing requirement and the change is a config update
- "This module could benefit from better documentation" without a specific confusing area

## 5. Issues on Unchanged Lines

Even if adjacent to the change, if the line itself was not modified, it is out of scope.

**Examples:**
- The diff adds a new function below an existing function that has a bug → the existing function's bug is not a finding
- A variable declared 20 lines above the diff has a misleading name → not a finding

## 6. Intentional Behavior Changes

If the stated purpose of the change is to modify behavior, do not flag the modified behavior as a bug. Flag it only if the implementation doesn't match the stated intent.

**Examples:**
- A PR titled "Change timeout from 30s to 60s" — do not flag "timeout was changed from 30s to 60s"
- A commit message says "Remove email validation for draft saves" — do not flag "email is not validated on save"

## 7. Lint-Silenced Issues

Code with explicit `// nolint`, `// eslint-disable`, `# noqa`, `@SuppressWarnings`, or equivalent suppress/ignore comments. The author has deliberately acknowledged the issue.

**Examples:**
- `// eslint-disable-next-line no-unused-vars` on a variable used only in a debug path
- `# nosec` on a hash function used for non-security checksumming

## 8. "I Would Have Done It Differently"

Preference-based alternatives that are not objectively better. If you can't articulate a concrete problem the current code causes, don't flag it.

**Examples:**
- "I would use a `switch` instead of `if/else`" when both are equally readable at this size
- "I prefer extracting this into a separate file" when the current placement is consistent with the codebase

## 9. Hypothetical Issues Without Evidence of Reachability

"What if someone passes null?" is not a finding unless you can trace a realistic code path where null actually reaches that point.

**Examples:**
- "This function doesn't handle `undefined` input" — but all callers validate before calling, and the function is not exported
- "What if the array is empty?" — but the array is populated from a required database field with a NOT NULL constraint

## 10. Issues Consistent With Existing Codebase Patterns

If the code follows an established pattern in the codebase, do not flag the pattern in this review. Codebase-wide pattern changes belong in a separate refactoring discussion, not a review of an individual change.

**Examples:**
- The codebase uses callbacks everywhere; this change adds another callback-based function → "use promises instead" is not a finding
- Error codes are returned as magic numbers throughout the codebase; this change follows the same convention → not a finding
