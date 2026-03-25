document.addEventListener('click', function(e) {
  var toggle = e.target.closest('.nav-menu-toggle');
  if (!toggle) return;
  var menu = document.getElementById('nav-menu');
  if (!menu) return;
  var expanded = toggle.getAttribute('aria-expanded') === 'true';
  toggle.setAttribute('aria-expanded', String(!expanded));
  menu.classList.toggle('nav-menu--open');
});

document.addEventListener('keydown', function(e) {
  if (e.key !== 'Escape') return;
  var toggle = document.querySelector('.nav-menu-toggle');
  if (!toggle || toggle.getAttribute('aria-expanded') !== 'true') return;
  var menu = document.getElementById('nav-menu');
  toggle.setAttribute('aria-expanded', 'false');
  if (menu) menu.classList.remove('nav-menu--open');
  toggle.focus();
});
