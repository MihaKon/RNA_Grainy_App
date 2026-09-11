from pathlib import Path

import httpx

RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_URL = "https://files.rcsb.org/download/{pdb_id}.cif"

DEFAULT_DOWNLOAD_LIMIT_BYTES = 512 * 1024 * 1024
DEFAULT_PAGE_SIZE = 1_000
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

    def get_rna_structure_ids(self) -> list[str]:
        #
        return []

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
