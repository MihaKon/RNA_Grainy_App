from pathlib import Path

import httpx

RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_URL = "https://files.rcsb.org/download/{pdb_id}.cif"

PDB_AUDIT_DIRECTORY = Path(__file__).resolve().parent
CACHE_DIRECTORY = PDB_AUDIT_DIRECTORY / "cache" / "structures"


class RcsbClient:
    def __init__(self) -> None:
        self.cache_directory = CACHE_DIRECTORY

        self.cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "RcsbClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_all_rna_structure_ids(self) -> list[str]:
        query = {
            "query": {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": ("rcsb_entry_info.polymer_entity_count_RNA"),
                    "operator": "greater",
                    "value": 0,
                },
            },
            "return_type": "entry",
            "request_options": {
                "return_all_hits": True,
                "results_verbosity": "compact",
            },
        }

        response = self.client.post(
            RCSB_SEARCH_URL,
            json=query,
        )

        response.raise_for_status()
        response_data = response.json()
        results = response_data.get("result_set", [])

        return [str(pdb_id.upper()) for pdb_id in results]

    def download_structure(self, pdb_id: str) -> str | None:
        url = RCSB_URL.format(pdb_id=pdb_id)
        with self.client.stream("GET", url) as response:
            try:
                response.raise_for_status()
            except Exception as e:
                raise e

            file_content = bytearray()
            for chunk in response.iter_bytes():
                file_content.extend(chunk)

        return file_content.decode("utf-8")

    def download_structures(
        self,
        pdb_ids: list[str],
    ) -> list[str]:
        contents: list[str] = []
        for pdb_id in pdb_ids:
            path = self.download_structure(pdb_id)
            if path is not None:
                contents.append(path)
        return contents
