"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, TypedDict

from langchain_core.runnables import RunnableConfig
from typing import Annotated, Optional, List, Literal, Any
from langchain_core.tools import tool
from typing_extensions import TypedDict
from datetime import datetime

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field, EmailStr, HttpUrl, RootModel
import aiohttp
from dotenv import load_dotenv
import os
import json
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from concurrent.futures import ThreadPoolExecutor
import asyncio
from src.services.devskiller import DevskillerService
from src.services.devskiller_video import DevskillerVideoService

client = DevskillerService()

from src.types.devskiller import EventPayload, Assessment, DevSkillerResponse

load_dotenv()

devskiller_api_url = "https://api.devskiller.com"

class Configuration(TypedDict):
    pass


@dataclass
class State:
    payload: EventPayload
    assessment: Optional[Assessment] = None
    is_autoevaluation_ready: bool = False
    mock: str = ""
    video_bytes: Optional[bytes] = None


async def retrieve_devskiller_assessment(state: State):
    event_payload = EventPayload.model_validate(state.payload) if not isinstance(state.payload, EventPayload) else state.payload
    
    if len(event_payload.root) > 0:
        event = event_payload.root[0]
        candidate_id, assessment_id = event.candidateId, event.assessmentId
        assessment = await client.get_assessment(candidate_id, assessment_id)
        return {
            "assessment": assessment
        }
    return state  # Return unchanged state if no events found

async def autoevaluation_ready(state: State):
    if state.assessment:
        return {
            "is_autoevaluation_ready": state.assessment.status == "AUTO_ASSESSMENT_READY"
        }
    return state

def routing_function(state: State) -> bool:
    return state.assessment is not None and state.assessment.status == "AUTO_ASSESSMENT_READY"

async def mock_false_node(state: State):
    return {"mock": "This is the false branch"}

async def download_devskiller_video_node(state: State):
    """
    Node to authenticate as node user and download a Devskiller video.
    Expects the video URL in state.payload.root[0].videoUrl (or adjust as needed).
    """
    video_service = None
    try:
        # Example: get video URL from state (adjust as needed)
        event_payload = EventPayload.model_validate(state.payload) if not isinstance(state.payload, EventPayload) else state.payload
        if len(event_payload.root) > 0:
            # You may want to pass the video URL in the payload or set it elsewhere
            video_url = getattr(event_payload.root[0], "videoUrl", None)
            if not video_url:
                # fallback: hardcoded or from assessment, etc.
                video_url = "https://app.devskiller.com/rest/admin/candidates/fbd1b0af-25e1-4576-a078-c5c8b6659974/invitations/11e98fec-dc81-4677-a9cc-5b8b7e9f816c/answerSheet/S1F/answers/2105736/video-capture/download"
            
            print(f"Starting video download from {video_url}")
            video_service = DevskillerVideoService()
            
            # First authenticate to get cookies
            cookies = await video_service.authenticate(
                username=os.getenv("DEVSKILLER_USERNAME"),
                password=os.getenv("DEVSKILLER_PASSWORD")
            )
            
            # Then download using those cookies
            save_path = f"video_{event_payload.root[0].assessmentId if len(event_payload.root) > 0 else 'download'}.mp4"
            video_bytes = await video_service.download_video(
                video_url=video_url, 
                cookies=cookies,
                save_path=save_path
            )
            
            print(f"Video downloaded: {len(video_bytes)} bytes. Saved to {save_path}")
            return {"video_bytes": video_bytes}
        return state
    except Exception as e:
        print(f"Error in download_devskiller_video_node: {str(e)}")
        return state
    finally:
        # Always close the browser to free resources
        if video_service:
            await video_service.close()

graph = (
    StateGraph(State, config_schema=Configuration)
    .add_node(retrieve_devskiller_assessment)
    .add_node(autoevaluation_ready)
    .add_node(mock_false_node)
    .add_node(download_devskiller_video_node)
    .add_edge(START, "retrieve_devskiller_assessment")
    .add_conditional_edges(
        "retrieve_devskiller_assessment",
        routing_function,
        {True: "autoevaluation_ready", False: "mock_false_node"}
    )
    .add_edge("autoevaluation_ready", "download_devskiller_video_node")
    .add_edge("mock_false_node", END)
    .add_edge("download_devskiller_video_node", END)
    .compile(name="Scale Grading Agent")
)
