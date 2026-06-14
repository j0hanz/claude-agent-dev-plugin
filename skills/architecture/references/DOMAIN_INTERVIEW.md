# Domain Interview Guide

When a user picks an architectural candidate, you need to understand the domain boundaries before proposing code changes. This guide provides a structured interview to clarify terminology, constraints, and the target interface.

> **Ask every question with the three-option Decision Protocol from SKILL.md:** option 1 is your **✅ Recommended** answer with the evidence behind it, option 2 is the **second-most-likely** answer, and option 3 is **a custom answer** the user types themselves. Options below are templates — fill the brackets from the actual code you scanned, never leave them generic. Ask one question at a time.

---

## Why Interview?

Architectural refactors fail when:

- The new module is named for its implementation, not its domain concept
- Constraints are discovered mid-refactor and invalidate the plan
- The interface is designed without understanding what callers actually need

A 5-10 minute interview prevents this.

---

## Interview Procedure

### Step 1: Establish Canonical Terms (2-3 minutes)

**Goal**: Users and code should use the same vocabulary.

**Questions** (ask ONE at a time, listen for ambiguity):

1. **"What is the core concept we're extracting?"**
   1. ✅ Recommended — **`[pre-analyzed concept, e.g. Auth]`** — the dominant concern in the files you scanned (cite the giveaway, e.g. "bcrypt + jwt + user lookup are all co-located here").
   2. Also likely — **`[the second concept the code hints at, e.g. Session]`** — if they frame the boundary differently than the imports suggest.
   3. Something else — they name a concept you didn't infer; capture their exact word.
   - Listen for hesitation. If they pause, fall back to: "Is this about `[concept A]` or `[concept B]`?"

2. **"When you talk about this with your team, what do you call it?"**
   1. ✅ Recommended — **`[canonical term, e.g. auth]`** — matches how the code/folders already read.
   2. Also likely — **`[the class/file name in use, e.g. AuthService]`** — the literal symbol name, if that's their shared vocabulary.
   3. Something else — they use a different team word; adopt it verbatim as the canonical term.
   - Establish: we'll call it `[chosen term]` in the refactored code.

3. **"Does this module depend on a concept that deserves its own domain?"**
   1. ✅ Recommended — **Yes, keep `[dependency, e.g. User]` separate** — you saw it imported but with its own distinct responsibility.
   2. Also likely — **No, fold it in** — if the dependency is only ever used by this module and nothing else.
   3. Something else — they identify a different boundary; map it out with them.
   - Example: "Auth depends on User — separate module, or part of Auth?"

### Step 2: Understand Constraints (2-3 minutes)

**Goal**: Identify constraints that affect the interface shape.

**Questions**:

1. **"What parts of the system currently depend on this logic?"**
   1. ✅ Recommended — **The callers I found: `[list the actual callers, e.g. routes, middleware, the cron job]`** — these are every import site the scan surfaced.
   2. Also likely — **Those plus runtime/dynamic callers I can't see statically** — if they reach it via DI, reflection, or an HTTP boundary.
   3. Something else — they know a caller the scan missed; add it to the interface's required surface.
   - This tells you what the interface must support.

2. **"Is there anything about the current implementation that's non-negotiable?"**
   1. ✅ Recommended — **Preserve `[key mechanism, e.g. bcrypt hashing]`** — the behavior most likely bound by compatibility or compliance.
   2. Also likely — **A performance/latency contract** — e.g. it must stay sync, or sub-millisecond, or cache-backed.
   3. Something else — they name a different hard constraint; record it before designing the interface.

3. **"Are there features or edge cases we should NOT touch in this refactor?"**
   1. ✅ Recommended — **Leave `[out-of-scope logic, e.g. third-party OAuth]` alone** — adjacent but separable from the candidate seam.
   2. Also likely — **Nothing off-limits — extract the whole concern** — if the module is cohesive enough to move wholesale.
   3. Something else — they fence off a different area; scope strictly around it.

### Step 3: Propose the Interface (3-5 minutes)

**Goal**: Agree on what the new module will export and how callers will use it.

**After the interview**, propose the interface shape using examples from `INTERFACE_SHAPES.md`.

**Say something like:**

> "Based on what you've described, I'm proposing we extract a module called `[Term]` with these responsibilities:
>
> - **What it does**: [1 sentence — the domain logic]
> - **What callers will see**: [3-5 key operations]
> - **What it hides**: [infrastructure details]
>
> Here's what the usage would look like:
>
> ```typescript
> import { operation1, operation2 } from './auth';
>
> const result = await operation1(input);
> ```
>
> Does this interface feel right?"

Offer the confirmation as three options:

1. ✅ Recommended — **Yes, proceed with this design** — it covers the callers and constraints you described.
2. Also likely — **Close, but one signature needs to change** — e.g. error vs. null, sync vs. async (name the specific one you're unsure about).
3. Something else — **It's not what I imagined** — then ask: "What's different from what you pictured?"

Iterate until they choose option 1.

### Step 4: Apply the Deletion Test (1 minute)

**Say**: "Let me check this with the deletion test: if we deleted this module, what happens to its logic?"

1. ✅ Recommended — **It duplicates across callers** — confirms a deep, high-leverage module (you'd copy `[key logic]` into `[N]` callers). This is the green light.
2. Also likely — **It just moves elsewhere intact** — the module is shallow; reconsider the extraction or pick a different seam.
3. Something else — **partly both** — they describe a mixed outcome; weigh whether the duplicated part alone justifies the seam.

**Green light**: option 1 — duplication across 3-5 callers means it earns its keep.

**Red flag**: option 2 — if the logic would just move to one caller, go back to Step 3 and refine the boundaries.

---

## Example Interview

### Candidate: Extract Auth from Scattered Files

Notice how each question offers a grounded **Recommended** answer, a real **Also likely** alternative, and a **custom** escape hatch — and how the recommendation cites what was seen in the code.

#### Step 1: Canonical Terms

> **You**: "What is the core concept we're extracting?
>
> 1. ✅ Recommended — **Auth** — `password.ts`, `token.ts`, and the login route all cluster around credentials and JWTs.
> 2. Also likely — **Session** — if you think of this as session lifecycle rather than credential checking.
> 3. Something else — tell me your word for it."
>
> **User**: "Auth. We have password hashing in one place, JWT in another..."
>
> **You**: "When you talk with your team, what do you call it?
>
> 1. ✅ Recommended — **`auth`** — shortest, matches the folder you'll create.
> 2. Also likely — **`LoginService`** — the current class name, if that's the shared vocabulary.
> 3. Something else — your team's term."
>
> **User**: "We say 'auth'. `LoginService` is confusing — it doesn't just log in, it also generates tokens."
>
> **You**: "Then `auth` it is. The auth module will need to look up users. Is that part of Auth or separate?
>
> 1. ✅ Recommended — **Separate** — keeps Auth pure; the caller passes in a user or a lookup function (Auth never imports the user store).
> 2. Also likely — **Part of Auth** — if Auth is the only thing that ever reads users.
> 3. Something else — describe the split you want."
>
> **User**: "Separate. Auth doesn't know about users — we pass in a user object or a lookup function."
>
> **You**: "Perfect — Auth stays pure. Same question for roles/permissions:
>
> 1. ✅ Recommended — **Separate module** — credential checking ≠ access control; they change for different reasons.
> 2. Also likely — **Inside Auth** — if roles are only ever derived during authentication.
> 3. Something else — your call."
>
> **User**: "Roles are separate. Auth just validates credentials."

#### Step 2: Constraints

> **You**: "What currently depends on this logic?
>
> 1. ✅ Recommended — **The callers I found: routes, API middleware** — every static import site of the auth functions.
> 2. Also likely — **Those plus a runtime caller** — e.g. a CLI or job that reaches it dynamically and won't show in the import graph.
> 3. Something else — name a caller I missed."
>
> **User**: "Option 2 — routes and middleware, plus a CLI tool that logs users in programmatically."
>
> **You**: "So three callers. Anything non-negotiable about the implementation?
>
> 1. ✅ Recommended — **Preserve bcrypt password hashing** — it's the kind of thing compliance usually pins down.
> 2. Also likely — **A latency contract** — token checks must stay fast/sync.
> 3. Something else — your hard constraint."
>
> **User**: "Bcrypt is non-negotiable — compliance. Speed is fine, bcrypt is slow by design anyway."
>
> **You**: "Anything we should NOT touch?
>
> 1. ✅ Recommended — **Leave OAuth alone** — it's adjacent but separable from the password seam.
> 2. Also likely — **Nothing off-limits** — extract the whole auth concern at once.
> 3. Something else — fence off a different area."
>
> **User**: "Keep OAuth out of this one. We'll tackle that separately."

#### Step 3: Propose Interface

> **You**: "Based on that, here's the interface:
>
> ```typescript
> // What Auth exports
> export async function authenticate(user: User, password: string): Promise<Token>;
> export async function register(email: string, password: string): Promise<{ token: Token }>;
> export function verifyToken(token: Token): { userId: string };
>
> // How routes use it
> app.post('/login', async (req, res) => {
>   const user = await findUserByEmail(req.body.email);
>   const token = await authenticate(user, req.body.password);
>   res.json({ token });
> });
> ```
>
> All hashing and JWT generation stay inside; callers never import bcrypt or jsonwebtoken. Does this interface feel right?
>
> 1. ✅ Recommended — **Yes, proceed** — covers all three callers and keeps bcrypt internal.
> 2. Also likely — **Close, but `verifyToken`'s failure behavior needs deciding** — throw vs. return null.
> 3. Something else — it's not what you pictured; tell me what's off."
>
> **User**: "Option 2 — I want to be sure how `verifyToken` signals an invalid token."
>
> **You**: "Then let's decide that one signature:
>
> 1. ✅ Recommended — **Throws** — aligns with your existing catch-all middleware, so callers wrap it in try/catch.
> 2. Also likely — **Returns `{ userId } | null`** — if you'd rather branch on the result explicitly.
> 3. Something else — a Result type or status enum."
>
> **User**: "Throws is fine. We already catch it in middleware."
>
> **You**: "Done — `verifyToken` throws on invalid token; callers wrap it in try/catch."

#### Step 4: Deletion Test

> **You**: "Last check — if we deleted the auth module, what happens to password hashing and token generation?
>
> 1. ✅ Recommended — **Duplicates across callers** — routes, middleware, and the CLI would each re-implement it.
> 2. Also likely — **Moves to one place intact** — meaning it's shallow and not worth a module.
> 3. Something else — a mix."
>
> **User**: "Option 1 — ugh, everywhere. Routes, middleware, CLI would all duplicate it."
>
> **You**: "Exactly. Duplicating complex logic across 3+ callers is what makes this extraction worth doing."

---

## Interview Pitfalls

### ❌ Pitfall 1: Proposing Before Understanding

**Bad**: "So we'll extract a UserAuthenticationService that implements..."

**Good**: Ask questions first. Then propose.

### ❌ Pitfall 2: Assuming You Know the Domain

**Bad**: "I know how auth works. Let me just design the interface."

**Good**: Ask the user what auth means in _their_ system. Authentication is different in every codebase.

### ❌ Pitfall 3: Letting Ambiguity Slide

**Bad**: "You mention 'user lookup.' Does that include roles?"

User: "Yeah, kind of."

You: "OK, I'll include it."

**Good**: Clarify. "Just password validation, or the whole access control system?"

### ❌ Pitfall 4: Skipping Constraints

**Bad**: "Let's extract it."

**Good**: Ask about compliance, performance, edge cases before designing.

---

## Questions Cheat Sheet

Each entry below is `Question → ✅ Recommended / Also likely / Custom`. Fill the brackets from the code you scanned; option 3 is always "the user's own answer."

**For understanding the domain:**

- "What is the core concept here?" → ✅ `[pre-analyzed concept, e.g. Auth]` / `[second concept, e.g. Session]` / their own word
- "What do you and your team call it?" → ✅ `[canonical term, e.g. auth]` / `[the symbol name in code, e.g. AuthService]` / their term
- "Does this depend on a concept that deserves its own domain?" → ✅ Keep `[dependency, e.g. User]` separate / Fold it in / a different boundary

**For understanding callers:**

- "What depends on this logic?" → ✅ `[the callers the scan found]` / those plus a dynamic/runtime caller / a caller I missed
- "Do callers need one interface or different operations?" → ✅ Unified `[core operations]` / split by caller type / their answer

**For understanding constraints:**

- "What's non-negotiable in the implementation?" → ✅ Preserve `[key mechanism]` / a latency/perf contract / a different hard constraint
- "What should we NOT touch in this refactor?" → ✅ Leave `[out-of-scope logic]` alone / nothing off-limits / a different fenced area

**For confirming the interface:**

- "Does this interface match what you imagined?" → ✅ Yes, proceed / close but one signature changes / not what I pictured
- "Sync or async?" → ✅ `[sync or async, from codebase patterns]` / the opposite / their preference
- "On failure — throw or return null?" → ✅ `[throw or null, from codebase patterns]` / the opposite / a Result/status type

**For confirming the extraction is worth it:**

- "If we deleted this module, what happens to its logic?" → ✅ Duplicates across callers (deep, keep it) / moves elsewhere intact (shallow, reconsider) / a mix

---

## When to Stop the Interview

You have enough information when you can describe:

1. **The module's name** and what it does
2. **3-5 operations** it will export
3. **What infrastructure it hides** (database, HTTP, filesystem)
4. **Who depends on it** and how
5. **Non-negotiables** that affect the interface

If you still have questions after this, ask them. An extra minute of clarification prevents an hour of rework.
