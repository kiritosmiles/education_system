"""
基于 LangChain 的文本切块工具。

使用 RecursiveCharacterTextSplitter 对文本进行递归切块，
并为每个切块提供丰富的元数据信息。
"""

import logging
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.file_reader import read_file

logger = logging.getLogger(__name__)

# ---------- 默认参数 ----------
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    separators: Optional[list[str]] = None,
    source_file: str = "",
    doc_id: str = "",
    extra_metadata: Optional[dict] = None,
) -> list[dict]:
    """
    使用 LangChain RecursiveCharacterTextSplitter 对文本进行切块。

    Args:
        text: 待切块的纯文本内容
        chunk_size: 每个切块的最大字符数，默认 500
        chunk_overlap: 相邻切块的重叠字符数，默认 50
        separators: 分隔符优先级列表，默认按段落/句子/标点递归切分
        source_file: 来源文件名，写入元数据
        doc_id: 文档唯一标识，写入元数据
        extra_metadata: 额外的自定义元数据字典

    Returns:
        切块列表，每个元素为 dict，包含：
        - content: 切块文本内容
        - metadata: 元数据字典，包含 chunk_index、chunk_size、total_chunks、
                    char_start、char_end、source_file、doc_id 及自定义字段
    """
    if not text or not text.strip():
        logger.warning("输入文本为空，返回空列表")
        return []

    if separators is None:
        separators = DEFAULT_SEPARATORS

    # 构建切分器
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,
        is_separator_regex=False,
    )

    # 执行切块
    langchain_docs = splitter.create_documents([text])
    total_chunks = len(langchain_docs)

    # 计算每个 chunk 在原文中的大致字符位置
    char_cursor = 0
    results: list[dict] = []

    for idx, doc in enumerate(langchain_docs):
        chunk_content = doc.page_content
        chunk_len = len(chunk_content)

        # 在原文中查找该 chunk 的起始位置（从上一次位置往后找）
        found_pos = text.find(chunk_content, char_cursor)
        if found_pos != -1:
            char_start = found_pos
            char_end = found_pos + chunk_len
            char_cursor = found_pos + 1
        else:
            # 未能精确匹配时使用估算位置
            char_start = char_cursor
            char_end = char_cursor + chunk_len
            char_cursor = char_end

        # 组装元数据
        metadata = {
            "chunk_index": idx,
            "chunk_size": chunk_len,
            "chunk_overlap": chunk_overlap,
            "total_chunks": total_chunks,
            "char_start": char_start,
            "char_end": char_end,
            "source_file": source_file,
            "doc_id": doc_id,
        }

        # 合入额外元数据
        if extra_metadata:
            metadata.update(extra_metadata)

        results.append({
            "content": chunk_content,
            "metadata": metadata,
        })

    logger.info(f"文本切块完成: 原文长度={len(text)}, 切块数={total_chunks}, "
                f"chunk_size={chunk_size}, overlap={chunk_overlap}")
    return results

if __name__ == "__main__":
    text = read_file("../static/《三国演义》.txt")
    results = chunk_text(text)
    print(results)
