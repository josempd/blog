<script>
  let { endpoint = "/search" } = $props();

  let open = $state(false);
  let query = $state("");
  let resultsHtml = $state("");
  let loading = $state(false);
  let error = $state("");
  let activeIndex = $state(-1);

  /** @type {HTMLInputElement | undefined} */
  let inputEl;
  /** @type {HTMLDivElement | undefined} */
  let dialogEl;
  /** @type {ReturnType<typeof setTimeout> | undefined} */
  let debounceTimer;

  function openDialog() {
    open = true;
    query = "";
    resultsHtml = "";
    error = "";
    activeIndex = -1;
    setTimeout(() => inputEl?.focus(), 0);
  }

  function closeDialog() {
    open = false;
    query = "";
    resultsHtml = "";
    error = "";
    activeIndex = -1;
  }

  function isInputFocused() {
    const tag = document.activeElement?.tagName;
    return (
      tag === "INPUT" ||
      tag === "TEXTAREA" ||
      tag === "SELECT" ||
      /** @type {HTMLElement | null} */ (document.activeElement)?.isContentEditable
    );
  }

  function handleKeydown(/** @type {KeyboardEvent} */ e) {
    if (!open) {
      if (e.key === "/" && !isInputFocused()) {
        e.preventDefault();
        openDialog();
      }
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        openDialog();
      }
      return;
    }

    if (e.key === "Escape") {
      e.preventDefault();
      closeDialog();
      return;
    }

    const links = /** @type {NodeListOf<HTMLElement>} */ (
      dialogEl?.querySelectorAll(".post-card h2 a") ?? []
    );
    if (e.key === "ArrowDown") {
      e.preventDefault();
      activeIndex = Math.min(activeIndex + 1, links.length - 1);
      links[activeIndex]?.focus();
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (activeIndex <= 0) {
        activeIndex = -1;
        inputEl?.focus();
      } else {
        activeIndex--;
        links[activeIndex]?.focus();
      }
    }
  }

  async function doSearch(/** @type {string} */ q) {
    if (!q.trim()) {
      resultsHtml = "";
      error = "";
      return;
    }
    loading = true;
    error = "";
    try {
      const res = await fetch(`${endpoint}?q=${encodeURIComponent(q.trim())}`, {
        headers: { "HX-Request": "true" },
      });
      if (!res.ok) throw new Error(`Search failed (${res.status})`);
      resultsHtml = await res.text();
      activeIndex = -1;
    } catch (err) {
      error = err instanceof Error ? err.message : "Search failed";
      resultsHtml = "";
    } finally {
      loading = false;
    }
  }

  function handleInput(/** @type {Event} */ e) {
    query = /** @type {HTMLInputElement} */ (e.target).value;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => doSearch(query), 200);
  }

  function handleBackdropClick(/** @type {MouseEvent} */ e) {
    if (e.target === e.currentTarget) {
      closeDialog();
    }
  }

  function handleDialogKeydown(/** @type {KeyboardEvent} */ e) {
    if (e.key !== "Tab") return;
    const focusable = /** @type {NodeListOf<HTMLElement>} */ (
      dialogEl?.querySelectorAll(
        'input, a[href], button, [tabindex]:not([tabindex="-1"])'
      ) ?? []
    );
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  $effect(() => {
    const link = /** @type {HTMLElement | null} */ (document.querySelector(".nav-search"));
    if (link) link.style.display = "none";
    return () => {
      if (link) link.style.display = "";
    };
  });
</script>

<svelte:window onkeydown={handleKeydown} />

<button
  class="search-trigger"
  onclick={openDialog}
  aria-label="Search posts (press / or Cmd+K)"
>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
  <span class="search-shortcut"><kbd>/</kbd></span>
</button>

{#if open}
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="search-overlay"
  onclick={handleBackdropClick}
  onkeydown={handleDialogKeydown}
>
  <div
    class="search-dialog"
    role="dialog"
    aria-modal="true"
    aria-label="Search posts"
    bind:this={dialogEl}
  >
    <div class="search-dialog-header">
      <input
        bind:this={inputEl}
        type="search"
        class="search-dialog-input"
        placeholder="Search posts..."
        value={query}
        oninput={handleInput}
        aria-label="Search posts"
      />
      <button
        class="search-dialog-close"
        onclick={closeDialog}
        aria-label="Close search"
      >
        <kbd>Esc</kbd>
      </button>
    </div>
    <div class="search-dialog-results">
      {#if loading}
        <p class="search-dialog-status">Searching...</p>
      {:else if error}
        <p class="search-dialog-status" role="alert">Error: {error}</p>
      {:else if resultsHtml}
        {@html resultsHtml}
      {:else if query.trim()}
        <p class="search-dialog-status">No results for "{query}".</p>
      {:else}
        <p class="search-dialog-status">Type to search posts.</p>
      {/if}
    </div>
  </div>
</div>
{/if}
