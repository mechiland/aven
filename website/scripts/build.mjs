import { mkdir, rm, cp, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { render } from '../src/page.mjs';
import { locales } from '../src/content.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
await rm(root + 'dist', { recursive: true, force: true });
await mkdir(root + 'dist', { recursive: true });
await cp(root + 'public', root + 'dist', { recursive: true });
for (const [lang, content] of Object.entries(locales)) {
  await mkdir(root + `dist/${lang}`, { recursive: true });
  await writeFile(root + `dist/${lang}/index.html`, render(lang, content));
}
await writeFile(root + 'dist/index.html', render('zh-cn', locales['zh-cn']));
await writeFile(root + 'dist/404.html', `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found · Aven</title><link rel="stylesheet" href="/styles.css"><main class="not-found"><a class="wordmark" href="/">aven</a><h1>404</h1><p>Page not found / 页面不存在</p><a class="button" href="/">返回首页</a><a class="text-link" href="/en/">English home</a></main></html>`);
console.log('Built Aven: /, /zh-cn/, /en/ and 404.');
