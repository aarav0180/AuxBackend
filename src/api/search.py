"""
Search API endpoints for JioSaavn integration.
"""

from fastapi import APIRouter, Query

from src.models.schemas import SearchSongsResponse, SongDetail, SongSuggestion
from src.services.jiosaavn_service import jiosaavn_service
from src.core.exceptions import SongNotFoundError

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "/songs",
    response_model=SearchSongsResponse,
    summary="Search for songs",
    description="Search for songs using JioSaavn API.",
)
async def search_songs(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum results"),
) -> SearchSongsResponse:
    """
    Search for songs.
    
    This endpoint allows users to find songs to add to their room's queue.
    """
    results = await jiosaavn_service.search_songs(query, limit)
    
    return SearchSongsResponse(
        success=True,
        query=query,
        results=results,
        total=len(results),
    )


@router.get(
    "/songs/{song_id}",
    response_model=SongDetail,
    summary="Get song details",
    description="Get detailed information about a specific song.",
)
async def get_song_details(song_id: str) -> SongDetail:
    """Get detailed song information."""
    song = await jiosaavn_service.get_song_details(song_id)
    
    if song is None:
        raise SongNotFoundError(song_id)
    
    return song


@router.get(
    "/songs/{song_id}/suggestions",
    response_model=SongSuggestion,
    summary="Get song suggestions",
    description="Get song suggestions based on a specific song.",
)
async def get_song_suggestions(
    song_id: str,
    limit: int = Query(default=10, ge=1, le=50),
) -> SongSuggestion:
    """Get suggestions based on a song."""
    suggestions = await jiosaavn_service.get_song_suggestions(song_id, limit)
    
    return SongSuggestion(
        success=True,
        suggestions=suggestions,
    )
