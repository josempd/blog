---
name: htmx-svelte-islands
description: >
  Architecture guide and code patterns for building with HTMX + Svelte 5 islands
  on a server-rendered backend (FastAPI + Jinja2, Django, Flask, or similar).
  Use this skill whenever the user is working with HTMX, Svelte islands, SSE
  streaming, or any hybrid server-render + progressive enhancement frontend
  pattern. Triggers include: asking about HTMX vs Svelte decisions, building
  agent UIs with streaming output, setting up Svelte islands in a non-SvelteKit
  project, handling island lifecycle with hx-boost, cross-island communication,
  Svelte actions, component sandboxing without Storybook, SSE auth, or any
  mention of Jinja2 + HTMX + Svelte in the same stack. Also use when the user
  asks about frontend architecture for an AI agent platform, token streaming UI,
  or async task status polling.
---

# HTMX + Svelte 5 Islands

Patterns for hybrid server-render + progressive enhancement frontends.
The full reference is in `references/frontend.md` — read it when you need
specific code patterns, checklist items, or anti-patterns.

---

## Core Principle

Server renders everything. JS enhances what the server can't.

Default: Jinja2 + HTMX. Svelte enters only when the UI has client-side state
complexity that doesn't belong on the server.

---

## Decision Rule

**Does this interaction require client-side state?**

- No → HTMX (fetch + swap server-rendered HTML, polling, forms, pagination)
- Yes → Svelte island (streaming, local state, localStorage persistence, complex
  multi-step interactions)

When unsure, default to HTMX. Promoting to an island later is easier than
demoting one.

---

## Shared Library — Always Create First

Before writing any island, create `islands/src/lib/` with three files.
These solve fundamental problems that every island will hit:

| File | Solves |
|---|---|
| `registry.js` | Islands dying on `hx-boost` navigation; idempotent mounts |
| `events.js` | Cross-island communication without coupling |
| `actions.js` | Shared DOM behavior (scrollToBottom, copyOnClick, clickOutside) |

→ See `references/frontend.md#svelte-5-islands-shared-library` for full
implementations with copy-paste code.

---

## Key Patterns (quick reference)

**HTMX:** Always include real `href`. Always `hx-indicator`. Always check
`HX-Request` header in routes. Partials are first-class routes.

**Islands:** All mounts use `register()` from registry, not bare `if (el)`.
Props from `data-*` validated with `requireDataset()`. Error state always
rendered. Scripts load via `page_islands` context var, not inline.

**SSE streaming:** Use `fetch` + `ReadableStream`, not `EventSource`.
`EventSource` can't set `Authorization` headers. Use cookie auth for SSE.

**Cross-island state:** Only via `events.js` `dispatch`/`listen`. Never via
DOM reads or shared globals.

**HTMX + island coexistence:** Islands must listen on `htmx:afterSwap` if
their content depends on HTMX-swapped DOM (e.g. TableOfContents rebuilding
headings after a partial load).

---

## AI Agent Platform (streaming + polling)

For agent UIs combining streaming responses and async task status:

- **Token streaming** → Svelte island with `fetch` + `ReadableStream` +
  `scrollToBottom` action + dispatch to `events.js`
- **Task status** → HTMX polling with self-removing trigger (pending partial
  includes `hx-trigger`, complete partial does not — polling stops automatically)
- **Hybrid page** → tool call log via HTMX polling, streaming response via
  Svelte island, controls via HTMX forms

→ See `references/frontend.md#ai-agent-platform-extension` for full patterns
including `AgentResponse.svelte`, FastAPI SSE endpoint, and agent run page layout.

---

## No Storybook

Storybook solves a team coordination problem that doesn't exist here. Use a
`/dev/components` route (mounted only when `DEBUG=True`) with fixture data
instead. See `references/frontend.md#component-development-sandbox`.

---

## Checklist (shipping any page or partial)

Read the full checklist in `references/frontend.md#template-checklist` before
reviewing or shipping. Key items agents miss most often:

- `requireDataset()` on every mount that uses `data-*` props
- `el.dataset.mounted` guard in every `register()` call
- `page_islands` context var in every route that uses islands
- SSE endpoints use cookie auth, not `Authorization` header

---

## When to read `references/frontend.md`

Read it when you need:
- Full working code for any pattern (HTMX, islands, streaming, polling)
- The complete shared library implementations (`registry.js`, `events.js`, `actions.js`)
- Vite config for auto-discovery of islands
- CSS token conventions
- Anti-patterns section (full list)
- Agent platform file/scope structure