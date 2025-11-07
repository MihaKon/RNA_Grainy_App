import httpx
from typing import Optional

client = httpx.AsyncClient()

async def fetch_rscb_content(pdb_id: str) -> Optional[str]:
    pdb_id = pdb_id.strip().upper()
    url = f"https://files.rcsb.org/download/{pdb_id}.cif"
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        if e.response.status_code == 404:
            print(f"RCSB file with ID {pdb_id} not found.")
        else:
            print(f"Error fetching RCSB file: {e}")
        return None
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}.")
        return None
