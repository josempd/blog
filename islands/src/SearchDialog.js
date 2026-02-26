import { mount } from "svelte";
import SearchDialog from "./SearchDialog.svelte";

const el = document.getElementById("search-island");
if (el) {
  mount(SearchDialog, { target: el, props: { ...el.dataset } });
}
