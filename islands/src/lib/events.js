/**
 * Dispatch a custom event on window for cross-island communication.
 * @param {string} name
 * @param {Record<string, unknown>} detail
 */
export function dispatch(name, detail = {}) {
  window.dispatchEvent(new CustomEvent(name, { detail }));
}

/**
 * Listen for a custom event on window. Returns a cleanup function.
 * @param {string} name
 * @param {(detail: unknown) => void} handler
 */
export function listen(name, handler) {
  /** @type {EventListener} */
  const wrapped = (e) => handler(/** @type {CustomEvent} */ (e).detail);
  window.addEventListener(name, wrapped);
  return () => window.removeEventListener(name, wrapped);
}
