"""
Milvus 向量数据库初始化脚本。

在 default 数据库中创建集合，通过 OpenAI SDK 调用阿里 DashScope 向量化模型：
1. sanguo_qa  —— 读取 sanguo_qa.json，向量化问答对并存入向量库
2. sanguo_text —— 读取切块后的《三国演义》.txt，向量化切块内容并存入向量库

BM25 稀疏向量由 Milvus 内置 BM25 Function 自动生成（插入文本字段时自动计算）。
"""

import json
import os
import logging

from openai import OpenAI
from pymilvus import (
    MilvusClient, DataType, CollectionSchema, FieldSchema,
    Function, FunctionType,
)

from app.config import get_settings
from app.utils.file_reader import read_file
from app.utils.text_chunker import chunk_text

logger = logging.getLogger(__name__)

# ---------- 常量 ----------
EMBEDDING_MODEL = "text-embedding-v3"
EMBEDDING_DIM = 1024
EMBEDDING_BATCH_SIZE = 10  # DashScope text-embedding-v3 单次上限

QA_COLLECTION = "sanguo_qa"
TEXT_COLLECTION = "sanguo_text"

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


# ============================================================
# OpenAI 客户端（DashScope 兼容模式）
# ============================================================
def _get_openai_client() -> OpenAI:
    """创建 OpenAI 客户端，连接 DashScope 兼容接口。"""
    settings = get_settings()
    return OpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    通过 OpenAI SDK 调用阿里 DashScope 向量化模型，分批获取文本向量。

    Args:
        texts: 文本列表

    Returns:
        向量列表，与输入顺序一一对应
    """
    client = _get_openai_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
            dimensions=EMBEDDING_DIM,
        )
        batch_embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        all_embeddings.extend(batch_embeddings)
        logger.info(f"Embedding 进度: {min(i + EMBEDDING_BATCH_SIZE, len(texts))}/{len(texts)}")

    return all_embeddings


# ============================================================
# 集合 Schema 定义
# ============================================================
def _build_qa_schema() -> CollectionSchema:
    """构建 sanguo_qa 集合的 Schema，BM25 稀疏向量由 Milvus Function 自动生成。"""
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        # 元数据
        FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=2000),
        FieldSchema(name="answer", dtype=DataType.VARCHAR, max_length=4000),
        FieldSchema(name="reason", dtype=DataType.VARCHAR, max_length=8000),
        FieldSchema(name="combined_text", dtype=DataType.VARCHAR, max_length=16000,
                    enable_analyzer=True, is_clustering_key=True),  # BM25 Function 输入字段
        FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="qa_index", dtype=DataType.INT64),
        # 稠密向量
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
        # 稀疏向量（BM25 Function 输出字段，由 Milvus 自动生成）
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
    ]

    # BM25 Function: 从 combined_text 自动生成稀疏向量
    bm25_function = Function(
        name="qa_bm25",
        input_field_names=["combined_text"],
        output_field_names=["sparse_vector"],
        function_type=FunctionType.BM25,
    )

    schema = CollectionSchema(fields=fields, functions=[bm25_function],
                              description="三国问答对向量集合（混合检索）")
    schema.verify()
    return schema


def _build_text_schema() -> CollectionSchema:
    """构建 sanguo_text 集合的 Schema，BM25 稀疏向量由 Milvus Function 自动生成。"""
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        # 元数据
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8000,
                    enable_analyzer=True, is_clustering_key=True),  # BM25 Function 输入字段
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="chunk_size", dtype=DataType.INT64),
        FieldSchema(name="total_chunks", dtype=DataType.INT64),
        FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="char_start", dtype=DataType.INT64),
        FieldSchema(name="char_end", dtype=DataType.INT64),
        # 稠密向量
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
        # 稀疏向量（BM25 Function 输出字段，由 Milvus 自动生成）
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
    ]

    # BM25 Function: 从 content 自动生成稀疏向量
    bm25_function = Function(
        name="text_bm25",
        input_field_names=["content"],
        output_field_names=["sparse_vector"],
        function_type=FunctionType.BM25,
    )

    schema = CollectionSchema(fields=fields, functions=[bm25_function],
                              description="三国演义文本切块向量集合（混合检索）")
    schema.verify()
    return schema


# ============================================================
# 创建集合 + 索引
# ============================================================
def _create_qa_collection(client: MilvusClient) -> None:
    """创建 sanguo_qa 集合及索引。若旧集合存在则删除重建。"""
    if client.has_collection(QA_COLLECTION):
        logger.info(f"删除已存在的集合 {QA_COLLECTION}，将重建")
        client.drop_collection(QA_COLLECTION)

    schema = _build_qa_schema()
    client.create_collection(collection_name=QA_COLLECTION, schema=schema)
    logger.info(f"集合 {QA_COLLECTION} 创建成功")

    _create_indexes(client, QA_COLLECTION)


def _create_text_collection(client: MilvusClient) -> None:
    """创建 sanguo_text 集合及索引。若旧集合存在则删除重建。"""
    if client.has_collection(TEXT_COLLECTION):
        logger.info(f"删除已存在的集合 {TEXT_COLLECTION}，将重建")
        client.drop_collection(TEXT_COLLECTION)

    schema = _build_text_schema()
    client.create_collection(collection_name=TEXT_COLLECTION, schema=schema)
    logger.info(f"集合 {TEXT_COLLECTION} 创建成功")

    _create_indexes(client, TEXT_COLLECTION)


def _create_indexes(client: MilvusClient, collection_name: str) -> None:
    """为集合创建稠密向量索引和 BM25 稀疏向量索引。"""
    index_params = client.prepare_index_params()
    # 稠密向量索引
    index_params.add_index(
        field_name="dense_vector",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": 128},
    )
    # BM25 稀疏向量索引（字段由 BM25 Function 自动填充）
    index_params.add_index(
        field_name="sparse_vector",
        index_type="SPARSE_INVERTED_INDEX",
        metric_type="BM25",
    )

    client.create_index(collection_name=collection_name, index_params=index_params)
    logger.info(f"集合 {collection_name} 索引创建成功（dense + sparse）")

    client.load_collection(collection_name=collection_name)
    logger.info(f"集合 {collection_name} 已加载到内存")


# ============================================================
# 数据写入方法
# ============================================================
def insert_qa_data(client: MilvusClient) -> None:
    """
    读取 sanguo_qa.json 文件，通过 OpenAI SDK 调用阿里向量化模型，
    将问答对原数据 + 稠密向量存入 sanguo_qa 集合。

    BM25 稀疏向量由 Milvus 内置 BM25 Function 自动生成：
    插入 combined_text 字段后，Milvus 自动分词并计算 sparse_vector。
    """
    # 读取 JSON 数据
    json_path = os.path.join(STATIC_DIR, "sanguo_qa.json")
    with open(json_path, "r", encoding="utf-8") as f:
        qa_list = json.load(f)
    logger.info(f"加载问答对数量: {len(qa_list)}")

    # 拼接组合文本（用于稠密向量化和 BM25 稀疏向量自动生成）
    combined_texts = [
        f"问题：{item['question']} 答案：{item['answer']} 解析：{item.get('reason', '')}"
        for item in qa_list
    ]

    # 调用向量化模型生成稠密向量
    logger.info("开始向量化问答对...")
    all_embeddings = get_embeddings(combined_texts)

    # 组装插入数据（不需要手动指定 sparse_vector，BM25 Function 自动填充）
    data = []
    for idx, (qa, emb) in enumerate(zip(qa_list, all_embeddings)):
        data.append({
            "question": qa["question"],
            "answer": qa["answer"],
            "reason": qa.get("reason", ""),
            "combined_text": combined_texts[idx],
            "source_file": "sanguo_qa.json",
            "qa_index": idx,
            "dense_vector": emb,
        })

    client.insert(collection_name=QA_COLLECTION, data=data)
    logger.info(f"集合 {QA_COLLECTION} 插入 {len(data)} 条记录")


def insert_text_data(client: MilvusClient) -> None:
    """
    读取《三国演义》.txt 文件，通过 text_chunker 切块后，
    通过 OpenAI SDK 调用阿里向量化模型，将切块内容 + 稠密向量存入 sanguo_text 集合。

    BM25 稀疏向量由 Milvus 内置 BM25 Function 自动生成：
    插入 content 字段后，Milvus 自动分词并计算 sparse_vector。
    """
    # 读取并切块
    txt_path = os.path.join(STATIC_DIR, "《三国演义》.txt")
    full_text = read_file(txt_path)
    chunks = chunk_text(
        text=full_text,
        source_file="《三国演义》.txt",
        doc_id="sanguo_novel",
    )
    logger.info(f"《三国演义》切块数量: {len(chunks)}")

    # 提取切块文本用于向量化
    chunk_texts = [item["content"] for item in chunks]

    # 调用向量化模型生成稠密向量
    logger.info("开始向量化文本切块...")
    all_embeddings = get_embeddings(chunk_texts)

    # 组装插入数据（不需要手动指定 sparse_vector，BM25 Function 自动填充）
    data = []
    for chunk_item, emb in zip(chunks, all_embeddings):
        meta = chunk_item["metadata"]
        data.append({
            "content": chunk_item["content"],
            "chunk_index": meta["chunk_index"],
            "chunk_size": meta["chunk_size"],
            "total_chunks": meta["total_chunks"],
            "source_file": meta["source_file"],
            "char_start": meta["char_start"],
            "char_end": meta["char_end"],
            "dense_vector": emb,
        })

    client.insert(collection_name=TEXT_COLLECTION, data=data)
    logger.info(f"集合 {TEXT_COLLECTION} 插入 {len(data)} 条记录")


# ============================================================
# 主入口
# ============================================================
def init_milvus_db() -> MilvusClient:
    """
    初始化 Milvus 向量数据库：创建集合、写入向量化数据。

    Returns:
        MilvusClient 实例
    """
    settings = get_settings()
    uri = settings.MILVUS_URI
    logger.info(f"连接 Milvus: {uri}")

    client = MilvusClient(uri=uri, db_name="default")

    # 创建集合及索引
    _create_qa_collection(client)
    _create_text_collection(client)

    # 写入向量化数据
    insert_qa_data(client)
    insert_text_data(client)

    logger.info("Milvus 向量数据库初始化完成")
    return client


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_milvus_db()
