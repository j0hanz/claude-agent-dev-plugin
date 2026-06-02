---
name: brainstorming
description: "Structured requirements discovery before implementation. Trigger on 'let's build', 'add a feature', 'we need a new', 'I want to implement', 'add X to', 'create a Y', ambiguous design, or unclear terminology — even when the user says 'just build it'. Proactively offer before any implementation begins. Prevents rework by catching problems early."
---

## Routing

| Condition                                                                                                   | Action                                      |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| "let's build X", "add a feature", "we need a new Y", "I want to implement Z", any new component or behavior | **Run** — even if user says "just build it" |
| Domain terminology ambiguous, foundational assumptions unvalidated                                          | **Run**                                     |
| User unsure how to approach a design problem                                                                | **Run**                                     |
| Bug fix with clearly defined problem and root cause                                                         | **Skip**                                    |
| Pure refactor with no behavior change                                                                       | **Skip**                                    |
| Documentation-only update                                                                                   | **Skip**                                    |
| Design already explicitly approved, implementation is the next step                                         | **Skip**                                    |

# Brainstorming

## Conversation Rhythm

**rhythm:** one question at a time — wait for each answer before asking the next.

**Fast Track (resistant users):**
If the user declines brainstorming or insists on "just coding" after your first Phase 1 attempt:

1. Acknowledge the request for speed.
2. Spawn `codebase-scanner`.
3. Present a **single, grounded proposal** based on the scanner's report.
4. If approved, skip to Phase 5.

## Do Not

- **Ask leading questions** — let the user define the domain.
- **Assume two terms mean the same thing** — inventory ALL contexts before drilling into any one.
- **Capture implementation details** during discovery — capture WHAT a concept IS, not HOW it is built.
- **Write code or scaffolding before design is approved.**

## Red Flags

| Thought                              | Reality                                                   |
| ------------------------------------ | --------------------------------------------------------- |
| "The requirements are obvious"       | Assumptions cause rework. Clarify anyway.                 |
| "I'll start simple and iterate"      | Design approval comes first — see the gate below.         |
| "We can figure out edge cases later" | Edge cases belong in the spec, not the debugger.          |
| "This is too small to need design"   | Small features accumulate into large regrets.             |
| "The user said just build it"        | Offer a quick brainstorm first. User can decline.         |
| "Everyone knows what X means"        | Ambiguous terms corrupt specs. Capture them in Phase 2.   |
| "I'll define terms after we design"  | Terminology conflicts surface in specs at the worst time. |

**Design approval gate:** Do not write any code, scaffolding, or invoke any implementation skill until the user has explicitly approved a design in Phase 4.

## Dispatch Agents

Spawn via Agent tool. Do not redo their work manually.

| Agent              | File                         | When to spawn                                  |
| ------------------ | ---------------------------- | ---------------------------------------------- |
| `codebase-scanner` | `agents/codebase-scanner.md` | Start of Phase 1, before asking any questions  |
| `design-proposer`  | `agents/design-proposer.md`  | Start of Phase 4, before presenting approaches |

## Phase 1: Discovery (Read Before Asking)

Spawn `codebase-scanner` — pass the feature description exactly as stated. Wait for the Codebase Context Report.

Summarize your understanding in one paragraph, drawing from the report: what was found, what constraints exist, what Key Unknowns were flagged, and what you don't know yet. Ask the user to confirm.

**scope-check:** If discovery reveals the feature is >4x larger than expected, suggest splitting into phases.

**domain-trigger:** If steps 1–5 reveal ambiguous or conflicting terminology, run Phase 2 before continuing.

### Phase 1 Example

**User says:** "We need to add search to our product."

**Your understanding statement:**
"I understand you need full-text search for your product so users can find data faster. Currently, I don't know: if you want real-time indexing, if search needs to be fuzzy, or if there are performance constraints. Do I have this right?"

## Phase 2: Domain Clarity (When Terminology is Ambiguous)

**Skip** if domain terminology is clear and consistent throughout code, docs, and user language.

**Definition is clear when:**

- User can explain WHAT the concept IS (not just what it does)
- User can explain how it differs from similar terms (Account vs Organization vs Customer)
- User can point to where it appears in code/docs/conversations

**Not clear if:** Definition relies on "everyone knows what this means" or varies by team.

**Invoke when:** same term has multiple meanings, team and code use different names for the same concept, user asks "what do we call X?", or docs are inconsistent.

**Fundamental disagreement:** If domain experts disagree on WHAT we're building, document both positions and escalate before proceeding to Phase 4.

For each ambiguous term:

1. Ask the user to define it in their own words — never lead with a definition.
2. Ask where it appears: code, docs, team discussions?
3. If two teams have valid reasons for different terms: document both with a boundary — don't force one side to abandon their mental model.

**3-turn rule:** If 3 questions fail to define a term clearly, mark it TBD with an owner and move on.

**Output format for captured terms:**

```
[Canonical Term]: [Definition]. Aliases: [alias1, alias2]
(TBD: [Question] — Owner: [Role/Person])
Conflict resolution: [how overlapping usages were resolved]
```

Offer to write findings to `glossary.md` or `CONTEXT.md` at Phase 5 transition.

## Phase 3: Expert Clarification (Surface the Unsaid)

Pick 1–2 techniques based on conversation signals. Do not run all five as a script.

| Situation                                              | Use This            | Reason                                      |
| ------------------------------------------------------ | ------------------- | ------------------------------------------- |
| User says "just build it" or requirements seem obvious | **Why (Five Whys)** | Uncovers hidden motivation                  |
| Large scope or complex dependencies                    | **Premortem**       | Surfaces organizational/technical risks     |
| Success criteria vague ("just make it fast")           | **Success Logic**   | Clarifies acceptance criteria               |
| Feature creep risk or unclear boundaries               | **Anti-Scope**      | Defines what we're explicitly NOT building  |
| Feature handles sensitive data or user permissions     | **Trust Breach**    | Identifies security/privacy vulnerabilities |

**Depth check:** After 1–2 techniques, ask: "Are there other risks or unknowns that could derail this?"

- Yes → apply one more technique, then proceed regardless
- No → document TBD items and proceed to Phase 4

**Hard limit: 4 questions total within Phase 3.** Unresolved questions become TBD items with an owner.

1. **The "Why" (Five Whys):** "Why is this needed _now_? What fails if we don't do this?"
2. **The Premortem:** "Imagine we've implemented this and it's a disaster. What's the most likely thing that went wrong?"
3. **Success Logic:** "How will we know this is a success without using the word 'functional'? What behavior change should we see?"
4. **The "Anti-Scope":** "What's a related feature that we are _strictly_ choosing NOT to build today?"
5. **The Trust Breach:** "If a malicious actor wanted to abuse this feature to access unauthorized data, what would be their easiest path?"

## Phase 4: Design Proposal

Compress the Codebase Context Report before spawning:

```bash
python <skill-dir>/scripts/compress_report.py <path-to-report.json>
# or pipe directly:
echo '<report-json>' | python <skill-dir>/scripts/compress_report.py
```

If the script fails, pass the raw report as-is.

Spawn `design-proposer` with a context packet containing:

- Feature description (confirmed in Phase 1)
- Codebase Context Report (compressed)
- Domain terms (from Phase 2, or "Phase 2 skipped")
- Risks and success criteria (from Phase 3, or "Phase 3 skipped")
- Any constraints the user stated explicitly

Present the design proposals in sections. Validate each section before continuing.

**Design approval gate:** Ask: "Which approach should we move forward with and why?"

Wait for explicit commitment:

- "We'll go with Approach B because..."
- "Let's do Option 1, here's why..."

Ambiguous responses ("sounds good") → clarify which specific approach they're choosing.

## Phase 5: Transition

1. Summarize the approved approach in one short paragraph: chosen option and key tradeoffs.
2. If Phase 2 captured terms or Phase 3 captured risks: offer to write to `glossary.md` or `CONTEXT.md`. **If there are Open TBDs, offer to save them to `TODO.md` or a tracker.**
3. Produce the Design Brief below and stop — do not invoke `/plan` or write code automatically. Conclude: "You can now use `/plan` to generate a detailed implementation plan based on this brief. Would you like me to start that for you?"

**Required output format:**

```markdown
## Design Brief

**Chosen approach:** [Approach letter + name, e.g., "Approach B — Event-sourced queue"]
**Why:** [Key tradeoff in 1-2 sentences; what this gains and what it costs]
**Architecture:**

- [Component 1: responsibility]
- [Component 2: responsibility]
- [Key data flow between them]

**Success criteria:** [Observable signals — what user/system will do differently]
**Open TBDs:** [Unresolved items with owner and due date, or "None"]
```

## Command Usage & Troubleshooting

**When to use:**

- Scope or approach is unclear before starting a feature.
- Domain terminology is ambiguous (e.g., "task", "session", "context").
- Multiple implementation approaches exist and the right one isn't decided.
- A stakeholder description needs to become concrete requirements.

Prefer `planning` skill when requirements are clear. Prefer direct implementation when requirements and approach are both decided.

**Troubleshooting:**

- **Skill returns with no questions** — Input is too narrow. Add context about the feature goal and rerun.
- **Requirements feel incomplete** — Ask to explore edge cases, failure modes, or "what should NOT happen."
- **Brainstorm diverges from goal** — Add a constraint upfront (e.g., "only changes within the hook layer, no new agents").
- **Success Criteria** — All ambiguous terms defined, scope boundaries clear, key design decisions documented with rationale, no open questions remain.
