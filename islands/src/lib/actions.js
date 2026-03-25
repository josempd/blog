/**
 * Svelte action: calls callback when user clicks outside the node.
 */
export function clickOutside(node, callback) {
  function handleClick(e) {
    if (!node.contains(e.target)) {
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
