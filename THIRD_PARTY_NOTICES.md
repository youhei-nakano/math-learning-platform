# Third-Party Notices

The project source is licensed under MIT, but third-party packages and bundled assets retain their own licenses.

## Runtime and development packages

JavaScript and Python dependencies are declared in `apps/web/package-lock.json`, `services/research-api/requirements*.txt`, and `services/learning-map-api/pyproject.toml`. Their package metadata and upstream distributions are the authoritative license sources. Important direct Web dependencies include React and KaTeX (MIT) and PDF.js (`pdfjs-dist`, Apache-2.0).

## Bundled PDF.js assets

Files under `apps/web/public/pdfjs/` originate from the installed PDF.js distribution:

- PDF.js distribution: Apache License 2.0; see `apps/web/public/pdfjs/LICENSE`.
- Adobe CMaps: license retained in `apps/web/public/pdfjs/cmaps/LICENSE`.
- Liberation fonts: SIL Open Font License 1.1; see `apps/web/public/pdfjs/standard_fonts/LICENSE_LIBERATION`.
- Foxit/PDFium fonts: BSD-style redistribution terms; see `apps/web/public/pdfjs/standard_fonts/LICENSE_FOXIT`.

Do not remove these notices when redistributing the corresponding assets.

## Evaluation fixtures

The small PDFs and cases under `services/research-api/evaluation/datasets/demo-v1/` and `demo-v2/` are generated from checked-in original fixture text and released under CC0-1.0 as declared in their README and dataset metadata. They are not copied textbook or research-paper pages.

## Removed assets

Legacy Kuromoji dictionary binaries were removed from the complete public Git history because the current application did not reference them and their precise provenance and redistribution terms were not documented in the source repository.
