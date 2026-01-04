"""
Command router
"""

from fastapi import APIRouter

from app.schemas.models import CommandRequest, CommandResponse
from app.services.database import get_user_profile
from app.services.agent import process_command

router = APIRouter()


@router.post("/command", response_model=CommandResponse)
async def handle_command(request: CommandRequest):
    """處理自然語言指令"""
    try:
        # Get user profile if user_id provided
        user_profile = None
        if request.user_id:
            user_profile = await get_user_profile(request.user_id)
        
        message, tool_results = await process_command(request.text, user_profile)
        
        return CommandResponse(
            success=True,
            message=message,
            tool_calls=tool_results
        )
        
    except Exception as e:
        return CommandResponse(
            success=False,
            message=f"Error: {str(e)}",
            tool_calls=[]
        )
