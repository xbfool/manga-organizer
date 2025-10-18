#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
嵌套RAR处理器 V2 - 集成元数据功能
功能：
- 递归解压嵌套RAR
- 从Bangumi/AniList获取元数据
- 生成ComicInfo.xml并嵌入CBZ
- 基于元数据的智能命名
- 原子操作（每个文件完整处理或从头开始）
"""

import os
import sys
import io
import re
import shutil
import rarfile
import zipfile
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import tempfile

# 导入元数据模块
from simple_tracker import SimpleTracker
from metadata_bangumi import BangumiAPI, MangaMetadata
from metadata_anilist import AniListAPI
from comicinfo_generator import ComicInfoGenerator

# Windows UTF-8 编码设置
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 修复Windows下sys.argv的Unicode编码问题
    try:
        from ctypes import POINTER, byref, cdll, c_int, windll
        from ctypes.wintypes import LPCWSTR, LPWSTR

        GetCommandLineW = cdll.kernel32.GetCommandLineW
        GetCommandLineW.argtypes = []
        GetCommandLineW.restype = LPCWSTR

        CommandLineToArgvW = windll.shell32.CommandLineToArgvW
        CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
        CommandLineToArgvW.restype = POINTER(LPWSTR)

        cmd = GetCommandLineW()
        argc = c_int(0)
        argv_unicode = CommandLineToArgvW(cmd, byref(argc))

        argv_list = [argv_unicode[i] for i in range(argc.value)]

        script_index = 0
        for i, arg in enumerate(argv_list):
            if arg.endswith('.py'):
                script_index = i
                break

        if script_index > 0:
            sys.argv = argv_list[script_index:]
    except Exception as e:
        print(f"Warning: Failed to get Unicode command line arguments: {e}", file=sys.stderr)

# 配置UnRAR工具路径
rarfile.UNRAR_TOOL = r"C:\Program Files\UnRAR\UnRAR.exe"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nested_rar_processor_v2.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """单个文件处理结果"""
    original_path: str
    series_name: str
    output_files: List[str]
    metadata_found: bool
    metadata_source: Optional[str]
    success: bool
    error: Optional[str] = None
    processing_time: float = 0.0


class NestedRARProcessorV2:
    """嵌套RAR处理器 V2"""

    # 日文标记模式
    JAPANESE_TAG_PATTERNS = [
        r'【一般コミック】\s*',
        r'【少年コミック】\s*',
        r'【青年コミック】\s*',
        r'【少女コミック】\s*',
        r'【女性コミック】\s*',
        r'【成年コミック】\s*',
        r'【漫画雑誌】\s*',
        r'\[一般コミック\]\s*',
        r'\[少年コミック\]\s*',
        r'\[青年コミック\]\s*',
    ]

    # 卷号提取模式
    VOLUME_PATTERNS = [
        (r'第(\d+)巻', 'v{:02d}'),
        (r'第(\d+)卷', 'v{:02d}'),
        (r'[Vv]ol[._\s]*(\d+)', 'v{:02d}'),
        (r'v(\d+)', 'v{:02d}'),
        (r'\s+(\d{2,3})\s*', 'v{:02d}'),
        (r'[_-](\d{2,3})[\._]', 'v{:02d}'),
    ]

    # 支持的图片格式
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    # RAR扩展名
    RAR_EXTENSIONS = {'.rar', '.cbr'}

    def __init__(self, output_dir: str, temp_dir: Optional[str] = None,
                 enable_metadata: bool = True, dry_run: bool = False):
        """
        初始化处理器

        Args:
            output_dir: 输出目录
            temp_dir: 临时目录
            enable_metadata: 启用元数据获取
            dry_run: 预演模式
        """
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "manga_temp"
        self.enable_metadata = enable_metadata
        self.dry_run = dry_run

        # 创建目录
        if not dry_run:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir.mkdir(parents=True, exist_ok=True)

        # 初始化跟踪器
        self.tracker = SimpleTracker()

        # 初始化元数据API
        if enable_metadata:
            self.bangumi_api = BangumiAPI(rate_limit_delay=1.0)
            self.anilist_api = AniListAPI(rate_limit_delay=1.0)
        else:
            self.bangumi_api = None
            self.anilist_api = None

        # ComicInfo生成器
        self.comicinfo_gen = ComicInfoGenerator()

        # 统计信息
        self.stats = {
            'total': 0,
            'processed': 0,
            'skipped': 0,
            'failed': 0,
            'metadata_found': 0,
            'metadata_failed': 0
        }

        # 处理结果列表
        self.results: List[ProcessResult] = []

    def _clean_series_name(self, filename: str) -> str:
        """
        清理系列名

        Args:
            filename: 原文件名

        Returns:
            清理后的系列名
        """
        name = Path(filename).stem

        # 移除日文标记
        for pattern in self.JAPANESE_TAG_PATTERNS:
            name = re.sub(pattern, '', name)

        # 移除"全X巻"等标记
        name = re.sub(r'全\d+巻', '', name)
        name = re.sub(r'全\d+卷', '', name)

        # 移除引号标记
        name = re.sub(r'[「」『』\[\]（）()]', '', name)

        # 清理多余空格
        name = re.sub(r'\s+', ' ', name).strip()
        name = name.strip(' -_')

        return name

    def _extract_volume_number(self, filename: str) -> Optional[int]:
        """
        提取卷号

        Args:
            filename: 文件名

        Returns:
            卷号（整数）或None
        """
        name = Path(filename).stem

        for pattern, _ in self.VOLUME_PATTERNS:
            match = re.search(pattern, name)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None

    def _fetch_metadata(self, series_name: str) -> Optional[MangaMetadata]:
        """
        获取元数据

        Args:
            series_name: 系列名

        Returns:
            元数据对象或None
        """
        if not self.enable_metadata:
            return None

        logger.info(f"正在获取元数据: {series_name}")

        # 优先尝试Bangumi
        if self.bangumi_api:
            try:
                metadata = self.bangumi_api.search_manga(series_name)
                if metadata:
                    logger.info(f"从Bangumi获取到元数据: {metadata.title_zh or metadata.title}")
                    return metadata
            except Exception as e:
                logger.warning(f"Bangumi API失败: {e}")

        # 备用AniList
        if self.anilist_api:
            try:
                metadata = self.anilist_api.search_manga(series_name)
                if metadata:
                    logger.info(f"从AniList获取到元数据: {metadata.title}")
                    return metadata
            except Exception as e:
                logger.warning(f"AniList API失败: {e}")

        logger.warning(f"未找到元数据: {series_name}")
        return None

    def _is_nested_rar(self, rar_path: Path) -> Tuple[bool, int]:
        """
        检测是否为嵌套RAR

        Args:
            rar_path: RAR文件路径

        Returns:
            (是否嵌套, 内层RAR数量)
        """
        try:
            with rarfile.RarFile(str(rar_path)) as rf:
                inner_rars = []
                for name in rf.namelist():
                    ext = Path(name).suffix.lower()
                    if ext in self.RAR_EXTENSIONS:
                        inner_rars.append(name)

                return len(inner_rars) > 0, len(inner_rars)
        except Exception as e:
            logger.error(f"检测嵌套RAR失败 {rar_path}: {e}")
            return False, 0

    def _create_cbz_from_directory(self, source_dir: Path, cbz_path: Path) -> bool:
        """
        从目录创建CBZ文件

        Args:
            source_dir: 源目录
            cbz_path: CBZ文件路径

        Returns:
            是否成功
        """
        try:
            # 收集所有图片文件
            image_files = []
            for ext in self.IMAGE_EXTENSIONS:
                image_files.extend(source_dir.rglob(f'*{ext}'))
                image_files.extend(source_dir.rglob(f'*{ext.upper()}'))

            if not image_files:
                logger.warning(f"未找到图片文件: {source_dir}")
                return False

            # 排序
            image_files.sort()

            logger.info(f"找到 {len(image_files)} 个图片文件，正在打包...")

            # 创建CBZ
            with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for img_file in image_files:
                    arcname = img_file.relative_to(source_dir)
                    zf.write(img_file, arcname)

            logger.info(f"创建CBZ成功: {cbz_path.name}")
            return True

        except Exception as e:
            logger.error(f"创建CBZ失败 {cbz_path}: {e}")
            return False

    def _process_single_rar(self, rar_path: Path, metadata: Optional[MangaMetadata]) -> List[str]:
        """
        处理单个RAR文件（可能嵌套）

        Args:
            rar_path: RAR文件路径
            metadata: 元数据对象

        Returns:
            生成的CBZ文件路径列表
        """
        start_time = time.time()
        output_files = []

        # 创建临时目录
        temp_root = self.temp_dir / f"temp_{int(time.time())}_{rar_path.stem}"
        temp_root.mkdir(parents=True, exist_ok=True)

        try:
            # 检测嵌套
            is_nested, inner_count = self._is_nested_rar(rar_path)

            if is_nested:
                logger.info(f"检测到嵌套RAR，包含 {inner_count} 个内层RAR")

                # 解压外层
                outer_extract_dir = temp_root / "outer"
                outer_extract_dir.mkdir(exist_ok=True)

                logger.info("解压外层RAR...")
                with rarfile.RarFile(str(rar_path)) as rf:
                    rf.extractall(str(outer_extract_dir))

                # 查找内层RAR
                inner_rars = []
                for ext in self.RAR_EXTENSIONS:
                    inner_rars.extend(outer_extract_dir.rglob(f'*{ext}'))

                logger.info(f"找到 {len(inner_rars)} 个内层RAR文件")

                # 处理每个内层RAR
                for idx, inner_rar in enumerate(sorted(inner_rars), 1):
                    logger.info(f"处理内层RAR [{idx}/{len(inner_rars)}]: {inner_rar.name}")

                    # 提取卷号
                    volume_num = self._extract_volume_number(inner_rar.name)

                    # 解压内层RAR
                    inner_extract_dir = temp_root / f"inner_{idx}"
                    inner_extract_dir.mkdir(exist_ok=True)

                    with rarfile.RarFile(str(inner_rar)) as rf:
                        rf.extractall(str(inner_extract_dir))

                    # 生成CBZ文件名
                    if metadata and metadata.title_zh:
                        series_title = metadata.title_zh
                    elif metadata:
                        series_title = metadata.title
                    else:
                        series_title = self._clean_series_name(rar_path.name)

                    if volume_num:
                        cbz_name = f"{series_title} v{volume_num:02d}.cbz"
                    else:
                        cbz_name = f"{series_title} {idx:02d}.cbz"

                    # 清理非法字符
                    cbz_name = re.sub(r'[<>:"/\\|?*]', '', cbz_name)

                    cbz_path = self.output_dir / cbz_name

                    # 创建CBZ
                    if self._create_cbz_from_directory(inner_extract_dir, cbz_path):
                        # 生成并嵌入ComicInfo.xml
                        if metadata:
                            try:
                                comicinfo_xml = self.comicinfo_gen.generate(metadata, volume_num)
                                self.comicinfo_gen.embed_into_cbz(cbz_path, comicinfo_xml)
                            except Exception as e:
                                logger.warning(f"嵌入ComicInfo失败: {e}")

                        output_files.append(str(cbz_path))

                    # 立即清理该内层RAR的临时目录（节省空间，避免混淆）
                    if inner_extract_dir.exists():
                        shutil.rmtree(inner_extract_dir, ignore_errors=True)
                        logger.info(f"已清理临时目录: inner_{idx}")

            else:
                # 非嵌套RAR，直接处理
                logger.info("非嵌套RAR，直接处理")

                extract_dir = temp_root / "extract"
                extract_dir.mkdir(exist_ok=True)

                with rarfile.RarFile(str(rar_path)) as rf:
                    rf.extractall(str(extract_dir))

                # 生成文件名
                if metadata and metadata.title_zh:
                    series_title = metadata.title_zh
                elif metadata:
                    series_title = metadata.title
                else:
                    series_title = self._clean_series_name(rar_path.name)

                volume_num = self._extract_volume_number(rar_path.name)

                if volume_num:
                    cbz_name = f"{series_title} v{volume_num:02d}.cbz"
                else:
                    cbz_name = f"{series_title}.cbz"

                cbz_name = re.sub(r'[<>:"/\\|?*]', '', cbz_name)
                cbz_path = self.output_dir / cbz_name

                # 创建CBZ
                if self._create_cbz_from_directory(extract_dir, cbz_path):
                    # 生成并嵌入ComicInfo.xml
                    if metadata:
                        try:
                            comicinfo_xml = self.comicinfo_gen.generate(metadata, volume_num)
                            self.comicinfo_gen.embed_into_cbz(cbz_path, comicinfo_xml)
                        except Exception as e:
                            logger.warning(f"嵌入ComicInfo失败: {e}")

                    output_files.append(str(cbz_path))

        finally:
            # 清理临时文件
            if temp_root.exists():
                shutil.rmtree(temp_root, ignore_errors=True)

        processing_time = time.time() - start_time
        logger.info(f"处理完成，耗时: {processing_time:.2f}秒，生成 {len(output_files)} 个文件")

        return output_files

    def process_file(self, rar_path: Path) -> ProcessResult:
        """
        处理单个文件（原子操作）

        Args:
            rar_path: RAR文件路径

        Returns:
            处理结果
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"开始处理: {rar_path.name}")
        logger.info(f"{'='*80}")

        start_time = time.time()

        # 提取系列名
        series_name = self._clean_series_name(rar_path.name)

        # 获取元数据
        metadata = self._fetch_metadata(series_name)

        metadata_found = metadata is not None
        metadata_source = metadata.source if metadata else None

        try:
            # 处理文件
            output_files = self._process_single_rar(rar_path, metadata)

            if output_files:
                processing_time = time.time() - start_time

                result = ProcessResult(
                    original_path=str(rar_path),
                    series_name=series_name,
                    output_files=output_files,
                    metadata_found=metadata_found,
                    metadata_source=metadata_source,
                    success=True,
                    processing_time=processing_time
                )

                logger.info(f"✓ 处理成功: {len(output_files)} 个文件")
                return result
            else:
                raise Exception("未生成任何输出文件")

        except Exception as e:
            logger.error(f"✗ 处理失败: {e}")

            result = ProcessResult(
                original_path=str(rar_path),
                series_name=series_name,
                output_files=[],
                metadata_found=metadata_found,
                metadata_source=metadata_source,
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )

            return result

    def process_batch(self, rar_files: List[Path], max_files: Optional[int] = None):
        """
        批量处理文件

        Args:
            rar_files: RAR文件列表
            max_files: 最大处理文件数
        """
        self.stats['total'] = len(rar_files)

        if max_files:
            rar_files = rar_files[:max_files]
            logger.info(f"限制处理前 {max_files} 个文件")

        for idx, rar_file in enumerate(rar_files, 1):
            logger.info(f"\n进度: [{idx}/{len(rar_files)}] {rar_file.name}")

            # 检查是否已处理
            if self.tracker.is_completed(str(rar_file)):
                logger.info("已处理，跳过")
                self.stats['skipped'] += 1
                continue

            # 处理文件
            result = self.process_file(rar_file)
            self.results.append(result)

            # 更新统计
            if result.success:
                self.stats['processed'] += 1
                if result.metadata_found:
                    self.stats['metadata_found'] += 1
                else:
                    self.stats['metadata_failed'] += 1

                # 标记为已完成（原子操作的最后一步）
                self.tracker.mark_completed(str(rar_file))
                logger.info("✓ 已标记为完成")
            else:
                self.stats['failed'] += 1

        # 打印最终统计
        self.print_summary()

    def print_summary(self):
        """打印处理摘要"""
        logger.info(f"\n{'='*80}")
        logger.info("处理摘要")
        logger.info(f"{'='*80}")
        logger.info(f"总文件数: {self.stats['total']}")
        logger.info(f"已处理: {self.stats['processed']}")
        logger.info(f"已跳过: {self.stats['skipped']}")
        logger.info(f"失败: {self.stats['failed']}")
        logger.info(f"元数据找到: {self.stats['metadata_found']}")
        logger.info(f"元数据失败: {self.stats['metadata_failed']}")

        tracker_stats = self.tracker.get_stats()
        logger.info(f"\n总已完成数: {tracker_stats['total_completed']}")
        logger.info(f"{'='*80}\n")

    def save_report(self, report_path: str):
        """保存处理报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'tracker_stats': self.tracker.get_stats(),
            'results': [asdict(r) for r in self.results]
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"报告已保存: {report_path}")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='嵌套RAR处理器 V2 - 集成元数据')
    parser.add_argument('--input', '-i', help='输入目录或文件')
    parser.add_argument('--output', '-o', help='输出目录')
    parser.add_argument('--temp', '-t', help='临时目录（可选）')
    parser.add_argument('--max-files', '-n', type=int, help='最大处理文件数（用于测试）')
    parser.add_argument('--dry-run', '-d', action='store_true', help='预演模式')
    parser.add_argument('--report', '-r', help='保存处理报告')
    parser.add_argument('--no-metadata', action='store_true', help='禁用元数据获取')
    parser.add_argument('--use-config', action='store_true', help='使用config.json中的路径')

    args = parser.parse_args()

    # 读取配置
    input_dir = args.input
    output_dir = args.output

    if args.use_config or not input_dir or not output_dir:
        try:
            config_path = Path('config.json')
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if not input_dir:
                        input_dir = config.get('paths', {}).get('comics_input')
                    if not output_dir:
                        output_dir = config.get('paths', {}).get('comics_output')
                    logger.info(f"从config.json读取路径配置")
                    logger.info(f"输入: {input_dir}")
                    logger.info(f"输出: {output_dir}")
        except Exception as e:
            logger.warning(f"无法读取config.json: {e}")

    if not input_dir or not output_dir:
        logger.error("必须指定--input和--output参数，或在config.json中配置路径")
        return

    # 创建处理器
    processor = NestedRARProcessorV2(
        output_dir=output_dir,
        temp_dir=args.temp,
        enable_metadata=not args.no_metadata,
        dry_run=args.dry_run
    )

    # 收集RAR文件
    input_path = Path(input_dir)
    if input_path.is_file():
        rar_files = [input_path]
    elif input_path.is_dir():
        rar_files = []
        for ext in NestedRARProcessorV2.RAR_EXTENSIONS:
            rar_files.extend(input_path.glob(f'*{ext}'))
        rar_files.sort()
    else:
        logger.error(f"无效的输入路径: {input_path}")
        return

    logger.info(f"找到 {len(rar_files)} 个RAR文件")

    # 批量处理
    processor.process_batch(rar_files, max_files=args.max_files)

    # 保存报告
    if args.report:
        processor.save_report(args.report)

    logger.info("处理完成")


if __name__ == '__main__':
    main()
