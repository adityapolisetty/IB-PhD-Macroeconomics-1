# IB PhD Macroeconomics 1

A course companion for the `adityapolisetty/IB-PhD-Macroeconomics-1` repository, with seven interactive lessons, written economic intuition, LaTeX equations and Jupyter notebooks. The interface uses a warm paper background, serif headings, restrained colour and custom SVG charts.

[Open the course website](https://adityapolisetty.github.io/IB-PhD-Macroeconomics-1/).

Built with Astro, MDX, Svelte and D3. Static deployment on GitHub Pages. There is no Python server and no account requirement for students.

## Local development

Use Node.js 22.12 or newer and pnpm 11.19 (the pinned package manager):

```sh
pnpm install
pnpm dev
```

```sh
pnpm test
pnpm build
pnpm preview
```

`pnpm test` checks the economic mechanisms and numerical calculations. Building renders the MDX, mathematics, routes and interactive components, and copies the seven notebooks into the public output.

## Lessons

| Tutorial | Lesson | Notebook |
| --- | --- | --- |
| 1 | Solow convergence and Euler stepping | `Tutorial_1.ipynb` |
| 2 | Consumption, wealth and the terminal condition | `Tutorial_2.ipynb` |
| 3 | Saddle-path shooting | `Tutorial_3.ipynb` |
| 6 | One Bellman update at a time | `Tutorial_6.ipynb` |
| 7 | Extraction, homogeneity and capacity cost | `Tutorial_7.ipynb` |
| 9 | Investment frictions and inaction | `Tutorial_9.ipynb` |
| 10 | Numerical and log-linear RBC policies | `Tutorial_10.ipynb` |

The numbering follows the teaching plan; tutorials 4, 5 and 8 have no Python section.

## Customise the aesthetics

- **Colours, typography, spacing and widths:** `src/styles/global.css`. Change the tokens at the top; the charts use the same palette as the pages.
- **Navigation and lesson titles:** `src/lib/lessons.js`.
- **Page structure:** `src/layouts/SiteLayout.astro` and `LessonLayout.astro`.
- **Written intuition, equations and code steps:** `src/content/lessons/*.mdx`.
- **Axes, lines, legends, tooltips and responsive chart behaviour:** `src/components/LineChart.svelte`.
- **Each model's controls and interpretation:** its `*Explorer.svelte` component.
- **Live model equations and calibration:** `src/lib/models.js`.

The theme uses system fonts, including a serif font stack. Dependencies and mathematical fonts are bundled into the site. No CDN is needed for the finished pages.

Each lesson moves through intuition, model, a prediction, an experiment and interpretation. Keep experiments small enough to explain one mechanism at a time. The questions reveal their answers through native disclosure controls.

## Notebooks and reference scripts

The seven notebooks are in `public/notebooks/` and remain available when this folder is cloned as a standalone repository. While working in the local AP course folder, builds refresh these copies from `../Tutorials/` when that folder is present. `reference-python/` holds copies of all seven Python scripts named in the tutorial plan; the originals are not modified.

## Reproduce the precomputed models

The extraction, investment and RBC curves are in `src/data/model-data.json`. They were solved using the reference scripts' equations and calibration. Run with Python and NumPy:

```sh
python scripts/precompute-models.py
```

To reuse the expensive RBC solution while recalculating extraction and investment:

```sh
python scripts/precompute-models.py --reuse-rbc
```

Details and numerical differences from the reference scripts are recorded in `src/data/PROVENANCE.md`. Parameter selectors for these three models select actual precomputed solutions; they do not interpolate between arbitrarily chosen calibrations.

## Publish on GitHub Pages

The live site publishes from the `gh-pages` branch. In **Settings → Pages**, the source is **Deploy from a branch → gh-pages → / (root)**. To publish an update with an authenticated Git installation:

```sh
pnpm test
pnpm run publish
```

The publish script builds with this repository's URL prefix, prepares the ignored `.pages-publish/` folder and pushes the generated files to `gh-pages`. Commit and push your lesson/source edits to `main` separately. Internal links, notebooks, fonts and interactive assets use the repository prefix. For a manual build:

```sh
SITE_URL=https://adityapolisetty.github.io BASE_PATH=/IB-PhD-Macroeconomics-1 pnpm build
```

On PowerShell, set `SITE_URL` and `BASE_PATH` with `$env:SITE_URL` and `$env:BASE_PATH` before running `pnpm build`.

An optional Actions workflow is provided in `deployment/github-actions.yml.example`. With GitHub credentials that can upload workflows, move it to `.github/workflows/deploy.yml` and change Pages' source to **GitHub Actions** to publish automatically on pushes to `main` or `master`. It obtains the origin and repository subpath from Pages.

## Browser verification

`scripts/check-browser.cjs` exercises all seven lessons, their primary controls, notebook links, equation rendering and layouts at desktop and mobile widths. Run it against a local preview with Playwright available; set `PLAYWRIGHT_MODULE_PATH` and `CHROME_PATH` when using an existing installation. Screenshots and browser profiles stay in the ignored `.verification/` directory.
