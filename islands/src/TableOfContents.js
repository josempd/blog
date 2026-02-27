import { mount } from "svelte";
import TableOfContents from "./TableOfContents.svelte";

const el = document.getElementById("toc-island");
if (el) {
  mount(TableOfContents, { target: el });
}
