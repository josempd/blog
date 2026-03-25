(function() {
  var u = 'contact', d = 'jmpd.sh';
  function initContact() {
    document.querySelectorAll('[data-contact]').forEach(function(el) {
      el.href = 'mailto:' + u + '@' + d;
    });
  }
  initContact();
  document.addEventListener('htmx:afterSettle', initContact);
})();
