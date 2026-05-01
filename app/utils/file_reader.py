"""
文件读取工具：支持读取 txt、json、doc、docx、pdf 等格式的文件，返回纯文本内容。
"""

import os
import json
import logging

logger = logging.getLogger(__name__)


def read_file(file_path: str) -> str:
    """
    读取文件内容，根据文件扩展名自动选择对应的解析方式。

    Args:
        file_path: 文件的绝对路径或相对路径

    Returns:
        文件的纯文本内容 (str)

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不支持的文件格式
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    readers = {
        ".txt": _read_txt,
        ".json": _read_json,
        ".docx": _read_docx,
        ".doc": _read_doc,
        ".pdf": _read_pdf,
    }

    reader = readers.get(ext)
    if reader is None:
        raise ValueError(f"不支持的文件格式: {ext}，目前支持: {', '.join(readers.keys())}")

    return reader(file_path)


def _read_json(file_path: str) -> str:
    """读取 json 文件，返回格式化后的 JSON 字符串。"""
    encodings = ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                data = json.load(f)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise UnicodeDecodeError("json", b"", 0, 1, f"无法用常见编码解码文件: {file_path}")


def _read_txt(file_path: str) -> str:
    """读取 txt 文件，自动尝试常见编码。"""
    encodings = ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise UnicodeDecodeError("txt", b"", 0, 1, f"无法用常见编码解码文件: {file_path}")


def _read_docx(file_path: str) -> str:
    """读取 docx 文件。"""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("读取 docx 文件需要安装 python-docx：pip install python-docx")

    doc = Document(file_path)
    paragraphs = [para.text for para in doc.paragraphs]
    return "\n".join(paragraphs)


def _read_doc(file_path: str) -> str:
    """
    读取 doc 文件。
    优先尝试使用 win32com (Windows + Word)，不可用时尝试 antiword。
    """
    # 方式1: win32com (Windows 环境下需要安装 Microsoft Word)
    try:
        import win32com.client

        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        try:
            doc = word.Documents.Open(os.path.abspath(file_path))
            text = doc.Content.Text
            doc.Close(False)
            return text.strip()
        finally:
            word.Quit()
    except Exception:
        logger.debug("win32com 读取 .doc 文件失败，尝试其他方式")

    # 方式2: antiword (需要系统安装 antiword)
    try:
        import subprocess

        result = subprocess.run(
            ["antiword", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        logger.debug("antiword 读取 .doc 文件失败")

    raise RuntimeError(
        "读取 .doc 文件失败。请安装以下任一依赖：\n"
        "  1. Windows 环境: pip install pywin32 (需已安装 Microsoft Word)\n"
        "  2. Linux 环境: sudo apt-get install antiword"
    )


def _read_pdf(file_path: str) -> str:
    """读取 pdf 文件。优先使用 pdfplumber，备选 PyPDF2。"""
    # 方式1: pdfplumber (解析效果更好)
    try:
        import pdfplumber

        texts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    texts.append(page_text)
        return "\n".join(texts)
    except ImportError:
        logger.debug("pdfplumber 未安装，尝试 PyPDF2")
    except Exception as e:
        logger.debug(f"pdfplumber 读取失败: {e}")

    # 方式2: PyPDF2
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        texts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text)
        return "\n".join(texts)
    except ImportError:
        raise ImportError("读取 pdf 文件需要安装 pdfplumber 或 PyPDF2：pip install pdfplumber")
    except Exception as e:
        raise RuntimeError(f"读取 PDF 文件失败: {e}")
