import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.utils.dify_client import chat_message, upload_file, extract_chat_answer
from app.config import get_settings

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
    """发送聊天消息（文本+文件一起提交）"""
    try:
        if not query:
            raise HTTPException(status_code=400, detail="请输入文本内容")

        user = f"user_{uid}"

        # 1. 上传文件到Dify，获取file_id列表
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

        # 2. 调用Dify Chat API（文本+文件引用），uid/token作为inputs传入
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
