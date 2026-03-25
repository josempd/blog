document.addEventListener('click', function(e) {
  if (!e.target.closest('#theme-toggle')) return;
  var html = document.documentElement;
  var current = html.getAttribute('data-theme');
  var next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
});
