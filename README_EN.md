# Yuque Lakebook Converter

A tool for converting Yuque exported `.lakebook` files to Markdown format, **designed specifically for migrating from Yuque to Obsidian**.

Based on [yuque2markdown](https://github.com/alswl/yuque2markdown) with improvements, added table document conversion functionality that supports converting to Obsidian Sheet Plus plugin format, allowing you to seamlessly edit tables in Obsidian.

[中文](README.md) | English

## Features

1. **Convert Documents to Markdown**: Convert Yuque regular documents to Markdown format, ready to use in Obsidian
2. **Convert Tables to Sheet Plus Format**: Convert Yuque table documents to Obsidian Sheet Plus plugin format (**requires Sheet Plus plugin installation**), supports direct table editing in Obsidian
3. **Convert Tables to CSV**: Alternative option, convert table documents to CSV format (no plugin dependency)
4. **Preserve Directory Structure**: Output folder structure matches Yuque knowledge base structure for easy migration
5. **Image Download**: Optional download of document images to local storage, ensuring proper display in Obsidian
6. **Multi-file Support**: Process multiple lakebook files at once for batch migration
7. **Organize by Knowledge Base**: Each knowledge base creates an independent subdirectory for easy management

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Export Lakebook Files

1. Log in to Yuque and enter your knowledge base
2. Click the "Settings" button in the top right corner
3. Click the "Export" button
4. Download the `.lakebook` file

### 2. Convert Documents

#### Convert a Single File

```bash
python lakebook_converter.py /path/to/your/file.lakebook /path/to/output/folder
```

#### Convert Multiple Files

```bash
python lakebook_converter.py file1.lakebook file2.lakebook file3.lakebook /path/to/output/folder
```

#### Convert All Lakebook Files in a Directory

```bash
python lakebook_converter.py /path/to/lakebook/directory /path/to/output/folder
```

#### Convert Tables to CSV (Default)

```bash
python lakebook_converter.py /path/to/your/file.lakebook /path/to/output/folder --convert-sheets
# Or explicitly specify format
python lakebook_converter.py /path/to/your/file.lakebook /path/to/output/folder --convert-sheets --sheet-format csv
```

#### Convert Tables to Obsidian Sheet Plus Format (Recommended for Obsidian)

**Note: This format requires installing the [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) plugin in Obsidian to properly display and edit tables.**

```bash
python lakebook_converter.py /path/to/your/file.lakebook /path/to/output/folder --convert-sheets --sheet-format sheet
```

#### Download Images to Local

```bash
python lakebook_converter.py /path/to/your/file.lakebook /path/to/output/folder --download-image
```

#### Complete Examples

```bash
# Convert multiple files, including tables to CSV, and download images
python lakebook_converter.py book1.lakebook book2.lakebook output --convert-sheets --download-image

# Convert all files in a directory
python lakebook_converter.py ./lakebooks output --convert-sheets --download-image
```

## Parameters

- `lakebook`: Lakebook file path or directory (required, supports multiple files or directories)
- `output`: Output directory (required)
- `--convert-sheets`: Convert table documents to CSV or Sheet Plus format (by default only converts regular documents to Markdown)
- `--sheet-format {csv,sheet}`: Table output format, options: `csv` (CSV file) or `sheet` (Obsidian Sheet Plus format), default: `csv`
- `--download-image`: Download images to local (images will be saved in `attachments` folder)

## Features

- **Multi-file Support**: Process multiple lakebook files at once
- **Directory Scanning**: Specify a directory to automatically find all .lakebook files within it
- **Organize by Knowledge Base**: Each knowledge base creates an independent subdirectory to avoid file confusion
- **Auto-detect Knowledge Base Name**: Extract knowledge base name from lakebook file as directory name

## Output Structure

Converted files are organized by knowledge base (book), with each knowledge base in its own folder:

```
output/
├── KnowledgeBase1/
│   ├── DocumentTitle1.md
│   ├── DocumentTitle2.md
│   ├── Subdirectory/
│   │   ├── SubDocument1.md
│   │   └── TableDocument.csv
│   └── attachments/  (if using --download-image)
│       ├── DocumentTitle1_001.jpg
│       └── DocumentTitle1_002.png
├── KnowledgeBase2/
│   ├── DocumentTitle1.md
│   └── ...
└── KnowledgeBase3/
    └── ...
```

## How It Works

1. **Extract Lakebook**: Lakebook file is a tar archive containing JSON files for all documents
2. **Parse Directory Structure**: Read directory structure (TOC) from `$meta.json`
3. **Convert Documents**:
   - **Regular Documents (Doc)**: Convert from HTML to Markdown
   - **Table Documents (Sheet)**: Parse compressed table data, convert to CSV or Obsidian Sheet Plus format

## Table Data Format

Yuque tables use `lakesheet` format with zlib compression. The tool automatically:
1. Decompresses zlib compressed data
2. Parses JSON format table structure
3. Extracts cell data
4. Converts according to selected format

### CSV Format

Converts to standard CSV files that can be opened with Excel, Numbers, and other tools.

### Obsidian Sheet Plus Format (Recommended for Obsidian Migration)

**⚠️ Important: This format depends on the [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) plugin. If you plan to migrate documents to Obsidian, it's recommended to use this format as it allows direct table editing in Obsidian with Excel-like functionality.**

Converts to Obsidian Sheet Plus plugin format, allowing direct table editing in Obsidian with Excel-like functionality.

**Format Features:**
- Complete table data structure, including styles, cell types, etc.
- Supports different data types: numbers, text, dates, etc.
- Automatically identifies headers and applies styles
- Can be directly edited and manipulated in Obsidian
- **Automatic Date Conversion**: Automatically converts Excel date serial numbers to readable date format

**Format Structure:**
- Frontmatter: `excel-pro-plugin: parsed`
- Sheet code block: Contains complete table JSON data (including styles, cell data, etc.)
- MultiSheet code block: Table tab configuration

**Example Format:**
```markdown
---

excel-pro-plugin: parsed

---
```sheet
{"id":"...","sheetOrder":["..."],"name":"WorkLog_2026.md","appVersion":"0.15.0","locale":"enUS","styles":{...},"sheets":{...},"resources":[...]}
```

```multiSheet
{"tabs":[{"key":"sheet","type":"sheet","label":"Sheet"}],"defaultActiveKey":"sheet"}
```

**Usage Instructions (Migration to Obsidian):**
1. **Install Plugin**: Install the [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) plugin in Obsidian
2. **Convert Tables**: Use `--sheet-format sheet` parameter to convert table documents
3. **Import to Obsidian**: Copy the converted `.md` files to your Obsidian vault
4. **Open and Edit**: Open the file in Obsidian, tables will render automatically and can be edited directly

## Notes

- **Obsidian Sheet Plus Plugin**: If using `--sheet-format sheet` format, you must install the Sheet Plus plugin in Obsidian to properly display and edit tables
- Ensure sufficient disk space for output files
- Conversion may take some time if there are many documents
- Table conversion skips completely blank rows
- Image download requires network connection
- Converted Markdown files do not include title lines (titles are reflected in filenames)

## Troubleshooting

### Issue: Table Conversion Failed

- Check if the table document has data
- Some special format tables may not be parsed correctly

### Issue: Image Download Failed

- Check network connection
- Some image links may have expired

### Issue: Dependency Installation Failed

- Ensure Python 3.7+ is used
- Try using `pip3` instead of `pip`

## References

- [yuque2markdown](https://github.com/alswl/yuque2markdown) - Original tool
- [Yuque Open Platform Documentation](https://www.yuque.com/yuque/developer/lt69uo)
- [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) - Obsidian table plugin
