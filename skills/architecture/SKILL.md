---
name: architecture
description: "Use when a codebase has structural problems (circular deps, God modules, testability issues) or when designing new systems. Trigger on 'architecture review', 'where should this code live', 'too coupled', 'God class', 'design this system'."
disable-model-invocation: false
allowed-tools: Bash(node *), AskUserQuestion
---

# Architecture

## Decision Protocol (how to ask EVERY question)

This skill is conversational: you route, interview, and confirm seams by asking the user. Every question — routing, the domain interview, the Deletion/Swap tests, interface confirmation — MUST be offered as **exactly three options derived from your own analysis**, never generic boilerplate:

1. **✅ Recommended — `<concrete answer>`** — the option your evidence most supports. Append one line of _that evidence_: caller count, the specific imports you saw, churn, the detected framework, file size. This is what makes the skill smart — the recommendation is earned, not guessed.
2. **Also likely — `<the second-most-plausible concrete answer>`** — a real alternative the user might hold, not a strawman. Append one line on the condition under which this becomes the right call.
3. **Something else (your call)** — none fit, or it's a blend of 1 and 2; the user answers in their own words.

Rules:

- Options 1 and 2 are **specific answers**, not "yes / no". When the honest answer space is binary, make option 1 the recommended verdict and option 2 the opposite verdict — each carrying its own evidence.
- **Ground every recommendation.** Cite the file, import, or number that justifies it. If you lack the data to rank the options, say so and tag the pick `(low confidence)` rather than fabricating evidence.
- Ask **one** question at a time and wait for the answer before the next.
- **Rendering:** when the `AskUserQuestion` tool is available, ask through it — put option 1's label first with a `(Recommended)` suffix, option 2 as the alternative, and let the tool's automatic "Other" choice serve as option 3 (the custom answer). When it is not available, present the three options as the numbered markdown block shown above. Candidate selection in Phase 2 is the one exception (it is a 3–6 item menu, handled in that section).

## Before Routing

If the user's message provides no clear intent — a single word, a vague noun, no codebase context — ask one targeted question before selecting a mode, using the **Decision Protocol** above:

> "To get started, which fits best?
>
> 1. ✅ **Recommended — Diagnose existing code** — find and fix structural issues (circular deps, God modules, testability barriers) in a codebase that already exists.
> 2. **Design something new** — decide where new logic should live and how to shape its boundaries from a blank page.
> 3. **Something else** — neither is quite it; tell me what you're after in a sentence."

**Pick the Recommended option from context, don't hard-code it:** mark **Diagnose** as recommended when a codebase is present in the working directory or the user pasted existing code; mark **Design** as recommended when there is no code to look at. State the signal you used in one line (e.g. "recommending Diagnose — I can see a `src/` directory").

Only apply the routing table once you have enough signal to distinguish Mode A from Mode B. Do not silently analyze a nearby codebase just because one exists; confirm it's the intended target first.

## Routing

Read this first — pick one mode and follow only that section.

| Signal                                                                                                                  | Mode                  |
| ----------------------------------------------------------------------------------------------------------------------- | --------------------- |
| Codebase already exists; user wants to find/fix structural problems (coupling, God modules, testability, circular deps) | **MODE A — DIAGNOSE** |
| New feature or module; user asks where logic should live, which pattern to pick, how to design interfaces               | **MODE B — DESIGN**   |

When in doubt: if there's code to look at **and the user has indicated they want a diagnosis**, use Mode A. If there's a blank page, use Mode B.

---

## MODE A — DIAGNOSE: Analyze an Existing Codebase

Surface **deepening opportunities** — places where a shallow module could become a deep one with better leverage, testability, and locality. Explore first, present candidates, then deepen conversationally. Don't design solutions before you've seen the problem.

### Reference Materials

Bundled guides in `references/`:

- **SEAMS_BY_EXAMPLE.md** — 3 detailed examples of good and bad seams (Auth, Payment, Repository patterns) with code
- **INTERFACE_SHAPES.md** — how to design interfaces when deepening modules; shows before/after code
- **ADR_TEMPLATE.md** — lightweight template for recording architectural decisions that shouldn't be revisited
- **DOMAIN_INTERVIEW.md** — structured interview to align terminology before refactoring
- **MIGRATION_STRATEGIES.md** — how to safely execute a seam refactoring in production (Strangler Fig, Branch by Abstraction, Parallel Run, Feature Flag, Expand-Contract). Load when the user asks "how do we actually get there?"

Load these as needed during the 3-phase procedure.

### Core Heuristics

Claude, you already understand SOLID principles and cohesion. Do not regurgitate them. Instead, apply these battle-tested diagnostics for identifying poor boundaries:

- **The Deletion Test**: If removing a module would spread its complexity across N callers, it earns its keep. If callers wouldn't notice, it is shallow and should be collapsed.
- **The Seam Test**: Can business logic be tested without booting a database, making an HTTP call, or touching the filesystem? If no, the seam is drawn at the mechanism layer, not the domain layer.
- **The Locality Test**: Can a maintainer (or AI context window) understand a module without reading its dependents? Circular imports or 5+ file dependency chains for one feature indicate shattered locality.

### Anti-Patterns (What NOT to do)

Architectural refactoring fails when it adds indirection without adding depth. **NEVER** propose the following common AI-flavored refactoring mistakes:

- **NEVER propose an Event Bus/PubSub to solve direct coupling.** It does not decouple logic; it just makes the coupling implicit, destroying code navigation and trace-ability. Use explicit function passing or composition instead.
- **NEVER group files by technical role (e.g., `utils/`, `controllers/`, `types/`).** This destroys locality. Always group by domain concept (e.g., `billing/`, `auth/`). A `utils/` folder is a complexity graveyard.
- **NEVER extract a base class (Inheritance) when Composition is possible.** Inheritance chains hide state and make AI navigation harder. Propose wrapper classes, higher-order functions, or strategy interfaces.
- **NEVER propose variable renaming or formatting as an "architecture" fix.** If the interface boundary doesn't change, the depth hasn't changed.

### Three-Phase Procedure

#### Phase 1: Explore

Walk the codebase using the automated analysis scripts. Scripts gracefully skip inaccessible directories and unreadable files. All scripts support TypeScript, JavaScript, and Python projects — no configuration needed.

- **INTELLIGENT PRE-CHECK**: First inspect the project dependencies (`package.json`, `pyproject.toml`, `requirements.txt`, or `setup.py`) to auto-detect the web framework, ORM, database client, and libraries (e.g., Express, Prisma, Django, FastAPI, SQLAlchemy, Stripe, etc.). Use these identified names in the scripts below instead of guessing.
- **MANDATORY — RUN SCRIPT**: **Locality Check**: Run `node <skill-dir>/scripts/check-locality.mjs [dir]` to find circular dependencies and "God modules" (high fan-out). Example: `node <skill-dir>/scripts/check-locality.mjs src`
- **MANDATORY — RUN SCRIPT**: **Bleed Detection**: Run `node <skill-dir>/scripts/detect-bleed.mjs [domain_dir] [infra_packages]` using the detected dependencies. Examples: `node <skill-dir>/scripts/detect-bleed.mjs src/domain express,prisma,typeorm` — for Python/FastAPI: `node <skill-dir>/scripts/detect-bleed.mjs src/domain sqlalchemy,django,flask,fastapi,celery,requests`
- **RECOMMENDED — RUN SCRIPT**: **Git Coupling**: Run `node <skill-dir>/scripts/git-coupling.mjs [dir]` to find files that always change together in git history — the hidden coupling that import graphs cannot reveal. Example: `node <skill-dir>/scripts/git-coupling.mjs src`. If the output shows pairs with >5 co-changes that have no imports of each other, those are your highest-priority seam candidates.
- **RECOMMENDED — RUN SCRIPT**: **Hotspot Detection**: Run `node <skill-dir>/scripts/detect-hotspots.mjs [dir] [infra_packages]` using the detected dependencies. Example: `node <skill-dir>/scripts/detect-hotspots.mjs src express,prisma,sqlalchemy`
- **PATH & EXISTENCE VERIFICATION**: Before presenting any candidate paths to the user in Phase 2, verify that the files actually exist on the filesystem using read or find tools.

**After scripts complete — spawn the `architecture-scanner` subagent** (`agents/architecture-scanner.md`):

```
Agent(
  description: "Architecture scan of [target_dir]",
  prompt: |
    target_dir: [the directory you scanned]
    locality_output: [paste full stdout of check-locality.mjs here]
    bleed_output: [paste full stdout of detect-bleed.mjs here]
    git_coupling_output: [paste full stdout of git-coupling.mjs here, or "skipped — not a git repo"]
    hotspot_output: [paste full stdout of detect-hotspots.mjs here, or "skipped"]
)
```

The agent reads every flagged file, applies the Deletion/Seam/Locality tests, and returns a `candidates` JSON array ranked by impact. **Use that array as your Phase 2 input** — each element maps directly to the candidate format in Phase 2. Skip manual file reading in the main context when the agent is available.

**If no directory is available** (user pasted inline code without a path):

- Skip the scripts.
- Tell the user: "Running manual analysis on the provided code — if you have a project directory, share the path for automated scanning."
- Proceed with manual friction-signal identification below.

**Manual Exploration** (if scripts don't fit the project structure, or no directory is available):

Look for these friction signals:

1. **Scattered Logic**: A single feature change requires touching 3+ unrelated files.
2. **Infrastructure Bleed**: Domain logic modules import `express.Request`, database entity types, or UI frameworks (mechanism bleeding into policy).
3. **Size/Complexity**: Files exceed ~300 lines where intent is lost in boilerplate.
4. **Tangled Dependencies**: Modules form a web where you can't understand one without reading 5+ others.
5. **Testability Barriers**: You can't unit-test domain logic without mocking infrastructure (database, HTTP, filesystem).

#### Phase 2: Present Candidates

You must constrain yourself. Do NOT write implementation code, typed interface signatures, or seam proposals in Phase 2 — no function bodies, class implementations, interface definitions, or working logic. These belong exclusively in Phase 3 AFTER the user selects a candidate. List **3–6 deepening opportunities**, ordered by impact. Use this exact format:

```markdown
**[Short Name of Opportunity]**

- **Files:** `src/foo.ts`, `src/bar.ts`
- **The Bleed:** [1 sentence: What mechanism is leaking, or what makes this shallow?]
- **The Deepening:** [Plain English: Where the new boundary goes and why it increases leverage.]
- **Impact:** [Locality | Testability | AI-Navigability]
- **Risk:** [LOW | MEDIUM | HIGH] — [1 sentence: callers + test coverage + churn. e.g. "8 callers, no test file, changed 12 times in 90 days."]
```

**Risk scoring guide** (run `node <skill-dir>/scripts/estimate-risk.mjs <root> <file...>` for exact numbers, or estimate manually):

- **HIGH**: >5 callers, OR >2 callers with no tests
- **MEDIUM**: 2–5 callers, OR no tests with active churn
- **LOW**: ≤1 caller and has test coverage
- **No directory available**: Cannot count callers or churn. Use `MEDIUM` for files with multiple infrastructure imports, `LOW` for logic-only files. Label as: `Risk: MEDIUM (estimated — no directory for caller count)`

**Refer to SEAMS_BY_EXAMPLE.md in references/ for 3 real examples of good and bad seams.**

**Example candidate**:

```markdown
**Extract Auth Domain from Scattered Files**

- **Files:** `src/auth.ts`, `src/middleware.ts`, `src/utils.ts`, `src/routes/login.ts`
- **The Bleed:** Password hashing is in utils, JWT generation is in middleware, user lookup is in routes. Each change requires touching 4 files. Testing requires a database.
- **The Deepening:** Consolidate password hashing, token generation, and credential validation into one `auth/` module. Routes and middleware become thin adapters that call auth, not the other way around. Tests can mock the user lookup, so no database needed.
- **Impact:** Locality (auth logic concentrated in one module) | Testability (test password and token logic in isolation) | AI-Navigability (one module to understand instead of four)
- **Risk:** MEDIUM — 3 callers, no dedicated test file, changed 7 times in 90 days.
```

End your response by asking the user to choose, framed as three paths (the candidate menu is the one place options 1 and 2 point at list items rather than free-form answers):

> "Which candidate should we deepen first?
>
> 1. ✅ **Recommended — Candidate 1** — highest impact-to-risk ratio (<one-line evidence: caller count, missing tests, churn>).
> 2. **Also strong — Candidate \<N\>** — <one line on why it's the runner-up: e.g. lower risk, or unblocks the others>.
> 3. **Something else** — a different candidate from the list above, or an angle I haven't surfaced — tell me which and I'll dig in."

**STOP HERE.** Do not proceed to Phase 3 content (seam interfaces, domain interview, migration strategies) until the user has selected a candidate in their next message. Do not append bonus analysis, interface sketches, or migration notes below the question.

#### Phase 3: Domain Interview & Handoff

Once the user picks a candidate, do NOT start writing code immediately.

1. **Align Terminology**: Conduct a brief interview (1 question at a time, see **DOMAIN_INTERVIEW.md** in references/) to establish Canonical Terms and resolve ambiguous concepts. **MANDATORY**: Ask every interview question through the **Decision Protocol** — a Recommended answer grounded in your code analysis, a second plausible answer, and a custom option — so the user can confirm with a single tap instead of composing prose.

2. **Propose the Seam**: Only after the domain language is clear, propose the concrete refactoring — specifically, the _new interface shape_ using the agreed-upon glossary terms. Examples are in **INTERFACE_SHAPES.md** in references/. Show what callers will import and use; don't write implementation yet.

3. **Apply the Deletion Test aloud**, using the Decision Protocol: "If we deleted this module, what happens to its logic?"
   1. ✅ **Recommended — It duplicates across callers** — confirms a deep, high-leverage module worth extracting (you found \<N\> callers that would each re-implement it).
   2. **It just moves elsewhere intact** — the module is shallow; reconsider the extraction or pick a different seam.
   3. **Something else** — partly both, or you see a third outcome; describe it.

4. Wait for user approval before modifying files.

5. **Migration Path:** When the user approves a seam, load **MIGRATION_STRATEGIES.md** from references/ and recommend the appropriate strategy for their situation (Strangler Fig for module replacement, Branch by Abstraction for inserting a new interface, Feature Flag if they need instant rollback). State the strategy name and the first concrete step.

6. **Handoff:** This skill diagnoses and proposes seams — it does not implement them. Once a seam is approved, execute it with the `refactor` skill for a behavior-preserving extraction, or hand the proposed seam to `planning` when the change spans multiple files or phases.

**Required output for Mode A:** A ranked candidate list (3–6 items in Phase 2 format) + a proposed seam interface (typed signatures only, no implementation bodies) for the user-selected candidate. No code changes. No file edits until the user explicitly approves and the appropriate downstream skill is invoked.

### When to Stop

Stop proposing candidates when:

- The remaining friction is purely cosmetic (variable renaming, moving files without changing imports/structure).
- The next refactor crosses a documented ADR boundary not worth reopening.
- The codebase is a throwaway script or proof-of-concept where leverage doesn't matter.

---

## MODE B — DESIGN: Design New Architecture

### Core Philosophy

Architecture is the set of decisions that are hard to change later. Your goal is to maximize **Reversibility** and **Boundary Integrity**. Do not just "clean the code"; design the system to survive the "Churn of Infrastructure" (frameworks, DBs, APIs).

### Four-Step Procedure

#### Step 1: Diagnose

Before proposing a structure, run this diagnosis:

1. **Identify the Core Domain**: What is the "Business Fact" this code exists to manage? Separate this from the "Mechanism" (how it's stored or delivered).
2. **Map the Change Drivers**: Ask, using the Decision Protocol: "If we change the mechanism (swap SQL for NoSQL, Web for CLI), what should break?"
   1. ✅ **Recommended — Only the infrastructure adapters** — the core domain stays untouched; this is the boundary we're aiming for.
   2. **The domain breaks too** — today's design leaks the mechanism into policy, which is exactly the seam to fix.
   3. **Something else** — a different blast radius; describe it.

3. **Boundary Stress Test**: Mentally attempt to move a feature module to a separate repository. If the "seams" are bleeding implementation details, the boundary is wrong.
4. **Select Pattern**:
   - **MANDATORY**: If considering a specific pattern (Layered, Hexagonal, CQRS, etc.), you MUST read `references/architecture-patterns.md` to evaluate its failure modes before recommending.

#### Step 2: Propose

5. **Define the Public Surface**: Design the API (interfaces/types) of the module as if it were a third-party library. Show what callers will import — don't write implementation yet.

#### Step 3: Confirm

6. **Apply the Swap Test**, using the Decision Protocol: "If we swapped [the concrete mechanism — e.g., the database, the payment provider], what changes?"
   1. ✅ **Recommended — Only the infrastructure adapters** — the seam isolates the mechanism cleanly; proceed to scaffold.
   2. **Domain code changes too** — the proposed boundary still leaks; tighten it before scaffolding.
   3. **Something else** — describe what you expect to change, and we'll check the seam against it.

#### Step 4: Scaffold (after user approves the design)

Once the user approves: load **MIGRATION_STRATEGIES.md** and name the appropriate strategy (Strangler Fig, Branch by Abstraction, Feature Flag, etc.) with its first concrete step. Then offer to scaffold the boundary skeleton:

```
node <skill-dir>/scripts/scaffold-boundary.mjs <domain> <pattern> [output-dir]
# pattern: hexagonal | vertical-slice | layered
# Example: node <skill-dir>/scripts/scaffold-boundary.mjs notifications hexagonal src
```

The scaffold generates typed interface stubs (ports, adapters, entities) as a starting point with no implementation. Invoke the `refactor` or `planning` skill for implementation once the user confirms the scaffold structure.

### Expert Principles

- **Prefer Duplication over the Wrong Abstraction**: In early-stage features, allow two modules to have similar code rather than creating a `shared` module that couples them forever.
- **Dependencies Point Toward Stability**: Outer layers (UI, DB) depend on the Domain (Logic), never the reverse. The Domain should not know it's being saved to a database.
- **The "utils" Grave**: `utils`, `common`, and `shared` are where architectural integrity goes to die. If logic is shared, it usually belongs in a named domain concept or a specific infrastructure adapter.
- **Policy vs. Mechanism**: High-level policy (Business Rules) must be physically separated from low-level mechanism (HTTP status codes, SQL queries).

### Boundary Integrity Checks

- **No Framework Leakage**: Business logic should not import framework-specific decorators or types (e.g., `@nestjs/common`, `Express.Request`).
- **Explicit Seams**: Use Interfaces/Abstract classes at boundaries. The implementation (Adapter) lives in the Infrastructure layer; the Interface lives in the Domain layer (Dependency Inversion).
- **Narrow Public API**: Only export the minimum required. Keep internal helpers and state truly private within the module.

### When to Simplify (The YAGNI Threshold)

Do NOT escalate to architecture if:

- The code is a throwaway migration or one-off script.
- The feature has zero external dependencies and very low logic complexity.
- The user is asking for a "Proof of Concept" where speed of validation outweighs long-term maintenance.

### Expert NEVER List

- **NEVER** use "Generic" naming (`Manager`, `Processor`, `Service`) without a domain prefix that explains the _what_.
- **NEVER** allow the database schema to dictate the Domain Model. Use separate types for DB entities and Domain objects.
- **NEVER** use "Hidden Coupling" (Global state, Singletons that hold logic, implicit environment variable dependencies).
- **NEVER** implement CQRS or Event Sourcing just for "scalability" unless you can identify a specific read-model bottleneck that justifies the 5x increase in complexity.
- **NEVER** let a "Utility" module grow past 3 unrelated functions. Split it by domain responsibility immediately.
- **NEVER** propose an internal Event Bus or message broker to decouple modules within the same codebase. This applies in both new designs and refactoring scenarios. It makes coupling implicit and untraceable. Use explicit interface injection or function composition instead.

**Required output for Mode B:** A proposed public surface (interface/type signatures — no implementation bodies), the result of the Swap Test stated explicitly ("If we swapped X, only Y would change"), and a single ADR entry using the template in `references/ADR_TEMPLATE.md`. After user approval, proceed to Step 4 (migration strategy + scaffold offer).
