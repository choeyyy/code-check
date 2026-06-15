# Review Rubric

Not every dimension applies to every change. Use judgment — focus on the lenses most relevant to the diff under review.

---

## Correctness & Safety

### Correctness

- **Edge cases**: empty collections, nil/null/undefined, zero-length strings, boundary values, integer overflow
- **Off-by-one**: loop bounds, slice indices, fence-post errors
- **Error handling**: unchecked returns, swallowed exceptions, missing fallback paths, error propagation that loses context
- **State & race conditions**: shared mutable state, concurrent access without synchronization, order-dependent initialization
- **Idempotency**: repeated calls producing different results when they shouldn't, missing deduplication on retries
- **Concurrency**: deadlocks, livelocks, starvation, incorrect lock granularity, async/await misuse

**Rule**: When flagging a potential bug, TRACE the execution path through the code. Show the specific sequence of calls/states that leads to the failure. Do not just assert "this could be nil" — demonstrate HOW it becomes nil and WHEN that path is reachable.

### Security

- **Input tracing**: for every flagged security issue, show the path from untrusted input to the dangerous sink. No path = no finding.
- **Injection sinks**: SQL, command, template, log injection — trace the tainted data flow
- **Auth gaps**: missing authorization checks on state-changing operations, privilege escalation paths
- **Secrets exposure**: hardcoded credentials, secrets in logs/URLs/error messages, leaked tokens in client-side code
- **TOCTOU**: time-of-check to time-of-use gaps in file operations, permission checks, resource access

### Root Causes vs Symptoms

Flag when the code treats symptoms rather than fixing the underlying problem:

- Guard clauses that mask invariant violations — the nil check hides a broken contract upstream
- Retry/fallback logic that papers over a broken dependency contract instead of fixing it
- Type casts or assertions that silence a modeling error — the types don't fit because the data model is wrong
- Catch-all exception handlers that swallow errors the caller needs to know about

---

## Structural Integrity

- **Boundary discipline**: does each module/function/class own a clear responsibility? Are boundaries crossed without going through the proper interface?
- **Abstraction level mixing**: business logic tangled with I/O, presentation mixed with domain rules, orchestration inlined with computation
- **Coupling**: changes in one module forcing changes in unrelated modules, shared mutable state across boundaries, implicit dependencies
- **Data model fit**: does the data structure match the domain concept it represents? Are there fields that are "sometimes present" without the type reflecting that?
- **Bolted-on vs integrated**: is new functionality grafted onto the side with special cases, or integrated into the existing design?

---

## Verification

- **Test coverage**: are the changed code paths tested? Are the interesting edge cases covered?
- **Behavior vs implementation tests**: do tests verify what the code does (behavior) or how it does it (implementation)? Implementation-coupled tests are fragile.
- **Invariant assertions**: are critical invariants asserted in tests or enforced in code? Could a future change silently violate them?

---

## Complexity Budget

- **Single-callsite abstractions**: a function/class/interface used in exactly one place with no realistic prospect of reuse — just inline it
- **Dead code**: unreachable branches, unused parameters, commented-out code, vestigial imports
- **Over-engineering**: layers of indirection, strategy patterns, factory patterns, or plugin systems for problems that don't yet exist
- **Premature parameterization**: making things configurable before there's a second use case

---

## Code Health

This section covers code-quality dimensions. Quality-focused reviewers should concentrate here.

### Structural Simplification

Look for "code judo" opportunities — ambitious moves that simplify the code structurally rather than adding to its complexity:

- Can a new abstraction or refactored data model eliminate an entire category of special cases?
- Is there a simpler framing of the problem that makes the current approach unnecessary?
- Would changing the order of operations or the ownership of data remove coordination complexity?

### File & Module Size

Files exceeding ~1000 lines are a smell. Flag when a change grows a file past this threshold or adds significant complexity to an already-large file without splitting.

### Spaghetti Growth

Watch for ad-hoc conditionals accumulating in existing code:

- New `if/else` branches added to already-complex functions
- Boolean parameters that fork behavior deep inside a call chain
- Feature flags or type-checks scattered across multiple layers instead of polymorphism or configuration

### Design Cleanliness Over "It Works"

Bias toward cleaning the design, not just accepting working code. "It works" is necessary but not sufficient. Flag:

- Working code that makes the next change harder
- Patterns that will be copy-pasted rather than abstracted
- Temporary hacks without TODO/tracking for removal

### Boring Over Magical

Prefer direct, boring, maintainable code over clever or magical approaches:

- Metaprogramming where a simple function would suffice
- Dynamic dispatch/reflection where static types would be clearer
- DSLs or code generation for problems a loop would solve

### Type & Boundary Cleanliness

- Are types precise? (`string` where an enum would be exact, `any` where a union would be safe)
- Do function signatures match their actual contracts? (accepting broader types than used, returning narrower types than documented)
- Are nullability/optionality boundaries explicit in the type system?

### Canonical Placement & Reuse

- Is the new code in the canonical location for its concern? (utility in domain layer, domain logic in controller, etc.)
- Does it duplicate logic that already exists in a helper or shared module?
- Would extracting a helper make both the new and existing code cleaner?

### Unnecessary Sequential Orchestration

- Are operations serialized that could run concurrently?
- Are there sequential API calls that could be batched?
- Is there synchronous blocking where async would be appropriate?
