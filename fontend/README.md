# LoveMediator Frontend

React + TypeScript + Vite frontend for the LoveMediator app.

## Commands

```bash
pnpm install
pnpm run dev
pnpm run build
pnpm run build:readable
pnpm run assets:readable
pnpm run lint
pnpm run test
pnpm run test:e2e
```

## Source Structure

```text
src/
|- app/                    # bootstrap, router, route preload, providers, app state
|- shared/                 # config, shared libs, http client, layout, ui, styles
|  |- api/
|  |- config/
|  |- layout/
|  |- lib/
|  |- styles/
|  `- ui/
|- domains/                # business domains
|  |- auth/
|  |- home/
|  |- mediation/
|  |- calendar/
|  |- invite/
|  `- profile/
`- test/                   # vitest + msw helpers
```

Each domain follows the same internal shape:

```text
domains/<name>/
|- api/
|- model/
|- ui/
|- page/
`- index.ts
```

## Architecture Rules

- `app` can import domain business APIs and stores from `@/domains/*`.
- Page components live under `domains/*/page` and are lazy-loaded through `app/routes`.
- `shared` must stay reusable and should not depend on domain business logic.
- Legacy folders like `src/pages`, `src/components`, `src/api`, `src/hooks`, `src/stores`, `src/types` are compatibility shims only.
- Persist keys stay unchanged:
  - `love-mediator-auth`
  - `love-mediator-app`

## Build Output Structure

Production build now splits the old monolithic asset into maintainable chunks:

```text
dist/assets/
|- entries/               # boot entry
|- chunks/
|  |- vendor/             # react, data, forms, visual libs
|  |- LoginPage-*.js
|  |- HomePage-*.js
|  |- MediationPage-*.js
|  `- ...
`- styles/
   `- index-*.css
```

`pnpm run assets:readable` formats every generated JS/CSS asset recursively under `dist/assets`.

## Testing Baseline

- Unit/component: Vitest + Testing Library
- API mocking: MSW
- Smoke E2E: Playwright

Production build excludes `*.test.ts(x)` and `src/test/**`, so test scaffolding does not affect shipped code.
