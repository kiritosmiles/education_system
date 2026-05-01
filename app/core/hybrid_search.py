"""
混合检索核心模块。

基于 Milvus 向量数据库的两个集合（sanguo_qa、sanguo_text），
实现稠密向量 + BM25 稀疏向量的混合检索，使用 RRF 融合排序，
最终由 LLM 整合检索结果生成带出处的回答。
"""

import logging
import re
from typing import Optional

from openai import OpenAI
from pymilvus import MilvusClient, AnnSearchRequest, Function, FunctionType

from app.config import get_settings
from app.utils.init_milvus_db import get_embeddings, EMBEDDING_DIM

logger = logging.getLogger(__name__)

# ---------- 常量 ----------
QA_COLLECTION = "sanguo_qa"
TEXT_COLLECTION = "sanguo_text"

QA_SEARCH_FIELDS = ["question", "answer", "reason", "combined_text", "source_file", "qa_index"]
TEXT_SEARCH_FIELDS = ["content", "chunk_index", "source_file", "char_start", "char_end"]

# LLM 模型
LLM_MODEL = "qwen-plus"


# ============================================================
# Milvus 客户端
# ============================================================
def _get_milvus_client() -> MilvusClient:
    """获取 Milvus 客户端连接。"""
    settings = get_settings()
    return MilvusClient(uri=settings.MILVUS_URI, db_name="default")


def _get_openai_client() -> OpenAI:
    """获取 OpenAI 客户端（DashScope 兼容模式）。"""
    settings = get_settings()
    return OpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


# ============================================================
# 混合检索
# ============================================================
def _hybrid_search_qa(query: str, top_k: int = 5) -> list[dict]:
    """
    在 sanguo_qa 集合上执行混合检索（稠密向量 + BM25 稀疏向量，RRF 融合）。

    Args:
        query: 用户查询文本
        top_k: 返回条数

    Returns:
        检索结果列表
    """
    client = _get_milvus_client()

    # 1) 稠密向量检索请求
    query_dense = get_embeddings([query])[0]
    dense_req = AnnSearchRequest(
        data=[query_dense],
        anns_field="dense_vector",
        param={"metric_type": "COSINE", "params": {"nprobe": 16}},
        limit=top_k,
    )

    # 2) BM25 稀疏向量检索请求（直接传入查询文本，Milvus 自动分词）
    sparse_req = AnnSearchRequest(
        data=[query],
        anns_field="sparse_vector",
        param={"metric_type": "BM25"},
        limit=top_k,
    )

    # 3) RRF 融合排序
    rrf_ranker = Function(
        name="rrf",
        input_field_names=[],
        function_type=FunctionType.RERANK,
        params={"reranker": "rrf", "k": 60},
    )

    results = client.hybrid_search(
        collection_name=QA_COLLECTION,
        reqs=[dense_req, sparse_req],
        ranker=rrf_ranker,
        limit=top_k,
        output_fields=QA_SEARCH_FIELDS,
    )

    hits = []
    for hit in results[0]:
        item = {}
        for field in QA_SEARCH_FIELDS:
            item[field] = hit.get(field)
        item["score"] = hit.get("distance")
        hits.append(item)

    logger.info(f"QA 混合检索返回 {len(hits)} 条结果")
    return hits


def _hybrid_search_text(query: str, top_k: int = 5) -> list[dict]:
    """
    在 sanguo_text 集合上执行混合检索（稠密向量 + BM25 稀疏向量，RRF 融合）。

    Args:
        query: 用户查询文本
        top_k: 返回条数

    Returns:
        检索结果列表
    """
    client = _get_milvus_client()

    # 1) 稠密向量检索请求
    query_dense = get_embeddings([query])[0]
    dense_req = AnnSearchRequest(
        data=[query_dense],
        anns_field="dense_vector",
        param={"metric_type": "COSINE", "params": {"nprobe": 16}},
        limit=top_k,
    )

    # 2) BM25 稀疏向量检索请求
    sparse_req = AnnSearchRequest(
        data=[query],
        anns_field="sparse_vector",
        param={"metric_type": "BM25"},
        limit=top_k,
    )

    # 3) 加权分数融合（weighted）
    weighted_ranker = Function(
        name="weighted",
        input_field_names=[],
        function_type=FunctionType.RERANK,
        params={"reranker": "weighted", "weights": [0.7, 0.3]},
    )

    results = client.hybrid_search(
        collection_name=TEXT_COLLECTION,
        reqs=[dense_req, sparse_req],
        ranker=weighted_ranker,
        limit=top_k,
        output_fields=TEXT_SEARCH_FIELDS,
    )

    hits = []
    for hit in results[0]:
        item = {}
        for field in TEXT_SEARCH_FIELDS:
            item[field] = hit.get(field)
        item["score"] = hit.get("distance")
        hits.append(item)

    logger.info(f"Text 混合检索返回 {len(hits)} 条结果")
    return hits


# ============================================================
# 构建检索上下文
# ============================================================
def _build_context(qa_hits: list[dict], text_hits: list[dict]) -> str:
    """
    将检索结果格式化为 LLM 可用的上下文文本，包含出处信息。

    Args:
        qa_hits: QA 集合检索结果
        text_hits: Text 集合检索结果

    Returns:
        格式化后的上下文字符串
    """
    context_parts = []

    # 问答对出处
    if qa_hits:
        context_parts.append("===== 问答对参考 =====")
        for i, hit in enumerate(qa_hits, 1):
            context_parts.append(
                f"【问答出处 {i}】\n"
                f"  问题：{hit.get('question', '')}\n"
                f"  答案：{hit.get('answer', '')}\n"
                f"  解析：{hit.get('reason', '')}\n"
                f"  来源：{hit.get('source_file', '')} (第{hit.get('qa_index', '')}条)\n"
                f"  相关度：{hit.get('score', 0):.4f}"
            )

    # 原文出处
    if text_hits:
        context_parts.append("\n===== 原文参考 =====")
        for i, hit in enumerate(text_hits, 1):
            context_parts.append(
                f"【原文出处 {i}】\n"
                f"  内容：{hit.get('content', '')}\n"
                f"  来源：{hit.get('source_file', '')} "
                f"(第{hit.get('chunk_index', '')}块, 字符位置{hit.get('char_start', '')}-{hit.get('char_end', '')})\n"
                f"  相关度：{hit.get('score', 0):.4f}"
            )

    return "\n".join(context_parts)


# ============================================================
# LLM 回答生成
# ============================================================
def _generate_answer(query: str, context: str) -> str:
    """
    调用 LLM 基于检索上下文生成回答，要求附带出处。

    Args:
        query: 用户问题
        context: 检索上下文

    Returns:
        LLM 生成的回答（含出处）
    """
    client = _get_openai_client()

    system_prompt = (
        "你是一个三国演义知识专家。请根据下方提供的参考资料回答用户的问题。\n"
        "要求：\n"
        "1. 回答必须基于参考资料，不要编造信息\n"
        "2. 引用资料时，必须写出具体的引用内容，并在引用后标注出处编号，格式为：\n"
        "   「具体引用的内容」【出处 N】\n"
        "   示例：刘备、关羽、张飞在桃园结为兄弟「桃园三结义」【出处 1】；"
        "后关羽败走麦城被孙权所杀「败走麦城后为孙权所害」【出处 3】\n"
        "3. 如果参考资料不足以回答问题，请如实说明\n"
        "4. 回答要简洁、准确、有条理\n"
        "5. 尽可能多引用不同出处的内容，让回答有据可查"
    )

    user_prompt = f"参考资料：\n{context}\n\n用户问题：{query}"

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    answer = response.choices[0].message.content
    logger.info(f"LLM 生成回答，token 用量: {response.usage.total_tokens if response.usage else 'N/A'}")
    return answer


# ============================================================
# 主入口
# ============================================================
def hybrid_search_answer(
    query: str,
    qa_top_k: int = 5,
    text_top_k: int = 5,
) -> dict:
    """
    混合检索 + LLM 生成回答。

    流程：
    1. 在 sanguo_qa 集合上执行混合检索（稠密 + BM25，RRF 融合）
    2. 在 sanguo_text 集合上执行混合检索（稠密 + BM25，加权分数融合）
    3. 将检索结果格式化为上下文
    4. 调用 LLM 生成带出处的回答

    Args:
        query: 用户输入的问题
        qa_top_k: QA 集合检索条数
        text_top_k: Text 集合检索条数

    Returns:
        {"answer": LLM回答文本, "qa_sources": 问答出处列表, "text_sources": 原文出处列表}
    """
    logger.info(f"混合检索开始，问题: {query}")

    # 并行混合检索两个集合
    qa_hits = _hybrid_search_qa(query, top_k=qa_top_k)
    text_hits = _hybrid_search_text(query, top_k=text_top_k)

    # 构建上下文
    context = _build_context(qa_hits, text_hits)

    if not qa_hits and not text_hits:
        return {
            "answer": "抱歉，未在知识库中找到与您问题相关的内容。",
            "qa_sources": [],
            "text_sources": [],
        }

    # LLM 生成回答
    answer = _generate_answer(query, context)

    # 从回答中提取实际引用的出处编号
    cited_qa_indices = sorted(set(int(m) for m in re.findall(r"【问答出处\s*(\d+)】", answer)))
    cited_text_indices = sorted(set(int(m) for m in re.findall(r"【原文出处\s*(\d+)】", answer)))

    # 统一编号：问答出处从 1 开始，原文出处紧接其后，避免标号重复
    qa_index_map = {old: new for new, old in enumerate(cited_qa_indices, 1)}
    text_start = len(cited_qa_indices) + 1
    text_index_map = {old: new for new, old in enumerate(cited_text_indices, text_start)}

    # 替换回答文本中的旧编号为统一新编号
    def _replace_qa(m):
        old = int(m.group(1))
        return f"【出处 {qa_index_map[old]}】"

    def _replace_text(m):
        old = int(m.group(1))
        return f"【出处 {text_index_map[old]}】"

    answer = re.sub(r"【问答出处\s*(\d+)】", _replace_qa, answer)
    answer = re.sub(r"【原文出处\s*(\d+)】", _replace_text, answer)

    # 构建出处详情（使用统一编号）
    qa_sources = []
    for i, hit in enumerate(qa_hits, 1):
        if i in qa_index_map:
            qa_sources.append({
                "index": qa_index_map[i],
                "type": "qa",
                "question": hit.get("question", ""),
                "answer": hit.get("answer", ""),
                "reason": hit.get("reason", ""),
                "source_file": hit.get("source_file", ""),
                "qa_index": hit.get("qa_index", 0),
                "score": round(hit.get("score", 0), 4),
            })

    text_sources = []
    for i, hit in enumerate(text_hits, 1):
        if i in text_index_map:
            text_sources.append({
                "index": text_index_map[i],
                "type": "text",
                "content": hit.get("content", ""),
                "source_file": hit.get("source_file", ""),
                "chunk_index": hit.get("chunk_index", 0),
                "char_start": hit.get("char_start", 0),
                "char_end": hit.get("char_end", 0),
                "score": round(hit.get("score", 0), 4),
            })

    # 合并并按统一编号排序
    all_sources = qa_sources + text_sources
    all_sources.sort(key=lambda x: x["index"])

    logger.info("混合检索 + LLM 回答完成")
    return {
        "answer": answer,
        "sources": all_sources,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = hybrid_search_answer("关羽是怎么死的？")
    print(result["answer"])
    print("\n--- Sources ---")
    for s in result["sources"]:
        print(f"  {s}")
