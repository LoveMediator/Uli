# LoveMediator Frontend

React + TypeScript + Vite frontend for the LoveMediator app.

## Commands

```bash
pnpm install
pnpm run dev
pnpm run build
pnpm run lint
pnpm run preview
```

## Source Structure

```text
src/
|- app/                    # app bootstrap, router, route preload, providers, app state
|- shared/                 # config, shared libs, http client, layout, ui, styles
|  |- api/
|  |- config/
|  |- layout/
|  |- lib/
|  |- styles/
|  `- ui/
`- domains/                # business domains
   |- auth/
   |- home/
   |- mediation/
   |- calendar/
   |- invite/
   `- profile/
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
- New code must live under `src/app`, `src/shared`, or `src/domains`.
- `dist` is a build artifact, not a maintenance target.
- Persist keys stay unchanged:
  - `love-mediator-auth`
  - `love-mediator-app`

## Build Output Structure

Production build splits assets by entry, page chunk, shared chunk, and vendor group:

```text
dist/assets/
|- entries/
|- chunks/
|  |- vendor/
|  `- *.js
`- styles/
   `- *.css
```
