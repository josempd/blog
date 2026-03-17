document.addEventListener("click", async function (e) {
  var btn = e.target.closest("[data-copy-md]");
  if (!btn) return;
  try {
    var res = await fetch(btn.dataset.copyMd);
    var text = await res.text();
    await navigator.clipboard.writeText(text);
    var label = btn.querySelector("span");
    var original = label.textContent;
    label.textContent = "Copied!";
    setTimeout(function () { label.textContent = original; }, 1500);
  } catch (_) {
    /* clipboard or fetch unavailable — silently degrade */
  }
});
