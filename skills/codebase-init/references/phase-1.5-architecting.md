# Phase 1.5 — Architecting & Convention Mapping

From the Phase 1 Environment Discovery data, extract these specific signals **before** proceeding to Phase 2 (Draft).

## Architecting Pattern Detection

Use file structure to identify the pattern:

| Pattern                   | Detection Signals                                                                             | Example                          |
| ------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------- |
| **MVC/REST API**          | `src/routes/`, `src/controllers/`, `src/models/` present                                      | Express app, Django, Spring Boot |
| **Modular/Feature-based** | `src/<feature>/` structure (e.g., `src/auth/`, `src/users/`) with per-feature files           | Feature-scoped modules           |
| **Layered/DDD**           | `src/api/`, `src/domain/`, `src/infra/`, `src/application/` clear separation                  | Domain-driven design             |
| **Monorepo**              | `turbo.json`, `pnpm-workspace.yaml`, `nx.json`, `lerna.json`, or `workspaces` in package.json | Workspace-based projects         |
| **Microservices**         | Multiple `package.json` / `go.mod` / etc. in separate dirs with independent tooling           | Services in separate paths       |
| **Monolith + CLI**        | Multiple entry points (`src/server.ts`, `src/cli.ts`, `cmd/`)                                 | API + CLI tools                  |
| **Unclear**               | Pattern doesn't match above → Ask the user                                                    | Don't guess                      |

## What to Extract

Document these findings concisely (not as prose):

- **Tech Stack:** Language(s), primary framework, ORM/database if applicable, build tool
- **Architecting:** Which pattern from table above?
- **Conventions:** If detectable from file structure:
  - File naming patterns (e.g., `.handler.ts`, `.service.ts`, `_test.go`)
  - Error handling approach (if visible from code)
  - Key module organization

**Verify, don't guess** — if a convention can't be confidently detected from static analysis, ask the user.

## Phase 1.5 → Phase 2 Template Decision Tree

### Decision 1: Is this a monorepo?

- Check for: `turbo.json`, `pnpm-workspace.yaml`, `nx.json`, `lerna.json`, or `workspaces` in package.json
- → YES: not a `--language` case — assemble by hand using `guide.md` §1 "Monorepo" pattern
- → NO: Continue to Decision 2

### Decision 2: What's the primary language?

This picks the `--language` value for Phase 2's `scaffold-agents-md` command (see `guide.md` §1):

| Language              | Marker Files                                         | `--language` value                                                           |
| --------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------- |
| JavaScript/TypeScript | `package.json` (Node env)                            | `node`                                                                       |
| Python                | `pyproject.toml`, `.venv/`, `poetry.lock`, `uv.lock` | `python`                                                                     |
| Go                    | `go.mod`, `go.sum`                                   | `go`                                                                         |
| Rust                  | `Cargo.toml`, `Cargo.lock`                           | `rust`                                                                       |
| Java                  | `pom.xml`, `build.gradle`                            | `java`                                                                       |
| C# / .NET             | `.csproj`, `.sln`                                    | `dotnet`                                                                     |
| JavaScript (Bun)      | `bun.lockb`                                          | `bun`                                                                        |
| Multiple languages    | Various (2+ languages)                               | not a single value — assemble by hand using `guide.md` §1 "Polyglot" pattern |

### Decision 3: Customize for Your Project

Once `scaffold-agents-md` has produced the skeleton:

1. Keep all **required sections** (see "Required Sections" in SKILL.md Phase 2) — they're already in the right order; don't reorder
2. Add any extra sections the project genuinely needs beyond the skeleton (e.g., a deployment-specific section) — only if grounded in real repo signals, never speculative
3. Drop generated sections that don't apply (rare — the skeleton is already minimal)
4. Fill **project-specific conventions** into the `## Key Conventions` TODO (3-7 lines; see `guide.md` §2.5)

For **monorepos specifically:**

- Are all packages the same language? Generate once with that `--language`, then add the Monorepo pattern on top
- Different languages per package? Generate a root skeleton for the dominant language, then add package-level AGENTS.md overrides (see `guide.md` §1)
