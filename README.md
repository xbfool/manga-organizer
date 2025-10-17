# 漫画收藏标准化整理工具

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

自动化整理、转换和标准化漫画文件的Python工具，支持日漫、美漫、港漫和连环画。

## ✨ 功能特性

- 🔍 **智能扫描和分类** - 自动识别漫画类型（日漫、美漫、港漫、连环画）
- 🔄 **真实格式转换** - RAR/CBR → CBZ（真实解压重压缩，非简单重命名）
- 📚 **元数据提取** - 智能识别系列名、卷号、作者、语言版本
- 📁 **标准化目录结构** - 按照规范的分类规则重组文件
- 🏷️ **规范文件命名** - 统一格式：`作品名 - 卷号.cbz`
- 🌐 **多源元数据查询** - 支持Bangumi、trace.moe、AniList、ComicVine等API
- 📦 **Komga准备工具** - 本地获取元数据，生成ComicInfo.xml，整理为Komga就绪目录
- 🏷️ **ComicInfo.xml生成** - 符合Anansi Project v2.0标准，完美兼容Komga
- 🖼️ **封面管理** - 自动下载系列封面，提取CBZ内封面
- 💾 **非破坏性整理** - 保留原文件，创建新目录
- 📊 **详细报告** - 生成JSON格式的分析和处理报告
- 🔒 **安全可靠** - 预演模式、详细日志、可随时中断

## 📋 目录

- [快速开始](#快速开始)
- [安装](#安装)
- [使用方法](#使用方法)
- [Komga准备工具](#komga准备工具)
- [目录结构](#目录结构)
- [命名规范](#命名规范)
- [元数据查询](#元数据查询)
- [配置](#配置)
- [常见问题](#常见问题)
- [贡献](#贡献)
- [许可证](#许可证)

## 🚀 快速开始

### 前置要求

- Python 3.12+
- [Conda](https://docs.conda.io/en/latest/miniconda.html) 或 Python 环境管理工具
- [UnRAR](https://www.rarlab.com/rar_add.htm) 工具（处理RAR/CBR文件必需）

### Windows 快速安装

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/manga-organizer.git
cd manga-organizer
```

2. **运行环境配置脚本**
```bash
scripts\setup_environment.bat
```

3. **测试环境**
```bash
scripts\run_test.bat
```

4. **开始整理**
```bash
scripts\run_organizer.bat
```

## 📦 安装

### 方法1：使用Conda（推荐）

```bash
# 创建虚拟环境
conda create -n manga python=3.12 -y

# 激活环境
conda activate manga

# 安装依赖
pip install -r requirements.txt
```

### 方法2：使用pip

```bash
# 创建虚拟环境
python -m venv venv

# 激活环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 安装UnRAR（必需）

#### Windows
1. 下载：https://www.rarlab.com/rar_add.htm
2. 解压到固定位置（如 `C:\Program Files\UnRAR\`）
3. 脚本已配置路径为 `C:\Program Files\UnRAR\UnRAR.exe`

#### Linux
```bash
sudo apt-get install unrar
```

#### macOS
```bash
brew install unrar
```

## 🎯 使用方法

### 基本用法

1. **将工具放在漫画收藏根目录**

2. **运行主脚本**
```bash
python src/manga_organizer.py
```

3. **选择模式**
   - `y` - 开始整理（实际执行）
   - `d` - 预演模式（仅显示效果，不修改文件）
   - `n` - 取消

### 命令行用法

```bash
# 环境测试
python src/test_environment.py

# 元数据查询测试
python src/metadata_fetcher.py

# 主程序（交互模式）
python src/manga_organizer.py
```

### 使用批处理脚本（Windows）

```bash
# 环境配置
scripts\setup_environment.bat

# 环境测试
scripts\run_test.bat

# 运行整理
scripts\run_organizer.bat
```

## 📦 Komga准备工具

### 概述

Komga准备工具专为拥有**远程Komga服务器**的用户设计。它在本地完成所有元数据获取和目录整理工作，输出一个**Komga就绪的目录**，可以直接复制到远程服务器。

#### 适用场景

- ✅ 你有一个远程Komga服务器（NAS、VPS等）
- ✅ 本地机器网络条件更好，适合查询元数据
- ✅ 希望本地准备好一切，再整体传输到服务器
- ✅ 需要ComicInfo.xml元数据嵌入每个CBZ文件

#### 工作流程

```
本地准备 → 整体传输 → Komga自动识别
```

1. **本地准备阶段**（本工具）
   - 扫描现有漫画收藏
   - 从多个API源获取元数据（中文优先）
   - 生成ComicInfo.xml并嵌入CBZ文件
   - 下载系列封面
   - 整理为Komga标准目录结构

2. **传输阶段**（用户操作）
   - 使用rsync/robocopy/scp等工具
   - 将整个输出目录复制到Komga服务器

3. **Komga识别阶段**（自动）
   - Komga读取ComicInfo.xml
   - 自动显示中文标题、作者、简介等
   - 无需在服务器上配置元数据插件

### 元数据源

工具支持多个API源，按优先级自动聚合元数据：

| 数据源 | 类型 | 语言 | 需要API Key | 优先级 |
|--------|------|------|-------------|--------|
| **Bangumi** | 日漫/动画 | 中文原生 | ❌ 否 | 1 |
| **trace.moe** | AniList代理 | 中文翻译 | ❌ 否 | 2 |
| **AniList** | 日漫/轻小说 | 日/英 | ❌ 否 | 3 |
| **ComicVine** | 美漫 | 英文 | ⚠️ 需要（免费） | 4 |

#### 语言优先级

工具会按以下顺序选择标题和简介：

```
中文 > 日文 > 罗马音 > 英文
```

例如：
- Bangumi提供中文标题："灌篮高手"
- AniList提供日文标题："スラムダンク"
- 最终选用："灌篮高手"（中文优先）

### 配置

编辑 `config.json` 中的 `komga_prepare` 部分：

```json
{
  "komga_prepare": {
    "source_dirs": [
      "Z:/漫画/日漫",
      "Z:/漫画/美漫",
      "Z:/漫画/港漫"
    ],
    "output_dir": "Z:/漫画-Komga就绪",

    "language_priority": ["zh", "ja", "romaji", "en"],

    "metadata_sources": {
      "bangumi": {
        "enabled": true,
        "priority": 1
      },
      "trace_moe": {
        "enabled": true,
        "priority": 2
      },
      "anilist": {
        "enabled": true,
        "priority": 3
      },
      "comicvine": {
        "enabled": false,
        "api_key": "",
        "priority": 4
      }
    },

    "cover_download": true,
    "create_series_comicinfo": false
  }
}
```

#### 配置说明

- `source_dirs`: 要处理的源目录列表
- `output_dir`: 输出目录（Komga就绪目录）
- `language_priority`: 语言优先级（zh=中文, ja=日文, romaji=罗马音, en=英文）
- `metadata_sources`: 启用的元数据源
- `cover_download`: 是否下载封面
- `create_series_comicinfo`: 是否创建系列级ComicInfo.xml（通常不需要）

#### ComicVine API Key（可选）

如果需要美漫元数据：

1. 注册账号：https://comicvine.gamespot.com/
2. 获取API Key：https://comicvine.gamespot.com/api/
3. 填入配置文件的 `api_key` 字段
4. 设置 `enabled: true`

### 使用方法

#### 1. 激活环境

```bash
conda activate manga
```

#### 2. 运行准备工具

```bash
python src/komga_prepare.py
```

或使用自定义配置文件：

```bash
python src/komga_prepare.py --config my_config.json
```

#### 3. 查看进度

工具会显示实时进度：

```
==================================================
Komga准备工具
==================================================
扫描目录: Z:\漫画\日漫

找到 156 个系列，共 2341 卷

[1/156] 处理: 灌篮高手
  ✓ 获取元数据: 灌篮高手
    复制: 灌篮高手 v01.cbz
    复制: 灌篮高手 v02.cbz
    ...

[2/156] 处理: 海贼王
  ✓ 获取元数据: ONE PIECE 航海王
    ...
```

#### 4. 检查输出

输出目录结构：

```
Z:/漫画-Komga就绪/
├── 日漫-中文版/
│   ├── 井上雄彦/
│   │   └── 灌篮高手/
│   │       ├── cover.jpg              # 系列封面
│   │       ├── 灌篮高手 v01.cbz        # 内含ComicInfo.xml
│   │       ├── 灌篮高手 v02.cbz
│   │       └── ...
│   └── 尾田荣一郎/
│       └── ONE PIECE 航海王/
│           ├── cover.jpg
│           ├── ONE PIECE 航海王 v01.cbz
│           └── ...
├── 日漫-日文版/
├── 美漫/
├── 港漫/
└── TRANSFER_MANIFEST.txt          # 传输清单
```

每个CBZ文件内部结构：

```
灌篮高手 v01.cbz
├── ComicInfo.xml                  # 元数据文件
├── 001.jpg                        # 漫画页面
├── 002.jpg
└── ...
```

#### 5. 检查ComicInfo.xml

可以解压任一CBZ文件查看：

```bash
unzip -p "灌篮高手 v01.cbz" ComicInfo.xml
```

示例输出：

```xml
<?xml version="1.0" ?>
<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Series>灌篮高手</Series>
  <Number>1</Number>
  <Count>31</Count>
  <Writer>井上雄彦</Writer>
  <Publisher>集英社</Publisher>
  <Year>1990</Year>
  <Summary>描述高中篮球队的热血青春故事...</Summary>
  <Genre>运动, 青春, 励志</Genre>
  <Manga>Yes</Manga>
  <LanguageISO>zh</LanguageISO>
  <Notes>Metadata from Bangumi (ID: 959)</Notes>
</ComicInfo>
```

### 传输到Komga服务器

准备完成后，使用以下方法传输到Komga服务器：

#### 方法1: rsync（推荐，支持增量）

```bash
# Windows → Linux服务器
rsync -avz --progress "Z:/漫画-Komga就绪/" user@server:/data/komga/comics/
```

#### 方法2: robocopy（Windows原生）

```bash
robocopy "Z:\漫画-Komga就绪" "\\server\komga\comics" /E /MT:8
```

#### 方法3: 直接复制到NAS

```bash
# 映射网络驱动器后
xcopy "Z:\漫画-Komga就绪\*" "\\NAS\comics\" /E /H /C /I
```

#### 方法4: scp（单次传输）

```bash
scp -r "Z:/漫画-Komga就绪" user@server:/data/komga/comics/
```

### 传输后操作

1. **触发Komga扫描**
   - 登录Komga Web界面
   - 进入库设置
   - 点击"扫描库文件"

2. **验证元数据**
   - 检查系列标题是否显示为中文
   - 检查作者、简介是否正确
   - 检查封面是否显示

3. **问题排查**
   - 如果元数据未显示，检查Komga设置中"导入ComicInfo"是否启用
   - 如果封面未显示，检查文件权限
   - 查看Komga日志：`/config/logs/`

### ComicInfo.xml标准

工具生成的ComicInfo.xml符合 **Anansi Project v2.0** 标准，包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `Series` | 系列名 | 灌篮高手 |
| `Number` | 卷/期号 | 1 |
| `Count` | 总卷/期数 | 31 |
| `Writer` | 作者 | 井上雄彦 |
| `Penciller` | 画师 | 井上雄彦 |
| `Translator` | 翻译者 | （如有） |
| `Publisher` | 出版社 | 集英社 |
| `Year` | 出版年份 | 1990 |
| `Month` | 出版月份 | 12 |
| `Summary` | 简介 | 描述内容 |
| `Genre` | 类型标签 | 运动, 青春 |
| `Manga` | 是否为漫画 | Yes |
| `LanguageISO` | 语言代码 | zh, ja, en |
| `CommunityRating` | 评分 | 4.5 (0-5分) |
| `Tags` | 额外标签 | 热血, 经典 |
| `Notes` | 备注 | Metadata from Bangumi |

### 统计报告

完成后会生成处理统计：

```
==================================================
处理统计
==================================================
系列总数: 156
已处理系列: 154
卷总数: 2341
已处理卷: 2320
元数据找到: 148
元数据未找到: 6
错误: 2
==================================================
```

### 日志文件

- `komga_prepare.log` - 详细执行日志
- `TRANSFER_MANIFEST.txt` - 传输命令清单（在输出目录）

### 性能建议

- **首次运行**: 建议先测试小批量（10-20个系列）
- **网络**: API查询需要稳定网络连接
- **速度**: 约每秒处理1-2个系列（取决于网络速度）
- **并发**: 目前为串行处理，未来版本将支持并发

### 故障排查

#### 问题: 元数据未找到

**可能原因:**
- 系列名与API数据库不匹配
- 网络连接问题
- API源未启用

**解决方法:**
1. 查看日志了解具体API响应
2. 尝试手动搜索确认是否存在
3. 调整系列名称（重命名父目录）
4. 启用更多元数据源

#### 问题: ComicInfo.xml未生效

**可能原因:**
- Komga未启用ComicInfo导入
- CBZ文件损坏
- XML格式错误

**解决方法:**
1. 检查Komga设置 → 导入 → "导入ComicInfo.xml元数据"
2. 解压CBZ验证XML存在
3. 使用XML验证工具检查格式

#### 问题: 传输速度慢

**解决方法:**
1. 使用 rsync 增量传输（只传新文件）
2. 启用多线程传输（robocopy `/MT:8`）
3. 考虑先传输元数据较小的文件
4. 使用局域网直连（避免WiFi）

## 📂 目录结构

### 输入结构（示例）

```
你的漫画文件夹/
├── 日漫/
│   ├── mokuro/
│   ├── 已整理2025/
│   └── 漫画整理-日漫中文/
│       ├── 名人/
│       │   ├── 井上雄彦/
│       │   └── 尾田荣一郎/
│       └── 非名人/
├── 美漫/
│   ├── New52/
│   ├── Marvel/
│   └── DC/
├── 港漫/
└── 连环画/
```

### 输出结构

```
漫画-已整理/
├── 日漫/
│   ├── 中文版/
│   │   └── [漫画家]/
│   │       └── [作品名]/
│   │           ├── 作品名 - 001.cbz
│   │           ├── 作品名 - 002.cbz
│   │           └── ...
│   ├── 日文版/
│   └── 双语版/
├── 美漫/
│   ├── 漫威/
│   ├── DC/
│   └── 其他/
├── 港漫/
│   └── [系列名]/
└── 连环画/
    └── [分类]/
```

## 🏷️ 命名规范

### 文件命名格式

```
作品名 - 卷号.cbz
```

**示例：**
- `灌篮高手 - 001.cbz`
- `Action Comics - 001.cbz`
- `神兵玄奇 - 01.cbz`

### 卷号格式

- 自动补零到3位（日漫、港漫）
- 保持原格式（美漫通常带期号）

### 支持的文件格式

| 源格式 | 目标格式 | 处理方式 |
|--------|----------|---------|
| `.zip` | `.cbz` | 重命名 |
| `.rar` | `.cbz` | 真实转换 |
| `.cbr` | `.cbz` | 真实转换 |
| `.cbz` | `.cbz` | 保持原样 |
| `.pdf` | `.pdf` | 保持原样 |

## 🌐 元数据查询

### 支持的API源

工具支持多个元数据源，自动聚合信息以提供最完整的中文元数据。

#### Bangumi（番组计划）
- ✅ 免费，无需API key
- ✅ 中文原生数据
- ✅ 日漫、动画、游戏等
- 📡 API: https://api.bgm.tv

```python
from src.metadata_sources import BangumiSource

bangumi = BangumiSource()
metadata = bangumi.search("灌篮高手")
print(f"标题: {metadata.title_zh}")
print(f"作者: {', '.join(metadata.authors)}")
```

#### trace.moe（AniList代理）
- ✅ 免费，无需API key
- ✅ AniList数据 + 中文翻译
- ✅ 提供AniList不支持的中文标题
- 📡 API: https://trace.moe/anilist/

```python
from src.metadata_sources import TraceMoeSource

trace_moe = TraceMoeSource()
metadata = trace_moe.search("SLAM DUNK")
print(f"中文标题: {metadata.title_zh}")  # 灌篮高手
```

#### AniList（日漫/轻小说）
- ✅ 免费，无需API key
- ✅ 50万+ 条目
- ✅ 日文、罗马音、英文支持
- 📡 API: https://graphql.anilist.co

```python
from src.metadata_sources import AniListSource

anilist = AniListSource()
metadata = anilist.search("ONE PIECE")
print(f"日文标题: {metadata.title_native}")
print(f"罗马音: {metadata.title_romaji}")
```

#### ComicVine（美漫）
- ⚠️ 需要免费API key
- ⚠️ 限制：200请求/小时
- ✅ 漫威、DC等美漫完整数据
- 📡 API: https://comicvine.gamespot.com/api

```python
from src.metadata_sources import ComicVineSource

config = {'api_key': 'YOUR_API_KEY'}
comicvine = ComicVineSource(config)
metadata = comicvine.search("Batman")
print(f"出版社: {metadata.publisher}")
```

**获取ComicVine API key：** https://comicvine.gamespot.com/api/

### 使用示例

#### 单个源查询

```bash
# 测试Bangumi
python -c "from src.metadata_sources import BangumiSource; print(BangumiSource().search('海贼王'))"

# 测试trace.moe
python -c "from src.metadata_sources import TraceMoeSource; print(TraceMoeSource().search('火影忍者'))"
```

#### 多源聚合查询（Komga准备工具使用）

```python
from src.metadata_sources import BangumiSource, TraceMoeSource, AniListSource

# 多个源查询并合并
sources = [BangumiSource(), TraceMoeSource(), AniListSource()]

final_metadata = None
for source in sources:
    metadata = source.search("灌篮高手")
    if metadata:
        if final_metadata is None:
            final_metadata = metadata
        else:
            final_metadata.merge(metadata)

# 结果包含所有源的信息
print(final_metadata.get_best_title())  # 中文优先
```

## ⚙️ 配置

### config.json

```json
{
  "paths": {
    "target_directory": "漫画-已整理",
    "temp_directory": ".temp_conversion"
  },
  "formats": {
    "target_format": "cbz"
  },
  "naming": {
    "format": "{series_name} - {volume}",
    "volume_padding": 3
  }
}
```

### 自定义分类关键词

编辑 `src/manga_organizer.py`:

```python
CATEGORY_KEYWORDS = {
    '日漫': ['日漫', '日本', 'japanese', 'manga', 'jp', '你的关键词'],
    '美漫': ['美漫', '美国', 'american', 'comics', 'marvel', 'dc'],
    # ...
}
```

## 📊 输出文件

### 日志文件
- `manga_organizer.log` - 详细执行日志

### 报告文件
- `manga_analysis.json` - 扫描分析报告
- `manga_final_report.json` - 最终处理报告

### 报告结构示例

```json
{
  "timestamp": "2025-01-17T12:00:00",
  "stats": {
    "total_files": 60656,
    "processed": 12345,
    "converted": 5678,
    "errors": 10
  },
  "files": [...]
}
```

## ❓ 常见问题

### Q: 原文件会被删除吗？
**A:** 不会。脚本只复制文件到新目录，原文件保持不变。处理完成后原目录会被重命名为 `[已处理]原目录名`。

### Q: 处理60000+文件需要多长时间？
**A:** 取决于文件大小和是否需要格式转换：
- 纯重命名/移动：约1-2小时
- 包含RAR→CBZ转换：可能需要数小时

### Q: 可以中途停止吗？
**A:** 可以。按 `Ctrl+C` 停止，已处理的文件会保留。

### Q: 如何恢复原状？
**A:** 删除 `漫画-已整理` 目录，将标记为 `[已处理]` 的目录重命名回原名即可。

### Q: RAR文件无法处理
**A:**
1. 确认UnRAR已安装
2. 检查路径配置是否正确
3. 查看日志文件获取详细错误

### Q: 文件名乱码
**A:** Windows下可能需要设置环境变量：
```bash
set PYTHONIOENCODING=utf-8
```

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [AniList](https://anilist.co/) - 提供日漫元数据API
- [ComicVine](https://comicvine.gamespot.com/) - 提供美漫元数据API
- [rarfile](https://github.com/markokr/rarfile) - Python RAR文件处理库

## 📮 联系方式

- Issues: [GitHub Issues](https://github.com/yourusername/manga-organizer/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/manga-organizer/discussions)

## 🗺️ 路线图

### 已完成 ✅

- [x] 多元数据源（Bangumi、trace.moe、AniList、ComicVine）
- [x] ComicInfo.xml自动生成（Anansi v2.0标准）
- [x] 封面下载和管理
- [x] Komga准备工具（本地元数据处理）
- [x] 语言优先级系统（中文优先）
- [x] 元数据聚合和合并

### 规划中 📋

- [ ] GUI图形界面
- [ ] Web界面
- [ ] 多线程并行处理
- [ ] 重复文件检测
- [ ] 增量更新支持
- [ ] Docker支持
- [ ] 批量重命名工具
- [ ] 自动识别系列关联
- [ ] 元数据缓存系统
- [ ] Komga API直接集成

---

**注意：** 本工具仅供个人学习和整理使用。请尊重版权，支持正版。
