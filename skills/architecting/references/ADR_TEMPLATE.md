# Architecture Decision Record (ADR) Template

Use this template to record architectural decisions that should not be revisited without explicit reasoning.

**When to write an ADR:**

- When rejecting a refactoring for load-bearing reasons
- When establishing a boundary that future explorations should respect
- When a refactoring contradicts a previous decision

---

## Template

```markdown
# ADR-NNNN: [Short Title]

**Date**: YYYY-MM-DD
**Status**: [Accepted | Superseded | Deprecated]

## Problem

[1-2 sentences describing the architectural tension or constraint that prompted this decision]

## Decision

[Plain English explanation of what we decided]

## Rationale

[Why this decision is better than alternatives. Include trade-offs.]

## Implications

[What this means for future refactoring, testing, and new feature work]

## Related Issues

[Link to relevant GitHub issues, tickets, or ADRs]
```

---

## Examples

See [ADR_EXAMPLES.md](ADR_EXAMPLES.md) for concrete examples:

- **ADR-0001**: Auth Domain Boundaries
- **ADR-0002**: Repository Interfaces for Data Access
- **ADR-0003**: No Circular Dependencies Between Domain Modules
- **ADR-0004**: Utils Folder is Forbidden

---

## Tips for Writing ADRs

- **Assume the decision will be revisited in 2 years**: Write clearly enough that future-you understands why this was chosen.
- **Distinguish load-bearing reasons from aesthetic ones**: "Testability" is load-bearing. "I prefer this structure" is not.
- **Record the problem, not the solution**: Future teams might solve it differently.
- **Link to related decisions**: If you're superseding another ADR, say so explicitly.
- **Implications are key**: They tell future explorers what not to do.
