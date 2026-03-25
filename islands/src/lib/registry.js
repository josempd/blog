const registry = new Map();

/**
 * Register an island mount function. Runs immediately and on every
 * htmx:afterSettle (so islands survive hx-boost navigation).
 */
export function register(name, mountFn) {
  registry.set(name, mountFn);
  mountFn();
}

/**
 * Validate that required data-* attributes exist on an element.
 * Throws a clear error if any are missing.
 */
export function requireDataset(el, keys) {
  for (const key of keys) {
    if (!(key in el.dataset)) {
      throw new Error(`Island mount: missing data-${key} on #${el.id}`);
    }
  }
}

document.addEventListener("htmx:afterSettle", () => {
  for (const mountFn of registry.values()) {
    mountFn();
  }
});
