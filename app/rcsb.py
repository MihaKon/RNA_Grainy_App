import httpx
from httpx import HTTPStatusError

from app.exceptions import FileProcessingError
from app.settings import MAX_RCSB_UPLOAD_SIZE, RCSB_URL


client = httpx.AsyncClient()


async def fetch_rcsb_file(rcsb_id: str) -> str | None:
    rcsb_id = rcsb_id.strip().upper()
    url = RCSB_URL + f"{rcsb_id}.cif"

    async with client.stream("GET", url) as response:
        try:
            response.raise_for_status()
        except HTTPStatusError:
            return None

        file_content = bytearray()
        async for chunk in response.aiter_bytes():
            if len(file_content) + len(chunk) > MAX_RCSB_UPLOAD_SIZE:
                max_size_mb = MAX_RCSB_UPLOAD_SIZE / (1024 * 1024)
                raise FileProcessingError(
                    f"The requested RCSB file exceeds the {max_size_mb:g} MB size limit"
                )
            file_content.extend(chunk)

    try:
        return file_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FileProcessingError("The RCSB file has invalid text encoding.") from exc
