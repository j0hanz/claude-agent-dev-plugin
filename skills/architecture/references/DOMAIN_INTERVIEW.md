# Domain Interview Guide

When a user picks an architectural candidate, you need to understand the domain boundaries before proposing code changes. This guide provides a structured interview to clarify terminology, constraints, and the target interface.

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

1. **"In your domain, what is the core concept we're extracting? (Recommended: [Pre-analyzed concept, e.g. Auth, Billing])"**
   - Examples: "We're extracting Auth," "We're extracting the Order calculation," "We're extracting billing"
   - Listen for: Do they have a clear name? Do they hesitate?
   - If hesitation: "Help me understand — is this about [concept A] or [concept B]?"

2. **"When you talk about this with your team, what do you call it? (Recommended: [Canonical Term, e.g. auth])"**
   - Clarifies team terminology. They might call it "the Auth module" but the code calls it "AuthService."
   - Establish: We'll call it `[Canonical Term]` in the refactored code.

3. **"Are there concepts this module will depend on that should have their own domains? (Recommended: Keep [Concept, e.g. User] as a separate domain module/concept)"**
   - Example: "Auth depends on User. Should User be a separate module?"
   - Example: "Payment depends on Customer. Is Customer part of Payment or separate?"
   - Map out the boundaries.

### Step 2: Understand Constraints (2-3 minutes)

**Goal**: Identify constraints that affect the interface shape.

**Questions**:

1. **"What parts of the system currently depend on this logic? (Recommended: Focus on known callers: [List found callers])"**
   - List the callers: routes, other modules, workflows, etc.
   - Example: "Routes call it, the scheduler calls it, a cron job calls it."
   - This tells you what the interface must support.

2. **"Is there anything about the current implementation that's non-negotiable? (Recommended: Preserve the core logic of [Key mechanism, e.g., bcrypt password hashing] for compatibility/safety)"**
   - Example: "We can't change how password hashing works because of compliance."
   - Example: "We must support both sync and async password checks."
   - Example: "Users expect sub-millisecond latency, so we need caching."

3. **"Are there any features or edge cases we shouldn't touch during this refactor? (Recommended: Focus strictly on extracting [core candidate logic] and leave [potential out-of-scope logic, e.g., third-party OAuth] untouched for now)"**
   - Scope constraints. Example: "Don't change how OAuth works, just focus on password auth."

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
> Does this feel right? (Recommended response: Yes, proceed with this interface design.)"

**If they say "no,"** ask: "What's different from what you imagined?"

Iterate until they say "yes."

### Step 4: Apply the Deletion Test (1 minute)

**Say**: "Let me check this with the deletion test: If we deleted this module, would we have to duplicate its logic across callers, or would the logic just move elsewhere? (Recommended check: Yes, we would have to duplicate the logic across callers, confirming this is a deep, high-leverage module)."

**Expected answer**: "We'd have to duplicate it across 3-5 callers" (= it earns its keep, good deepening opportunity).

**Red flag**: "The logic would just move to the caller" (= module is shallow, reconsider extraction).

If red flag, go back to Step 3 and refine the boundaries.

---

## Example Interview

### Candidate: Extract Auth from Scattered Files

#### Step 1: Canonical Terms

> **You**: "In your domain, what is the core concept we're extracting? (Recommended: Auth)"
>
> **User**: "Authentication. We have password hashing in one place, JWT in another..."
>
> **You**: "When you talk with your team, what do you call it? (Recommended: auth)"
>
> **User**: "We usually say 'auth'. The LoginService class is confusing because it doesn't just log in — it also generates tokens."
>
> **You**: "Got it. We'll use 'auth' as the canonical term. The new module will be `auth/`. Inside, we'll separate concerns clearly — passwords, tokens, and the main authenticate operation. Does that match what you do mentally?"
>
> **User**: "Yes, exactly."
>
> **You**: "The auth module will need to look up users. Is that 'part of Auth' or something separate? (Recommended: Separate user lookup from auth)"
>
> **User**: "Separate. Auth doesn't know about users — we pass in a user object or a lookup function."
>
> **You**: "Perfect. So Auth is pure, and the caller handles 'get the user, then authenticate them.' Next question: Are there other concepts — like roles or permissions — that should be separate from Auth? (Recommended: Keep roles/permissions as a separate module)"
>
> **User**: "Roles are separate. Auth just validates credentials. Roles check what you can do after you're authenticated."

#### Step 2: Constraints

> **You**: "What parts of the system currently depend on auth logic? (Recommended: Focus on routes, middleware, and CLI callers)"
>
> **User**: "Routes use it, obviously. The API middleware. We also have a CLI tool that logs users in programmatically."
>
> **You**: "So three callers. Do they all need the same interface, or do they call different operations? (Recommended: Keep interface unified with authenticate, register, and verifyToken)"
>
> **User**: "They all do login and token verification. The CLI also does registration, but routes don't."
>
> **You**: "Got it. Our interface will support login, register, and verifyToken. Any non-negotiables? (Recommended: Preserve bcrypt password hashing and token validation)"
>
> **User**: "Password hashing must use bcrypt — no shortcuts for compliance. It should be fast, but bcrypt is already slow by design, so that's fine."
>
> **You**: "Anything we should not touch? (Recommended: Focus strictly on the password-based auth seam, leaving OAuth untouched for now)"
>
> **User**: "Yeah, keep OAuth out of this refactor. We'll tackle that separately."

#### Step 3: Propose Interface

> **You**: "Based on what you described, here's the interface I'm proposing:
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
> All password hashing and JWT generation happen inside. Callers don't import bcrypt or jsonwebtoken. Does this feel right? (Recommended response: Yes, proceed with this interface design.)"
>
> **User**: "Yes, but I want to make sure verifyToken doesn't throw when the token is invalid. We handle that explicitly."
>
> **You**: "Good catch. Let me adjust:
>
> ```typescript
> export function verifyToken(token: Token): { userId: string } | null;
> ```
>
> Or would you prefer it throws an error and you catch it? (Recommended: Throw error to align with current catch-all middleware)"
>
> **User**: "Throws is fine. We already catch it in middleware."
>
> **You**: "Perfect. So verifyToken throws on invalid token. Callers wrap it in try-catch."

#### Step 4: Deletion Test

> **You**: "Let me apply the deletion test: If we deleted the auth module, where would password hashing and token generation go? (Recommended check: Yes, we would have to duplicate the logic across callers, confirming this is a deep, high-leverage module)."
>
> **User**: "Ugh, everywhere. Routes, middleware, CLI — they'd all duplicate it."
>
> **You**: "Exactly. The fact that you'd duplicate complex logic across 3+ callers means this extraction is worth doing."

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

**For understanding the domain:**

- "What is the core concept here? (Recommended: [Pre-analyzed Concept, e.g. Auth, Billing])"
- "When you talk about this with your team, what do you call it? (Recommended: [Canonical Term, e.g. auth])"
- "Are there concepts this module will depend on that should have their own domains? (Recommended: Keep [Concept, e.g. User] as a separate domain module/concept)"

**For understanding callers:**

- "What parts of the system currently depend on this logic? (Recommended: Focus on known callers: [List found callers])"
- "Do they all need the same interface, or do they call different operations? (Recommended: Keep interface unified with [List core operations])"

**For understanding constraints:**

- "Is there anything about the current implementation that's non-negotiable? (Recommended: Preserve the core logic of [Key mechanism] for compatibility/safety)"
- "Are there any features or edge cases we shouldn't touch during this refactor? (Recommended: Focus strictly on extracting [core candidate logic] and leave [out-of-scope logic] untouched)"

**For confirming the interface:**

- "Does this match what you imagined? (Recommended response: Yes, proceed with this interface design.)"
- "Should this be sync or async? (Recommended: [Sync or Async, based on codebase patterns])"
- "What happens when it fails? Error or null? (Recommended: [Error or Null, based on codebase patterns])"

**For confirming the extraction is worth it:**

- "If we deleted this module, would we have to duplicate its logic across callers, or would the logic just move elsewhere? (Recommended check: Yes, we would have to duplicate the logic across callers, confirming this is a deep, high-leverage module)."

---

## When to Stop the Interview

You have enough information when you can describe:

1. **The module's name** and what it does
2. **3-5 operations** it will export
3. **What infrastructure it hides** (database, HTTP, filesystem)
4. **Who depends on it** and how
5. **Non-negotiables** that affect the interface

If you still have questions after this, ask them. An extra minute of clarification prevents an hour of rework.
