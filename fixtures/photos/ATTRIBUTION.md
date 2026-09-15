# Photo and media fixtures

These are informational test files, not Aven artwork. Downloaded image/video
bytes are unchanged. Only the filenames were changed to exercise mixed Chinese
and Latin UI text. `manifest.json` records source URLs, sizes and SHA-256 hashes.

| File | Source and credit | Terms |
| --- | --- | --- |
| `00-地出-Earthrise.jpg` | [Earthrise](https://science.nasa.gov/resource/image-earthrise/), William Anders, Apollo 8 / NASA | [NASA media guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/) permit factual informational image use. This fixture does not imply NASA endorsement. |
| `01-瀑布横幅-EXIF-1.jpg` | [Pierre Bouillot](https://unsplash.com/photos/v15iOM6pWgI), annotations by Dave Perrett | [EXIF examples repository](https://github.com/recurser/exif-orientation-examples) distributes its test images under MIT; see `LICENSE-exif.txt`. |
| `02-瀑布竖幅-EXIF-1.jpg` | [John Salvino](https://unsplash.com/photos/1PPpwrTNkJI), annotations by Dave Perrett | Same MIT test-image terms. |
| `03-旋转方向-EXIF-6.jpg` | Pierre Bouillot, annotations by Dave Perrett | Same MIT test-image terms. Orientation 6, 1200 × 1800 stored pixels, should display as a correctly oriented landscape. |
| `04-透明色阶-Transparency.png` | Willem van Schaik, [PngSuite via Go](https://github.com/golang/go/tree/master/src/image/png/testdata/pngsuite) | Permission to use, copy and distribute for any purpose without fee; `LICENSE-pngsuite.txt`. Original 32 × 32 RGBA decoder fixture. |
| `05-花开-Flower.webm` | [MDN interactive-examples](https://github.com/mdn/interactive-examples/tree/main/live-examples/media/cc0-videos) contributors | CC0 1.0, `LICENSE-mdn.txt`. The current MDN shared-assets copy is byte-identical to this source. |

The EXIF images carry large English position labels intentionally: correctness
means “top” is actually at the top after decoding. Those labels are pixels in the
test photograph and are **not** evidence of Aven Latin typography. Use the real
Chinese filenames, native menus, and typography paragraphs for text evaluation.

The 32 × 32 transparency fixture should stay small under the no-upscale default;
zoom it manually when checking alpha edges. Do not call that expected behavior a
failure. Use `00-地出-Earthrise.jpg` for the ordinary photo-view screenshot.
