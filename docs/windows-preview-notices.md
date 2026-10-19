# Artifact-specific notice review for the private preview

This file accompanies a **private, unaccepted** candidate. It does not certify
redistribution completeness. The prior inventory is in
[dependency-licenses.md](dependency-licenses.md); its historical counts/paths do
not describe this artifact. The actual manifest and analysis-components.json
are authoritative for collected files/modules; build-environment.json describes
all installed build packages, including tools that may not themselves ship.

The builder includes Ravel LICENSE, the existing complete collected
THIRD-PARTY-NOTICES.txt, the current interpreter LICENSE, and actual supplied
license/NOTICE/COPYING/AUTHORS files from every installed pinned distribution.
`notices/python-components.json` identifies versions, supplied paths and source
indexes. The source archive contains the exact declared Ravel build inputs,
including MIT-owned styles/branding. Additional source archives and their exact
upstream URL/checksum map are under dependency-sources when supplied.

Review the actual files, not only Python package names. NiceGUI's complete data
package includes optional element bundles, fonts and frontend code even when a
control is not used. No asset removal is assumed safe merely because a page did
not request it. Keep supplied attribution and identify modifications. Review
both loose data/native files and bytecode modules recorded in the analysis.

| Finding | Artifact review requirement |
| --- | --- |
| Python runtime/packages | Match exact runtime version and each collected Python module/native extension to the recorded pins and actual supplied texts; retain relevant vendor notices |
| MPL-covered bidict/certifi/orjson and setuptools schemas | Retain terms/notices, exact corresponding-source versions and modification status. orjson's MPL AND (Apache OR MIT) expression must not be flattened. Supplied source archives/URL+hash records do not replace file-level scope review. |
| Vue/Quasar/Socket.IO/DOMPurify/Tailwind/Immutable | Existing collected texts/headers are retained; confirm actual shipped versions, embedded/transitive notices and DOMPurify's header/text terms against this candidate |
| UnoCSS/Sass/fonts/optional elements | Resolve actual bundle versions, source-to-file/font mapping and nested dependency notices; dependency ranges alone do not establish exact shipped versions |
| CPython/native/vendor/Microsoft runtimes | Map actual DLL/extension versions and provenance, included license/redistribution/source requirements; the CPython top-level license is not a complete native-vendor inventory |
| PyInstaller/setuptools/vendor code | Bootloader exception does not waive other components' terms; retain runtime-hook and vendor notices for code actually collected |
| Docutils helpers | Determine which files actually ship and their supplied per-file exceptions, rather than classifying every file by one project-level label |

These artifact-specific gaps remain explicit public-distribution blockers until
their evidence is recorded. The private build can still be functionally tested.
No public release/tag/upload or broader license/clinical/platform acceptance is
authorized by producing this candidate. Keep normal operating-system protections
enabled and record actual behavior separately from notice review.

## Evidence prepared for this candidate

The source collection retains the exact55 pinned Python distribution sdists
and CPython3.14.8 source archive, with upstream URLs and checked SHA-256 values.
This includes bidict/certifi/orjson/setuptools corresponding source without
flattening their terms. Archives remain unmodified. It also retains the official
CPython Windows-x64 SPDX document and the tagged NiceGUI3.18.0 core extraction
script/package lock. The interpreter SBOM is supporting provenance, not proof
that every component in the installer is shipped in this smaller artifact.

All16 actual WOFF2 files were decoded separately for review with fontTools4.42.0
and Brotli1.1.0; neither tool is installed in the build environment or bundled.
Their CSS family associations, byte hashes, embedded copyright/version/license
URL records are retained in `dependency-sources/embedded-font-records.json`.
Observed versions: Roboto3.009(2024), Material Icons1.017, the three alternate
Icons families'2022-08-02 build timestamps, and Material Symbols2.911. Roboto's
embedded URL identifies the Open Font License; its upstream OFL text and the
Material Design project license/readme are retained. The guessed Google Fonts
Material Symbols OFL path returned404; do not infer OFL from its family name.
Exact source/license correspondence for that font variant remains review work.

The tagged core npm lock fixes UnoCSS66.6.0, Sass1.94.0, Immutable5.1.9 and
DOMPurify3.4.16. The collector checks every resolved archive's SHA-512 integrity,
retains supplied notices/source, and compares direct-copy assets against actual
shipped bytes. Differences remain explicit with retained diffs. Quasar's first
observed difference is removed whitespace on blank comment lines, not a version
change; confirm the complete diff and comparison result. The upstream script
minifies Sass/Immutable/DOMPurify with an unpinned npx Terser, so those transformed
files require separate correspondence review rather than an invented byte match.
DOMPurify3.4.16's versioned README explicitly labels terms MPL-2.0 OR Apache-2.0;
retain that explanation and its full supplied license alongside the header.

The preview builder excludes data for eleven unused lazy optional element
families, with a local hook preventing the default hook from collecting them
again. `omitted-assets.json` records the selection; build validation refuses
reintroduced data and actual narrowed-artifact browser checks are required.
It also excludes the unused nonproduction Vue/Quasar JavaScript files; the app
always selects production JavaScript. The retained upstream diffs identify their
trailing-whitespace changes, while the production versions match exactly.
This removes their bundled npm libraries, rather than waiving their licenses.
The initial artifact's75 loose Docutils files contain no editor/emacs helper;
the analysis inventory and final manifest must confirm this for the candidate.

Outstanding public-review points are concrete: transformed core-asset provenance,
font-variant license/source correspondence, native/Rust vendor file coverage and
Microsoft runtime redistribution terms. No clean-machine/protection behavior or
redistribution approval is implied by retaining source and notice material.

Rebuild checks exposed unrelated Python bytecode under a directory named
`packaging/licenses` and environment-specific pip RECORD entries. Notice
collection now includes supplied text rather than cache/code files. The frozen
folder omits installation RECORD files that describe the build venv's CLI
wrappers; its actual manifest describes the shipped files instead. Installed
environments/source archives stay untouched. Module/data provenance is sorted
and excludes generated containers and omitted installation records. Comparison
still verifies each actual manifest and stable file bytes, and compares every
decoded member of the standard-library/source ZIPs when container bytes vary.

Notice texts use short content-addressed filenames under `notices/texts` so
component/version/vendor nesting does not exceed Windows path limits. Every
component retains the original supplied path, actual text SHA-256 and copied
path in python-components.json; identical texts may share a file. Originals and
all distinct text remain intact. Choose a reasonably short writable build and
extraction directory; the final inventory reports actual relative path lengths.
