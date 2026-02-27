<script>
  import { onMount } from "svelte";

  let activeId = $state("");
  let navEl = null;

  onMount(() => {
    navEl = document.getElementById("toc-nav");
    if (!navEl) return;

    const links = [...navEl.querySelectorAll("a[href^='#']")];
    const headingIds = links.map((a) => a.getAttribute("href").slice(1));
    const headings = headingIds
      .map((id) => document.getElementById(id))
      .filter(Boolean);

    if (headings.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            activeId = entry.target.id;
          }
        }
      },
      { rootMargin: "-80px 0px -70% 0px" },
    );

    for (const h of headings) observer.observe(h);

    return () => observer.disconnect();
  });

  $effect(() => {
    if (!navEl) return;

    for (const a of navEl.querySelectorAll("a[href^='#']")) {
      const id = a.getAttribute("href").slice(1);
      if (id === activeId) {
        a.classList.add("toc-active");
        a.scrollIntoView({ block: "nearest", behavior: "smooth" });
      } else {
        a.classList.remove("toc-active");
      }
    }
  });
</script>
