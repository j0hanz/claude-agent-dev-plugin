# Code Review Pattern Catalog

Extended reference for the reviewer subagent's findings (Tiers 1-4). See [patterns_examples.md](patterns_examples.md) for code examples.

## Security Patterns (Tier 1 - Blocking)

- **Command Injection**: User input reaches a shell command without sanitization. Use `execFile`/array args or an allowlist.
- **SQL Injection**: User input concatenated into a SQL string. Use parameterized queries.
- **Hardcoded Secret**: Credential, key, or token stored in source. Use `process.env`/environment variables.
- **Path Traversal**: User input constructs paths without validation. Verify path starts with base directory path.
- **Insecure Deserialization**: Deserializing untrusted data with formats enabling arbitrary object instantiation (e.g., `yaml.load`, `pickle`). Use safe/JSON parsers.

## Correctness Patterns (Tier 2 - Blocking)

- **Swallowed Error**: Exception caught and ignored. Log with context or re-raise.
- **Off-by-One**: Loop/slice boundary is incorrect (e.g. `< arr.length - 1`). Use proper boundaries.
- **Async Without Await**: Async call not awaited, dropping promise or ignoring failure. Use `await`.
- **Mutating Input Parameter**: Modifying arguments in-place, causing side effects. Copy arguments before mutating.
- **Inverted Boolean Condition**: A condition logically inverted. Correct the logic.

## Performance Patterns (Tier 3 - Advisory)

- **N+1 Query**: Database/network call inside a loop. Batch queries (e.g., `WHERE id = ANY(...)`).
- **Unnecessary Collection Copy**: Copying collection when reference or generator is sufficient (e.g., list comprehension vs generator).

## API & Reuse Patterns (Tier 4 - Advisory)

- **Breaking Change Without Migration**: Changing signature without a default value or deprecation path.
- **Reinvented Utility**: Duplicating logic already in the codebase (e.g., debouncing, throttling).

## Plugin-Specific Patterns (Tier 4 - Advisory)

Review these only for Claude Code plugins:

- **Invalid Agent Color**: Using hex values (e.g. `'#198754'`) instead of named colors (`green`, `red`, etc.) in frontmatter.
- **Undocumented Frontmatter**: Frontmatter fields not in the spec (e.g., `name` in command frontmatter).
- **Hook with Hardcoded Path**: Hook using absolute/local paths. Use `${CLAUDE_PLUGIN_ROOT}`.
- **Skill Description with Angle Brackets**: Using `<` or `>` in skill description frontmatter, which breaks parsing.
