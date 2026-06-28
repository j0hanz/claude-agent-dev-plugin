# Interface Shapes & Seams: From Problem to Proposal

When deepening a module, you'll propose a "new interface shape" — the boundary callers see — and the "seams" inside it where behavior can be swapped without editing code in place. These are two angles on the same boundary: shape is what callers depend on, seams are where you cut the internals for testability. This guide shows both with three concrete examples.

**Shape checklist** (apply when proposing the public interface):

- [ ] Can I test the domain without the infrastructure? (use mocks/adapters)
- [ ] Do callers need to import from multiple files? (should be one or two)
- [ ] Are infrastructure details hidden? (callers don't see Stripe, database, Express)
- [ ] Do types describe intent, not mechanism? (`ChargeRequest`, not `StripeChargeParams`)
- [ ] Is the interface smaller than the implementation? (yes = deep, no = shallow)

**Seam checklist** (apply when splitting internals):

- [ ] Does the interface name describe what it does, not how it works?
- [ ] Can you swap the implementation without changing callers?
- [ ] Does deletion move complexity, not eliminate it?
- [ ] Are dependencies flowing in one direction (no cycles)?

If any answer is "no," redraw the boundary.

---

## Example 1: Auth Scattered Across Files

**Bad** — logic split across `auth.ts`, `middleware.ts`, `utils.ts`. Callers must know where to import `login`, that middleware needs wiring into Express, and how to compose the pieces. Testing `login()` requires a database. Shape is SHALLOW (caller's knowledge ≈ implementation's complexity) and the seam is wrong (routes call domain logic directly, no boundary to mock).

```typescript
// auth.ts
export async function login(email: string, password: string) { ... }
// middleware.ts
export function authMiddleware() { ... }
// utils.ts
export function hashPassword(password: string) { ... }
```

**Good** — one module, domain logic takes a `User` object instead of touching the database, adapters bridge to infra:

```typescript
// auth/password.ts, auth/tokens.ts — pure domain, no db/Express knowledge
export async function verifyPassword(password: string, hash: string): Promise<boolean>;
export function generateToken(userId: string): string;

// auth/authenticate.ts — orchestrator, still pure domain
export async function login(user: User, passwordAttempt: string): Promise<{ token: string }> {
  if (!(await verifyPassword(passwordAttempt, user.passwordHash)))
    throw new Error('Invalid password');
  return { token: generateToken(user.id) };
}

// infra/users-repository.ts — adapter: looks up the user, then calls domain login()
export async function loginUser(email: string, password: string) {
  const user = await db.users.findOne({ email });
  return login(user, password); // domain doesn't know about the db
}
```

Caller now only needs `import { loginUser } from './infra/users-repository'`. **Shape**: deep — one call instead of three things to know. **Seam**: between `auth/` (domain) and `infra/` (adapters); domain never imports infra, so tests pass a plain `User` object with no database.

---

## Example 2: God Module / Circular Dependency

**Bad** — one 400-line `order.ts` does validation, calculation, persistence, and notification, so testing requires mocking the database, an email queue, and a logger. Worse, if `payment-service.ts` calls back into `order-service.ts` to notify it, Order and Payment can't be tested or split apart — a cycle.

```typescript
// order/order-service.ts
import { processPayment } from '../payment/payment-service';
export async function createOrder(items) {
  const payment = await processPayment(calculateTotal(items)); // Order → Payment
  ...
}
// payment/payment-service.ts
import { notifyOrderCreated } from '../order/order-service'; // Payment → Order: CYCLE
```

**Good** — pure calculation/validation split from the orchestrator, dependencies flow one way:

```typescript
// domain/order/order.ts — calculation + validation only, no I/O
export function calculateOrderPrice(items: OrderItem[]): PricedOrder { ... }
export function validateItems(items: OrderItem[]): void { ... }

// domain/order/order-repository.ts — interface, no implementation
export interface IOrderRepository {
  save(order: { userId: string; items: OrderItem[]; pricing: PricedOrder }): Promise<Order>;
}

// infra/order-workflow.ts — orchestrator (NOT domain): persistence + side effects happen here
export async function createOrderWorkflow(repo: IOrderRepository, userId: string, items: OrderItem[]) {
  validateItems(items);
  const pricing = calculateOrderPrice(items);
  const order = await repo.save({ userId, items, pricing });
  await emailQueue.publish('order.created', { orderId: order.id }); // side effect, lives in infra
  return order;
}
```

Tests exercise `calculateOrderPrice`/`validateItems` directly with no mocks at all, or pass an in-memory `IOrderRepository`. **Shape**: caller sees `createOrderWorkflow(repo, userId, items)` instead of five intermixed concerns. **Seam**: between domain modules (pure, no I/O) and the orchestrator that composes them with infrastructure — one direction only, so neither side needs the other to test.

---

## Example 3: Repository — Shallow vs. Deep

**Shallow** — a class that just forwards to the database adds no value; the interface is as complex as the implementation. Deletion test: delete this class and the logic just moves to the caller, unchanged.

```typescript
export class UserRepository {
  findById(id: string) {
    return db.users.findOne({ id });
  }
  create(email: string, hash: string) {
    return db.users.create({ email, passwordHash: hash });
  }
}
```

**Deep** — an interface that hides the database entirely, with a swappable in-memory adapter for tests:

```typescript
// domain/user/user-repository.ts — abstract
export interface IUserRepository {
  findUserByEmail(email: string): Promise<User | null>;
  storeNewUser(email: string, passwordHash: string): Promise<User>;
}

// infra/postgres-user-repository.ts and infra/in-memory-user-repository.ts both implement it

// domain/auth/authenticate.ts — depends on the interface, not a concrete impl
export async function register(
  repo: IUserRepository,
  email: string,
  password: string,
): Promise<User> {
  if (await repo.findUserByEmail(email)) throw new Error('Already registered');
  return repo.storeNewUser(email, await hashPassword(password));
}

// test/auth.test.ts — no database needed
const user = await register(new InMemoryUserRepository(), 'test@example.com', 'password123');
```

**Shape**: deep — callers depend on `findUserByEmail`/`storeNewUser`, never on `db`. **Seam**: between `authenticate.ts` (domain) and the two repository adapters; production swaps in Postgres, tests swap in memory, with zero changes to `register()`. Deletion test: delete the interface and the database knowledge bleeds back into every caller — that's the sign the abstraction is earning its keep.
