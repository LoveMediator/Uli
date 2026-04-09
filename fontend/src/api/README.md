# API Layer

`src/api` is now a backward-compatible facade.

Real implementations live in:

- `src/shared/api/http` for the HTTP client and response helpers
- `src/shared/api/types` for protocol types
- `src/domains/*/api` for domain-level API modules

Use these newer entry points for ongoing development:

- `@/domains/auth`
- `@/domains/calendar`
- `@/domains/home`
- `@/domains/mediation`

The old `src/api/*` files remain only to avoid breaking existing imports during migration.
