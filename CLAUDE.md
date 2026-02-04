# CLAUDE.md

## Development Principles

1. **Ask clarifying questions** — Always ask as many questions as needed before implementing. Never assume.
2. **Check existing code first** — Before implementing any function or system, search the current codebase to see if it already exists.
3. **Reuse existing code above all else** — Prefer wiring into existing functions and modules. This ensures easy integration.
4. **Recommend session splits** — If a task is too large for one session, recommend splitting it up.
5. **Modularity** — The project must be as modular as possible. Small, focused modules with clear responsibilities.
6. **TDD** — Follow Test-Driven Development. Write tests first, then implement to make them pass.
7. **150-line file limit** — All Python files must stay under 150 lines. If a file exceeds this, refactor or split it.
8. **No hardcoded secrets or paths** — Never hardcode secrets, credentials, file paths, URLs, or environment-specific values in source code. All such values must come from `config.json` or environment variables.

## Related Projects (Read-Only)

The following sibling projects provide context for this project. **They must NEVER be modified — read only.**

- `/Users/work/Desktop/Folders/Projects/GmailAsReferee`
- `/Users/work/Desktop/Folders/Projects/GmailAsAdmin`
- `/Users/work/Desktop/Folders/Projects/GmailAsServerRami/GmailAsServer`
- `/Users/work/Desktop/Folders/Projects/GmailAsPlayer`
