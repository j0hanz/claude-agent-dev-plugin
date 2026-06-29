# Domain Interview Guide

To understand domain boundaries before proposing architectural changes, use a structured interview.

> **Decision Protocol**: Ask questions with a three-option protocol: (1) Recommended answer based on static scan, (2) second-most-likely option, (3) custom write-in. Fill brackets with actual scanned code details. Ask one question at a time.

## Why Interview?

Refactors fail if modules are named for implementation rather than domain concepts, or if calling context/constraints are misunderstood. A short interview prevents this.

## Interview Steps

### Step 1: Establish Canonical Terms (2-3 mins)

_Goal: Align vocabulary between user and codebase._

1. **"What core concept are we extracting?"**
   - Recommended: `[analyzed concept, e.g., Auth]` (citing bcrypt/JWT co-location).
   - Also likely: `[second concept, e.g., Session]`.
   - Custom option.
2. **"What do you and your team call this?"**
   - Recommended: `[canonical term, e.g., auth]`.
   - Also likely: `[class/file name, e.g., AuthService]`.
   - Custom option.
3. **"Does this module depend on a concept deserving its own domain?"**
   - Recommended: Yes, keep `[dependency, e.g., User]` separate.
   - Also likely: No, fold it in.
   - Custom option.

### Step 2: Understand Constraints (2-3 mins)

_Goal: Identify constraints shaping the interface._

1. **"What parts of the system currently depend on this logic?"**
   - Recommended: Callers found: `[list scanned callers, e.g., routes, middleware]`.
   - Also likely: Scanned callers plus runtime/dynamic dependencies.
   - Custom option.
2. **"Is any part of the current implementation non-negotiable?"**
   - Recommended: Preserve `[key mechanism, e.g., bcrypt hashing]`.
   - Also likely: Performance/latency requirements (e.g., must stay synchronous).
   - Custom option.
3. **"What logic should we NOT touch?"**
   - Recommended: Leave `[out-of-scope logic, e.g., third-party OAuth]` alone.
   - Also likely: Extract the entire concern.
   - Custom option.

### Step 3: Propose the Interface (3-5 mins)

_Goal: Agree on exports and caller usage._
Propose interface shape (e.g., using patterns from `INTERFACE_SHAPES.md`) and get confirmation:

- Recommended: Yes, proceed with this design.
- Also likely: Close, but signature `X` needs to change (e.g., throw vs. return null).
- Custom option.

### Step 4: Apply Deletion Test (1 min)

_Goal: Verify extraction value._
Ask: _"If we deleted this module, what happens to its logic?"_

- Recommended: It duplicates across callers (confirms a deep, high-leverage module).
- Also likely: It just moves elsewhere intact (shallow module; reconsider extraction).
- Custom option.

## Example Dialog (Extracting Auth)

- **Concept**:
  - **Agent**: "What core concept are we extracting? (1) Recommended: Auth (based on password.ts and token.ts), (2) Session, (3) Custom."
  - **User**: "Auth. We have password hashing and JWT scattered."
- **Term**:
  - **Agent**: "What do you call it? (1) Recommended: `auth`, (2) `LoginService`, (3) Custom."
  - **User**: "We say 'auth'."
- **Dependencies**:
  - **Agent**: "Should we keep User lookup separate? (1) Recommended: Yes, pass user/lookup function to Auth, (2) No, fold user DB access into Auth, (3) Custom."
  - **User**: "Separate. Auth shouldn't know user database details."
- **Callers & Constraints**:
  - **Agent**: "What depends on this? (1) Recommended: routes and middleware, (2) routes/middleware plus runtime callers, (3) Custom."
  - **User**: "Option 2 — we also have a CLI tool logging in."
  - **Agent**: "Any non-negotiables? (1) Recommended: Keep bcrypt hashing, (2) Latency requirement, (3) Custom."
  - **User**: "Bcrypt is non-negotiable."
- **Proposal & Verification**:
  - **Agent**: Proposes interface hiding bcrypt/JWT:
    ```typescript
    export async function authenticate(user: User, pass: string): Promise<Token>;
    export function verifyToken(token: Token): { userId: string }; // throws on invalid
    ```
    "Does this look right? (1) Recommended: Yes, (2) Close, but signature change, (3) Custom."
  - **User**: "Looks good, let's proceed."
- **Deletion Test**:
  - **Agent**: "If deleted, what happens? (1) Recommended: Duplicates across 3 callers, (2) Moves intact, (3) Custom."
  - **User**: "Option 1. It would duplicate across routes, middleware, and CLI."

## Interview Pitfalls

- **Proposing Before Understanding**: Avoid designing interfaces before asking questions.
- **Assuming You Know the Domain**: Always ask how terms and logic behave in their specific system.
- **Letting Ambiguity Slide**: Clarify fuzzy boundaries (e.g., separating authentication from access control).
- **Skipping Constraints**: Identify compliance, latency, or out-of-scope logic first.

## When to Stop

Stop the interview when you can define:

1. Module name and core role.
2. 3-5 exported operations.
3. Hidden infrastructure details (DB, network, etc.).
4. Caller dependencies.
5. Critical constraints affecting signature design.
