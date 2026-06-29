# Migration Strategies

Use this reference when the user has approved a seam (Mode A) or a new architecture (Mode B) and needs to know HOW to get from the current state to the target state without breaking production.

## The Core Problem

Architecture proposals fail at execution because teams try to do a "Big Bang" rewrite — swapping the entire implementation in one PR. This destroys git blame, breaks bisect, and creates multi-week merge conflicts. Every strategy below avoids the Big Bang.

## Strategy 1: Strangler Fig

**Use when:** Replacing a large, working module with a better-structured one.

**Mechanism:**

1. Create the new module alongside the old one (do not delete anything yet).
2. Route ONE caller to the new module. Ship it. Verify.
3. Migrate callers one by one, deleting old code only when it has zero callers.
4. Once the old module is empty, delete it.

**Key rule:** The old code and the new code coexist. You never have a broken intermediate state. Each step is independently shippable.

**Failure mode:** Keeping the old module "just in case" forever. Set a deletion date when you start.

## Strategy 2: Branch by Abstraction

**Use when:** A module needs a new seam inserted (e.g., extracting a port/adapter boundary) without changing behavior.

**Mechanism:**

1. Extract an interface (the "abstraction") in front of the existing implementation.
2. Make all callers use the interface — the implementation doesn't change yet.
3. Write the new implementation behind the interface.
4. Swap the implementation. Delete the old one.

**Key rule:** At step 2, all tests still pass and behavior is identical. The interface is the seam you're inserting.

**Example:**

```typescript
// Step 1: extract interface
interface UserRepository {
  findById(id: string): Promise<User>;
  save(user: User): Promise<void>;
}

// Step 2: wrap existing Prisma calls behind it
class PrismaUserRepository implements UserRepository { ... }

// Step 3: callers now use UserRepository, not PrismaClient directly
// Step 4: swap in a new implementation (e.g., in-memory for tests)
```

## Strategy 3: Parallel Run

**Use when:** You need to validate that new logic produces the same results as old logic before cutting over.

**Mechanism:**

1. Run both old and new implementations for every request.
2. Compare outputs. Log discrepancies.
3. Once discrepancy rate is zero over N requests, cut over to new implementation.
4. Delete old implementation.

**Key rule:** No user-visible behavior change at any step. The parallel run is invisible to callers.

**Best for:** Payment processing, pricing engines, permission checks — anywhere a silent difference is a production incident.

## Strategy 4: Feature Flag Cutover

**Use when:** You need to deploy incrementally and roll back instantly if something breaks.

**Mechanism:**

1. Put the new implementation behind a flag (`USE_NEW_PRICING_ENGINE=true`).
2. Deploy to production with the flag off.
3. Enable for internal users → 1% of traffic → 10% → 100%.
4. Once stable, delete the flag and old implementation.

**Key rule:** The flag must be cheap to flip (env var or config, not a code deploy). If flipping the flag requires a deploy, this strategy loses its rollback advantage.

**Failure mode:** Flag accumulation. Flags that never get cleaned up become permanent tech debt. Set a cleanup date when you create the flag.

## Strategy 5: Seam Introduction (Feathers)

**Use when:** Working in legacy code with no tests — you need to add tests before you can safely refactor.

**Mechanism:**

1. Find a "seam" — a place where you can change behavior without modifying the code itself (e.g., a dependency you can swap via constructor injection).
2. Introduce the seam (extract a constructor parameter or use a factory).
3. Write tests using the seam to inject fakes.
4. Refactor safely under test coverage.

**Reference:** Michael Feathers, "Working Effectively with Legacy Code"

## Strategy 6: Expand-Contract (for Database Schemas)

**Use when:** Moving domain concepts between tables or renaming columns.

**Mechanism:**

1. **Expand:** Add the new column/table. Write code that writes to both old and new.
2. **Migrate:** Backfill the new column/table from the old one.
3. **Contract:** Remove reads from the old location. Then remove the old column/table.

**Key rule:** Never rename a column directly in a single migration — that's a Big Bang and breaks deploys in flight.

## Choosing a Strategy

| Situation                                      | Strategy              |
| ---------------------------------------------- | --------------------- |
| Replacing a whole module with a new one        | Strangler Fig         |
| Inserting a new interface/seam boundary        | Branch by Abstraction |
| New logic must produce identical output        | Parallel Run          |
| Need instant rollback capability               | Feature Flag          |
| No tests exist, need safety before refactoring | Seam Introduction     |
| Database schema change                         | Expand-Contract       |

## Anti-Patterns to Avoid

- **Big Bang Rewrite:** Rewriting a module completely in a single PR. Always breaks something and the diff is unreviable.
- **Rename-and-Hope:** Renaming modules without changing their imports or callers. Creates the illusion of structure.
- **Flag Soup:** More than 3 active feature flags touching the same module. Combinatorial state explosion.
- **Permanent Parallel Run:** Never cutting over because "we might need the old code." Set a deadline.
