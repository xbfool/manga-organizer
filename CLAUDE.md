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

---

## 🚧 待完成功能清单

### 1. 嵌套RAR处理功能（优先级：高）

#### 背景
- 发现位置：`Z:/漫画/日漫/日语原版/Comics/`（1.1TB数据）
- 典型结构：
  ```
  【一般コミック】 CLAMP 「カードキャプターさくら 全12巻」.rar  ← 外层RAR
  ├── 【一般コミック】 CLAMP 「カードキャプターさくら 第01巻」.rar  ← 内层RAR
  ├── 【一般コミック】 CLAMP 「カードキャプターさくら 第02巻」.rar
  └── ...
  ```
- 问题：可能存在多层嵌套（2层、3层或更多）
- 要求：PDF文件不处理，保持原样

#### 功能需求

**1.1 探测功能**
- [ ] 创建 `rar_inspector.py` - RAR结构探测工具
- [ ] 实现 `inspect_rar_structure()` - 递归分析RAR内容
- [ ] 生成探测报告：
  - 嵌套层级
  - 内层文件类型统计
  - 目录结构规范度评分
  - 文件命名规范度评分
- [ ] 支持详细模式和简单模式

**1.2 嵌套RAR检测**
- [ ] 添加 `_is_nested_rar(rar_path)` 方法
  - 检测RAR内部是否包含RAR文件
  - 统计嵌套层数
  - 识别"全X卷"类型的打包方式
- [ ] 添加 `_analyze_inner_structure(rar_path)` 方法
  - 分析内层文件命名规范
  - 检测目录结构
  - 识别系列名和卷号

**1.3 递归解压处理**
- [ ] 添加 `_process_nested_rar(rar_path, max_depth=5)` 方法
  - 支持多层嵌套递归解压
  - 设置最大深度限制（防止无限递归）
  - 每层解压后清理临时文件
- [ ] 临时目录管理
  - 创建分层临时目录结构
  - 每层处理完自动清理
  - 异常时保留临时文件用于调试

**1.4 目录结构验证**
- [ ] 添加 `_validate_directory_structure()` 方法
  - 检查最终解压后的目录是否规范
  - 识别不规范的目录结构（多层嵌套、混乱命名）
  - 自动修正常见问题
- [ ] 添加 `_normalize_extracted_files()` 方法
  - 扁平化过深的目录结构
  - 移除无用的中间目录
  - 统一文件命名格式

**1.5 文件名规范检测**
- [ ] 添加 `_clean_filename()` 方法
  - 移除日文标记：【一般コミック】、【少年コミック】等
  - 移除括号标记：（第XX巻）、[完]、[未] 等
  - 提取标准系列名和卷号
  - 示例：
    ```
    【一般コミック】 CLAMP 「カードキャプターさくら 第01巻」.rar
    → カードキャプターさくら v01.cbz
    ```
- [ ] 添加文件名模式识别
  - 日文漫画命名模式
  - 英文/中文命名模式
  - 自定义模式支持

### 2. 渐进式处理系统（优先级：高）

#### 背景
- 大规模处理（1.1TB）需要数小时甚至数天
- 需要支持分批处理、断点续传
- 每天只处理一部分，逐步完成

#### 功能需求

**2.1 进度跟踪**
- [ ] 创建进度数据库（SQLite）
  - 记录每个文件的处理状态
  - 支持状态：待处理、处理中、已完成、失败
  - 记录处理时间戳
- [ ] 添加 `--resume` 参数支持断点续传
- [ ] 生成进度报告：
  ```
  总文件数: 1000
  已完成: 250 (25%)
  失败: 5
  剩余: 745
  预计剩余时间: 3小时
  ```

**2.2 批次处理**
- [ ] 添加 `--batch-size` 参数（每批处理数量）
- [ ] 添加 `--max-time` 参数（最大运行时间）
- [ ] 添加 `--daily-limit` 参数（每天处理上限）
- [ ] 自动保存进度，安全退出

**2.3 错误处理**
- [ ] 详细错误日志
  - 记录失败文件路径
  - 记录错误类型和堆栈
  - 支持错误文件重试
- [ ] 创建失败文件清单：`failed_files.json`
- [ ] 添加 `--retry-failed` 参数重新处理失败文件

**2.4 性能优化**
- [ ] 添加并发处理支持（多线程/多进程）
- [ ] 智能调度：
  - 先处理小文件（快速见效）
  - 后处理大文件（避免阻塞）
- [ ] 磁盘空间监控
  - 定期检查可用空间
  - 空间不足时暂停并提醒

### 3. 探测工具开发（优先级：中）

**3.1 创建独立探测脚本**
- [ ] 文件：`src/rar_inspector.py`
- [ ] 功能：
  - 扫描指定目录
  - 分析所有RAR文件
  - 生成详细报告
- [ ] 使用方式：
  ```bash
  # 简单模式
  python src/rar_inspector.py --dir "Z:/漫画/日漫/日语原版/Comics" --mode simple

  # 详细模式
  python src/rar_inspector.py --dir "Z:/漫画/日漫/日语原版/Comics" --mode detailed --output report.json
  ```

**3.2 报告内容**
- [ ] 文件统计
  - 总文件数、总大小
  - 嵌套RAR数量
  - 最大嵌套层数
- [ ] 结构分析
  - 目录结构类型分布
  - 命名规范问题列表
  - 需要特殊处理的文件列表
- [ ] 处理建议
  - 预计处理时间
  - 所需磁盘空间
  - 潜在问题警告

### 4. 配置增强（优先级：中）

**4.1 嵌套RAR配置**
```json
{
  "nested_rar": {
    "enabled": true,
    "max_depth": 5,
    "auto_detect": true,
    "flatten_structure": true,
    "clean_japanese_tags": true,
    "patterns_to_remove": [
      "【一般コミック】",
      "【少年コミック】",
      "【青年コミック】"
    ]
  }
}
```

**4.2 渐进式处理配置**
```json
{
  "progressive_processing": {
    "enabled": true,
    "batch_size": 100,
    "max_daily_files": 500,
    "max_session_time_minutes": 120,
    "auto_save_interval_minutes": 10,
    "progress_db": ".progress.db"
  }
}
```

### 5. 测试计划（优先级：高）

**5.1 单元测试**
- [ ] 测试嵌套RAR检测
- [ ] 测试递归解压
- [ ] 测试文件名清理
- [ ] 测试进度保存和恢复

**5.2 集成测试**
- [ ] 小规模测试（10个嵌套RAR）
- [ ] 中等规模测试（100个文件）
- [ ] 断点续传测试
- [ ] 错误恢复测试

**5.3 性能测试**
- [ ] 测试不同批次大小的性能
- [ ] 测试并发处理效果
- [ ] 内存使用监控
- [ ] 磁盘I/O监控

### 6. 文档更新（优先级：低）

- [ ] 更新 README.md - 添加嵌套RAR处理说明
- [ ] 更新 README.md - 添加渐进式处理使用指南
- [ ] 创建 NESTED_RAR_GUIDE.md - 嵌套RAR处理详细指南
- [ ] 更新配置文件示例

### 实施顺序建议

**第一阶段：探测和分析**
1. 创建 `rar_inspector.py` 探测工具
2. 对 Comics 目录进行全面探测
3. 分析结果，确定处理策略

**第二阶段：基础功能**
1. 实现嵌套RAR检测
2. 实现单层递归解压
3. 小规模测试验证

**第三阶段：完整功能**
1. 实现多层递归解压
2. 添加目录结构验证
3. 添加文件名清理

**第四阶段：渐进式处理**
1. 实现进度跟踪系统
2. 添加批次处理
3. 添加断点续传

**第五阶段：优化和测试**
1. 性能优化
2. 完整测试
3. 文档更新

### 注意事项

1. **临时空间需求**：处理1.1TB数据可能需要2-3TB临时空间
2. **处理时间**：预计需要数天时间，建议每天处理一部分
3. **错误处理**：遇到损坏的RAR文件要跳过，记录日志
4. **PDF文件**：所有PDF不解压，不转换，跳过处理
5. **备份建议**：处理前确认原文件有备份
6. **进度可视化**：考虑添加进度条显示
7. **日志详细度**：记录每个文件的处理过程，便于调试

### 当前状态

**已完成功能（2025-10-18）：**

- ✅ 基础Komga准备工具完成
- ✅ 格式转换功能完成
- ✅ 元数据聚合完成
- ✅ 系列名清理完成
- ✅ **嵌套RAR处理 - 完成**
  - ✅ RAR探测工具（`src/rar_inspector.py`）
  - ✅ 嵌套RAR递归解压
  - ✅ 日文标记清理
  - ✅ 卷号提取和标准化
  - ✅ CBZ自动生成
  - ✅ 即时临时文件清理（避免文件混淆）
- ✅ **元数据集成 - 完成**
  - ✅ Bangumi API客户端（`src/metadata_bangumi.py`）
  - ✅ AniList API客户端（`src/metadata_anilist.py`，备用）
  - ✅ ComicInfo.xml生成器（`src/comicinfo_generator.py`）
  - ✅ 自动嵌入ComicInfo.xml到CBZ
  - ✅ 基于元数据的智能命名
- ✅ **进度跟踪 - 完成**
  - ✅ 简化跟踪器（`src/simple_tracker.py`）
  - ✅ JSON格式（人类可读）
  - ✅ 原子操作（每个文件完整处理或从头开始）
  - ✅ 已完成文件自动跳过
- ✅ **V2处理器 - 完成**（`src/nested_rar_processor_v2.py`）
  - ✅ 完整功能集成
  - ✅ Windows中文/日文路径支持
  - ✅ 配置文件路径读取（`config.json`）
  - ✅ 测试通过（1文件→4个CBZ，73秒）

**测试结果：**
- 📊 Comics目录扫描：1,472个RAR文件
- 📊 嵌套RAR占比：87%（1,284个）
- 📊 单文件处理：成功生成4个CBZ（1.3GB）
- ⚡ 处理速度：~20秒/卷
- ✅ 临时文件清理：即时清理，无混淆风险

**待完成：**
- 🚧 全量处理（1,472个文件）
- 🚧 元数据匹配优化（改进搜索关键词提取）
- 🚧 封面下载功能（可选）

**当前可用工具：**
1. `test_v2.ps1` - 测试V2处理器（单文件）
2. `run_inspector.ps1` - RAR结构探测
3. `view_progress.ps1` - 查看处理进度
4. `test_from_config.ps1` - 使用配置文件测试
