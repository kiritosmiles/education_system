import logging
import uuid
import httpx
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def chat_message(query: str, user: str = "system", inputs: dict = None, uid: str = "", token: str = "") -> dict:
    """
    调用Dify Chatbot API（阻塞模式）
    :param query: 用户提问内容
    :param user: 用户标识
    :param inputs: 工作流输入变量
    :param uid: 用户uid
    :param token: 用户token
    :return: API返回结果
    """
    url = f"{settings.DIFY_BASE_URL}/v1/chat-messages"
    headers = {
        "Authorization": f"Bearer {settings.DIFY_WORK_REPO_SUM_API_KEY}",
        "Content-Type": "application/json"
    }
    final_inputs = dict(inputs or {})
    if uid:
        final_inputs["uid"] = uid
    if token:
        final_inputs["token"] = token
    payload = {
        "inputs": final_inputs,
        "query": query,
        "response_mode": "blocking",
        "user": user,
        "conversation_id": ""
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            logger.error(f"Dify API错误: status={response.status_code}, body={response.text}")
            raise Exception(f"Dify API错误({response.status_code}): {response.text}")
        return response.json()


def extract_chat_answer(result: dict) -> str:
    """
    从Dify Chatbot返回结果中提取回答文本
    """
    answer = result.get("answer", "")
    return answer


def extract_workflow_output(result: dict) -> str:
    """
    从Dify工作流返回结果中提取输出文本
    """
    data = result.get("data", {})
    outputs = data.get("outputs", {})
    # 尝试常见的输出字段名
    for key in ("text", "output", "result", "summary", "content"):
        if key in outputs and outputs[key]:
            return outputs[key]
    # 如果没有匹配到，返回整个outputs的字符串
    if outputs:
        return str(outputs)
    return ""
