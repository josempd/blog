import { mount } from "svelte";
import { register } from "../../lib/registry.js";
import TableOfContents from "./TableOfContents.svelte";

register("TableOfContents", () => {
  const el = document.getElementById("toc-island");
  if (!el || el.dataset.mounted) return;
  el.dataset.mounted = "true";
  mount(TableOfContents, { target: el });
});
