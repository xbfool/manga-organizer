# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

漫画收藏标准化整理工具 - 自动化整理、转换和标准化漫画文件的Python项目。

### 核心功能
- 扫描和分类漫画文件（日漫、美漫、港漫、连环画）
- 真实格式转换（RAR/CBR/ZIP → CBZ）
- 智能提取元数据（系列名、卷号、作者）
- 标准化文件命名和目录结构
- 非破坏性整理（保留原文件，创建新目录）

### 文件规模
- 约 60,656 个漫画文件
- 多种格式：.zip、.rar、.cbz、.cbr、.pdf、.7z
- 总存储空间：Z:\漫画（约 11.7 TB 可用）

## Python环境配置

### Conda环境
- **环境名称**: `manga`
- **Python版本**: 3.12.12
- **Conda路径**: `C:\Users\xbfoo\miniconda3`
- **环境路径**: `C:\Users\xbfoo\miniconda3\envs\manga`

### 依赖包
```bash
pip install rarfile
```

### 激活环境
```bash
# 命令行方式
"C:\Users\xbfoo\miniconda3\Scripts\activate.bat" manga

# 或使用便捷脚本（推荐）
run_test.bat          # 运行环境测试
run_organizer.bat     # 运行整理工具
```

## UnRAR工具配置

### 路径配置
- **安装位置**: `C:\Program Files\UnRAR\`
- **可执行文件**: `C:\Program Files\UnRAR\UnRAR.exe`

### 代码中的配置
所有脚本中已硬编码UnRAR路径：
```python
import rarfile
rarfile.UNRAR_TOOL = r"C:\Program Files\UnRAR\UnRAR.exe"
```

### 注意事项
- UnRAR用于处理 .rar 和 .cbr 格式文件
- 需要真实解压和重新压缩，不是简单重命名
- 确保 `UnRAR.exe` 存在于配置路径

## 项目结构

```
Z:\漫画\
├── manga_organizer.py          # 主整理脚本
├── test_environment.py         # 环境测试脚本
├── requirements.txt            # Python依赖清单
├── config.json                 # 配置文件
├── README_整理工具.md          # 详细使用说明
├── setup_environment.bat       # 环境配置脚本
├── run_test.bat               # 测试脚本
├── run_organizer.bat          # 运行脚本
├── CLAUDE.md                  # 本文件
│
├── 日漫/                      # 原始文件（多个子目录）
├── 美漫/
├── 港漫/
├── 连环画/
│
└── 漫画-已整理/                # 输出目录（整理后）
    ├── 日漫/
    │   ├── 中文版/
    │   │   └── [漫画家]/[作品]/
    │   ├── 日文版/
    │   └── 双语版/
    ├── 美漫/
    │   ├── 漫威/
    │   ├── DC/
    │   └── 其他/
    ├── 港漫/
    └── 连环画/
```

## 常用命令

### 环境管理
```bash
# 创建环境
"C:\Users\xbfoo\miniconda3\Scripts\conda.exe" create -n manga python=3.12 -y

# 激活环境
"C:\Users\xbfoo\miniconda3\Scripts\activate.bat" manga

# 安装依赖
pip install rarfile

# 测试环境
python test_environment.py
```

### 运行整理工具
```bash
# 方式1: 使用批处理脚本（推荐）
run_organizer.bat

# 方式2: 直接运行Python
"C:\Users\xbfoo\miniconda3\envs\manga\python.exe" manga_organizer.py
```

### 开发和测试
```bash
# 运行环境检查
python test_environment.py

# 预演模式（不实际修改文件）
python manga_organizer.py
# 然后选择 'd' (dry-run)

# 小批量测试
# 修改脚本中的 batch_size 参数或先测试单个子目录
```

## 核心架构

### MangaOrganizer 类
主要的整理器类，负责：
- 文件扫描和分析
- 格式转换
- 目录重组
- 报告生成

### MangaFile 数据类
存储单个漫画文件的元数据：
- original_path: 原始路径
- file_type: 文件类型（zip/rar/cbz/cbr）
- category: 分类（日漫/美漫/港漫/连环画）
- language: 语言版本（中文版/日文版/双语版）
- series_name: 系列名
- volume: 卷号
- author: 作者
- target_path: 目标路径

### 分类逻辑

#### 自动分类关键词
```python
CATEGORY_KEYWORDS = {
    '日漫': ['日漫', '日本', 'japanese', 'manga', 'jp'],
    '美漫': ['美漫', '美国', 'american', 'comics', 'marvel', 'dc'],
    '港漫': ['港漫', '香港', 'hongkong', 'hk'],
    '连环画': ['连环画', '小人书']
}

LANGUAGE_KEYWORDS = {
    '中文版': ['中文', '中译', '汉化', 'chinese', 'cn'],
    '日文版': ['日文', '日语', '原版', 'japanese', 'jp', 'raw'],
    '双语版': ['双语', '中日', '合版', 'bilingual']
}
```

#### 目录结构规则
- **日漫**: 语言版本 → 漫画家 → 作品系列
- **美漫**: 出版商（漫威/DC/其他）→ 系列
- **港漫**: 系列名
- **连环画**: 分类 → 作品名

### 命名规范

标准文件名格式：`作品名 - 卷号.cbz`

示例：
- `灌篮高手 - 001.cbz`
- `Action Comics - 001.cbz`
- `神兵玄奇 - 01.cbz`

卷号提取模式：
```python
patterns = [
    r'(.+?)[_\s-]+[Vv]ol[._\s]*(\d+)',      # Vol_01
    r'(.+?)[_\s-]+第?(\d+)[卷集话]',         # 第01卷
    r'(.+?)[_\s-]+(\d{2,3})',                # 系列名-001
    r'(.+?)[_\s]+(\d+)',                     # 系列名 01
]
```

## 格式转换

### 真实转换（非重命名）
```python
# RAR/CBR → CBZ
1. 解压RAR文件到临时目录
2. 遍历所有文件
3. 重新打包为ZIP（CBZ）
4. 清理临时文件
```

### 支持的格式
- `.zip` → `.cbz`（重命名）
- `.rar` → `.cbz`（真实转换）
- `.cbr` → `.cbz`（真实转换）
- `.cbz` → 保持原样
- `.pdf` → 保持原样

## 处理流程

### 完整流程
1. **扫描阶段**: 遍历所有子目录，收集文件信息
2. **分析阶段**: 提取元数据，生成 `manga_analysis.json`
3. **转换阶段**: 按需转换格式（RAR/CBR → CBZ）
4. **重组阶段**: 复制到新目录结构
5. **标记阶段**: 原目录重命名为 `[已处理]原目录名`
6. **报告阶段**: 生成 `manga_final_report.json`

### 安全特性
- ✅ 原文件不被删除或修改
- ✅ 预演模式（dry-run）可测试效果
- ✅ 详细日志记录所有操作
- ✅ 错误不会中断整个流程
- ✅ 可以随时中断（Ctrl+C）

## 输出文件

### 日志文件
- `manga_organizer.log` - 详细执行日志（UTF-8编码）

### 报告文件
- `manga_analysis.json` - 扫描分析报告
  - 文件列表
  - 分类统计
  - 识别的元数据

- `manga_final_report.json` - 最终整理报告
  - 处理统计
  - 转换记录
  - 错误列表
  - 每个文件的处理状态

### 报告结构
```json
{
  "timestamp": "2025-01-17T...",
  "stats": {
    "total_files": 60656,
    "processed": 12345,
    "converted": 5678,
    "errors": 10,
    "skipped": 100
  },
  "files": [
    {
      "original_path": "...",
      "target_path": "...",
      "processed": true,
      "error": null
    }
  ]
}
```

## 性能优化

### 批处理
- 默认每 100 个文件输出一次进度
- 可调整 `batch_size` 参数

### 临时文件管理
- 转换过程使用 `.temp_conversion/` 目录
- 每个文件转换后立即清理临时文件

### 内存优化
- 流式处理文件列表
- 不一次性加载所有文件内容

## 故障排除

### 常见问题

**编码问题（Windows）**
```python
# 脚本已自动处理UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

**RAR文件处理失败**
- 检查UnRAR路径是否正确
- 检查文件是否损坏
- 查看日志文件获取详细错误

**内存不足**
- 减小 batch_size
- 分批处理不同分类
- 先处理较小的文件

**文件名乱码**
- 检查原文件编码
- 可能需要手动重命名原文件

## Windows特定配置

### 路径处理
- 使用 `pathlib.Path` 处理路径
- 字符串路径使用原始字符串（r-string）

### 编码设置
- 所有文件操作使用 UTF-8 编码
- 日志文件使用 UTF-8 编码
- 输出重定向到 UTF-8

### 批处理脚本
- 所有 .bat 文件使用 `chcp 65001` 设置UTF-8
- 使用 `call` 命令激活Conda环境

## 扩展和定制

### 添加新的分类关键词
修改 `manga_organizer.py` 中的字典：
```python
CATEGORY_KEYWORDS = {
    '日漫': [..., '新关键词'],
}
```

### 修改命名格式
在 `generate_target_path()` 方法中调整：
```python
file_name = f"{series_name} - {volume}.cbz"
```

### 添加网络元数据查询
可扩展添加：
- API调用获取漫画信息
- 自动补充缺失的作者/系列信息
- 封面下载

## 注意事项

1. **大规模处理**: 60,000+ 文件需要数小时，建议分批处理
2. **磁盘空间**: 整理过程会复制文件，确保有足够空间
3. **格式转换**: RAR→CBZ 耗时较长，建议先预演评估
4. **原文件安全**: 原文件被标记但不删除，可随时恢复
5. **日志重要性**: 出现问题时查看日志文件

## 未来改进方向

- [ ] 添加GUI界面
- [ ] 实现网络元数据查询（豆瓣、MyAnimeList等）
- [ ] 支持增量更新（只处理新文件）
- [ ] 添加重复文件检测
- [ ] 支持封面提取和显示
- [ ] 多线程并行处理
- [ ] 生成HTML预览报告
