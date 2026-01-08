# 语雀 Lakebook 转换工具

[中文](README.md) | [English](README_EN.md)

将语雀导出的 `.lakebook` 文件转换为 Markdown，**专为迁移到 Obsidian 设计**。

## 功能

- 普通文档 → Markdown
- 表格文档 → Obsidian Sheet Plus 格式（需安装[插件](https://github.com/ljcoder2015/obsidian-sheet-plus)）或 CSV
- 保持目录结构，支持批量处理，可选下载图片

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### 1. 导出 Lakebook

1. 登录语雀，进入知识库
2. 左侧栏 > books > book，点击右侧 "..." → "设置" → 弹出框继续点击 "设置"
3. 底部 book setting 点击 "导出"
4. 下载 `.lakebook` 文件

### 2. 转换

```bash
# 基本用法
python lakebook_converter.py file.lakebook output/

# 转换表格（Sheet Plus 格式，推荐用于 Obsidian）
python lakebook_converter.py file.lakebook output/ --convert-sheets --sheet-format sheet

# 批量转换并下载图片
python lakebook_converter.py *.lakebook output/ --convert-sheets --sheet-format sheet --download-image
```

## 参数

- `lakebook`: 文件或目录路径（支持多个）
- `output`: 输出目录
- `--convert-sheets`: 转换表格文档
- `--sheet-format {csv,sheet}`: 表格格式，默认 `csv`，`sheet` 需安装 Obsidian Sheet Plus 插件
- `--download-image`: 下载图片到本地

## 输出结构

```
output/
├── 知识库1/
│   ├── 文档1.md
│   ├── 表格.md (Sheet Plus 格式)
│   └── attachments/ (图片)
└── 知识库2/
    └── ...
```

## 表格格式

### Sheet Plus 格式（推荐）

**需安装 [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) 插件**

- 支持在 Obsidian 中直接编辑，类似 Excel
- 自动转换日期格式
- 保留样式和数据类型

### CSV 格式

标准 CSV 文件，可用 Excel 等工具打开。

## 注意事项

- Sheet Plus 格式需在 Obsidian 中安装对应插件
- 转换后的 Markdown 不包含标题行（标题在文件名中）
- 图片下载需要网络连接
- 转换后的 Markdown 文件不包含标题行（标题已体现在文件名中）
- 确保使用 Python 3.7+
- 尝试使用 `pip3` 而不是 `pip`

## 参考

- [yuque2markdown](https://github.com/alswl/yuque2markdown) - 原始工具
- [语雀开放平台文档](https://www.yuque.com/yuque/developer/lt69uo)
- [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) - Obsidian 表格插件
