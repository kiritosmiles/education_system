import logging
import os
import json
from typing import AsyncGenerator
import httpx
from app.config import get_settings

# 清除代理设置，确保直连 Dify API
for _key in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy'):
    os.environ.pop(_key, None)
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

settings = get_settings()
logger = logging.getLogger(__name__)

# ── 全局连接池复用 ──
# 长连接复用，避免每次请求都新建 TCP 连接
_http_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    """获取全局复用的 httpx.AsyncClient（懒初始化）"""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=120)
    return _http_client


async def close_http_client():
    """应用关闭时调用，释放连接池"""
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


async def chat_message(
    query: str,
    user: str = "system",
    inputs: dict = None,
    uid: str = "",
    token: str = "",
    api_key: str = "",
    conversation_id: str = "",
    files: list = None,
) -> dict:
    """
    调用Dify Chatbot API（阻塞模式）
    适用于：定时任务、日报总结等不需要流式的场景
    """
    url = f"{settings.DIFY_BASE_URL}/v1/chat-messages"
    key = api_key or settings.DIFY_WORK_REPO_SUM_API_KEY
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
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
        "conversation_id": conversation_id,
    }
    if files:
        payload["files"] = files
    client = await get_http_client()
    response = await client.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        logger.error(f"Dify API错误: status={response.status_code}, body={response.text}")
        raise Exception(f"Dify API错误({response.status_code}): {response.text}")
    return response.json()


async def chat_message_stream(
    query: str,
    user: str = "system",
    inputs: dict = None,
    uid: str = "",
    token: str = "",
    api_key: str = "",
    conversation_id: str = "",
    files: list = None,
) -> AsyncGenerator[str, None]:
    """
    调用Dify Chatbot API（流式模式），逐token返回SSE事件
    适用于：AI聊天等需要实时展示的场景

    yield 格式: "data: {json}\n\n" (标准SSE格式)
    事件类型:
      - message: AI回答的增量文本 (event=data)
      - message_end: 回答结束，含conversation_id (event=message_end)
      - error: 错误信息
    """
    url = f"{settings.DIFY_BASE_URL}/v1/chat-messages"
    key = api_key or settings.DIFY_CHAT_API_KEY
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    final_inputs = dict(inputs or {})
    if uid:
        final_inputs["uid"] = uid
    if token:
        final_inputs["token"] = token
    payload = {
        "inputs": final_inputs,
        "query": query,
        "response_mode": "streaming",
        "user": user,
        "conversation_id": conversation_id,
    }
    if files:
        payload["files"] = files

    client = await get_http_client()
    async with client.stream("POST", url, json=payload, headers=headers) as response:
        if response.status_code != 200:
            body = await response.aread()
            error_msg = f"Dify API错误({response.status_code}): {body.decode()}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'event': 'error', 'message': error_msg})}\n\n"
            return

        async for line in response.aiter_lines():
            line = line.strip()
            if not line:
                continue
            # Dify SSE 格式: "event: xxx\ndata: {json}"  或纯 "data: {json}"
            if line.startswith("data:"):
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    yield "data: [DONE]\n\n"
                    return
                try:
                    data = json.loads(data_str)
                    event_type = data.get("event", "")

                    if event_type == "message":
                        # 增量回答文本
                        answer_chunk = data.get("answer", "")
                        yield f"data: {json.dumps({'event': 'message', 'answer': answer_chunk})}\n\n"

                    elif event_type == "message_end":
                        # 回答结束，携带 conversation_id 和 metadata
                        yield f"data: {json.dumps({'event': 'message_end', 'conversation_id': data.get('conversation_id', ''), 'metadata': data.get('metadata', {})})}\n\n"

                    elif event_type == "error":
                        yield f"data: {json.dumps({'event': 'error', 'message': data.get('message', '未知错误')})}\n\n"

                    elif event_type in ("workflow_started", "node_started", "node_finished", "workflow_finished"):
                        # 工作流中间事件，透传给前端（可选展示进度）
                        yield f"data: {json.dumps({'event': event_type, 'data': data})}\n\n"

                except json.JSONDecodeError:
                    logger.warning(f"流式响应解析失败: {data_str}")
                    continue


async def upload_file(file_bytes: bytes, filename: str, user: str, api_key: str = "") -> dict:
    """
    上传文件到Dify
    """
    url = f"{settings.DIFY_BASE_URL}/v1/files/upload"
    key = api_key or settings.DIFY_CHAT_API_KEY
    headers = {
        "Authorization": f"Bearer {key}",
    }
    client = await get_http_client()
    response = await client.post(
        url,
        headers=headers,
        data={"user": user},
        files={"file": (filename, file_bytes)},
    )
    if response.status_code not in (200, 201):
        logger.error(f"Dify文件上传错误: status={response.status_code}, body={response.text}")
        raise Exception(f"Dify文件上传错误({response.status_code}): {response.text}")
    return response.json()


def extract_chat_answer(result: dict) -> str:
    """从Dify Chatbot返回结果中提取回答文本（阻塞模式）"""
    answer = result.get("answer", "")
    return answer


def extract_workflow_output(result: dict) -> str:
    """从Dify工作流返回结果中提取输出文本"""
    data = result.get("data", {})
    outputs = data.get("outputs", {})
    for key in ("text", "output", "result", "summary", "content"):
        if key in outputs and outputs[key]:
            return outputs[key]
    if outputs:
        return str(outputs)
    return ""
