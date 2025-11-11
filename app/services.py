import httpx

client = httpx.AsyncClient()

class RCSBServiceError(Exception):
    pass

class RCSBNotFoundError(Exception):
    def __init__(self, rcsb_id: str):
        self.rcsb_id = rcsb_id
        self.message = f"Structure with ID '{rcsb_id}' not found."
        super().__init__(self.message)


async def fetch_rcsb_file(rcsb_id: str) -> str:
    rcsb_id = rcsb_id.strip().upper()
    url = f"https://files.rcsb.org/download/{rcsb_id}.cif"
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        if e.response.status_code == 404:
            raise RCSBNotFoundError(rcsb_id) from e
        else:
            raise RCSBServiceError(f"HTTP Error: {e}") from e
    except httpx.RequestError as e:
        raise RCSBServiceError(f"Request error: {e}") from e
