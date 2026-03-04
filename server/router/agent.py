from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agents.agent_building import vl_llm_node, MessagesState
import json
import os
import base64

router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)

class BuildingAnalysisRequest(BaseModel):
    basic_image_name: str  # Filename of the basic image
    comparison_image_name: str  # Filename of the comparison image
    description: str | None = None  # Description of the building

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@router.post("/building/stream")
async def stream_building_analysis(request: BuildingAnalysisRequest):
    """
    Stream the building analysis report.
    """
    # Define file paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # server/
    files_dir = os.path.join(base_dir, "files")
    
    img1_path = os.path.join(files_dir, request.basic_image_name)
    img2_path = os.path.join(files_dir, request.comparison_image_name)
    
    # Check if files exist
    if not os.path.exists(img1_path):
        raise HTTPException(status_code=404, detail=f"Basic image not found: {request.basic_image_name}. Please upload the file first.")
    if not os.path.exists(img2_path):
        raise HTTPException(status_code=404, detail=f"Comparison image not found: {request.comparison_image_name}. Please upload the file first.")

    try:
        img1_b64 = encode_image(img1_path)
        img2_b64 = encode_image(img2_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading images: {str(e)}")

    state = MessagesState(
        basic_image=img1_b64,
        comparison_image=img2_b64,
        description=request.description or ""
    )

    def generate():
        # vl_llm_node returns an iterator of AIMessageChunk
        for chunk in vl_llm_node(state):
            # Try to get reasoning content
            reasoning = chunk.additional_kwargs.get("reasoning_content", "")
            if reasoning:
                yield f"data: {json.dumps({'reasoning': reasoning}, ensure_ascii=False)}\n\n"

            if chunk.content:
                # Format as SSE data
                yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/")
async def root():
    return "Hello, Agent!"
