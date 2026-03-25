import { mount } from "svelte";
import { register, requireDataset } from "../../lib/registry.js";
import SearchDialog from "./SearchDialog.svelte";

register("SearchDialog", () => {
  const el = document.getElementById("search-island");
  if (!el || el.dataset.mounted) return;
  requireDataset(el, ["endpoint"]);
  el.dataset.mounted = "true";
  mount(SearchDialog, { target: el, props: { endpoint: el.dataset.endpoint } });
});
