---
name: architecting
description: "Expert architecture review and system design for problems spanning 2+ files or crossing module boundaries — circular dependencies, God modules, or boundary violations (bleed). Not for single-file cleanup (see refactor). Trigger on: 'architecture review', 'restructure across modules', 'too coupled', 'design this system', 'where should this code live', 'God class', 'circular deps', 'dependency mapping', 'domain boundaries'."
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

1. **Explore** (Phase 1):
   - Detect tech stack.
   - Run from `scripts/` (all accept a target dir positional arg, default shown):
     - `python check_locality.py [dir=src]`
     - `python detect_bleed.py [dir=src/domain] [--infra-prefixes express,typeorm,prisma,fs,path,react,mongoose]`
     - `python git_coupling.py [dir=.] [--min-count 3] [--since "6 months ago"] [--top-n 20]`
     - `python detect_hotspots.py [dir=src] [--since "6 months ago"]`
   - **Fallback**: Manually analyze imports, "God" modules (>500 lines/20+ exports), and history.
   - Dispatch `general-purpose` agent using `references/dispatch-template.md`.
2. **Present** (Phase 2): List 3-6 opportunities: [Name], [Files], [Bleed], [Deepening], [Impact], [Risk], [Mermaid]. End by asking: "Which of these candidates interests you most?"
3. **Align**:
   - Interview via `references/DOMAIN_INTERVIEW.md`.
   - Propose Seam: Interface definition, data flow, "Before vs After" Mermaid graph — use `references/INTERFACE_SHAPES.md` for the interface design and `references/SEAMS_BY_EXAMPLE.md` for worked good-vs-bad seam code.
4. **Record ADR**: Write an ADR in `docs/adr/` using `references/ADR_TEMPLATE.md`.
5. **Brief & Handoff**: Write `architecture-brief.json` (see `references/brief-schema.json`). Read `references/MIGRATION_STRATEGIES.md` to pick how to execute the change without a Big Bang rewrite. Handoff to `refactor` or `planning`.

**action: MODE B — DESIGN**

1. **Diagnose**: Identify Core Domain vs Mechanism.
2. **Select Pattern**: Use `references/architecture-patterns.md`.
3. **Stress Test**: Apply Swap Test (If [mechanism] changes, what breaks?).
4. **Record ADR**: Write an ADR in `docs/adr/` using `references/ADR_TEMPLATE.md`.
5. **Scaffold**: Write `architecture-brief.json` (see `references/brief-schema.json`). If integrating with an existing system, read `references/MIGRATION_STRATEGIES.md` for the cutover plan. Run `python scaffold_boundary.py <domain> [pattern=hexagonal] [output_dir=src] [--force]` — `pattern` is one of `hexagonal`, `vertical-slice`, `layered`, `clean-architecture`, `cqrs` (the other patterns in `references/architecture-patterns.md` — event-driven, event sourcing, modular monolith — have no scaffold and must be created manually).

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

- Never use PubSub for direct coupling (use composition).
- Never use `utils/`, `common/`, or `shared/` (use domain-based grouping).
- Never extract base class if composition is possible.
- Never share DB schemas across bounded contexts.
