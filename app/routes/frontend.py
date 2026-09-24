from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.settings import FRONTEND_DIST_DIR

IMMUTABLE_CACHE_CONTROL = "public, max-age=31536000, immutable"

router = APIRouter(include_in_schema=False)


@router.api_route("/{path:path}", methods=["GET", "HEAD"])
async def serve_frontend(path: str) -> FileResponse:
    """Serve the built React app: its files as they are, any other path as index.html."""
    if path == "api" or path.startswith("api/"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")

    dist_dir = FRONTEND_DIST_DIR.resolve()
    requested = (dist_dir / path).resolve()
    if path and requested.is_relative_to(dist_dir) and requested.is_file():
        # Vite fingerprints everything under assets/, so those files never change.
        if requested.is_relative_to(dist_dir / "assets"):
            return FileResponse(
                requested, headers={"Cache-Control": IMMUTABLE_CACHE_CONTROL}
            )
        return FileResponse(requested)

    index = dist_dir / "index.html"
    if not index.is_file():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Frontend build not found. Run `npm run build` in frontend/.",
        )
    return FileResponse(index, headers={"Cache-Control": "no-cache"})
