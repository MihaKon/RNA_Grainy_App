# RNAgrainy

> A universal platform for generating, visualizing, and comparing coarse-grained RNA structure models.

[**Open RNAgrainy**](https://rnagrainy.cs.put.poznan.pl/) ·
[**Documentation**](https://rnagrainy.cs.put.poznan.pl/documentation/)

![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20HTMX%20%7C%20Alpine.js%20%7C%20Tailwind%20%7C%20Gemmi-blue)

## About

RNAgrainy is a web-based bioinformatics platform for generating, visualizing, and comparing coarse-grained representations of RNA structures.

The application enables the transformation of all-atom RNA structures into simplified coarse-grained representations using multiple models described in the scientific literature. It also provides tools for defining custom coarse-grained representations.

## Scientific Background

RNA molecules play essential roles in many biological processes, and understanding their structure and dynamics is important for studying their function.

All-atom molecular representations provide detailed structural information but may become computationally expensive when used in simulations of large RNA molecules or over long timescales. Coarse-grained models reduce the number of interaction sites by representing groups of atoms as simplified particles or pseudoatoms.

Different coarse-grained RNA models use different mapping strategies, resolutions, and representations. RNAgrainy provides a unified environment for generating and comparing these representations from the same input RNA structure.

## Key Features

* **Structure import:** Support for PDB and PDBx/mmCIF files, as well as direct retrieval of structures from the RCSB PDB database using a PDB ID. Predefined example structures can also be selected.
* **Coarse-grained model selection:** Selection of predefined RNA coarse-grained models described in the scientific literature.
* **Chain and structure model selection:** Users can select specific chains and structural models from the input structure.
* **Interactive visualization:** Comparison of the original all-atom structure and the generated coarse-grained representation using the Mol* molecular visualization library.
* **Custom model creator:** Define custom coarse-grained representations, pseudoatom mappings, and connectivity rules through an interactive editor, or load an existing model configuration from JSON.
* **Structure export:** Generated coarse-grained structures can be exported in standard PDB and PDBx/mmCIF formats.
* **Model documentation:** The application provides descriptions of supported coarse-grained models, atom mapping rules, and references to the original scientific literature.

## Supported Models

RNAgrainy currently supports the following predefined coarse-grained RNA models:

`NAST` · `YUP` · `Nares-2P` · `VFold` · `FebRNA` · `iFoldRNA` ·
`TopRNA` · `isRNA1` · `isRNA2` · `RNA-JP` · `SimRNA` · `HiRE-RNA`

Detailed descriptions, mapping rules, and references are available in the
[model documentation](https://rnagrainy.cs.put.poznan.pl/documentation/).

## Application Preview

### Main page

<img width="1535" height="863" alt="RNAgrainy main page" src="https://github.com/user-attachments/assets/e4b52f6a-f9f5-48b8-8177-77c652d099fc" />

### Coarse-grained structure comparison

<img width="1535" height="862" alt="RNAgrainy coarse-grained structure comparison" src="https://github.com/user-attachments/assets/2780ac8f-f267-4bbd-8927-4eb9bd0799bf" />

### Custom coarse-grained model creator

<img width="1535" height="862" alt="RNAgrainy custom coarse-grained model creator" src="https://github.com/user-attachments/assets/f293bfd9-343f-4b37-8785-d395826ae667" />

### Model documentation

<img width="1535" height="862" alt="RNAgrainy model documentation" src="https://github.com/user-attachments/assets/77a9fbe3-e0b3-4cce-8305-33a4074c5e01" />

## Local Development

### Requirements

Install the following tools:

- Python 3.12
- Pipenv
- Node.js 24 with npm
- Docker with Docker Compose

### Install dependencies

Install Pipenv:

```bash
python -m pip install pipenv==2026.6.2
```

Install Python dependencies, including development tools:

```bash
pipenv sync --dev
```

Install frontend build dependencies:

```bash
npm ci
```

Install the Git hooks configured by the project:

```bash
pipenv run pre-commit install
```

### Start the development environment

Start the Tailwind CSS watcher in the first terminal:

```bash
npm run dev
```

For the first run, build the Docker image and start the application in a second terminal:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build app
```

For subsequent runs, if the dependencies and Dockerfile have not changed, rebuilding is not required:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up app
```

The application is available at:

```text
http://127.0.0.1:5050
```

## Authors

### Development

[Sergiusz Urbaniak](https://github.com/serguppp)¹, [Michał Konon](https://github.com/mihakon)¹

### Scientific supervision

[Marta Szachniuk](https://www.cs.put.poznan.pl/mszachniuk/site/)¹˒²

¹ Institute of Computing Science, Poznan University of Technology, Poland  
² Institute of Bioorganic Chemistry, Polish Academy of Sciences, Poznan, Poland
