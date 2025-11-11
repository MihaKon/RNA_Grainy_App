import httpx
from typing import Optional

client = httpx.AsyncClient()

async def fetch_rcsb_content(rcsb_id: str) -> Optional[str]:
    rcsb_id = rcsb_id.strip().upper()
    url = f"https://files.rcsb.org/download/{rcsb_id}.cif"
    #TODO: this service should raise extensions
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        if e.response.status_code == 404:
            print(f"RCSB file with ID {rcsb_id} not found.")
        else:
            print(f"Error fetching RCSB file: {e}")
        return None
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}.")
        return None
