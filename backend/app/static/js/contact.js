(function() {
  var u = 'jmpd.chemist230', d = 'passmail.net';
  document.querySelectorAll('[data-contact]').forEach(function(el) {
    el.href = 'mailto:' + u + '@' + d;
  });
})();
