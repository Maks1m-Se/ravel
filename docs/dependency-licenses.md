# Prototype dependency and license inventory

The18October current-app private preview adds a separate
[artifact-specific review](windows-preview-notices.md) and
[repeatable build/checklist](windows-preview.md). Actual manifests, component
analysis, intact pinned source archives, tagged core npm provenance and decoded
font records supersede historical folder counts for that candidate only.
Public redistribution findings remain open; the historical inspection below
and prior evidence are preserved.

Inspected **11 October 2026**; scoped to the current Windows workbook experiment,
not a completed release/legal review. Established runtime/build/review locks are unchanged; a separate build candidate is recorded below.
Sources: actual installed `METADATA`, `RECORD`, license/NOTICE files from `.venv`,
the isolated packaging checkout environment and `outputs/workbook-review-env`.
Tables cover **48 runtime**, **7 build**, **4 review** pins (**58 distinct**).
Versioned PyPI links identify distributions; installed files, not project names,
were used for the license classification. Full inspected texts, source paths and
SHA-256 hashes are preserved in [third-party-notices.txt](third-party-notices.txt).
Each section is headed by package/version; that file also retains vendor notices,
Playwright's driver/Node notices, frontend headers and the actual CPython license.
It is a notice collection for review, not proof that all bundle obligations are met.

## Python distributions

Runtime pins come from [requirements.lock](../experiments/workbook/requirements.lock).
Build-only pins come from [requirements-build.lock](../experiments/workbook/requirements-build.lock);
PyInstaller's embedded bootloader/runtime hooks still affect redistributed output.
Review pins come from [requirements-review.lock](../experiments/workbook/requirements-review.lock)
and are not executable runtime requirements. Shared `typing_extensions` appears
in both relevant locks. License expressions below use installed metadata where
available, with direct text inspection for absent/ambiguous metadata.

### Runtime

| Distribution/version | Inspected license terms | Installed evidence |
| --- | --- | --- |
| [aiofiles 25.1.0](https://pypi.org/project/aiofiles/25.1.0/) | Apache-2.0 | `LICENSE`, `NOTICE` |
| [aiohappyeyeballs 2.7.1](https://pypi.org/project/aiohappyeyeballs/2.7.1/) | PSF-2.0 | `LICENSE` |
| [aiohttp 3.14.4](https://pypi.org/project/aiohttp/3.14.4/) | Apache-2.0 AND MIT | `LICENSE.txt`, `LICENSE` |
| [aiosignal 1.4.0](https://pypi.org/project/aiosignal/1.4.0/) | Apache-2.0 | `LICENSE` |
| [annotated-doc 0.0.5](https://pypi.org/project/annotated-doc/0.0.5/) | MIT | `LICENSE` |
| [annotated-types 0.8.0](https://pypi.org/project/annotated-types/0.8.0/) | MIT | `LICENSE` |
| [anyio 4.15.1](https://pypi.org/project/anyio/4.15.1/) | MIT | `LICENSE` |
| [attrs 26.1.0](https://pypi.org/project/attrs/26.1.0/) | MIT | `LICENSE` |
| [bidict 0.24.1](https://pypi.org/project/bidict/0.24.1/) | MPL-2.0 | `LICENSE` |
| [certifi 2026.7.22](https://pypi.org/project/certifi/2026.7.22/) | MPL-2.0 | `LICENSE` |
| [click 8.5.0](https://pypi.org/project/click/8.5.0/) | BSD-3-Clause | `LICENSE.txt` |
| [docutils 0.23](https://pypi.org/project/docutils/0.23/) | Public domain + BSD exceptions; GPL editor file (see COPYING) | `COPYING.rst` |
| [fastapi 0.143.0](https://pypi.org/project/fastapi/0.143.0/) | MIT | `LICENSE` |
| [frozenlist 1.8.0](https://pypi.org/project/frozenlist/1.8.0/) | Apache-2.0 | `LICENSE` |
| [h11 0.16.0](https://pypi.org/project/h11/0.16.0/) | MIT | `LICENSE.txt` |
| [httpcore 1.0.9](https://pypi.org/project/httpcore/1.0.9/) | BSD-3-Clause | `LICENSE.md` |
| [httptools 0.8.0](https://pypi.org/project/httptools/0.8.0/) | MIT | `LICENSE`, `LICENSE-MIT`, `LICENSE` |
| [httpx 0.28.1](https://pypi.org/project/httpx/0.28.1/) | BSD-3-Clause | `LICENSE.md` |
| [idna 3.20](https://pypi.org/project/idna/3.20/) | BSD-3-Clause | `LICENSE.md` |
| [ifaddr 0.2.0](https://pypi.org/project/ifaddr/0.2.0/) | MIT | `LICENSE.txt` |
| [itsdangerous 2.2.0](https://pypi.org/project/itsdangerous/2.2.0/) | BSD-3-Clause | `LICENSE.txt` |
| [Jinja2 3.1.6](https://pypi.org/project/Jinja2/3.1.6/) | BSD-3-Clause | `LICENSE.txt` |
| [markdown2 2.5.5](https://pypi.org/project/markdown2/2.5.5/) | MIT | `LICENSE.txt` |
| [MarkupSafe 3.0.4](https://pypi.org/project/MarkupSafe/3.0.4/) | BSD-3-Clause | `LICENSE.txt` |
| [multidict 6.9.1](https://pypi.org/project/multidict/6.9.1/) | Apache-2.0 | `LICENSE` |
| [nicegui 3.18.0](https://pypi.org/project/nicegui/3.18.0/) | MIT | `LICENSE` |
| [opentelemetry-api 1.45.1](https://pypi.org/project/opentelemetry-api/1.45.1/) | Apache-2.0 | `LICENSE` |
| [orjson 3.13.0](https://pypi.org/project/orjson/3.13.0/) | MPL-2.0 AND (Apache-2.0 OR MIT) | `LICENSE-APACHE`, `LICENSE-MIT`, `LICENSE-MPL-2.0` |
| [propcache 0.5.4](https://pypi.org/project/propcache/0.5.4/) | Apache-2.0 | `LICENSE`, `NOTICE` |
| [pydantic 2.14.0](https://pypi.org/project/pydantic/2.14.0/) | MIT | `LICENSE` |
| [pydantic_core 2.50.0](https://pypi.org/project/pydantic_core/2.50.0/) | MIT | `LICENSE` |
| [Pygments 2.21.0](https://pypi.org/project/Pygments/2.21.0/) | BSD-2-Clause | `AUTHORS`, `LICENSE` |
| [python-dotenv 1.2.4](https://pypi.org/project/python-dotenv/1.2.4/) | BSD-3-Clause | `LICENSE` |
| [python-engineio 4.14.0](https://pypi.org/project/python-engineio/4.14.0/) | MIT | `LICENSE` |
| [python-multipart 0.0.32](https://pypi.org/project/python-multipart/0.0.32/) | Apache-2.0 | `LICENSE.txt` |
| [python-socketio 5.17.0](https://pypi.org/project/python-socketio/5.17.0/) | MIT | `LICENSE` |
| [PyYAML 6.0.3](https://pypi.org/project/PyYAML/6.0.3/) | MIT | `LICENSE` |
| [simple-websocket 1.1.0](https://pypi.org/project/simple-websocket/1.1.0/) | MIT | `LICENSE` |
| [starlette 1.7.0](https://pypi.org/project/starlette/1.7.0/) | BSD-3-Clause | `LICENSE.md` |
| [tinycss2 1.5.1](https://pypi.org/project/tinycss2/1.5.1/) | BSD-3-Clause | `LICENSE` |
| [typing-inspection 0.4.4](https://pypi.org/project/typing-inspection/0.4.4/) | MIT | `LICENSE` |
| [typing_extensions 4.16.0](https://pypi.org/project/typing_extensions/4.16.0/) | PSF-2.0 | `LICENSE` |
| [uvicorn 0.54.0](https://pypi.org/project/uvicorn/0.54.0/) | BSD-3-Clause | `LICENSE.md` |
| [watchfiles 1.3.0](https://pypi.org/project/watchfiles/1.3.0/) | MIT | `LICENSE` |
| [webencodings 0.6.1](https://pypi.org/project/webencodings/0.6.1/) | BSD-3-Clause | `LICENSE` |
| [websockets 17.2](https://pypi.org/project/websockets/17.2/) | BSD-3-Clause | `LICENSE` |
| [wsproto 1.3.2](https://pypi.org/project/wsproto/1.3.2/) | MIT | `LICENSE` |
| [yarl 1.25.1](https://pypi.org/project/yarl/1.25.1/) | Apache-2.0 | `LICENSE`, `NOTICE` |

### Build

| Distribution/version | Inspected license terms | Installed evidence |
| --- | --- | --- |
| [altgraph 0.17.5](https://pypi.org/project/altgraph/0.17.5/) | MIT | `LICENSE` |
| [packaging 26.3](https://pypi.org/project/packaging/26.3/) | Apache-2.0 OR BSD-2-Clause | `LICENSE`, `LICENSE.APACHE`, `LICENSE.BSD` |
| [pefile 2024.8.26](https://pypi.org/project/pefile/2024.8.26/) | MIT | `LICENSE` |
| [pyinstaller 6.20.0](https://pypi.org/project/pyinstaller/6.20.0/) | GPL-2.0-or-later + bootloader exception; Apache-2.0 runtime hooks | `COPYING.txt` |
| [pyinstaller-hooks-contrib 2026.8](https://pypi.org/project/pyinstaller-hooks-contrib/2026.8/) | GPL-2.0-or-later build hooks; Apache-2.0 runtime hooks | `LICENSE` |
| [pywin32-ctypes 0.2.3](https://pypi.org/project/pywin32-ctypes/0.2.3/) | BSD-3-Clause | `LICENSE.txt` |
| [setuptools 65.5.0](https://pypi.org/project/setuptools/65.5.0/) | MIT | `LICENSE` |

### Review

| Distribution/version | Inspected license terms | Installed evidence |
| --- | --- | --- |
| [playwright 1.58.0](https://pypi.org/project/playwright/1.58.0/) | Apache-2.0 | `LICENSE`, `LICENSE`, `LICENSE`, `NOTICE`, `ThirdPartyNotices.txt` |
| [pyee 13.0.1](https://pypi.org/project/pyee/13.0.1/) | MIT | `LICENSE` |
| [greenlet 3.5.6](https://pypi.org/project/greenlet/3.5.6/) | MIT AND PSF-2.0 | `LICENSE`, `LICENSE.PSF` |
| [typing_extensions 4.16.0](https://pypi.org/project/typing_extensions/4.16.0/) | PSF-2.0 | `LICENSE` |

## Frontend and binary redistribution inspection

NiceGUI 3.18.0's wrapper collects its **whole package** as data, including unused
element bundles. Inspection covered `static/`, `templates/index.html`, eleven
element `package.json` manifests and the copied executable folder. The page
loads Vue, Quasar, Socket.IO, font CSS and NiceGUI assets; its styling/import
machinery may load other bundled resources. Being unused by this workbook does
not remove redistribution obligations for an asset shipped in the folder.

| Shipped resource | Established evidence | Remaining scope |
| --- | --- | --- |
| Vue 3.5.22 | Exact version and MIT attribution in JS; [tagged license](https://github.com/vuejs/core/blob/v3.5.22/LICENSE) copied | Retain copyright and complete MIT text |
| Quasar 2.18.5 | Exact version/MIT header; [tagged license](https://github.com/quasarframework/quasar/blob/quasar-v2.18.5/LICENSE) copied | CSS modifications and upstream attribution must remain identifiable |
| Socket.IO client 4.8.1 | Exact version/MIT header; [tagged monorepo license](https://github.com/socketio/socket.io/blob/socket.io-client%404.8.1/packages/socket.io-client/LICENSE) copied | Review bundled engine/parser subcomponents too |
| DOMPurify 3.4.16 | Header names Apache-2.0 and MPL-2.0; [tagged LICENSE](https://github.com/cure53/DOMPurify/blob/3.4.16/LICENSE) retrieved as Apache text | Resolve header/text discrepancy and embedded Babel helper notices before selecting terms |
| Tailwind 4.1.13 | Version literal in JS; [tagged MIT license](https://github.com/tailwindlabs/tailwindcss/blob/v4.1.13/LICENSE) copied | Audit embedded/transitive code notices; minified JS has no leading license banner |
| Immutable 5.1.9 `immutable.es.js` | Complete MIT permission/copyright header retained in notice collection | Version literal `5.1.9` confirmed in the shipped module; retain the complete header |
| UnoCSS runtime/presets; Sass compiled JS | Actual shipped JS inspected, no complete leading notice found | Exact versions, component licenses and transitive notices unresolved |
| Roboto; Material Icons and Material Symbols fonts | Eight font families identified in `fonts.css`, sixteen hashed WOFF2 files shipped | Exact font releases/source-to-file mapping and license texts unresolved; do not infer license from family name |
| Optional element bundles | Eleven manifests inspected: AG Grid, CodeMirror, ECharts/GL, nipplejs, JSON editor/AJV, Leaflet/draw, Mermaid, Plotly, Three/tween, Sortable, xterm | Manifests have dependency ranges, not proof of resolved bundled versions; all nested dependencies/embedded notices need audit |
| Ravel CSS, R mark, three toolbar SVGs and invented CSV | Repository-owned experiment resources under repository MIT license | No external icon library used for these original toolbar icons |
| CPython 3.11.0 and native DLLs/extensions | Actual `C:/Python311/LICENSE.txt` retained; bundled `python311.dll` observed | Complete included OpenSSL/SQLite/libffi/compression/Rust/C-vendor and Microsoft runtime notice/source mapping still required |
| Playwright review driver and Node | Actual driver LICENSE, package LICENSE/NOTICE and ThirdPartyNotices retained | Chrome is externally installed test software, not copied into Ravel; audit browser terms if redistribution is ever proposed |

## Established obligations and open release work

MIT/BSD require retention of copyright, permission/conditions and disclaimers
(in binary distributions, include the required text in accompanying materials).
Apache-2.0 requires its license and relevant supplied NOTICE attribution, plus
identification of modified files. Actual NOTICE files from aiofiles, propcache
and yarl are retained. aiohttp/httptools vendored parser notices are retained.
MPL-covered bidict, certifi and orjson code requires license notices and making
covered source available as specified; record versioned corresponding-source
locations and modification status before distributing. orjson's expression is
`MPL-2.0 AND (Apache-2.0 OR MIT)`; do not flatten it to MIT. Docutils' COPYING
lists public-domain files plus BSD exceptions and a GPL editor helper: determine
which files actually ship and retain their per-file notices. PyInstaller's
bootloader exception allows combined executables without imposing GPL on the
application; it does not waive other dependency terms. Runtime hooks have
Apache-2.0 terms. Review/build tools being separate does not automatically mean
none of their code is embedded.

The tested folder contains **only eight package license files** (attrs, click,
itsdangerous, MarkupSafe, NiceGUI, opentelemetry-api, pydantic and websockets).
The build recipe does not yet copy this notice collection into the distribution.
**Do not treat the current folder as license-complete or ready for public alpha.**
Remaining work: map the final artifact's embedded Python/native/frontend files
to exact versions and licenses; resolve fonts/UnoCSS/Sass/optional-bundle gaps;
review vendored components and source obligations; decide whether unused assets
can be omitted safely in a separately tested build; then include required notices
and source references in the artifact and verify them against its manifest.
Setuptools' vendored code and PyInstaller runtime hooks need artifact-specific
review as well. The initial inventory did not perform a license-based removal,
new package or rebuild; the candidate build follow-up is recorded below.
M0-07 is partial; R10 and all other release gates remain unverified.

## Python 3.14 candidate build dependency

The [candidate lock](../experiments/workbook/requirements-build-python314-candidate.lock)
differs only in **setuptools 80.9.0**, replacing 65.5.0 for the isolated trial.
PyInstaller 6.20.0 installed `METADATA` requires `setuptools>=42.0.0`; its
`PyInstaller/utils/hooks/setuptools.py` isolated import/probe uses this dependency.
Removal would violate that requirement. The original lock/table/notices remain
historical evidence and the default setup. See [trial commands](development.md#python-314-candidate-build-lock).

Inspected actual candidate environment files under
`outputs/python314-setuptools-candidate-2026-10-11/build-env/Lib/site-packages`:
`setuptools-80.9.0.dist-info/METADATA` declares Python >=3.9 and MIT;
`licenses/LICENSE` contains the MIT permission/disclaimer text.
[Versioned distribution](https://pypi.org/project/setuptools/80.9.0/),
[tagged source](https://github.com/pypa/setuptools/tree/v80.9.0) and
[upstream history](https://setuptools.pypa.io/en/stable/history.html#v80-9-0)
identify the candidate, not a latest-version or adoption claim.

All **24 actual wheel license/notice files** are appended to
[third-party-notices.txt](third-party-notices.txt) with source paths and original
SHA-256 hashes, preserving prior sections. Besides the top-level MIT license,
these cover vendored autocommand, backports.tarfile, importlib_metadata, inflect,
jaraco collections/context/functools/text, more_itertools, packaging, platformdirs,
tomli, typeguard, typing_extensions, wheel (including its vendored packaging),
zipp and two configuration notices. Retain each component's supplied conditions,
copyright/disclaimer and applicable Apache license/NOTICE attribution. The
configuration notices identify MPL-2.0 validate-pyproject schemas and BSD-3-Clause
fastjsonschema-derived code; retain those notices and review MPL corresponding
source obligations for the files actually shipped. Do not
flatten all vendored terms to setuptools' MIT classification.

The candidate bundle now includes a setuptools vendor import path. Collection of
wheel notices does not establish that all embedded/vendor files have been mapped,
that source obligations are discharged or that notices accompany the artifact.
The recipe still does not copy this notice collection. Existing frontend/native
gaps remain; redistribution approval and R10 remain unverified. No runtime/review
pin change or general dependency upgrade is proposed.
