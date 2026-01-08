#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语雀 Lakebook 转换工具
支持将 lakebook 文件中的文档转换为 Markdown 或 CSV 格式
- 普通文档 (Doc) -> Markdown
- 表格文档 (Sheet) -> CSV
"""

import json
import os
import random
import shutil
import sys
import argparse
import tarfile
import csv
import gzip
import zlib
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from markdownify import markdownify as md
    HAS_MARKDOWNIFY = True
except ImportError:
    HAS_MARKDOWNIFY = False
    print("警告: 未安装 markdownify，HTML 转换效果可能不佳。建议运行: pip install markdownify")

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("警告: 未安装 beautifulsoup4，无法下载图片。建议运行: pip install beautifulsoup4")

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("错误: 未安装 pyyaml，无法解析目录结构。请运行: pip install pyyaml")

try:
    from requests import get
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("警告: 未安装 requests，无法下载图片。建议运行: pip install requests")

import tempfile

TYPE_TITLE = "TITLE"
TYPE_DOC = "DOC"
TYPE_SHEET = "Sheet"
META_JSON = "$meta.json"
TMP_DIR = tempfile.gettempdir()

DEFAULT_HEADING_STYLE = "ATX"

content_type_to_extension = {
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/svg+xml": ".svg",
    "image/png": ".png",
}


def sanitizer_file_name(name):
    """清理文件名，移除非法字符"""
    name = name.replace("/", "_")
    name = name.replace("\\", "_")
    name = name.replace(" ", "_")
    name = name.replace("?", "_")
    name = name.replace("*", "_")
    name = name.replace("<", "_")
    name = name.replace(">", "_")
    name = name.replace("|", "_")
    name = name.replace('"', "_")
    name = name.replace(":", "_")
    return name


def read_toc_and_book_info(random_tmp_dir):
    """读取目录结构和 book 信息"""
    if not HAS_YAML:
        raise ImportError("需要安装 pyyaml: pip install pyyaml")
    
    f = open(os.path.join(random_tmp_dir, META_JSON), "r", encoding="utf-8")
    meta_file_str = json.loads(f.read())
    meta_str = meta_file_str.get("meta", "")
    meta = json.loads(meta_str)
    book_info = meta.get("book", {})
    toc_str = book_info.get("tocYml", "")
    toc = yaml.unsafe_load(toc_str)
    f.close()
    
    # 提取 book 信息
    book_name = book_info.get("name", "")
    book_path = book_info.get("path", "")
    # 如果没有 name，尝试从 path 中提取
    if not book_name and book_path:
        # path 格式通常是: https://www.yuque.com/username/repo
        parts = book_path.rstrip('/').split('/')
        if len(parts) > 0:
            book_name = parts[-1]
    
    # 如果还是没有，使用默认名称
    if not book_name:
        book_name = "未命名知识库"
    
    return toc, book_name


def parse_lakesheet(body: str) -> Optional[List[List[str]]]:
    """
    解析 lakesheet 格式的表格数据
    
    Args:
        body: Sheet 文档的 body 字段（JSON 字符串）
        
    Returns:
        表格数据（二维列表），如果解析失败返回 None
    """
    try:
        # body 是一个 JSON 字符串
        sheet_data = json.loads(body)
        
        # 检查格式
        if sheet_data.get("format") != "lakesheet":
            return None
        
        # sheet 字段包含压缩的数据
        sheet_str = sheet_data.get("sheet", "")
        if not sheet_str:
            return None
        
        # 将字符串转换为字节（使用 latin-1 编码保留所有字节值）
        if isinstance(sheet_str, str):
            sheet_bytes = sheet_str.encode('latin-1')
        else:
            sheet_bytes = sheet_str
        
        # 尝试 zlib 解压（lark sheet 使用 zlib 压缩）
        try:
            decompressed = zlib.decompress(sheet_bytes)
            sheet_json = json.loads(decompressed.decode('utf-8'))
        except:
            # 如果 zlib 失败，尝试 gzip
            try:
                decompressed = gzip.decompress(sheet_bytes)
                sheet_json = json.loads(decompressed.decode('utf-8'))
            except:
                # 如果都失败，尝试直接解析为 JSON
                try:
                    sheet_json = json.loads(sheet_str)
                except:
                    return None
        
        # 解析表格数据
        # sheet_json 可能是一个列表（多个工作表）或字典（单个工作表）
        all_rows = []
        
        if isinstance(sheet_json, list):
            # 多个工作表，取第一个
            if len(sheet_json) > 0:
                sheet_json = sheet_json[0]
            else:
                return None
        
        if isinstance(sheet_json, dict):
            # 查找 data 字段，包含单元格数据
            data = sheet_json.get('data', {})
            if not data:
                return None
            
            # 数据格式: {'行号': {'列号': {'v': 值, ...}, ...}, ...}
            # 获取所有行号和列号
            row_indices = sorted([int(k) for k in data.keys() if k.isdigit()])
            if not row_indices:
                return None
            
            # 获取最大列号
            max_col = 0
            for row_idx in row_indices:
                row_data = data.get(str(row_idx), {})
                col_indices = [int(k) for k in row_data.keys() if k.isdigit()]
                if col_indices:
                    max_col = max(max_col, max(col_indices))
            
            # 构建表格
            for row_idx in row_indices:
                row_data = data.get(str(row_idx), {})
                row = []
                for col_idx in range(max_col + 1):
                    cell = row_data.get(str(col_idx), {})
                    # 获取单元格值
                    value = cell.get('v', '')
                    # 如果值是字典（可能是链接等），提取文本
                    if isinstance(value, dict):
                        value = value.get('text', value.get('url', ''))
                    row.append(str(value) if value else '')
                
                # 只添加非空行
                if any(cell.strip() for cell in row):
                    all_rows.append(row)
        
        return all_rows if all_rows else None
        
    except Exception as e:
        print(f"解析表格数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def rows_to_sheet_plus_format(rows: List[List[str]], title: str, file_path: str = "") -> str:
    """
    将行数据转换为 Obsidian sheet plus 插件格式
    
    Args:
        rows: 二维列表，每行是一个列表
        title: 文档标题
        file_path: 文件路径（用于生成 name）
        
    Returns:
        Markdown 格式的字符串，包含 frontmatter 和 sheet 代码块
    """
    import uuid
    import string
    
    if not rows:
        return ""
    
    # 确保所有行的列数一致
    max_cols = max(len(row) for row in rows) if rows else 0
    if max_cols == 0:
        return ""
    
    # 补齐所有行的列数
    normalized_rows = []
    for row in rows:
        normalized_row = row + [''] * (max_cols - len(row))
        normalized_rows.append(normalized_row)
    
    # 生成唯一 ID
    sheet_id = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(6)])
    sheet_key = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(16)])
    
    # 定义默认样式
    def create_default_style(style_id: str, is_header: bool = False, is_number: bool = False) -> dict:
        """创建默认样式"""
        style = {
            "ff": "Arial" if is_header else "Calibri",
            "fs": 9 if is_header else 11,
            "it": 0,  # italic
            "bl": 1 if is_header else 0,  # bold
            "ul": {"s": 0, "cl": {"rgb": "rgb(0,0,0)"}},  # underline
            "st": {"s": 0, "cl": {"rgb": "rgb(0,0,0)"}},  # strikethrough
            "ol": {"s": 0, "cl": {"rgb": "rgb(0,0,0)"}},  # outline
            "tr": {"a": 0, "v": 0},  # text rotation
            "td": 0,  # text direction
            "cl": {"rgb": "rgb(0,0,0)"},  # color
            "ht": 0,  # horizontal alignment
            "vt": 2,  # vertical alignment
            "tb": 1,  # text wrap
            "pd": {"t": 0, "b": 2, "l": 2, "r": 2}  # padding
        }
        
        # 如果是表头，添加边框
        if is_header:
            style["bd"] = {
                "l": {"cl": {"rgb": "rgb(204,204,204)"}, "s": 1},
                "r": {"cl": {"rgb": "rgb(204,204,204)"}, "s": 1},
                "t": {"cl": {"rgb": "rgb(204,204,204)"}, "s": 1},
                "b": {"cl": {"rgb": "rgb(204,204,204)"}, "s": 1}
            }
        
        # 如果是数字，可能需要日期格式
        if is_number:
            style["n"] = {"pattern": "General"}
        
        return style
    
    # 生成样式 ID
    def generate_style_id() -> str:
        return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(6)])
    
    # 创建样式字典
    styles = {}
    header_style_id = generate_style_id()
    styles[header_style_id] = create_default_style(header_style_id, is_header=True)
    
    default_text_style_id = generate_style_id()
    styles[default_text_style_id] = create_default_style(default_text_style_id, is_header=False)
    
    # 构建 cellData
    cell_data = {}
    for row_idx, row in enumerate(normalized_rows):
        row_data = {}
        for col_idx, cell_value in enumerate(row):
            cell_str = str(cell_value).strip() if cell_value else ""
            # 统一按文本处理，避免日期/时间被当作数字显示
            cell_type = 1
            cell_value_processed = cell_str
            
            # 如果是数字（可能是日期序列号），尝试转换为日期字符串
            if cell_str and row_idx > 0:  # 跳过表头
                try:
                    num_value = float(cell_str)
                    from datetime import datetime, timedelta

                    # 情况 1：Excel 日期序列号（按“天”存储）
                    # 通常范围在 1 到 100000 之间（对应 1900-01-01 到 2173-10-14）
                    if 0 < num_value < 100000:
                        try:
                            # Excel 日期序列号从 1900-01-01 开始，但 Excel 错误地认为 1900 是闰年
                            # 所以实际起始日期是 1899-12-30
                            excel_epoch = datetime(1899, 12, 30)
                            dt = excel_epoch + timedelta(days=int(num_value))
                            if 1900 <= dt.year <= 2100:
                                cell_value_processed = dt.strftime('%Y-%m-%d')
                        except (ValueError, OSError, OverflowError):
                            # 如果转换失败，保持原值
                            pass

                    # 情况 2：Excel 日期以“秒”为单位存储（源数据示例：3942259200 等）
                    # 这些值对应 1899-12-30 作为起点的秒数
                    elif 3_000_000_000 <= num_value <= 5_000_000_000:
                        try:
                            excel_epoch_sec = datetime(1899, 12, 30)
                            dt = excel_epoch_sec + timedelta(seconds=int(num_value))
                            if 1900 <= dt.year <= 2100:
                                cell_value_processed = dt.strftime('%Y-%m-%d')
                        except (ValueError, OSError, OverflowError):
                            # 如果转换失败，保持原值
                            pass

                    # 其它范围的数字保持为字符串，避免误判为日期
                except (ValueError, TypeError):
                    # 不是数字，保持原值
                    pass
            
            # 选择样式：第一行用表头样式，其余用文本样式
            if row_idx == 0:
                style_id = header_style_id
            else:
                style_id = default_text_style_id
            
            # 构建单元格数据
            cell_obj = {
                "s": style_id,
                "v": cell_value_processed,
                "t": cell_type
            }
            
            row_data[str(col_idx)] = cell_obj
        
        if row_data:
            cell_data[str(row_idx)] = row_data
    
    # 构建 sheet 数据
    sheet_data = {
        "id": sheet_key,
        "name": "Sheet1",
        "tabColor": "",
        "hidden": 0,
        "rowCount": max(len(normalized_rows), 1000),
        "columnCount": max(max_cols, 20),
        "zoomRatio": 1,
        "freeze": {"xSplit": 0, "ySplit": 0, "startRow": -1, "startColumn": -1},
        "scrollTop": 0,
        "scrollLeft": 0,
        "defaultColumnWidth": 88,
        "defaultRowHeight": 24,
        "mergeData": [],
        "cellData": cell_data,
        "rowData": {},
        "columnData": {},
        "showGridlines": 1,
        "rowHeader": {"width": 46, "hidden": 0},
        "columnHeader": {"height": 20, "hidden": 0},
        "rightToLeft": 0
    }
    
    # 构建完整的 JSON 结构
    # 使用相对路径作为 name（去掉输出目录前缀）
    name = file_path if file_path else title
    if "/" in name:
        # 提取文件名部分
        name = name.split("/")[-1]
    # 去掉 .md 后缀（如果有）
    if name.endswith('.md'):
        name = name[:-3]
    
    sheet_json = {
        "id": sheet_id,
        "sheetOrder": [sheet_key],
        "name": name,
        "appVersion": "0.15.0",
        "locale": "enUS",
        "styles": styles,
        "sheets": {
            sheet_key: sheet_data
        },
        "resources": [
            {"name": "SHEET_UNIVER_THREAD_COMMENT_PLUGIN", "data": "{}"},
            {"name": "SHEET_RANGE_PROTECTION_PLUGIN", "data": ""},
            {"name": "SHEET_AuthzIoMockService_PLUGIN", "data": "{}"},
            {"name": "SHEET_WORKSHEET_PROTECTION_PLUGIN", "data": "{}"},
            {"name": "SHEET_WORKSHEET_PROTECTION_POINT_PLUGIN", "data": "{}"},
            {"name": "SHEET_DRAWING_PLUGIN", "data": "{}"},
            {"name": "SHEET_HYPER_LINK_PLUGIN", "data": f"{{\"{sheet_key}\":[]}}"},
            {"name": "SHEET_CONDITIONAL_FORMATTING_PLUGIN", "data": ""},
            {"name": "SHEET_OUTGOING_LINK_PLUGIN", "data": f"{{\"{sheet_key}\":[]}}"},
            {"name": "SHEET_NOTE_PLUGIN", "data": "{}"},
            {"name": "SHEET_DEFINED_NAME_PLUGIN", "data": "{}"},
            {"name": "SHEET_RANGE_THEME_MODEL_PLUGIN", "data": "{}"},
            {"name": "SHEET_DATA_VALIDATION_PLUGIN", "data": f"{{\"{sheet_key}\":[]}}"},
            {"name": "SHEET_FILTER_PLUGIN", "data": "{}"},
            {"name": "SHEET_TABLE_PLUGIN", "data": "{}"}
        ]
    }
    
    # 生成 Markdown 内容
    frontmatter = "---\n\nexcel-pro-plugin: parsed\n\n---"
    sheet_block = "```sheet\n" + json.dumps(sheet_json, ensure_ascii=False, separators=(',', ':')) + "\n```"
    multisheet_block = "```multiSheet\n{\"tabs\":[{\"key\":\"sheet\",\"type\":\"sheet\",\"label\":\"Sheet\"}],\"defaultActiveKey\":\"sheet\"}\n```"
    
    return f"{frontmatter}\n{sheet_block}\n\n{multisheet_block}\n"


def convert_sheet_to_sheet_plus(sheet_file_path: str, output_path: str, title: str) -> bool:
    """
    将 Sheet 文档转换为 Obsidian sheet plus 格式
    
    Args:
        sheet_file_path: Sheet JSON 文件路径
        output_path: 输出 Markdown 文件路径
        title: 文档标题
        
    Returns:
        是否成功转换
    """
    try:
        with open(sheet_file_path, "r", encoding="utf-8") as f:
            doc_str = json.loads(f.read())
        
        doc = doc_str.get("doc", {})
        body = doc.get("body", "")
        
        if not body:
            print(f"警告: {sheet_file_path} 的 body 为空")
            return False
        
        # 解析表格数据
        rows = parse_lakesheet(body)
        
        if not rows:
            print(f"警告: 无法解析 {sheet_file_path} 的表格数据")
            return False
        
        # 转换为 sheet plus 格式
        sheet_plus_content = rows_to_sheet_plus_format(rows, title, output_path)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(sheet_plus_content)
        
        print(f"✓ 已转换为 Sheet Plus 格式: {output_path} ({len(rows)} 行)")
        return True
        
    except Exception as e:
        print(f"✗ 转换失败 {sheet_file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False


def convert_sheet_to_csv(sheet_file_path: str, output_path: str) -> bool:
    """
    将 Sheet 文档转换为 CSV
    
    Args:
        sheet_file_path: Sheet JSON 文件路径
        output_path: 输出 CSV 文件路径
        
    Returns:
        是否成功转换
    """
    try:
        with open(sheet_file_path, "r", encoding="utf-8") as f:
            doc_str = json.loads(f.read())
        
        doc = doc_str.get("doc", {})
        body = doc.get("body", "")
        
        if not body:
            print(f"警告: {sheet_file_path} 的 body 为空")
            return False
        
        # 解析表格数据
        rows = parse_lakesheet(body)
        
        if not rows:
            print(f"警告: 无法解析 {sheet_file_path} 的表格数据")
            return False
        
        # 写入 CSV
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(rows)
        
        print(f"✓ 已转换为 CSV: {output_path} ({len(rows)} 行)")
        return True
        
    except Exception as e:
        print(f"✗ 转换失败 {sheet_file_path}: {e}")
        return False


def html_to_markdown(html: str) -> str:
    """将 HTML 转换为 Markdown"""
    if HAS_MARKDOWNIFY:
        return md(html, heading_style=DEFAULT_HEADING_STYLE)
    else:
        # 简化版转换
        from html import unescape
        import re
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', html)
        text = unescape(text)
        return text.strip()


def download_images_and_patch_html(output_dir_path, sanitized_title, html):
    """下载图片并更新 HTML 中的图片链接"""
    if not HAS_BS4 or not HAS_REQUESTS:
        return html
    
    bs = BeautifulSoup(html, "html.parser")
    if len(bs.find_all("img")) > 0:
        attachments_dir_path = os.path.join(output_dir_path, "attachments")
        if not os.path.exists(attachments_dir_path):
            os.makedirs(attachments_dir_path)
        no = 1
        for image in bs.find_all("img"):
            try:
                src = image.get("src", "")
                if not src:
                    continue
                print(f"下载图片: {src}")
                resp = get(src, timeout=10)
                file_name = sanitized_title + "_%03d%s" % (
                    no,
                    content_type_to_extension.get(resp.headers.get("Content-Type", ""), ".jpg"),
                )
                attachments_file_path = os.path.join(attachments_dir_path, file_name)
                with open(attachments_file_path, "wb") as f:
                    f.write(resp.content)
                no = no + 1
                image["src"] = "./attachments/" + file_name
            except Exception as e:
                print(f"下载图片失败: {e}")
        html = str(bs)
        return html
    else:
        return html


def pretty_md(text: str) -> str:
    """美化 Markdown 文本"""
    output = text
    lines = output.split("\n")
    for i in range(len(lines)):
        lines[i] = lines[i].rstrip()
    output = "\n".join(lines)
    
    # 移除多余的空行
    for i in range(50):
        output = output.replace("\n\n\n", "\n\n")
        if "\n\n\n" not in output:
            break
    
    return output


def extract_repos(repo_dir, output, toc, download_image, convert_sheets_to_csv, sheet_format, book_name=""):
    """提取并转换文档"""
    last_level = 0
    last_sanitized_title = ""
    path_prefixed = []
    
    for item in toc:
        t = item.get("type", "")
        url = str(item.get("url", ""))
        current_level = item.get("level", 0)
        title = str(item.get("title", ""))
        sanitized_title = sanitizer_file_name(str(title))
        
        if not title:
            continue
        
        # 确保文件名唯一
        while True:
            if os.path.exists(os.path.join(output, sanitized_title)):
                sanitized_title = sanitizer_file_name(str(title)) + str(
                    random.randint(0, 1000)
                )
            break

        # 处理目录层级
        if current_level > last_level:
            path_prefixed = path_prefixed + [last_sanitized_title]
        elif current_level < last_level:
            diff = last_level - current_level
            path_prefixed = path_prefixed[0:-diff]

        # 处理文档
        if t == TYPE_DOC:
            raw_path = os.path.join(repo_dir, url + ".json")
            if not os.path.exists(raw_path):
                print(f"警告: 文件不存在: {raw_path}")
                continue
            
            # 读取文档以确定实际类型
            raw_file = open(raw_path, "r", encoding="utf-8")
            doc_str = json.loads(raw_file.read())
            doc = doc_str.get("doc", {})
            doc_type = doc.get("type", "")
            doc_format = doc.get("format", "")
            
            # 判断是表格文档还是普通文档
            is_sheet = (doc_type == TYPE_SHEET) or (doc_format == "lakesheet")
            
            if is_sheet:
                # 表格文档转换
                if convert_sheets_to_csv:
                    output_dir_path = os.path.join(output, *path_prefixed)
                    if not os.path.exists(output_dir_path):
                        os.makedirs(output_dir_path)
                    
                    if sheet_format == "csv":
                        # 转换为 CSV
                        output_path = os.path.join(output_dir_path, sanitized_title + ".csv")
                        convert_sheet_to_csv(raw_path, output_path)
                    elif sheet_format == "sheet":
                        # 转换为 Obsidian sheet plus 格式
                        output_path = os.path.join(output_dir_path, sanitized_title + ".md")
                        convert_sheet_to_sheet_plus(raw_path, output_path, title)
                    else:
                        # 默认 CSV
                        output_path = os.path.join(output_dir_path, sanitized_title + ".csv")
                        convert_sheet_to_csv(raw_path, output_path)
                else:
                    print(f"跳过表格文档: {title} (使用 --convert-sheets 启用转换)")
            else:
                # 普通文档 -> Markdown
                output_dir_path = os.path.join(output, *path_prefixed)
                if not os.path.exists(output_dir_path):
                    os.makedirs(output_dir_path)
                
                html = doc.get("body") or doc.get("body_asl", "")

                if download_image:
                    html = download_images_and_patch_html(
                        output_dir_path, sanitized_title, html
                    )

                output_path = os.path.join(output_dir_path, sanitized_title + ".md")
                f = open(output_path, "w", encoding="utf-8")
                f.write(pretty_md(html_to_markdown(html)))
                f.close()
                print(f"✓ 已转换为 Markdown: {output_path}")

        last_sanitized_title = sanitized_title
        last_level = current_level


def extract_tar(tar_file, target_dir):
    """解压 tar 文件"""
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    tar = tarfile.open(tar_file)
    names = tar.getnames()
    for name in names:
        tar.extract(name, target_dir)
    tar.close()


def process_single_lakebook(lakebook_path, base_output_dir, download_image, convert_sheets_to_csv, sheet_format):
    """处理单个 lakebook 文件"""
    if not os.path.exists(lakebook_path):
        print(f"错误: Lakebook 文件不存在: {lakebook_path}")
        return False
    
    lakebook_filename = os.path.basename(lakebook_path)
    print(f"\n处理: {lakebook_filename}")
    
    # 从文件名提取目录名（去掉 .lakebook 后缀）
    book_dir_name = lakebook_filename
    if book_dir_name.endswith('.lakebook'):
        book_dir_name = book_dir_name[:-9]  # 去掉 .lakebook (9个字符)
    
    # 清理目录名，移除非法字符
    book_dir_name = sanitizer_file_name(book_dir_name)
    
    # 解压 lakebook 文件
    random_tmp_dir = os.path.join(TMP_DIR, f"lakebook_{os.getpid()}_{random.randint(1000, 9999)}")
    extract_tar(lakebook_path, random_tmp_dir)
    
    # 检测目录
    repo_dir = ""
    for root, dirs, files in os.walk(random_tmp_dir):
        for d in dirs:
            repo_dir = os.path.join(random_tmp_dir, d)
            break
    
    if not repo_dir:
        print(f"错误: {lakebook_path} 文件格式无效")
        shutil.rmtree(random_tmp_dir)
        return False

    try:
        toc, book_name = read_toc_and_book_info(repo_dir)
        print(f"知识库名称: {book_name}")
        print(f"总共 {len(toc)} 个文档")
        
        # 使用文件名作为目录名，而不是从 meta.json 提取的名称
        book_output_dir = os.path.join(base_output_dir, book_dir_name)
        if not os.path.exists(book_output_dir):
            os.makedirs(book_output_dir)
        
        extract_repos(repo_dir, book_output_dir, toc, download_image, convert_sheets_to_csv, sheet_format, book_name)
        
        print(f"✓ 已转换到: {book_output_dir}")
        return True
    except Exception as e:
        print(f"处理 {lakebook_path} 时出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时目录
        if os.path.exists(random_tmp_dir):
            shutil.rmtree(random_tmp_dir)


def main():
    parser = argparse.ArgumentParser(description="转换语雀 Lakebook 文件为 Markdown 或 CSV")
    parser.add_argument("lakebook", nargs="+", help="Lakebook 文件路径（支持多个文件或目录）")
    parser.add_argument("output", help="输出目录")
    parser.add_argument(
        "--download-image", 
        help="下载图片到本地", 
        action="store_true"
    )
    parser.add_argument(
        "--convert-sheets",
        help="将表格文档转换为 CSV 或 Sheet Plus 格式（默认只转换普通文档为 Markdown）",
        action="store_true"
    )
    parser.add_argument(
        "--sheet-format",
        choices=["csv", "sheet"],
        default="csv",
        help="表格输出格式：csv（CSV 文件）或 sheet（Obsidian Sheet Plus 格式），默认: csv"
    )
    args = parser.parse_args()
    
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    
    # 收集所有 lakebook 文件
    lakebook_files = []
    for item in args.lakebook:
        if os.path.isfile(item):
            if item.endswith('.lakebook'):
                lakebook_files.append(item)
            else:
                print(f"跳过非 lakebook 文件: {item}")
        elif os.path.isdir(item):
            # 如果是目录，查找其中的 .lakebook 文件
            for root, dirs, files in os.walk(item):
                for f in files:
                    if f.endswith('.lakebook'):
                        lakebook_files.append(os.path.join(root, f))
        else:
            print(f"警告: 文件或目录不存在: {item}")
    
    if not lakebook_files:
        print("错误: 未找到任何 .lakebook 文件")
        sys.exit(1)
    
    print(f"找到 {len(lakebook_files)} 个 lakebook 文件")
    
    # 处理每个文件
    success_count = 0
    for lakebook_file in lakebook_files:
        if process_single_lakebook(lakebook_file, args.output, args.download_image, args.convert_sheets, args.sheet_format):
            success_count += 1
    
    print(f"\n转换完成！成功处理 {success_count}/{len(lakebook_files)} 个文件")


if __name__ == "__main__":
    main()

