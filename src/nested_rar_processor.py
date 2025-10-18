#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
嵌套RAR处理器
功能：递归解压嵌套RAR，转换为CBZ，清理文件名
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
from datetime import datetime, timedelta
import logging
import tempfile

# 导入进度跟踪器
from progress_tracker import ProgressTracker

# Windows UTF-8 编码设置
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 修复Windows下sys.argv的Unicode编码问题
    # 使用Windows API获取正确的Unicode参数
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

        # 转换为Python列表
        argv_list = [argv_unicode[i] for i in range(argc.value)]

        # 找到实际脚本文件的位置（跳过python.exe和Python选项如-X utf8）
        script_index = 0
        for i, arg in enumerate(argv_list):
            if arg.endswith('.py'):
                script_index = i
                break

        # 替换sys.argv：脚本名 + 后续参数
        if script_index > 0:
            sys.argv = argv_list[script_index:]
    except Exception as e:
        # 如果API调用失败，记录错误但继续执行
        print(f"Warning: Failed to get Unicode command line arguments: {e}", file=sys.stderr)

# 配置UnRAR工具路径
rarfile.UNRAR_TOOL = r"C:\Program Files\UnRAR\UnRAR.exe"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nested_rar_processor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """处理结果"""
    original_path: str
    output_files: List[str]
    success: bool
    error: Optional[str] = None
    files_created: int = 0
    processing_time: float = 0.0


class NestedRARProcessor:
    """嵌套RAR处理器"""

    # 日文标记模式（需要移除）
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
        (r'第(\d+)巻', 'v{:02d}'),      # 第01巻
        (r'第(\d+)卷', 'v{:02d}'),      # 第01卷
        (r'[Vv]ol[._\s]*(\d+)', 'v{:02d}'),  # Vol 01
        (r'v(\d+)', 'v{:02d}'),         # v01
        (r'\s+(\d{2,3})\s*', 'v{:02d}'),  # 空格+数字
        (r'[_-](\d{2,3})[\._]', 'v{:02d}'),  # -01.
    ]

    # 支持的图片格式
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    # RAR扩展名
    RAR_EXTENSIONS = {'.rar', '.cbr'}

    def __init__(self, output_dir: str, temp_dir: Optional[str] = None, dry_run: bool = False,
                 enable_progress_tracking: bool = True, progress_file: Optional[str] = None,
                 auto_save_interval: int = 10):
        """
        初始化处理器

        Args:
            output_dir: 输出目录
            temp_dir: 临时目录（None则使用系统临时目录）
            dry_run: 预演模式（不实际处理）
            enable_progress_tracking: 启用进度跟踪
            progress_file: 进度文件路径
            auto_save_interval: 自动保存间隔（文件数）
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.temp_dir = Path(temp_dir) if temp_dir else None
        self.dry_run = dry_run
        self.auto_save_interval = auto_save_interval

        # 初始化进度跟踪器
        self.enable_progress_tracking = enable_progress_tracking
        if enable_progress_tracking:
            progress_path = progress_file or ".progress/processing_progress.json"
            self.progress_tracker = ProgressTracker(progress_path)
        else:
            self.progress_tracker = None

        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'cbz_created': 0,
            'total_size_processed': 0,
            'skipped': 0,
        }

        self.results: List[ProcessResult] = []
        self.session_start_time = None

    def process_rar_file(self, rar_path: Path) -> ProcessResult:
        """
        处理单个RAR文件

        Args:
            rar_path: RAR文件路径

        Returns:
            ProcessResult对象
        """
        start_time = datetime.now()
        file_path_str = str(rar_path)
        logger.info(f"开始处理: {rar_path.name}")

        # 标记开始处理
        if self.progress_tracker:
            self.progress_tracker.start_processing(file_path_str)

        if self.dry_run:
            logger.info("[预演模式] 跳过实际处理")
            return ProcessResult(
                original_path=file_path_str,
                output_files=[],
                success=True,
                files_created=0,
                processing_time=0.0
            )

        try:
            # 创建临时目录
            if self.temp_dir:
                temp_root = self.temp_dir / f"temp_{rar_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                temp_root.mkdir(parents=True, exist_ok=True)
            else:
                temp_root = Path(tempfile.mkdtemp(prefix=f"rar_process_{rar_path.stem}_"))

            try:
                # 检查是否是嵌套RAR
                is_nested, inner_rars = self._check_nested_rar(rar_path)

                if is_nested:
                    logger.info(f"检测到嵌套RAR，包含 {len(inner_rars)} 个内层RAR")
                    output_files = self._process_nested_rar(rar_path, temp_root)
                else:
                    logger.info("非嵌套RAR，直接转换")
                    output_files = self._process_single_rar(rar_path, temp_root)

                # 更新统计
                self.stats['total_processed'] += 1
                self.stats['successful'] += 1
                self.stats['cbz_created'] += len(output_files)
                self.stats['total_size_processed'] += rar_path.stat().st_size

                processing_time = (datetime.now() - start_time).total_seconds()

                result = ProcessResult(
                    original_path=file_path_str,
                    output_files=output_files,
                    success=True,
                    files_created=len(output_files),
                    processing_time=processing_time
                )

                # 标记处理完成
                if self.progress_tracker:
                    self.progress_tracker.mark_completed(file_path_str, output_files)

                logger.info(f"处理完成: 创建 {len(output_files)} 个CBZ文件，耗时 {processing_time:.2f}秒")
                return result

            finally:
                # 清理临时目录
                if temp_root.exists():
                    shutil.rmtree(temp_root, ignore_errors=True)
                    logger.debug(f"清理临时目录: {temp_root}")

        except Exception as e:
            error_msg = f"处理失败: {e}"
            logger.error(f"{rar_path.name}: {error_msg}")
            self.stats['total_processed'] += 1
            self.stats['failed'] += 1

            # 标记处理失败
            if self.progress_tracker:
                self.progress_tracker.mark_failed(file_path_str, error_msg)

            return ProcessResult(
                original_path=file_path_str,
                output_files=[],
                success=False,
                error=error_msg,
                processing_time=(datetime.now() - start_time).total_seconds()
            )

    def _check_nested_rar(self, rar_path: Path) -> Tuple[bool, List[str]]:
        """
        检查是否是嵌套RAR

        Args:
            rar_path: RAR文件路径

        Returns:
            (是否嵌套, 内层RAR文件列表)
        """
        inner_rars = []

        try:
            with rarfile.RarFile(str(rar_path)) as rf:
                for member in rf.infolist():
                    if not member.is_dir():
                        ext = Path(member.filename).suffix.lower()
                        if ext in self.RAR_EXTENSIONS:
                            inner_rars.append(member.filename)
        except Exception as e:
            logger.error(f"检查嵌套RAR失败 {rar_path}: {e}")
            return False, []

        return len(inner_rars) > 0, inner_rars

    def _process_nested_rar(self, rar_path: Path, temp_root: Path) -> List[str]:
        """
        处理嵌套RAR

        Args:
            rar_path: 外层RAR文件路径
            temp_root: 临时目录

        Returns:
            生成的CBZ文件列表
        """
        output_files = []

        # 第一步：解压外层RAR
        outer_extract_dir = temp_root / "outer"
        outer_extract_dir.mkdir(parents=True, exist_ok=True)

        logger.info("解压外层RAR...")
        with rarfile.RarFile(str(rar_path)) as rf:
            rf.extractall(str(outer_extract_dir))

        # 第二步：找到所有内层RAR文件
        inner_rars = []
        for item in outer_extract_dir.rglob('*'):
            if item.is_file() and item.suffix.lower() in self.RAR_EXTENSIONS:
                inner_rars.append(item)

        logger.info(f"找到 {len(inner_rars)} 个内层RAR文件")

        # 第三步：处理每个内层RAR
        for idx, inner_rar in enumerate(inner_rars, 1):
            logger.info(f"处理内层RAR [{idx}/{len(inner_rars)}]: {inner_rar.name}")

            try:
                # 为每个内层RAR创建临时目录
                inner_extract_dir = temp_root / "inner" / f"rar_{idx}"
                inner_extract_dir.mkdir(parents=True, exist_ok=True)

                # 解压内层RAR
                with rarfile.RarFile(str(inner_rar)) as rf:
                    rf.extractall(str(inner_extract_dir))

                # 清理文件名并生成CBZ
                cbz_name = self._clean_and_generate_cbz_name(inner_rar.name, rar_path.name)
                cbz_path = self.output_dir / cbz_name

                # 创建CBZ
                self._create_cbz_from_directory(inner_extract_dir, cbz_path)
                output_files.append(str(cbz_path))

                logger.info(f"创建CBZ: {cbz_name}")

            except Exception as e:
                logger.error(f"处理内层RAR失败 {inner_rar.name}: {e}")

        return output_files

    def _process_single_rar(self, rar_path: Path, temp_root: Path) -> List[str]:
        """
        处理单层RAR（直接转换为CBZ）

        Args:
            rar_path: RAR文件路径
            temp_root: 临时目录

        Returns:
            生成的CBZ文件列表
        """
        extract_dir = temp_root / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)

        # 解压RAR
        logger.info("解压RAR...")
        with rarfile.RarFile(str(rar_path)) as rf:
            rf.extractall(str(extract_dir))

        # 清理文件名
        cbz_name = self._clean_and_generate_cbz_name(rar_path.name, rar_path.name)
        cbz_path = self.output_dir / cbz_name

        # 创建CBZ
        self._create_cbz_from_directory(extract_dir, cbz_path)

        logger.info(f"创建CBZ: {cbz_name}")
        return [str(cbz_path)]

    def _clean_and_generate_cbz_name(self, filename: str, parent_name: str) -> str:
        """
        清理文件名并生成CBZ文件名

        Args:
            filename: 原始文件名
            parent_name: 父文件名（用于提取系列名）

        Returns:
            清理后的CBZ文件名
        """
        # 移除扩展名
        name = Path(filename).stem
        parent_stem = Path(parent_name).stem

        # 移除日文标记
        for pattern in self.JAPANESE_TAG_PATTERNS:
            name = re.sub(pattern, '', name)
            parent_stem = re.sub(pattern, '', parent_stem)

        # 提取卷号
        volume_num = None
        for pattern, format_str in self.VOLUME_PATTERNS:
            match = re.search(pattern, name)
            if match:
                volume_num = format_str.format(int(match.group(1)))
                # 移除卷号部分
                name = re.sub(pattern, '', name)
                break

        # 如果没找到卷号，尝试从文件名中提取数字
        if not volume_num:
            match = re.search(r'(\d{2,3})', name)
            if match:
                volume_num = f"v{int(match.group(1)):02d}"

        # 从父文件名提取系列名
        series_name = parent_stem

        # 移除"全X巻"等标记
        series_name = re.sub(r'全\d+巻', '', series_name)
        series_name = re.sub(r'全\d+卷', '', series_name)

        # 移除引号标记
        series_name = re.sub(r'[「」『』\[\]（）()]', '', series_name)

        # 清理多余空格
        series_name = re.sub(r'\s+', ' ', series_name).strip()
        series_name = series_name.strip(' -_')

        # 生成最终文件名
        if volume_num:
            cbz_name = f"{series_name} {volume_num}.cbz"
        else:
            cbz_name = f"{series_name}.cbz"

        # 清理非法字符
        cbz_name = re.sub(r'[<>:"/\\|?*]', '', cbz_name)

        return cbz_name

    def _create_cbz_from_directory(self, source_dir: Path, cbz_path: Path) -> None:
        """
        从目录创建CBZ文件

        Args:
            source_dir: 源目录
            cbz_path: CBZ文件路径
        """
        # 收集所有图片文件
        image_files = []
        for ext in self.IMAGE_EXTENSIONS:
            image_files.extend(source_dir.rglob(f'*{ext}'))
            image_files.extend(source_dir.rglob(f'*{ext.upper()}'))

        if not image_files:
            logger.warning(f"目录中没有找到图片文件: {source_dir}")
            return

        # 按文件名排序
        image_files.sort(key=lambda x: x.name)

        logger.info(f"找到 {len(image_files)} 个图片文件，正在打包...")

        # 创建CBZ（实际上是ZIP）
        with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_STORED) as zf:
            for img_file in image_files:
                # 使用相对路径作为压缩包内的路径
                arcname = img_file.relative_to(source_dir)
                zf.write(img_file, arcname)

        logger.debug(f"CBZ创建完成: {cbz_path}")

    def process_batch(self, rar_files: List[Path], max_files: Optional[int] = None,
                      resume: bool = True) -> None:
        """
        批量处理RAR文件（支持断点续传）

        Args:
            rar_files: RAR文件列表
            max_files: 最大处理文件数（用于测试）
            resume: 是否从上次中断处继续
        """
        self.session_start_time = datetime.now()

        # 准备文件列表
        if max_files:
            rar_files = rar_files[:max_files]
            logger.info(f"限制处理前 {max_files} 个文件")

        total = len(rar_files)

        # 初始化进度跟踪
        if self.progress_tracker:
            # 添加所有文件到进度跟踪器
            file_paths = [str(f) for f in rar_files]
            self.progress_tracker.add_files(file_paths)

            # 开始会话
            session_name = f"Batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.progress_tracker.start_session(total, session_name)

            # 如果启用断点续传，过滤已处理的文件
            if resume:
                files_to_process = []
                for rar_path in rar_files:
                    if not self.progress_tracker.is_file_processed(str(rar_path)):
                        files_to_process.append(rar_path)
                    else:
                        logger.info(f"跳过已处理文件: {rar_path.name}")
                        self.stats['skipped'] += 1

                skipped = total - len(files_to_process)
                if skipped > 0:
                    logger.info(f"断点续传：跳过 {skipped} 个已处理文件")

                rar_files = files_to_process
                total = len(rar_files)

        logger.info(f"开始批量处理 {total} 个文件...")

        try:
            for idx, rar_path in enumerate(rar_files, 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"进度: [{idx}/{total}] {rar_path.name}")
                logger.info(f"{'='*80}")

                result = self.process_rar_file(rar_path)
                self.results.append(result)

                # 自动保存进度
                if self.progress_tracker and idx % self.auto_save_interval == 0:
                    self.progress_tracker.save()
                    logger.debug(f"自动保存进度 ({idx}/{total})")

                # 每10个文件输出一次统计
                if idx % 10 == 0:
                    self._print_progress()

            logger.info("\n批量处理完成！")

            # 结束会话
            if self.progress_tracker:
                self.progress_tracker.end_session("completed")
                self.progress_tracker.save()

            self._print_final_report()

        except KeyboardInterrupt:
            logger.warning("\n处理被用户中断")

            # 保存进度
            if self.progress_tracker:
                self.progress_tracker.end_session("interrupted")
                self.progress_tracker.save()
                logger.info("进度已保存，可以稍后使用 --resume 继续")

            self._print_final_report()
            raise

        except Exception as e:
            logger.error(f"批量处理出错: {e}")

            # 保存进度
            if self.progress_tracker:
                self.progress_tracker.end_session("error")
                self.progress_tracker.save()

            self._print_final_report()
            raise

    def _print_progress(self) -> None:
        """打印进度统计"""
        logger.info(f"\n当前进度统计:")
        logger.info(f"  已处理: {self.stats['total_processed']}")
        logger.info(f"  成功: {self.stats['successful']}")
        logger.info(f"  失败: {self.stats['failed']}")
        logger.info(f"  跳过: {self.stats['skipped']}")
        logger.info(f"  创建CBZ: {self.stats['cbz_created']}")

        if self.progress_tracker:
            tracker_stats = self.progress_tracker.get_statistics()
            logger.info(f"  总进度: {tracker_stats['progress_percentage']:.1f}%")

    def _print_final_report(self) -> None:
        """打印最终报告"""
        print("\n" + "="*80)
        print("处理完成报告")
        print("="*80)
        print(f"总处理文件数: {self.stats['total_processed']}")
        print(f"成功: {self.stats['successful']}")
        print(f"失败: {self.stats['failed']}")
        print(f"跳过: {self.stats['skipped']}")
        print(f"创建CBZ文件: {self.stats['cbz_created']}")
        print(f"处理数据量: {self._format_size(self.stats['total_size_processed'])}")

        if self.session_start_time:
            duration = datetime.now() - self.session_start_time
            print(f"处理耗时: {duration}")

        # 显示进度跟踪器统计
        if self.progress_tracker:
            print("\n进度跟踪统计:")
            tracker_stats = self.progress_tracker.get_statistics()
            print(f"  总文件数: {tracker_stats['total_files']}")
            print(f"  待处理: {tracker_stats['pending']}")
            print(f"  已完成: {tracker_stats['completed']} ({tracker_stats['progress_percentage']:.1f}%)")
            print(f"  失败: {tracker_stats['failed']}")

        if self.stats['failed'] > 0:
            print(f"\n失败的文件:")
            for result in self.results:
                if not result.success:
                    print(f"  - {Path(result.original_path).name}: {result.error}")

        print("="*80)

    def save_report(self, output_file: str) -> None:
        """
        保存处理报告

        Args:
            output_file: 输出文件路径
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'results': [asdict(r) for r in self.results]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"报告已保存: {output_file}")

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='嵌套RAR处理器')
    parser.add_argument('--input', '-i', help='输入目录或文件（可选，不指定则从config.json读取）')
    parser.add_argument('--output', '-o', help='输出目录（可选，不指定则从config.json读取）')
    parser.add_argument('--temp', '-t', help='临时目录（可选）')
    parser.add_argument('--max-files', '-n', type=int, help='最大处理文件数（用于测试）')
    parser.add_argument('--dry-run', '-d', action='store_true', help='预演模式（不实际处理）')
    parser.add_argument('--report', '-r', help='保存处理报告到指定文件')
    parser.add_argument('--resume', action='store_true', help='断点续传（从上次中断处继续）')
    parser.add_argument('--no-progress', action='store_true', help='禁用进度跟踪')
    parser.add_argument('--progress-file', help='进度文件路径（默认：.progress/processing_progress.json）')
    parser.add_argument('--use-config', action='store_true', help='使用config.json中的路径配置')

    args = parser.parse_args()

    # 如果未指定input/output或使用--use-config，从config.json读取
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
    processor = NestedRARProcessor(
        output_dir=output_dir,
        temp_dir=args.temp,
        dry_run=args.dry_run,
        enable_progress_tracking=not args.no_progress,
        progress_file=args.progress_file
    )

    # 收集RAR文件
    input_path = Path(input_dir)
    if input_path.is_file():
        rar_files = [input_path]
    elif input_path.is_dir():
        rar_files = []
        for ext in NestedRARProcessor.RAR_EXTENSIONS:
            rar_files.extend(input_path.glob(f'*{ext}'))
        rar_files.sort()
    else:
        logger.error(f"无效的输入路径: {input_path}")
        return

    logger.info(f"找到 {len(rar_files)} 个RAR文件")

    # 批量处理
    processor.process_batch(rar_files, max_files=args.max_files, resume=args.resume)

    # 保存报告
    if args.report:
        processor.save_report(args.report)

    # 导出进度摘要
    if processor.progress_tracker and output_dir:
        summary_file = Path(output_dir) / "progress_summary.txt"
        processor.progress_tracker.export_summary(str(summary_file))

    logger.info("处理完成")


if __name__ == '__main__':
    main()
