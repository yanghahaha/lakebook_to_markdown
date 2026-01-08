# Yuque Lakebook Converter

[中文](README.md) | [English](README_EN.md)

Convert Yuque exported `.lakebook` files to Markdown, **designed for migrating to Obsidian**.

## Features

- Documents → Markdown
- Tables → Obsidian Sheet Plus format (requires [plugin](https://github.com/ljcoder2015/obsidian-sheet-plus)) or CSV
- Preserves directory structure, batch processing, optional image download

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Export Lakebook

1. Log in to Yuque and enter your knowledge base
2. Left sidebar > books > book, click "..." on the right → "Settings" → click "Settings" again in popup
3. At bottom of book settings, click "Export"
4. Download `.lakebook` file

### 2. Convert

```bash
# Basic usage
python lakebook_converter.py file.lakebook output/

# Convert tables (Sheet Plus format, recommended for Obsidian)
python lakebook_converter.py file.lakebook output/ --convert-sheets --sheet-format sheet

# Batch convert with image download
python lakebook_converter.py *.lakebook output/ --convert-sheets --sheet-format sheet --download-image
```

## Parameters

- `lakebook`: File or directory path (supports multiple)
- `output`: Output directory
- `--convert-sheets`: Convert table documents
- `--sheet-format {csv,sheet}`: Table format, default `csv`, `sheet` requires Obsidian Sheet Plus plugin
- `--download-image`: Download images locally

## Output Structure

```
output/
├── KnowledgeBase1/
│   ├── Document1.md
│   ├── Table.md (Sheet Plus format)
│   └── attachments/ (images)
└── KnowledgeBase2/
    └── ...
```

## Table Formats

### Sheet Plus Format (Recommended)

**Requires [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) plugin**

- Direct editing in Obsidian with Excel-like functionality
- Automatic date format conversion
- Preserves styles and data types

### CSV Format

Standard CSV files, openable with Excel and other tools.

## Notes

- Sheet Plus format requires installing the corresponding plugin in Obsidian
- Converted Markdown files don't include title lines (titles are in filenames)
- Image download requires network connection
- Converted Markdown files do not include title lines (titles are reflected in filenames)
- Ensure Python 3.7+ is used
- Try using `pip3` instead of `pip`

## References

- [yuque2markdown](https://github.com/alswl/yuque2markdown) - Original tool
- [Yuque Open Platform Documentation](https://www.yuque.com/yuque/developer/lt69uo)
- [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) - Obsidian table plugin
