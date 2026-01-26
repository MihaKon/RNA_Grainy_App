import httpx
from httpx import HTTPStatusError

from app.exceptions import FileProcessingError
from app.settings import MAX_RCSB_UPLOAD_SIZE

RCSB_URL = "https://files.rcsb.org/download/"
client = httpx.AsyncClient()


async def fetch_rcsb_file(rcsb_id: str) -> str | None:
    rcsb_id = rcsb_id.strip().upper()
    url = RCSB_URL + f"{rcsb_id}.cif"
    response = await client.get(url)
    try:
        response.raise_for_status()
    except HTTPStatusError:
        return None
    if response.num_bytes_downloaded > MAX_RCSB_UPLOAD_SIZE:
        raise FileProcessingError(
            f"File size exceeds maximum fetching file size of: {MAX_RCSB_UPLOAD_SIZE / 1024} KB."
        )
    return response.text
