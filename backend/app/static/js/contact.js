(function() {
  var u = 'contact', d = 'jmpd.sh';
  document.querySelectorAll('[data-contact]').forEach(function(el) {
    el.href = 'mailto:' + u + '@' + d;
  });
})();
