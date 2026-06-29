# Code Review Pattern Examples

This document contains code examples for the patterns listed in the main catalog.

---

## Security Patterns

### Command Injection

```js
// WRONG — shell=true with user input
exec(`git clone ${userInput}`);

// CORRECT — use array form, no shell interpolation
execFile('git', ['clone', userInput]);
```

### SQL Injection

```python
# WRONG
cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")

# CORRECT — parameterized
cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
```

### Hardcoded Secret

```js
// WRONG
const apiKey = 'sk-1234abcd...';

// CORRECT
const apiKey = process.env.API_KEY;
```

### Path Traversal

```python
# WRONG
open(os.path.join(base_dir, user_filename))

# CORRECT
safe = os.path.realpath(os.path.join(base_dir, user_filename))
if not safe.startswith(os.path.realpath(base_dir)):
    raise ValueError("Path traversal attempt")
```

### Insecure Deserialization

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

### Off-by-One

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

### Async Without Await

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

### Mutating Input Parameter

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

### Inverted Boolean Condition

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

---

## Performance Patterns

### N+1 Query

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

### Unnecessary Collection Copy

```python
# WRONG — copies entire list into memory
def first_match(items, pred):
    filtered = [x for x in items if pred(x)]
    return filtered[0] if filtered else None

# CORRECT — generator short-circuits at first match
def first_match(items, pred):
    return next((x for x in items if pred(x)), None)
```

---

## Plugin-Specific Patterns

### Invalid Agent Color

```yaml
# WRONG
color: '#198754'

# CORRECT — named values only
color: green
```

### Hook with Hardcoded Path

```json
// WRONG — machine-specific
"command": "/Users/alice/projects/my-plugin/hooks/runner.mjs session start"

// CORRECT — portable
"command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/runner.mjs\" session start"
```

### Skill Description with Angle Brackets

```yaml
# WRONG
description: "Use for <feature> tasks"

# CORRECT
description: "Use for feature tasks"
```
