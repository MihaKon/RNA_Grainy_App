# RNAgrainy

> A universal platform for generating, visualizing, and comparing coarse-grained RNA structure models.

[**Open RNAgrainy**](https://rnagrainy.cs.put.poznan.pl/) ·
[**Documentation**](https://rnagrainy.cs.put.poznan.pl/documentation/) ·
[**API**](#public-api)

![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20TypeScript%20%7C%20Tailwind%20%7C%20Mol*%20%7C%20Gemmi-blue)

## About

RNAgrainy converts full-atom RNA structures into published or custom coarse-grained
models and compares them in an interactive Mol* viewer.

## Scientific Background

Coarse-grained RNA models represent groups of atoms as pseudoatoms to reduce
computational cost. Models differ in resolution and atom mapping rules.

## Key Features

- **Input:** PDB/mmCIF uploads, RCSB PDB retrieval and built-in examples.
- **Model selection:** Published models with optional chain and structural model selection.
- **Visualization:** Interactive comparison of input and CG structures in Mol*.
- **Custom models:** Edit beads, atom mappings and connectivity; import/export JSON.
- **Export:** Download CG structures in PDB or mmCIF format.
- **Documentation:** Model descriptions, atom mappings and references.

## Supported Models

`NAST` · `YUP` · `Nares-2P` · `VFold` · `FebRNA` · `iFoldRNA` ·
`TopRNA` · `isRNA1` · `isRNA2` · `RNA-JP` · `SimRNA` · `HiRE-RNA`

See the [model documentation](https://rnagrainy.cs.put.poznan.pl/documentation/)
for details.

## Application Preview

### Main page

![RNAgrainy main page](docs/screenshots/main-page.png)

### Coarse-grained structure comparison

![RNAgrainy coarse-grained structure comparison](docs/screenshots/structure-comparison.png)

### Custom coarse-grained model creator

![RNAgrainy custom coarse-grained model creator](docs/screenshots/model-creator.png)

### Model documentation

![RNAgrainy model documentation](docs/screenshots/model-documentation.png)

## Public API

The public API requires no account or API key.

- **Server:** `https://rnagrainy.cs.put.poznan.pl`
- **Interactive API documentation:** [Swagger UI](https://rnagrainy.cs.put.poznan.pl/docs)

Conversion requests use `multipart/form-data` and return JSON with a
`workspace_id`, conversion summary and download paths.

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `GET` | `/api/config` | Supported formats, upload limits and preset IDs |
| `GET` | `/api/models` | Available coarse-grained models and their IDs |
| `POST` | `/api/coarse-grain/file` | Coarse-grain an uploaded PDB or mmCIF file |
| `POST` | `/api/coarse-grain/preset` | Coarse-grain a built-in example structure |
| `POST` | `/api/coarse-grain/rcsb` | Fetch a structure from RCSB PDB and coarse-grain it |
| `POST` | `/api/models/custom/validate` | Validate a custom model definition |
| `GET` | `/api/results/{workspace_id}` | Retrieve conversion metadata for an existing result |
| `GET` | `/api/results/{workspace_id}/{file_type}` | Retrieve a reference or CG file; requires `file_format` |

### Find and select a model

Examples use Bash, `curl` and `jq`.

```bash
BASE="https://rnagrainy.cs.put.poznan.pl"

curl --fail-with-body -sS "$BASE/api/models" -o models.json
jq -r '.[] | [.id, .name] | @tsv' models.json
```

Set `selected_model` to the model's **`id`**, e.g. `SimModel` for SimRNA:

```bash
MODEL="SimModel"

curl --fail-with-body -sS "$BASE/api/config" | jq
```

### Coarse-grain a structure

**Upload a local PDB or mmCIF file:**

```bash
curl --fail-with-body -sS "$BASE/api/coarse-grain/file" \
  -F "file=@structure.pdb" \
  -F "selected_model=$MODEL" \
  -o result-file.json
```

**Use a built-in preset:**

```bash
curl --fail-with-body -sS "$BASE/api/coarse-grain/preset" \
  -F "preset_id=1EHZ" \
  -F "selected_model=$MODEL" \
  -o result-preset.json
```

**Fetch a structure from RCSB PDB:**

```bash
curl --fail-with-body -sS "$BASE/api/coarse-grain/rcsb" \
  -F "rcsb_id=2F8S" \
  -F "selected_model=$MODEL" \
  -o result-rcsb.json
```

Optionally add `-F "chains=A,B"` or `-F "models=1,2"` to select input chains or
structural model numbers. By default, all chains and models are included.

### Use a custom model

Export a model from the Custom Model Creator on the
[RNAgrainy website](https://rnagrainy.cs.put.poznan.pl/), or save the
[example definition](tests/data/custom_model.json) as `custom_model.json`.

Validate the definition first. HTTP `204` means that validation succeeded:

```bash
curl --fail-with-body -sS "$BASE/api/models/custom/validate" \
  -F "custom_model_data=<custom_model.json" \
  -w '\nHTTP %{http_code}\n'
```

Then submit it with `selected_model=custom`:

```bash
curl --fail-with-body -sS "$BASE/api/coarse-grain/preset" \
  -F "preset_id=1EHZ" \
  -F "selected_model=custom" \
  -F "custom_model_data=<custom_model.json" \
  -o result-custom.json
```

Custom models also work with `/file` and `/rcsb`. The `<custom_model.json`
syntax sends JSON as a text form field.

### Download the result

Choose a saved response:

```bash
RESULT="result-preset.json"
jq '{workspace_id, atom_counts, files}' "$RESULT"

CG_URL=$(jq -er '.files.coarse_mmcif_url' "$RESULT")
curl --fail-with-body -sS "$BASE$CG_URL" -o coarse.mmcif
```

Prepend `$BASE` to returned paths. `reference_url` points to the input structure;
`coarse_pdb_url` is `null` when PDB output is unavailable:

```bash
PDB_URL=$(jq -r '.files.coarse_pdb_url // empty' "$RESULT")
if [ -n "$PDB_URL" ]; then
  curl --fail-with-body -sS "$BASE$PDB_URL" -o coarse.pdb
fi
```

### Open or share a result page

Open the result in the web viewer using its `workspace_id`:

```bash
WORKSPACE_ID=$(jq -er '.workspace_id' "$RESULT")
echo "$BASE/results/$WORKSPACE_ID"
```

The link works in other tabs and browsers while the result is available.
Retrieve its metadata directly with:

```bash
curl --fail-with-body -sS "$BASE/api/results/$WORKSPACE_ID" | jq
```

### Limits and availability

- Structure files: up to 100 MiB. Custom JSON: up to 5,000 characters and 8 KiB.
  Current limits are available at `/api/config`.
- Invalid input returns HTTP `422` with a JSON `detail` message; unavailable
  result files return HTTP `404`.
- Results are kept for 24 hours after processing. Opening the viewer or downloading
  files through the API does not change this period.

## Local Development

### Tech stack

- **Backend:** Python 3.12, FastAPI, Pydantic, Gemmi
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, TanStack Query, React Router,
  Mol*
- **Tooling:** Ruff, mypy, pytest, Playwright, ESLint, Prettier, Vitest, pre-commit
- **Deployment:** Docker, GitHub Actions

### Project structure

```text
app/                FastAPI backend and coarse-graining algorithm
frontend/           React frontend
tests/              Unit, integration and E2E tests
docs/screenshots/   Application screenshots
```

### Requirements

- Python 3.12 and Pipenv
- Node.js 24 with npm
- Docker with Docker Compose (optional)

### Install dependencies

Run from the repository root:

```bash
python -m pip install pipenv==2026.6.2
pipenv sync --dev
npm --prefix frontend ci
pipenv run pre-commit install
```

### Development

Backend:

```bash
pipenv run uvicorn app.main:app --port 5050 --reload
```

Frontend, in a separate terminal:

```bash
npm --prefix frontend run dev
```

Open `http://localhost:5173`. The frontend proxies API requests to
`http://127.0.0.1:5050`; override this with `BACKEND_URL`.

### Production build

```bash
npm --prefix frontend run build
pipenv run uvicorn app.main:app --port 5050
```

Or use Docker:

```bash
docker compose up --build
```

Open `http://127.0.0.1:5050`.

### Checks

Backend (build the frontend before running E2E tests):

```bash
pipenv run ruff check .
pipenv run mypy
pipenv run pytest tests/unit
pipenv run pytest tests/integration
pipenv run pytest tests/e2e
```

Frontend:

```bash
npm --prefix frontend run lint
npm --prefix frontend run format:check
npm --prefix frontend run typecheck
npm --prefix frontend test
```

Git hooks and CI automate the project checks.

## Authors

### Development

[Sergiusz Urbaniak](https://github.com/serguppp)¹, [Michał Konon](https://github.com/mihakon)¹

### Scientific supervision

[Marta Szachniuk](https://www.cs.put.poznan.pl/mszachniuk/site/)¹˒²

¹ Institute of Computing Science, Poznan University of Technology, Poland  
² Institute of Bioorganic Chemistry, Polish Academy of Sciences, Poznan, Poland
