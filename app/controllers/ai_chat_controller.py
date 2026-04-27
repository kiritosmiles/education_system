import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.utils.dify_client import chat_message, chat_message_stream, upload_file, extract_chat_answer
from app.utils.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from sqlalchemy.orm import Session
from fastapi import Depends

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai-chat", tags=["AI助手"])
settings = get_settings()


@router.post("/message")
async def send_message(
    query: str = Form(...),
    conversation_id: str = Form(""),
    uid: str = Form(""),
    token: str = Form(""),
    files: list[UploadFile] = File(default=[]),
):
    """发送聊天消息（阻塞模式，兼容旧逻辑）"""
    try:
        if not query:
            raise HTTPException(status_code=400, detail="请输入文本内容")

        user = f"user_{uid}"

        # 1. 上传文件到Dify
        uploaded_files = []
        for f in files:
            file_bytes = await f.read()
            filename = f.filename or "upload"
            result = await upload_file(
                file_bytes=file_bytes,
                filename=filename,
                user=user,
                api_key=settings.DIFY_CHAT_API_KEY,
            )
            file_type = "image" if f.content_type and f.content_type.startswith("image/") else "document"
            uploaded_files.append({
                "type": file_type,
                "transfer_method": "local_file",
                "upload_file_id": result.get("id", ""),
            })

        # 2. 调用Dify Chat API（阻塞模式）
        final_query = query or "请查看上传的文件"
        chat_inputs = {}
        if uid:
            chat_inputs["uid"] = uid
        if token:
            chat_inputs["token"] = token
        chat_result = await chat_message(
            query=final_query,
            user=user,
            inputs=chat_inputs,
            api_key=settings.DIFY_CHAT_API_KEY,
            conversation_id=conversation_id,
            files=uploaded_files if uploaded_files else None,
        )
        answer = extract_chat_answer(chat_result)
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "answer": answer,
                "conversation_id": chat_result.get("conversation_id", ""),
            },
        }
    except Exception as e:
        logger.error(f"AI聊天错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_message(
    request: Request,
    query: str = Form(...),
    conversation_id: str = Form(""),
    files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    流式聊天接口（SSE）
    前端通过 fetch + ReadableStream 实时渲染AI回答
    """
    if not query:
        raise HTTPException(status_code=400, detail="请输入文本内容")

    # 从请求头提取token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    user = f"user_{current_user.uid}"

    # 上传文件
    uploaded_files = []
    for f in files:
        file_bytes = await f.read()
        filename = f.filename or "upload"
        result = await upload_file(
            file_bytes=file_bytes,
            filename=filename,
            user=user,
            api_key=settings.DIFY_CHAT_API_KEY,
        )
        file_type = "image" if f.content_type and f.content_type.startswith("image/") else "document"
        uploaded_files.append({
            "type": file_type,
            "transfer_method": "local_file",
            "upload_file_id": result.get("id", ""),
        })

    chat_inputs = {"uid": str(current_user.uid), "token": token}

    async def event_generator():
        async for chunk in chat_message_stream(
            query=query,
            user=user,
            inputs=chat_inputs,
            api_key=settings.DIFY_CHAT_API_KEY,
            conversation_id=conversation_id,
            files=uploaded_files if uploaded_files else None,
        ):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
