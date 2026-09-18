import { repository, release, docs, scenes } from './content.mjs';
import { iso, downloadReady } from './release.mjs';

const chevron = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="m9 5 7 7-7 7" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const expand = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M14 4h6v6M20 4l-7 7M10 20H4v-6m0 6 7-7" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const arrow = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M12 4v15m-6-6 6 6 6-6M5 21h14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const globe = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/><ellipse cx="12" cy="12" rx="4" ry="9" stroke="currentColor" stroke-width="1.5"/><path d="M3 12h18" stroke="currentColor" stroke-width="1.5"/></svg>';
const esc = (s) => s.replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

export function render(lang, c) {
  const ids = ['everyday', 'compare', 'typography'];
  const assetVersion = `union-${iso.version}`;
  return `<!doctype html>
<html lang="${c.lang}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#fafbfa"><title>${c.title}</title>
  <meta name="description" content="${esc(c.description)}">
  <meta property="og:type" content="website"><meta property="og:title" content="${esc(c.title)}"><meta property="og:description" content="${esc(c.description)}">
  <link rel="canonical" href="/${lang}/"><link rel="alternate" hreflang="en" href="/en/"><link rel="alternate" hreflang="zh-CN" href="/zh-cn/"><link rel="alternate" hreflang="x-default" href="/">
  <link rel="icon" href="/assets/aven.svg" type="image/svg+xml"><link rel="stylesheet" href="/styles.css">
  <link rel="preload" href="/assets/aven-mail.png" as="image"><script src="/app.js" defer></script>
</head>
<body>
<a class="skip" href="#main">${c.skip}</a>
<header class="site-header">
  <nav class="nav wrap" aria-label="${c.navLabel}">
    <a class="wordmark" href="/${lang}/" aria-label="Aven"><img src="/assets/aven.svg" alt="" width="30" height="30">aven</a>
    <div class="nav-links" id="navigation">${c.nav.map((n, i) => `<a href="#${ids[i]}">${n}</a>`).join('')}</div>
    <div class="nav-actions"><a class="language" href="/${c.switchLang}/" lang="${c.switchLang === 'en' ? 'en' : 'zh-CN'}" hreflang="${c.switchLang === 'en' ? 'en' : 'zh-CN'}">${globe}<span>${c.switch}</span></a><a class="button button-small" href="#download">${c.get}</a><button class="menu-button" aria-expanded="false" aria-controls="navigation" aria-label="${c.menu}" data-open="${c.menu}" data-close="${c.closeMenu}"><span></span><span></span></button></div>
  </nav>
</header>
<main id="main">
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-copy wrap">
      <p class="eyebrow">${c.eyebrow}</p>
      <h1 id="hero-title">${c.hero}</h1>
      <p class="hero-intro">${c.intro}</p>
      <div class="hero-actions"><a class="button" href="#download">${c.get}</a><a class="text-link" href="#compare">${c.explore}${chevron}</a></div>
      <a class="release-line" href="#download">${c.version}${chevron}</a>
    </div>
    <figure class="hero-figure">
      <a href="/assets/aven-mail.png" class="hero-screen" data-lightbox aria-label="${c.screenshot}"><img src="/assets/aven-mail.png" alt="${c.heroAlt}" width="1920" height="1200" fetchpriority="high"><span class="expand-image">${expand}</span></a>
      <figcaption>${c.heroCaption}</figcaption>
    </figure>
  </section>

  <section class="everyday section" id="everyday" aria-labelledby="daily-title">
    <div class="section-heading wrap"><div><p class="eyebrow">${c.dailyEyebrow}</p><h2 id="daily-title">${c.dailyTitle}</h2></div><p class="section-intro">${c.dailyIntro}</p></div>
    <div class="experience wrap">
      <div class="tabs" role="tablist" aria-label="${c.tabsLabel}">${scenes.map((s, i) => `<button id="tab-${s.id}" role="tab" aria-controls="panel-${s.id}" aria-selected="${i === 0}" tabindex="${i === 0 ? '0' : '-1'}" data-tab="${s.id}">${c.labels[i]}</button>`).join('')}</div>
      ${scenes.map((s, i) => `<div class="experience-panel" role="tabpanel" id="panel-${s.id}" aria-labelledby="tab-${s.id}" tabindex="0" ${i === 0 ? '' : 'hidden'}>
        <div class="experience-copy"><div><span class="app-name">${s.app}</span><span class="capture-note">${c.captureLabel} ${s.round} · <a href="${repository}/blob/main/${s.aven}">${c.captureSource}</a></span><h3>${c.sceneTitle[i]}</h3></div><p>${c.sceneText[i]}</p></div>
        <a class="screenshot-link" data-lightbox href="/assets/aven-${s.id}.png" aria-label="${c.screenshot} — ${c.labels[i]}"><img src="/assets/aven-${s.id}.png" alt="Union · ${c.labels[i]} — ${c.sceneTitle[i]}" width="1920" height="1200" loading="lazy" decoding="async"><span class="expand-image">${expand}</span></a>
      </div>`).join('')}
      <p class="image-note">${c.imageNote}</p>
    </div>
  </section>

  <section class="comparison section" id="compare" aria-labelledby="compare-title">
    <div class="wrap">
      <div class="center-heading"><p class="eyebrow">${c.compareEyebrow}</p><h2 id="compare-title">${c.compareTitle}</h2><p class="section-intro">${c.compareIntro}</p></div>
      <div class="compare-tabs" aria-label="${c.compareLabel}">${scenes.map((s, i) => `<button data-compare="${s.id}" aria-pressed="${i === 0}">${c.labels[i]}</button>`).join('')}</div>
      <figure class="compare-figure">
        <div class="compare-stage" style="--split:50%">
          <img class="compare-after" id="after-image" src="/assets/aven-files.png" alt="Union · ${c.labels[0]}" width="1920" height="1200" loading="lazy">
          <img class="compare-before" id="before-image" src="/assets/stock-files.png" alt="${c.before} · ${c.labels[0]}" width="1920" height="1200" loading="lazy">
          <span class="compare-badge badge-before">${c.before}</span><span class="compare-badge badge-after">${c.after}</span>
          <span class="compare-divider" aria-hidden="true"><span>‹<b></b>›</span></span>
          <input type="range" class="compare-range" id="compare-range" min="0" max="100" value="50" aria-label="${c.slider}" aria-valuetext="${c.before} 50%, ${c.after} 50%">
        </div>
        <div class="compare-toolbar"><a id="stock-original" href="/assets/stock-files.png" data-lightbox>${c.before} ${expand}</a><span class="drag-hint">↔ ${c.drag}</span><a id="aven-original" href="/assets/aven-files.png" data-lightbox>${c.after} ${expand}</a></div>
        <figcaption><p id="compare-detail" class="compare-detail" aria-live="polite">${c.compareDetails[0]}</p><p class="compare-note">${c.compareNote}</p></figcaption>
      </figure>
    </div>
  </section>

  <section class="typography section" id="typography" aria-labelledby="type-title">
    <div class="wrap type-layout"><div class="type-copy"><p class="eyebrow">${c.typeEyebrow}</p><h2 id="type-title">${c.typeTitle}</h2><p class="section-intro">${c.typeIntro}</p><a class="text-link" data-lightbox href="/assets/aven-typography.png">${c.typeLink}${chevron}</a></div>
    <div class="type-specimen"><span class="specimen-label">Aa <span>字</span></span><p class="specimen-chinese" lang="zh-CN">${c.typeSample}</p><p class="specimen-english" lang="en">${c.typeEnglish}</p><div class="specimen-bottom"><span>${c.typeMeta}</span><span>${c.typeFamily}</span></div></div></div>
  </section>

  <section class="dock section" aria-labelledby="dock-title"><div class="wrap dock-layout">
    <div><p class="eyebrow">${c.dockEyebrow}</p><h2 id="dock-title">${c.dockTitle}</h2><p class="section-intro">${c.dockText}</p><a class="text-link" data-lightbox href="/assets/aven-mail.png">${c.dockLink}${chevron}</a></div>
    <a class="screenshot-link" data-lightbox href="/assets/aven-mail.png" aria-label="${c.dockLink}"><img src="/assets/aven-mail.png" alt="${c.heroAlt}" width="1920" height="1200" loading="lazy"><span class="expand-image">${expand}</span></a>
  </div></section>

  <section class="foundation section" aria-labelledby="foundation-title"><div class="wrap">
    <div class="center-heading"><p class="eyebrow">${c.foundationEyebrow}</p><h2 id="foundation-title">${c.foundationTitle}</h2><p class="section-intro">${c.foundationIntro}</p></div>
    <div class="foundation-grid">${c.foundation.map((item, i) => `<article><span class="foundation-mark" aria-hidden="true">${['↺', '＋', '⌘'][i]}</span><p class="app-name">${item[0]}</p><h3>${item[1]}</h3><p>${item[2]}</p>${i === 2 ? `<a class="text-link" href="${repository}">${c.source}${chevron}</a>` : ''}</article>`).join('')}</div>
  </div></section>

  <section class="download section" id="download" aria-labelledby="download-title"><div class="wrap">
    <img class="download-logo" src="/assets/aven.svg" width="84" height="84" alt="Aven"><p class="eyebrow">${c.downloadEyebrow}</p><h2 id="download-title">${c.downloadTitle}</h2><p class="section-intro">${c.downloadIntro}</p>
    <div class="download-actions">${downloadReady ? `<a class="button" href="${esc(iso.url)}" download="${esc(iso.filename)}">${c.download}${arrow}</a>` : `<span class="button button-pending" aria-disabled="true">${c.pendingDownload}</span>`}<a class="text-link" href="${docs}/ISO.md">${c.guide}${chevron}</a></div><p class="platform">${c.platform}</p><p class="prerelease">${c.prerelease}</p>
    ${downloadReady ? `<dl class="release-metadata"><div><dt>ISO</dt><dd>${esc(iso.filename)}</dd></div><div><dt>${c.sizeLabel}</dt><dd>${(iso.bytes / 1024 ** 3).toFixed(2)} GiB · ${new Intl.NumberFormat(lang).format(iso.bytes)} bytes</dd></div><div class="checksum"><dt>${c.checksumLabel}</dt><dd><code>${iso.sha256}</code></dd></div></dl>` : `<p class="release-pending">${c.pendingNote}</p>`}<a class="metadata-link" href="/release.json">${c.manifestLabel}</a>
    <details class="install-details"><summary>${c.installTitle}<span aria-hidden="true">+</span></summary><ol>${c.installSteps.map(s => `<li>${s}</li>`).join('')}</ol><p>${c.installNote}</p></details>
  </div></section>
</main>

<footer><div class="wrap">
  <div class="footer-top"><a class="wordmark" href="/${lang}/">aven</a><p>${c.footerLine}</p></div>
  <div class="evidence-note"><p><strong>${c.evidenceTitle}${lang === 'en' ? '.' : '。'}</strong> ${c.evidenceText}</p><p>${c.limits}</p><div class="evidence-links"><a href="${docs}/UNION-ISO-0.3.1.md">${c.evidence}</a><a href="${docs}/UNION-SEQUOIA.md">${c.critic}</a><a href="/credits.txt">${c.credits}</a></div></div>
  <div class="footer-bottom"><span>© 2026 ${c.copyright}</span><div><a href="${repository}">${c.footerSource}</a><a href="${downloadReady ? release : `${repository}/releases`}">${c.releaseNotes}</a></div><div class="footer-languages" aria-label="${c.languageLabel}">${globe}<a href="/zh-cn/" lang="zh-CN" ${lang === 'zh-cn' ? 'aria-current="page"' : ''}>简体中文</a><span>/</span><a href="/en/" lang="en" ${lang === 'en' ? 'aria-current="page"' : ''}>English</a></div></div>
</div></footer>
<dialog id="lightbox" aria-label="${c.screenshot}"><div class="lightbox-toolbar"><span>${c.screenshot}</span><div><a id="lightbox-original" href="/assets/aven-files.png" target="_blank" rel="noopener">${c.original}${expand}</a><button id="lightbox-close" aria-label="${c.dialogClose}">×</button></div></div><div class="lightbox-image"><img id="lightbox-image" alt="" width="1920" height="1200"></div><p>${c.zoomHint}</p></dialog>
<script type="application/json" id="scene-data">${JSON.stringify({ids: scenes.map(s => s.id), labels: c.labels, details: c.compareDetails, before: c.before, after: c.after, assetVersion, screenshot: c.screenshot}).replaceAll('<', '\\u003c')}</script>
</body></html>`.replaceAll(/((?:href|src)="\/assets\/[^"?]+)(")/g, `$1?v=${assetVersion}$2`);
}
