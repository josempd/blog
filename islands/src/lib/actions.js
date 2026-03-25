/**
 * Svelte action: calls callback when user clicks outside the node.
 * @param {HTMLElement} node
 * @param {() => void} callback
 */
export function clickOutside(node, callback) {
  function handleClick(/** @type {MouseEvent} */ e) {
    if (!node.contains(/** @type {Node | null} */ (e.target))) {
      callback();
    }
  }
  document.addEventListener("click", handleClick, true);
  return {
    destroy() {
      document.removeEventListener("click", handleClick, true);
    },
  };
}
