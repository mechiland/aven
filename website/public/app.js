const data = JSON.parse(document.getElementById('scene-data').textContent);
const menu = document.querySelector('.menu-button');
const nav = document.getElementById('navigation');
const closeMenu = () => {
  menu.setAttribute('aria-expanded', 'false');
  menu.setAttribute('aria-label', menu.dataset.open);
  nav.classList.remove('is-open');
};
menu.addEventListener('click', () => {
  const open = menu.getAttribute('aria-expanded') !== 'true';
  menu.setAttribute('aria-expanded', String(open));
  menu.setAttribute('aria-label', open ? menu.dataset.close : menu.dataset.open);
  nav.classList.toggle('is-open', open);
});
nav.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMenu));
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });

const tabs = [...document.querySelectorAll('[data-tab]')];
function selectTab(tab, focus = false) {
  tabs.forEach(t => {
    const selected = t === tab;
    t.setAttribute('aria-selected', String(selected));
    t.tabIndex = selected ? 0 : -1;
    document.getElementById(t.getAttribute('aria-controls')).hidden = !selected;
  });
  if (focus) tab.focus();
}
tabs.forEach((tab, i) => {
  tab.addEventListener('click', () => selectTab(tab));
  tab.addEventListener('keydown', e => {
    const keys = { ArrowRight: (i + 1) % tabs.length, ArrowLeft: (i - 1 + tabs.length) % tabs.length, Home: 0, End: tabs.length - 1 };
    if (Object.hasOwn(keys, e.key)) { e.preventDefault(); selectTab(tabs[keys[e.key]], true); }
  });
});

const range = document.getElementById('compare-range');
const stage = document.querySelector('.compare-stage');
function updateRange() {
  stage.style.setProperty('--split', `${range.value}%`);
  range.setAttribute('aria-valuetext', `${data.before} ${range.value}%, Aven ${100 - Number(range.value)}%`);
}
range.addEventListener('input', updateRange);
document.querySelectorAll('[data-compare]').forEach(button => button.addEventListener('click', () => {
  const id = button.dataset.compare;
  const index = data.ids.indexOf(id);
  document.querySelectorAll('[data-compare]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
  for (const [imageId, source] of [['before-image', 'stock'], ['after-image', 'aven']]) {
    const img = document.getElementById(imageId);
    img.src = `/assets/${source}-${id}.png`;
    img.alt = `${source === 'stock' ? data.before : 'Aven'} · ${data.labels[index]}`;
    document.getElementById(`${source}-original`).href = img.src;
  }
  document.getElementById('compare-detail').textContent = data.details[index];
  range.value = '50';
  updateRange();
}));

const dialog = document.getElementById('lightbox');
let lightboxTrigger;
document.querySelectorAll('[data-lightbox]').forEach(link => link.addEventListener('click', e => {
  if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || typeof dialog.showModal !== 'function') return;
  e.preventDefault();
  lightboxTrigger = link;
  const img = document.getElementById('lightbox-image');
  img.src = link.href;
  img.alt = link.querySelector('img')?.alt || link.getAttribute('aria-label') || link.textContent.trim() || data.screenshot;
  document.getElementById('lightbox-original').href = link.href;
  dialog.showModal();
  document.documentElement.classList.add('modal-open');
  document.getElementById('lightbox-close').focus();
}));
document.getElementById('lightbox-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); });
dialog.addEventListener('close', () => {
  document.documentElement.classList.remove('modal-open');
  lightboxTrigger?.focus({ preventScroll: true });
});

// Keep the current section when changing the page language.
document.querySelectorAll('.language, .footer-languages a').forEach(link => link.addEventListener('click', () => {
  if (location.hash) link.hash = location.hash;
}));
