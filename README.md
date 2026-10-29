# cloudformer.github.io

The IdleFree homepage: https://cloudformer.github.io/

- `index.html` — the page (no build step, no framework).
- `projects.json` — the two project tables (IdleFree Infra, IdleFree App). **The only file to edit** when a project
  is added, renamed or released: each project has `name`, `url`, `what`, `built_on`, `use`, `was` (idle cost,
  struck out), optional `now`, `status` and `live` (green pill). A section's `id` (`infra` / `app`) picks its color.
- `.nojekyll` — serve the files as they are.

Preview locally: `python3 -m http.server -d /Users/frankzhang/repo-private/cloudformer.github.io 8000`, then
open http://localhost:8000 (the page loads `projects.json` over HTTP, so opening the file directly shows no tables).
