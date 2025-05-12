from fastapi import APIRouter, Request, Path, Query
from typing import Optional

from app.services.docling import DoclingService
from app.core.config import settings

router = APIRouter()


@router.post("/convert/file")
async def convert_file(request: Request):
    """
    Process uploaded document files.
    
    Proxies file upload requests to the Docling API for conversion.
    """
    return await DoclingService.proxy_request(
        request=request,
        endpoint="/v1alpha/convert/file",
        method="POST",
        timeout=settings.DEFAULT_TIMEOUT
    )


@router.post("/convert/source")
async def convert_source(request: Request):
    """
    Process documents from URLs.
    
    Proxies URL-based document processing requests to the Docling API.
    """
    return await DoclingService.proxy_request(
        request=request,
        endpoint="/v1alpha/convert/source",
        method="POST",
        timeout=settings.DEFAULT_TIMEOUT
    )


@router.post("/convert/source/async")
async def convert_source_async(request: Request):
    """
    Initiate asynchronous document processing.
    
    Starts an asynchronous conversion job and returns a task ID.
    """
    return await DoclingService.proxy_request(
        request=request,
        endpoint="/v1alpha/convert/source/async",
        method="POST",
        timeout=settings.ASYNC_REQUEST_TIMEOUT
    )


@router.get("/status/poll/{task_id}")
async def poll_task_status(
    request: Request,
    task_id: str = Path(..., description="The ID of the task to check"),
    wait: Optional[float] = Query(0.0, description="How long to wait for a status change (in seconds)")
):
    """
    Check the status of an asynchronous conversion task.
    
    Args:
        task_id: The ID of the task to check
        wait: How long to wait for a status change (in seconds)
    """
    return await DoclingService.proxy_request(
        request=request,
        endpoint=f"/v1alpha/status/poll/{task_id}",
        method="GET",
        timeout=max(wait + 5.0, 30.0),
        query_params={"wait": wait} if wait > 0 else None
    )


@router.get("/result/{task_id}")
async def get_task_result(
    request: Request,
    task_id: str = Path(..., description="The ID of the task to retrieve results for")
):
    """
    Retrieve the result of a completed task.
    
    Args:
        task_id: The ID of the task to retrieve results for
    """
    return await DoclingService.proxy_request(
        request=request,
        endpoint=f"/v1alpha/result/{task_id}",
        method="GET",
        timeout=settings.RESULT_FETCH_TIMEOUT
    )