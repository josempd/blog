/**
 * Dispatch a custom event on window for cross-island communication.
 */
export function dispatch(name, detail = {}) {
  window.dispatchEvent(new CustomEvent(name, { detail }));
}

/**
 * Listen for a custom event on window. Returns a cleanup function.
 */
export function listen(name, handler) {
  const wrapped = (e) => handler(e.detail);
  window.addEventListener(name, wrapped);
  return () => window.removeEventListener(name, wrapped);
}
