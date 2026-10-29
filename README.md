# cloudformer.github.io

The IdleFree homepage: https://cloudformer.github.io/

- `index.html` — the page (no build step, no framework).
- `projects.json` — the two project tables (IdleFree Infra, IdleFree App). **The only file to edit** when a project
  is added, renamed or released: each project has `name`, `url`, `diagram`
  (architecture image, previewed on hover), `demo` (a link shows "demo" in the Demo column; empty shows "Coming soon"), `what`, `built_on`, `use`, `was` (idle cost,
  struck out), optional `now`, `status` and `live` (green pill). A section's `id` (`infra` / `app`) picks its color.
- `strings.json` — the Chinese text of the page (`zh`, keyed by each element's `data-i18n`); English is the page itself.
  `cloudformer.github.io/#zh` opens in Chinese; the EN / 中文 button switches and is remembered in the browser.
  Project tables stay English.
- `.nojekyll` — serve the files as they are.

Preview locally: `python3 -m http.server -d /Users/frankzhang/repo-private/cloudformer.github.io 8000`, then
open http://localhost:8000 (the page loads `projects.json` over HTTP, so opening the file directly shows no tables).
