# Code Review Pattern Catalog

Extended reference for Phase 2 findings. Load this file when you need a precise name, canonical description, or example fix for a pattern. Do not load by default.

---

## Table of Contents

1. [Security Patterns](#security-patterns)
2. [Correctness Patterns](#correctness-patterns)
3. [Performance Patterns](#performance-patterns)
4. [API & Reuse Patterns](#api--reuse-patterns)
5. [Plugin-Specific Patterns](#plugin-specific-patterns)

---

## Security Patterns

### Command Injection

**What it is:** User-controlled input reaches a shell command without sanitization.

```js
// WRONG — shell=true with user input
exec(`git clone ${userInput}`);

// CORRECT — use array form, no shell interpolation
execFile('git', ['clone', userInput]);
```

**Finding text:** "Command injection — `userInput` flows into shell string without sanitization."
**Fix:** Use `execFile` / array argument form, or validate `userInput` against an allowlist before use.

---

### SQL Injection

**What it is:** User input concatenated directly into a SQL string.

```python
# WRONG
cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")

# CORRECT — parameterized
cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
```

**Finding text:** "SQL injection — `name` is not parameterized."
**Fix:** Use bound parameters (placeholder syntax varies by driver: `%s`, `?`, `$1`).

---

### Hardcoded Secret

**What it is:** A credential, API key, or token stored literally in source code.

```js
// WRONG
const apiKey = 'sk-1234abcd...';

// CORRECT
const apiKey = process.env.API_KEY;
```

**Finding text:** "Hardcoded secret — `apiKey` should come from an environment variable or secret manager."
**Fix:** Move to `process.env`, `os.environ`, or a secrets manager. Add to `.gitignore` if stored in a config file.

---

### Path Traversal

**What it is:** User-controlled input used to construct file paths, allowing access outside the intended directory.

```python
# WRONG
open(os.path.join(base_dir, user_filename))

# CORRECT
safe = os.path.realpath(os.path.join(base_dir, user_filename))
if not safe.startswith(os.path.realpath(base_dir)):
    raise ValueError("Path traversal attempt")
```

**Finding text:** "Path traversal — `user_filename` is not validated to stay within `base_dir`."

---

### Insecure Deserialization

**What it is:** Deserializing untrusted data using a format that supports arbitrary object construction.

```python
# WRONG — yaml.load executes arbitrary Python
yaml.load(user_input)

# CORRECT
yaml.safe_load(user_input)
```

```python
# WRONG — pickle is unsafe with untrusted input
pickle.loads(user_bytes)

# CORRECT — use JSON or validate source before unpickling
json.loads(user_bytes)
```

---

## Correctness Patterns

### Swallowed Error

**What it is:** An exception is caught but not acted upon — failures disappear silently.

```js
// WRONG
try {
  await writeFile(path, data);
} catch (e) {
  // silence
}

// CORRECT — log with context, or re-raise
try {
  await writeFile(path, data);
} catch (e) {
  logger.error({ path, err: e }, 'writeFile failed');
  throw e;
}
```

**Finding text:** "Swallowed error — `catch` block is empty; failures in `writeFile` will be silently ignored."

---

### Off-by-One

**What it is:** Loop or slice boundary is one too many or one too few.

```js
// WRONG — skips last element
for (let i = 0; i < arr.length - 1; i++)

// CORRECT
for (let i = 0; i < arr.length; i++)
```

```python
# WRONG — misses final character
result = s[0:len(s) - 1]

# CORRECT
result = s[:-1]   # or s[:len(s)] for full slice
```

**Finding text:** "Off-by-one — loop condition `< arr.length - 1` excludes the last element."

---

### Async Without Await

**What it is:** An async call is not awaited — the caller proceeds before the operation completes, and errors are uncaught.

```js
// WRONG — promise is dropped
function save(data) {
  db.insert(data); // returns a Promise, not awaited
  return 'saved';
}

// CORRECT
async function save(data) {
  await db.insert(data);
  return 'saved';
}
```

**Finding text:** "Missing await — `db.insert` is async but not awaited; errors will be silently dropped and the caller will not see the result."

---

### Mutating Input Parameter

**What it is:** A function modifies its argument, creating unexpected side effects for the caller.

```python
# WRONG — modifies caller's list
def process(items):
    items.sort()
    return items[0]

# CORRECT — work on a copy
def process(items):
    sorted_items = sorted(items)
    return sorted_items[0]
```

**Finding text:** "Input mutation — `items.sort()` modifies the caller's list in place; use `sorted(items)` to avoid side effects."

---

### Inverted Boolean Condition

**What it is:** A condition is logically inverted, causing the code to run when it should not (or vice versa).

```js
// WRONG — runs when user is NOT admin
if (!user.isAdmin) {
  grantAdminAccess();
}

// CORRECT
if (user.isAdmin) {
  grantAdminAccess();
}
```

**Finding text:** "Inverted condition — `!user.isAdmin` grants admin access to non-admins."

---

## Performance Patterns

### N+1 Query

**What it is:** A loop executes a new database (or network) call per iteration, causing O(n) queries for a list of n items.

```python
# WRONG — one query per user
for user in users:
    user.orders = db.query("SELECT * FROM orders WHERE user_id = %s", user.id)

# CORRECT — one query total
user_ids = [u.id for u in users]
orders = db.query("SELECT * FROM orders WHERE user_id = ANY(%s)", user_ids)
order_map = group_by(orders, key=lambda o: o.user_id)
for user in users:
    user.orders = order_map.get(user.id, [])
```

**Finding text:** "N+1 query — `db.query` inside loop will execute once per user; batch with `WHERE user_id = ANY(%s)`."

---

### Unnecessary Collection Copy

**What it is:** A full copy of a large collection is made when a reference or iterator would suffice.

```python
# WRONG — copies entire list into memory
def first_match(items, pred):
    filtered = [x for x in items if pred(x)]
    return filtered[0] if filtered else None

# CORRECT — generator short-circuits at first match
def first_match(items, pred):
    return next((x for x in items if pred(x)), None)
```

**Finding text:** "Unnecessary copy — list comprehension builds full copy before returning first element; use `next()` with a generator."

---

## API & Reuse Patterns

### Breaking Change Without Migration

**What it is:** A public function's signature changes in a way that breaks existing callers, without a deprecation path.

```python
# BEFORE (public API)
def send_email(to, subject, body):

# AFTER (breaks callers who don't pass cc)
def send_email(to, subject, body, cc):
```

**Fix options:**

1. Add `cc=None` as a default (backward-compatible)
2. Keep old signature, add new overload
3. Deprecate old signature with a warning for one release cycle before removing

**Finding text:** "Breaking change — `send_email` now requires `cc`; existing callers will raise `TypeError`. Add `cc=None` default or version the API."

---

### Reinvented Utility

**What it is:** A new function duplicates functionality already in the codebase.

**How to detect:**

```bash
# Search for related concepts before declaring something new
git grep -n "debounce\|throttle" --
git grep -n "retry\|backoff" --
git grep -n "formatDate\|format_date\|toISO" --
```

**Finding text:** "Missed reuse — `debounce` already implemented at `src/utils/timing.mjs:34`; import from there instead."

---

## Plugin-Specific Patterns

### Invalid Agent Color

**What it is:** Agent frontmatter uses a hex code instead of a named color, which the Claude Code runtime does not support.

```yaml
# WRONG
color: '#198754'

# CORRECT — named values only
color: green
```

Valid values: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`

**Finding text:** "Invalid color — `'#198754'` is not a spec-allowed named color; change to `green`."

---

### Undocumented Frontmatter Field

**What it is:** A skill, agent, or command file contains a frontmatter field that is not in the Claude Code spec, causing it to be silently ignored.

```yaml
# WRONG — skill_composition is not a documented field
skill_composition: declined

# WRONG — name: in a command file is ignored (name derives from filename)
name: my-command
```

**Finding text:** "Undocumented frontmatter field — `skill_composition` is not in the subagent spec; remove to avoid confusion."

---

### Hook with Hardcoded Path

**What it is:** A hook command uses an absolute or machine-specific path instead of the portable `${CLAUDE_PLUGIN_ROOT}` variable.

```json
// WRONG — machine-specific
"command": "/Users/alice/projects/my-plugin/hooks/runner.mjs session start"

// CORRECT — portable
"command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/runner.mjs\" session start"
```

**Finding text:** "Hardcoded hook path — use `${CLAUDE_PLUGIN_ROOT}` for portability."

---

### Skill Description with Angle Brackets

**What it is:** A skill `description` field contains `<` or `>` characters, which the Claude Code manifest parser rejects.

```yaml
# WRONG
description: "Use for <feature> tasks"

# CORRECT
description: "Use for feature tasks"
```

**Finding text:** "Invalid description — angle brackets (`<`, `>`) are not allowed in skill `description` fields."
