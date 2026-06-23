---
name: architecting
description: "Conducts architecture reviews and system design. Not for single-file cleanup (see refactor). Trigger on: 'conduct an architecture review', 'restructure across modules', 'design this system', 'map dependencies', 'resolve circular dependencies', 'troubleshoot a God class', 'domain boundaries'."
disable-model-invocation: false
allowed-tools: Bash(python *), Bash(python3 *), AskUserQuestion
---

# architecting

```
Trigger: Review/Design Request
  -- existing code --> Mode A: DIAGNOSE
                          -> 1. Explore (scripts/manual)
                          -> 2. Present opportunities
                          -> 3. Align (interview/seam)
                          -> 4. Record ADR
                          -> Handoff: refactor/planning
  -- new module ----> Mode B: DESIGN
                          -> 1. Identify domain vs mechanism
                          -> 2. Select pattern
                          -> 3. Stress test (swap test)
                          -> 4. Record ADR
                          -> 5. Scaffold (brief/scripts)
```

**trigger:** Architecture review, design request, or structural issues (God modules, circular deps).

**action: Route & Confirm**
Route and confirm via `AskUserQuestion` (or 2-option markdown block) — the tool supplies a free-text "Other" automatically, so don't add one manually:

1. ✅ **Recommended** — [Mode A or B] based on [evidence: imports, size, churn, "existing code" vs "new module"].
2. **Alternative** — [The other mode] + condition under which it would actually apply instead.

**routing:**
| Mode | Focus |
| :--- | :--- |
| **A: DIAGNOSE** | Existing code. God modules, bleed, git coupling, circular deps. |
| **B: DESIGN** | New feature/module. Boundary integrity, reversibility, patterns. |

**action: MODE A — DIAGNOSE**

_CONTEXT LOADING RULE:_ Do NOT load design files (`references/architecture-patterns.md`) during Mode A.

1. **Explore** (Phase 1):
   - Detect tech stack.
   - Run from `scripts/` (all accept a target dir positional arg, default shown):
     - `python check_locality.py [dir=src]`
     - `python detect_bleed.py [dir=src/domain] [--infra-prefixes express,typeorm,prisma,fs,path,react,mongoose]`
     - `python git_coupling.py [dir=.] [--min-count 3] [--since "6 months ago"] [--top-n 20]`
     - `python detect_hotspots.py [dir=src] [--since "6 months ago"]`
   - **Fallback**: Manually analyze imports, "God" modules (>500 lines/20+ exports), and history.
   - Dispatch `general-purpose` agent using [`references/dispatch-template.md`](references/dispatch-template.md). **MANDATORY**: Only load this specific template when dispatching.
2. **Present** (Phase 2): List 3-6 opportunities: [Name], [Files], [Bleed], [Deepening], [Impact], [Risk], [Mermaid]. End by asking: "Which of these candidates interests you most?"
3. **Align**:
   - **MANDATORY - LOAD ON DEMAND**: Read [`references/DOMAIN_INTERVIEW.md`](references/DOMAIN_INTERVIEW.md) only when starting the domain interview.
   - **MANDATORY - READ BEFORE PROPOSING SEAM**: Read [`references/INTERFACE_SHAPES.md`](references/INTERFACE_SHAPES.md) and [`references/SEAMS_BY_EXAMPLE.md`](references/SEAMS_BY_EXAMPLE.md) completely to design the interface boundaries and data flows.
4. **Record ADR**: Write an ADR in `docs/adr/` using [`references/ADR_TEMPLATE.md`](references/ADR_TEMPLATE.md) as a reference.
5. **Brief & Handoff**: Write `architecture-brief.json` conforming to [`references/brief-schema.json`](references/brief-schema.json). Read [`references/MIGRATION_STRATEGIES.md`](references/MIGRATION_STRATEGIES.md) to choose a gradual migration path. Handoff to `refactor` or `planning`.

**action: MODE B — DESIGN**

_CONTEXT LOADING RULE:_ Do NOT load diagnostic templates (`references/dispatch-template.md`, `references/DOMAIN_INTERVIEW.md`, `references/SEAMS_BY_EXAMPLE.md`) during Mode B.

1. **Diagnose**: Identify Core Domain vs Mechanism.
2. **Select Pattern**: Read [`references/architecture-patterns.md`](references/architecture-patterns.md) to choose the optimal architecture pattern.
3. **Stress Test**: Apply Swap Test (If [mechanism] changes, what breaks?).
4. **Record ADR**: Write an ADR in `docs/adr/` using [`references/ADR_TEMPLATE.md`](references/ADR_TEMPLATE.md) as a reference.
5. **Scaffold**: Write `architecture-brief.json` conforming to [`references/brief-schema.json`](references/brief-schema.json). If integrating with an existing system, read [`references/MIGRATION_STRATEGIES.md`](references/MIGRATION_STRATEGIES.md) for the cutover plan. Run `python scaffold_boundary.py <domain> [pattern=hexagonal] [output_dir=src] [--force]` — `pattern` is one of `hexagonal`, `vertical-slice`, `layered`, `clean-architecture`, `cqrs` (the other patterns in `references/architecture-patterns.md` — event-driven, event sourcing, modular monolith — have no scaffold and must be created manually).

**heuristics:**

- **Deletion:** Would removal scatter complexity across callers?
- **Seam:** Is logic testable without I/O (DB/HTTP)?
- **Locality:** Can module be understood without reading 5+ dependents?
- **Stability:** UI/DB depends on Domain; never reverse.
- **Scale:** Single-developer, throwaway, or <1,000 lines? Skip formal patterns (hexagonal, CQRS, etc.) — the boilerplate isn't repaid at this scale. Say so explicitly (YAGNI).

**next skills:**

- `refactor`: To implement localized improvements found during diagnosis.
- `planning`: To create a formal spec for a new architectural design or major seam extraction.
- `multi-agent-development`: To execute the implementation of complex architectural changes.
- `diagnose`: If Mode A exploration surfaces a live bug (not just structural smell) that needs root-cause isolation before the architectural fix.

**constraint:**

- **Never use PubSub for direct coupling** because asynchronous message brokers should model notifications or eventual consistency; using them for synchronous, blocking logic obscures data flow and makes debugging extremely difficult. Use direct composition or interface dependency injection instead.
- **Never use `utils/`, `common/`, or `shared/` directories** because they quickly become catch-all bins that attract unrelated responsibilities, resulting in circular dependencies and broken boundaries. Group code by domain or feature instead.
- **Never extract a base class if composition is possible** because inheritance creates tight compile-time coupling and forces subclasses to inherit unnecessary behaviors, violating the Single Responsibility Principle. Use interface delegation or object composition instead.
- **Never share DB schemas across bounded contexts** because schema-level sharing bypasses domain code, creating hidden database-level coupling that prevents services from scaling, migrating, or deploying independently. Share data via APIs or events instead.

## Additional Resources

### Reference Files

For detailed workflows and templates, consult:

- **[`references/dispatch-template.md`](references/dispatch-template.md)** - Routing parameters for dispatching subagents.
- **[`references/DOMAIN_INTERVIEW.md`](references/DOMAIN_INTERVIEW.md)** - Interview guide for mapping architectural domains.
- **[`references/INTERFACE_SHAPES.md`](references/INTERFACE_SHAPES.md)** - Design guidelines and patterns for interfaces.
- **[`references/SEAMS_BY_EXAMPLE.md`](references/SEAMS_BY_EXAMPLE.md)** - Concrete code examples of good vs bad seams.
- **[`references/ADR_TEMPLATE.md`](references/ADR_TEMPLATE.md)** - Standard template for Architecture Decision Records (ADRs).
- **[`references/brief-schema.json`](references/brief-schema.json)** - Schema for architecture handoff briefs.
- **[`references/MIGRATION_STRATEGIES.md`](references/MIGRATION_STRATEGIES.md)** - Strategies for phased cutover and migrations.
- **[`references/architecture-patterns.md`](references/architecture-patterns.md)** - Cheat sheet for modular/architectural patterns.
