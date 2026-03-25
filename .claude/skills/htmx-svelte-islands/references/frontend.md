# Frontend Architecture: HTMX + Svelte 5 Islands

Reference for building and extending the jmpd.sh platform. Covers conventions,
decision rules, scaling patterns, and the path toward an AI Agent platform layer.

---

## Core Principle

**Server renders everything. JS enhances what the server can't.**

The default is Jinja2 + HTMX. Svelte only enters when the UI has state complexity
that doesn't belong on the server. This isn't a compromise — it's the architecture.
A page that works without JS and gets faster with it is strictly better than one
that requires JS to function at all.

---

## Decision Rule: HTMX vs Svelte Island

Ask one question: **does this interaction require client-side state?**

| Scenario | Use |
|---|---|
| Fetch and swap server-rendered HTML | HTMX |
| Form submission with validation feedback | HTMX |
| Infinite scroll / load more | HTMX |
| Tag filtering, search (full response from server) | HTMX |
| Polling for a status update | HTMX |
| Theme toggle (persisted in localStorage) | Svelte island |
| Search dialog with debounce + local results cache | Svelte island |
| Table of contents with scroll-tracked active state | Svelte island |
| Live token streaming from an AI response | Svelte island |
| Multi-step form with branching local state | Svelte island |
| Agent task timeline with WebSocket updates | Svelte island |

If you're unsure, default to HTMX. You can always promote an interaction to an island
if the server-rendered approach hits a wall. Going the other direction (demoting an
island) is more painful.

---

## HTMX Conventions

### Every request needs a target and a swap strategy

```html
<!-- Explicit. Never rely on implicit defaults. -->
<a
  href="/blog?tag=python"
  hx-get="/blog?tag=python"
  hx-target="#post-list"
  hx-swap="innerHTML"
  hx-push-url="true"
>python</a>
```

Always include the real `href`. HTMX enhances — it doesn't replace the link.

### Indicator on every async interaction

```html
<!-- Spinner lives next to the triggering element, not globally -->
<button
  hx-post="/api/v1/subscribe"
  hx-target="#subscribe-result"
  hx-swap="outerHTML"
  hx-indicator="#subscribe-spinner"
>
  Subscribe
  <span id="subscribe-spinner" class="htmx-indicator">…</span>
</button>
```

```css
/* In components.css */
.htmx-indicator { display: none; }
.htmx-request .htmx-indicator,
.htmx-request.htmx-indicator { display: inline; }
```

Never use a global spinner. Users need to know *what* is loading.

### Partials are first-class routes

Every HTMX target must have a corresponding route that returns *only* the partial,
not a full page. Use the `HX-Request` header to distinguish:

```python
# In pages/blog.py
@router.get("/blog")
async def blog_list(
    request: Request,
    tag: str | None = None,
    page: int = 1,
    templates: Jinja2Templates = Depends(get_templates),
):
    posts = await post_service.list(tag=tag, page=page)

    # HTMX request → return partial only
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/post_list.html",
            {"request": request, "posts": posts, "page": page},
        )

    # Full page request → return full layout
    return templates.TemplateResponse(
        "pages/blog_list.html",
        {"request": request, "posts": posts, "page": page},
    )
```

### Pagination with self-removing trigger

```html
<!-- Load more — appends below current results, replaces the trigger -->
<div id="load-more-trigger">
  <button
    hx-get="/blog?page={{ next_page }}"
    hx-target="#load-more-trigger"
    hx-swap="outerHTML"
    hx-indicator="#load-more-spinner"
  >
    Load more
    <span id="load-more-spinner" class="htmx-indicator">…</span>
  </button>
</div>
```

The partial response includes the next batch of posts *plus* a new trigger element,
or nothing if no more pages exist. When exhausted, the trigger disappears — no
client-side logic needed.

### Boost vs explicit hx-get

Use `hx-boost="true"` on `<nav>` for free SPA-style navigation on all internal links.
Use explicit `hx-get` when you need to control target, swap, or push-url behavior.
Never mix both on the same element.

```html
<!-- Navigation: boost is fine -->
<nav hx-boost="true">
  <a href="/">Home</a>
  <a href="/blog">Blog</a>
  <a href="/projects">Projects</a>
</nav>

<!-- Interaction with controlled target: explicit -->
<form
  hx-post="/api/v1/contact"
  hx-target="#contact-form"
  hx-swap="outerHTML"
>
```

### OOB swaps for multi-zone updates

When an action needs to update two parts of the page at once:

```html
<!-- Primary response swaps the button -->
<button id="like-btn" ...>❤️ 12</button>

<!-- OOB swap updates the header counter without a second request -->
<span id="header-like-count" hx-swap-oob="true">12</span>
```

Use this sparingly. If you need more than two OOB targets, the page design is
probably wrong.

---

## Svelte 5 Islands: Shared Library

**Create this before writing any island.** Three files in `islands/src/lib/` are the
foundation everything else builds on. Without them you'll re-solve the same problems
in each island independently.

```
islands/src/lib/
  registry.js    ← idempotent mount registry + hx-boost compatibility
  events.js      ← window-based cross-island event bus
  actions.js     ← reusable Svelte actions for DOM behavior
```

### `registry.js` — solves the boost + island lifecycle bug

With `hx-boost="true"` on nav, HTMX swaps `<body>` on navigation. Islands from the
previous page remain mounted; new page islands don't initialize because their
`index.js` already ran once. The registry makes every mount idempotent and re-runs
all mounts after every HTMX settle.

```javascript
// islands/src/lib/registry.js
const registry = new Map(); // name → mountFn

export function register(name, mountFn) {
  registry.set(name, mountFn);
  mountFn(); // initial mount attempt
}

export function requireDataset(el, keys) {
  const missing = keys.filter((k) => !(k in el.dataset));
  if (missing.length) {
    throw new Error(
      `[${el.id}] missing required dataset attributes: ${missing.join(", ")}`
    );
  }
  return el.dataset;
}

// Re-run all mounts after every HTMX navigation
document.addEventListener("htmx:afterSettle", () => {
  registry.forEach((mountFn) => mountFn());
});
```

Every `mountFn` must be idempotent — guard with `el.dataset.mounted`:

```javascript
// islands/src/islands/ThemeToggle/index.js
import { mount } from "svelte";
import { register, requireDataset } from "../../lib/registry.js";
import ThemeToggle from "./ThemeToggle.svelte";

register("ThemeToggle", () => {
  const el = document.getElementById("theme-toggle-island");
  if (!el || el.dataset.mounted) return;
  el.dataset.mounted = "true";

  const dataset = requireDataset(el, ["theme"]);
  mount(ThemeToggle, {
    target: el,
    props: { initialTheme: dataset.theme },
  });
});
```

### `events.js` — cross-island communication

Islands are isolated by design. The `window` event bus is how they coordinate without
coupling. This is the only sanctioned mechanism for cross-island state:

```javascript
// islands/src/lib/events.js

export function dispatch(name, detail = {}) {
  window.dispatchEvent(new CustomEvent(name, { detail }));
}

export function listen(name, handler) {
  window.addEventListener(name, handler);
  return () => window.removeEventListener(name, handler); // returns cleanup fn
}
```

Usage inside any island:

```javascript
// Dispatching
import { dispatch } from "../../lib/events.js";
dispatch("agent:status", { runId, status: "done" });

// Listening — return the cleanup fn from $effect so Svelte handles removal
import { listen } from "../../lib/events.js";
$effect(() => {
  return listen("agent:status", (e) => {
    if (e.detail.runId === runId) status = e.detail.status;
  });
});
```

Canonical event names for the agent platform:

| Event | Payload | Dispatched by | Consumed by |
|---|---|---|---|
| `agent:status` | `{ runId, status }` | AgentResponse | AgentTimeline, RunControls |
| `agent:token` | `{ runId, text }` | AgentResponse | (future: transcript export) |
| `agent:toolcall` | `{ runId, tool }` | AgentResponse | ToolCallViewer |

### `actions.js` — reusable DOM behavior

Svelte actions attach DOM behavior to elements without coupling component trees.
Since islands can't share component trees, actions are how you share behavior:

```javascript
// islands/src/lib/actions.js

// Auto-scroll to bottom as content streams in
export function scrollToBottom(node) {
  const observer = new MutationObserver(() => {
    node.scrollTop = node.scrollHeight;
  });
  observer.observe(node, { childList: true, subtree: true });
  return { destroy: () => observer.disconnect() };
}

// Copy to clipboard — for tool call inputs/outputs, code blocks
export function copyOnClick(node, text) {
  const handler = () => navigator.clipboard.writeText(text);
  node.addEventListener("click", handler);
  return {
    update: (newText) => { text = newText; },
    destroy: () => node.removeEventListener("click", handler),
  };
}

// Click outside — for search dialog, any modal island
export function clickOutside(node, callback) {
  const handler = (e) => { if (!node.contains(e.target)) callback(); };
  document.addEventListener("mousedown", handler);
  return { destroy: () => document.removeEventListener("mousedown", handler) };
}
```

Usage in components:

```svelte
<script>
  import { scrollToBottom, copyOnClick, clickOutside } from "../../lib/actions.js";
</script>

<!-- Streaming output auto-scrolls -->
<pre class="response-tokens" use:scrollToBottom>{tokens}</pre>

<!-- Tool call result with one-click copy -->
<pre use:copyOnClick={toolOutput}>{toolOutput}</pre>

<!-- Search dialog closes on outside click -->
<div class="dialog" use:clickOutside={close}>...</div>
```

---

## Svelte 5 Islands: Conventions

### File structure

```
islands/
  package.json
  vite.config.js
  src/
    lib/
      registry.js
      events.js
      actions.js
    islands/
      ThemeToggle/
        ThemeToggle.svelte
        index.js
      SearchDialog/
        SearchDialog.svelte
        index.js
      AgentResponse/
        AgentResponse.svelte
        index.js
      AgentTimeline/
        AgentTimeline.svelte
        index.js
      ToolCallViewer/
        ToolCallViewer.svelte
        index.js
```

### Embedding in Jinja2 templates

```html
<!-- Mount target — data-* attributes supply initial props -->
<div
  id="agent-response-island"
  data-agent-id="{{ agent.id }}"
  data-run-id="{{ run.id }}"
  data-autostart="{{ 'true' if run.status == 'running' else 'false' }}"
></div>
```

Scripts load via `page_islands` in `base.html` — never inline a `<script>` next to
the mount target:

```html
{# base.html — load only what this page declares #}
{% for island in page_islands | default([]) %}
<script type="module" src="/static/dist/islands/{{ island }}.js"></script>
{% endfor %}
```

Set per page in the route context:

```python
return templates.TemplateResponse(
    "pages/agent_run.html",
    {
        "request": request,
        "run": run,
        "page_islands": ["AgentResponse", "AgentTimeline", "ToolCallViewer"],
    },
)
```

### Component conventions (Svelte 5 runes)

```svelte
<script>
  // Props via $props() — not export let
  let { initialTheme = "light" } = $props();
  let theme = $state(initialTheme);

  function toggle() {
    theme = theme === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }
</script>

<button onclick={toggle} aria-label="Toggle theme">
  {theme === "light" ? "☀️" : "🌙"}
</button>
```

**Rules:**
- `$props()`, `$state()`, `$derived()`, `$effect()` — no Options API remnants.
- No global stores. Cross-island state goes through `events.js` only.
- No fetch calls to third-party APIs. Always proxy through FastAPI.
- `$effect` cleanup: return the unsubscribe function. The registry's
  `htmx:afterSettle` listener handles re-initialization.

### Error handling — standard pattern

Svelte 5 has no built-in error boundaries. Use this pattern consistently — don't
invent per-island variations:

```svelte
<script>
  let status = $state("idle"); // idle | loading | error | done
  let errorMessage = $state("");

  async function run() {
    status = "loading";
    try {
      await doWork();
      status = "done";
    } catch (err) {
      status = "error";
      errorMessage = err.message ?? "Something went wrong";
      console.error("[IslandName]", err);
    }
  }
</script>

{#if status === "error"}
  <div class="island-error" role="alert">
    {errorMessage}
    <button onclick={run}>Retry</button>
  </div>
{/if}
```

---

## Vite Config

Auto-discovers all `index.js` entry points — adding a new island requires no config
change:

```javascript
// islands/vite.config.js
import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { readdirSync, existsSync } from "fs";
import { resolve } from "path";

const islandsDir = resolve(__dirname, "src/islands");

const entries = Object.fromEntries(
  readdirSync(islandsDir)
    .filter((name) => existsSync(resolve(islandsDir, name, "index.js")))
    .map((name) => [name, resolve(islandsDir, name, "index.js")])
);

export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: "../backend/app/static/dist/islands",
    emptyOutDir: true,
    rollupOptions: {
      input: entries,
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: "[name]-[hash].js",
        assetFileNames: "[name][extname]",
      },
    },
  },
});
```

---

## Component Development Sandbox

No Storybook. Storybook solves a team coordination problem — design handoff, shared
component libraries, visual regression at scale. Here there's one operator, islands
tightly coupled to Jinja2 context, and a rapidly evolving prop contract. The overhead
of maintaining stories for islands that change their `data-*` contract every sprint
is real cost for near-zero benefit.

The right tool is a `/dev/components` route — only mounted when `DEBUG=True`:

```python
# backend/app/pages/dev.py
# Registered in main.py only when settings.DEBUG is True

@router.get("/dev/components")
async def component_sandbox(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
):
    return templates.TemplateResponse(
        "pages/dev/component_sandbox.html",
        {
            "request": request,
            "page_islands": ["ThemeToggle", "SearchDialog", "AgentResponse"],
            "fixtures": {
                "agent_id": "dev-agent-001",
                "run_id": "dev-run-001",
                "theme": "light",
            },
        },
    )
```

Revisit Storybook if the platform becomes a product with multiple engineers and a
design handoff requirement.

---

## CSS Architecture

Five files, loaded in order via `<link>` in `base.html`. No `@import`. No build step.

```
static/css/
  tokens.css      ← custom properties: colors, spacing, type, radius, shadow
  base.css        ← reset + body + typography defaults
  components.css  ← reusable patterns: card, button, tag, badge, nav, footer
  syntax.css      ← Pygments code highlighting (generated)
  utilities.css   ← single-purpose helpers: sr-only, truncate, visually-hidden
```

### Token conventions

```css
/* tokens.css */
:root {
  /* Spacing: geometric scale */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-7: 3rem;
  --space-8: 4rem;

  /* Type */
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;

  /* Color: neutrals + blue accent */
  --color-bg: #fff;
  --color-surface: #f9fafb;
  --color-surface-subtle: #f9fafb;
  --color-border: #e5e7eb;
  --color-text: #1a1a1a;
  --color-text-muted: #6b7280;
  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-code-bg: #f3f4f6;

  /* Component tokens */
  --radius-sm: 0.25rem;
  --radius: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);

  /* Prose */
  --prose-width: 65ch;

  /* Typography */
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: "SFMono-Regular", Menlo, Consolas, monospace;

  /* Motion */
  --duration-fast: 150ms;
  --duration-normal: 200ms;
}
```

Never use arbitrary values inline. If a value isn't in `tokens.css`, it doesn't exist.

---

## AI Agent Platform Extension

### 1. Streaming: SSE + Svelte

`hx-ext="sse"` swaps entire DOM nodes — it can't append characters to a streaming
element without flicker. Use a Svelte island for any AI response that streams.

**SSE auth caveat:** `EventSource` cannot set custom headers, including `Authorization`.
Use cookie-based auth for SSE endpoints. Set a session cookie on login alongside the
JWT — the simplest approach that works with the existing auth layer. Don't defer
this decision; retrofitting auth onto streaming endpoints is painful.

**FastAPI SSE endpoint:**

```python
# backend/app/api/routes/agents.py
from fastapi.responses import StreamingResponse

@router.post("/agents/{agent_id}/run")
async def run_agent(agent_id: str, payload: AgentRunRequest):
    async def event_stream():
        async for chunk in agent_service.stream(agent_id, payload):
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

**Svelte island consuming it:**

```svelte
<!-- AgentResponse.svelte -->
<script>
  import { dispatch } from "../../lib/events.js";
  import { scrollToBottom } from "../../lib/actions.js";

  let { agentId, runId, autostart = false } = $props();

  let tokens = $state("");
  let status = $state("idle"); // idle | running | done | error
  let errorMessage = $state("");

  async function startStream() {
    status = "running";
    dispatch("agent:status", { runId, status: "running" });
    try {
      const res = await fetch(`/api/v1/agents/${agentId}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_id: runId }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        for (const line of decoder.decode(value).split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6);
          if (data === "[DONE]") {
            status = "done";
            dispatch("agent:status", { runId, status: "done" });
            return;
          }
          try {
            const chunk = JSON.parse(data);
            tokens += chunk.text ?? "";
            dispatch("agent:token", { runId, text: chunk.text });
          } catch {}
        }
      }
    } catch (err) {
      status = "error";
      errorMessage = err.message ?? "Stream failed";
      dispatch("agent:status", { runId, status: "error" });
      console.error("[AgentResponse]", err);
    }
  }

  $effect(() => { if (autostart) startStream(); });
</script>

<div class="agent-response" data-status={status}>
  {#if status === "idle"}
    <button onclick={startStream}>Run</button>
  {:else if status === "error"}
    <div class="island-error" role="alert">
      {errorMessage}
      <button onclick={startStream}>Retry</button>
    </div>
  {:else}
    <pre class="response-tokens" use:scrollToBottom>{tokens}</pre>
    {#if status === "running"}
      <span class="cursor-blink" aria-hidden="true">▋</span>
    {/if}
  {/if}
</div>
```

### 2. Agent Task Lifecycle: HTMX polling

For background jobs, HTMX polling is the right tool. No WebSocket overhead, server
owns the state. The pending partial includes `hx-trigger`; the complete partial
doesn't — polling stops automatically:

```python
@router.get("/agents/tasks/{task_id}/status")
async def task_status(request: Request, task_id: str, ...):
    task = await task_service.get(task_id)
    template = (
        "partials/task_status_pending.html"
        if task.status in ("pending", "running")
        else "partials/task_status_complete.html"
    )
    return templates.TemplateResponse(template, {"request": request, "task": task})
```

```html
<!-- partials/task_status_pending.html — polls itself -->
<div
  id="task-status-{{ task.id }}"
  hx-get="/agents/tasks/{{ task.id }}/status"
  hx-trigger="every 2s"
  hx-target="this"
  hx-swap="outerHTML"
>
  <span class="status-dot status-dot--running"></span>
  {{ task.status }} — {{ task.progress_message }}
</div>

<!-- partials/task_status_complete.html — no trigger, polling stops -->
<div id="task-status-{{ task.id }}">
  <span class="status-dot status-dot--done"></span>
  Completed in {{ task.duration_ms }}ms
  <a href="/agents/tasks/{{ task.id }}/result">View result</a>
</div>
```

### 3. Agent Run Page: hybrid layout

```
pages/agent_run.html
  ├── Task header         (server-rendered, static)
  ├── Tool call log       (HTMX polled partial — server owns this state)
  ├── Streaming response  (Svelte island — client owns rendering)
  └── Run controls        (HTMX — form submissions, cancellation)
```

Islands that need to react to HTMX swapping content around them should listen on
`htmx:afterSwap`. For example, `TableOfContents` must rebuild its heading list after
HTMX loads a new post — otherwise it shows stale headings from the previous render:

```javascript
// islands/src/islands/TableOfContents/index.js
register("TableOfContents", () => {
  const el = document.getElementById("toc-island");
  if (!el || el.dataset.mounted) return;
  el.dataset.mounted = "true";

  const instance = mount(TableOfContents, { target: el });

  document.addEventListener("htmx:afterSwap", () => {
    instance.rebuild?.();
  });
});
```

### 4. New scopes and files for the agent platform

```
backend/app/
  models/agent.py          ← Agent, AgentRun, ToolCall, TaskResult (SQLModel)
  schemas/agent.py         ← AgentCreate, AgentRunResponse, ToolCallEvent (Pydantic)
  crud/agent.py            ← get_agent, create_run, append_tool_call, finish_run
  services/agent.py        ← orchestration: validate, dispatch, stream, cancel
  api/routes/agents.py     ← JSON API: /api/v1/agents/*, SSE endpoint
  pages/agents.py          ← HTML pages: /agents, /agents/{id}, /agents/runs/{id}
  pages/dev.py             ← /dev/components sandbox (DEBUG only)
  templates/
    pages/
      agent_list.html
      agent_detail.html
      agent_run.html
      dev/component_sandbox.html
    partials/
      tool_call_list.html
      tool_call_item.html
      task_status_pending.html
      task_status_complete.html
```

Add scope `agents` to commit convention and `docs/scopes.md`.

---

## Template Checklist

Before shipping any new page or partial:

- [ ] Real `href` on every link (HTMX enhances, doesn't replace)
- [ ] `hx-indicator` on every async interaction
- [ ] Semantic HTML: `<article>`, `<section>`, `<time datetime>`, heading hierarchy
- [ ] Visible focus styles on all interactive elements
- [ ] Islands load via `page_islands` — never inline `<script>` next to mount target
- [ ] `requireDataset()` called for all required `data-*` props in `index.js`
- [ ] `el.dataset.mounted` guard in every mount function (idempotent)
- [ ] Error state rendered and exposed — no silent failures
- [ ] Cross-island state via `events.js`, not DOM reads or shared globals
- [ ] No CDN script tags — everything vendored
- [ ] Only `tokens.css` custom properties for spacing, type, color
- [ ] HTMX partial routes check `HX-Request` and return only the partial
- [ ] SSE endpoints use cookie auth, not `Authorization` header

---

## Anti-Patterns

**Don't use HTMX for streaming tokens.** `hx-ext="sse"` swaps entire DOM nodes — it
can't append characters to a streaming element without flicker. Use a Svelte island.

**Don't use Svelte for content the server already owns.** A blog post body, a project
card, a tag list — pure server-render territory. Adding an island to wrap static
content adds JS weight for no benefit.

**Don't fetch third-party APIs directly from islands.** Proxy everything through
FastAPI. This keeps auth centralized and avoids CORS surprises.

**Don't share state between islands via the DOM.** Use `events.js`. Don't read
`data-*` attributes off sibling elements, don't reach into another island's mount
target.

**Don't skip the registry for any island that needs to survive boost navigation.**
If the island mounts once and is never re-checked, it dies on the second page load.
All islands use `register()`.

**Don't let HTMX responses return full pages.** Always check `HX-Request` in the
route handler. A full HTML document returned to a partial target renders `<html>`
inside a `<div>`.

**Don't use arbitrary spacing or font sizes.** If the value isn't in `tokens.css`,
it doesn't exist.

**Don't use `EventSource` for SSE.** It can't set `Authorization`. Use cookie-based
session auth for SSE endpoints and the `fetch` + `ReadableStream` pattern instead.