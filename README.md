# 语雀 Lakebook 转换工具

[中文](README.md) | [English](README_EN.md)

这是一个用于将语雀导出的 `.lakebook` 文件转换为 Markdown 格式的工具，**主要为从语雀迁移到 Obsidian 而设计**。

基于 [yuque2markdown](https://github.com/alswl/yuque2markdown) 改进，增加了表格文档转换功能，支持转换为 Obsidian Sheet Plus 插件格式，让你可以在 Obsidian 中无缝编辑表格。

## 功能特性

1. **普通文档转 Markdown**: 将语雀普通文档转换为 Markdown 格式，可直接在 Obsidian 中使用
2. **表格文档转 Sheet Plus 格式**: 将语雀表格文档转换为 Obsidian Sheet Plus 插件格式（**需要安装 Sheet Plus 插件**），支持在 Obsidian 中直接编辑表格
3. **表格文档转 CSV**: 备选方案，将表格文档转换为 CSV 格式（不依赖插件）
4. **保持目录结构**: 输出文件夹结构与语雀知识库结构相同，方便迁移
5. **图片下载**: 可选下载文档中的图片到本地，确保在 Obsidian 中正常显示
6. **多文件支持**: 支持一次处理多个 lakebook 文件，批量迁移
7. **按知识库分目录**: 每个知识库创建独立的子目录，便于管理

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 导出 Lakebook 文件

1. 登录语雀，进入你的知识库
2. 点击右上角的"设置"按钮
3. 点击"导出"按钮
4. 下载 `.lakebook` 文件

### 2. 转换文档

#### 转换单个文件

```bash
python lakebook_converter.py /path/to/your/file.lakebook /path/to/output/folder
```

#### 转换多个文件

```bash
python lakebook_converter.py file1.lakebook file2.lakebook file3.lakebook /path/to/output/folder
```

#### 转换目录中的所有 lakebook 文件

```bash
python lakebook_converter.py /path/to/lakebook/directory /path/to/output/folder
```

#### 转换表格为 CSV（默认）

```bash
python lakebook_converter.py /path/to/your/file.lakebook /path/to/output/folder --convert-sheets
# 或显式指定格式
python lakebook_converter.py /path/to/your/file.lakebook /path/to/output/folder --convert-sheets --sheet-format csv
```

#### 转换表格为 Obsidian Sheet Plus 格式（推荐用于 Obsidian）

**注意：此格式需要在 Obsidian 中安装 [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) 插件才能正常显示和编辑表格。**

```bash
python lakebook_converter.py /path/to/your/file.lakebook /path/to/output/folder --convert-sheets --sheet-format sheet
```

#### 下载图片到本地

```bash
python lakebook_converter.py /path/to/your/file.lakebook /path/to/output/folder --download-image
```

#### 完整示例

```bash
# 转换多个文件，包括表格转 CSV，并下载图片
python lakebook_converter.py book1.lakebook book2.lakebook output --convert-sheets --download-image

# 转换目录中的所有文件
python lakebook_converter.py ./lakebooks output --convert-sheets --download-image
```

## 参数说明

- `lakebook`: Lakebook 文件路径或目录（必需，支持多个文件或目录）
- `output`: 输出目录（必需）
- `--convert-sheets`: 将表格文档转换为 CSV 或 Sheet Plus 格式（默认只转换普通文档为 Markdown）
- `--sheet-format {csv,sheet}`: 表格输出格式，可选 `csv`（CSV 文件）或 `sheet`（Obsidian Sheet Plus 格式），默认: `csv`
- `--download-image`: 下载图片到本地（图片会保存在 `attachments` 文件夹中）

## 特性

- **多文件支持**: 可以一次处理多个 lakebook 文件
- **目录扫描**: 可以指定目录，自动查找其中的所有 .lakebook 文件
- **按知识库分目录**: 每个知识库会创建独立的子目录，避免文件混乱
- **自动识别知识库名称**: 从 lakebook 文件中提取知识库名称作为目录名

## 输出结构

转换后的文件会按知识库（book）分目录，每个知识库一个文件夹：

```
output/
├── 知识库1名称/
│   ├── 文档标题1.md
│   ├── 文档标题2.md
│   ├── 子目录/
│   │   ├── 子文档1.md
│   │   └── 表格文档.csv
│   └── attachments/  (如果使用 --download-image)
│       ├── 文档标题1_001.jpg
│       └── 文档标题1_002.png
├── 知识库2名称/
│   ├── 文档标题1.md
│   └── ...
└── 知识库3名称/
    └── ...
```

## 工作原理

1. **解压 Lakebook**: Lakebook 文件是一个 tar 压缩包，包含所有文档的 JSON 文件
2. **解析目录结构**: 从 `$meta.json` 中读取目录结构（TOC）
3. **转换文档**:
   - **普通文档 (Doc)**: 从 HTML 转换为 Markdown
   - **表格文档 (Sheet)**: 解析压缩的表格数据，转换为 CSV 或 Obsidian Sheet Plus 格式

## 表格数据格式

语雀表格使用 `lakesheet` 格式，数据经过 zlib 压缩。工具会自动：
1. 解压 zlib 压缩的数据
2. 解析 JSON 格式的表格结构
3. 提取单元格数据
4. 根据选择的格式进行转换

### CSV 格式

转换为标准的 CSV 文件，可以用 Excel、Numbers 等工具打开。

### Obsidian Sheet Plus 格式（推荐用于 Obsidian 迁移）

**⚠️ 重要提示：此格式依赖 [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) 插件。如果你计划将文档迁移到 Obsidian，建议使用此格式，因为它可以在 Obsidian 中直接编辑表格，支持类似 Excel 的功能。**

转换为 Obsidian Sheet Plus 插件格式，可以在 Obsidian 中直接编辑表格，支持类似 Excel 的功能。

**格式特点：**
- 完整的表格数据结构，包括样式、单元格类型等
- 支持数字、文本、日期等不同数据类型
- 自动识别表头并应用样式
- 可以在 Obsidian 中直接编辑和操作
- **日期自动转换**：自动将 Excel 日期序列号转换为可读的日期格式

**格式结构：**
- Frontmatter: `excel-pro-plugin: parsed`
- Sheet 代码块: 包含完整的表格 JSON 数据（包括样式、单元格数据等）
- MultiSheet 代码块: 表格标签配置

**示例格式：**
```markdown
---

excel-pro-plugin: parsed

---
```sheet
{"id":"...","sheetOrder":["..."],"name":"工作流水账_2026.md","appVersion":"0.15.0","locale":"enUS","styles":{...},"sheets":{...},"resources":[...]}
```

```multiSheet
{"tabs":[{"key":"sheet","type":"sheet","label":"Sheet"}],"defaultActiveKey":"sheet"}
```
```

**使用说明（迁移到 Obsidian）：**
1. **安装插件**：在 Obsidian 中安装 [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) 插件
2. **转换表格**：使用 `--sheet-format sheet` 参数转换表格文档
3. **导入 Obsidian**：将转换后的 `.md` 文件复制到你的 Obsidian 库中
4. **打开编辑**：在 Obsidian 中打开文件，表格会自动渲染，可以直接编辑

## 注意事项

- **Obsidian Sheet Plus 插件**：如果使用 `--sheet-format sheet` 格式，必须在 Obsidian 中安装 Sheet Plus 插件才能正常显示和编辑表格
- 确保有足够的磁盘空间存储输出文件
- 如果文档很多，转换可能需要一些时间
- 表格转换会跳过完全空白的行
- 图片下载需要网络连接
- 转换后的 Markdown 文件不包含标题行（标题已体现在文件名中）

## 故障排除

### 问题: 表格转换失败

- 检查表格文档是否有数据
- 某些特殊格式的表格可能无法正确解析

### 问题: 图片下载失败

- 检查网络连接
- 某些图片链接可能已失效

### 问题: 依赖安装失败

- 确保使用 Python 3.7+
- 尝试使用 `pip3` 而不是 `pip`

## 参考

- [yuque2markdown](https://github.com/alswl/yuque2markdown) - 原始工具
- [语雀开放平台文档](https://www.yuque.com/yuque/developer/lt69uo)
- [Obsidian Sheet Plus](https://github.com/ljcoder2015/obsidian-sheet-plus) - Obsidian 表格插件

