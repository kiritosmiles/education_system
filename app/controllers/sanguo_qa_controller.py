import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.utils.auth import get_current_user
from app.models.user import User
from app.core.hybrid_search import hybrid_search_answer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sanguo-qa", tags=["三国知识问答"])


class SanguoQARequest(BaseModel):
    question: str


@router.post("/ask")
async def ask_sanguo_question(
    request: SanguoQARequest,
    current_user: User = Depends(get_current_user),
):
    """三国知识问答接口：接收问题，调用混合检索 + LLM 生成回答。"""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="请输入问题")

    try:
        result = hybrid_search_answer(question)
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"],
            },
        }
    except Exception as e:
        logger.error(f"三国知识问答错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
