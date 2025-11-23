import httpx
from httpx import HTTPStatusError

RCSB_URL = "https://files.rcsb.org/download/"
client = httpx.AsyncClient()


class RCSBServiceError(Exception):
    pass


class RCSBNotFoundError(Exception):
    def __init__(self, rcsb_id: str):
        self.rcsb_id = rcsb_id
        self.message = f"Structure with ID '{rcsb_id}' not found."
        super().__init__(self.message)


async def fetch_rcsb_file(rcsb_id: str) -> str | None:
    rcsb_id = rcsb_id.strip().upper()
    url = RCSB_URL + f"{rcsb_id}.cif"
    response = await client.get(url)
    try:
        response.raise_for_status()
    except HTTPStatusError:
        return None
    return response.text
