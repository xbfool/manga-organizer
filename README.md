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
- 🌐 **元数据查询** - 支持从AniList、ComicVine等API获取漫画信息
- 💾 **非破坏性整理** - 保留原文件，创建新目录
- 📊 **详细报告** - 生成JSON格式的分析和处理报告
- 🔒 **安全可靠** - 预演模式、详细日志、可随时中断

## 📋 目录

- [快速开始](#快速开始)
- [安装](#安装)
- [使用方法](#使用方法)
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

### 支持的API

#### AniList（日漫）
- ✅ 免费，无需API key
- ✅ 50万+ 条目
- ✅ 多语言支持

```python
from src.metadata_fetcher import MetadataFetcherManager

manager = MetadataFetcherManager()
metadata = manager.fetch_metadata("SLAM DUNK", category='日漫')
print(f"作者: {metadata.author}")
print(f"卷数: {metadata.volumes}")
```

#### ComicVine（美漫）
- ⚠️ 需要免费API key
- ⚠️ 限制：200请求/小时

```python
manager = MetadataFetcherManager(comicvine_api_key="YOUR_API_KEY")
metadata = manager.fetch_metadata("Batman", category='美漫')
```

**获取API key：** https://comicvine.gamespot.com/api/

### 查询示例

```bash
# 测试元数据查询
python src/metadata_fetcher.py
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

- [ ] GUI图形界面
- [ ] Web界面
- [ ] 多线程并行处理
- [ ] 封面下载和管理
- [ ] 重复文件检测
- [ ] 增量更新支持
- [ ] Docker支持
- [ ] 更多元数据源
- [ ] ComicInfo.xml自动生成
- [ ] 批量重命名工具

---

**注意：** 本工具仅供个人学习和整理使用。请尊重版权，支持正版。
