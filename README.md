# cloudformer.github.io

The IdleFree homepage: https://cloudformer.github.io/

- `index.html` — the page (no build step, no framework).
- `projects.json` — the project rows, in two sections (IdleFree Infra, IdleFree App). **The only file to edit** when a
  project is added, renamed or released: each project has `name`, `url`, `diagram` (architecture image: the row's
  thumbnail, full size on hover), `what`, `built_on`, `was` (the idle cost it replaces, struck out), optional
  `idle_month` (that cost in USD per month: draws the grey bar), optional `now`, `status` and `live`. A section's `id`
  (`infra` / `app`) picks its color.
- `strings.json` — the page's own text, `en` and `zh` side by side under the same keys (each element's `data-i18n`).
  The English written in `index.html` is the fallback. `cloudformer.github.io/#zh` opens in Chinese; the 中文 / EN
  button switches and is remembered in the browser. Project rows stay English.
- Pulled live as the page loads: the GitHub avatar and name, each project's PyPI version (replaces `status` when the
  package exists), GitHub stars and last update. Unauthenticated GitHub API: 60 requests an hour per visitor, the page
  uses 8; past that the page shows `projects.json` as it is.
- `.nojekyll` — serve the files as they are.

Preview locally: `python3 -m http.server -d /Users/frankzhang/repo-private/cloudformer.github.io 8000`, then
open http://localhost:8000 (the page loads `projects.json` over HTTP, so opening the file directly shows no rows).
