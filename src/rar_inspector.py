#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAR结构探测工具
功能：递归分析RAR文件结构，检测嵌套层级，生成详细报告
"""

import os
import sys
import io
import re
import rarfile
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import defaultdict
import logging

# Windows UTF-8 编码设置
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置UnRAR工具路径
rarfile.UNRAR_TOOL = r"C:\Program Files\UnRAR\UnRAR.exe"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rar_inspector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class RARFileInfo:
    """RAR文件信息"""
    file_path: str
    file_size: int
    is_nested: bool
    nesting_level: int
    inner_rar_count: int
    inner_files: List[Dict[str, Any]]
    total_inner_files: int
    file_types: Dict[str, int]
    has_japanese_tags: bool
    japanese_tags: List[str]
    series_name: Optional[str] = None
    volume_info: Optional[str] = None
    needs_cleaning: bool = False
    analysis_errors: Optional[List[str]] = None


class RARInspector:
    """RAR文件探测器"""

    # 日文标记模式
    JAPANESE_TAG_PATTERNS = [
        r'【一般コミック】',
        r'【少年コミック】',
        r'【青年コミック】',
        r'【少女コミック】',
        r'【女性コミック】',
        r'【成年コミック】',
        r'【漫画雑誌】',
        r'\[一般コミック\]',
        r'\[少年コミック\]',
        r'\[青年コミック\]',
    ]

    # 卷号提取模式
    VOLUME_PATTERNS = [
        r'第(\d+)巻',
        r'第(\d+)卷',
        r'[Vv]ol[._\s]*(\d+)',
        r'v(\d+)',
        r'\s+(\d{2,3})\s*$',
    ]

    # RAR文件扩展名
    RAR_EXTENSIONS = {'.rar', '.cbr'}

    # 支持的漫画文件类型
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf', '.zip', '.cbz'}

    def __init__(self, target_dir: str, max_depth: int = 10, max_files: Optional[int] = None):
        """
        初始化探测器

        Args:
            target_dir: 目标目录
            max_depth: 最大嵌套深度
            max_files: 最大扫描文件数（用于测试，None表示无限制）
        """
        self.target_dir = Path(target_dir)
        self.max_depth = max_depth
        self.max_files = max_files
        self.rar_files: List[RARFileInfo] = []
        self.stats = {
            'total_rar_files': 0,
            'nested_rar_files': 0,
            'max_nesting_level': 0,
            'total_size': 0,
            'files_with_japanese_tags': 0,
            'files_needing_cleaning': 0,
            'analysis_errors': 0,
        }
        self.file_type_stats = defaultdict(int)

    def scan_directory(self) -> None:
        """扫描目录中的所有RAR文件"""
        logger.info(f"开始扫描目录: {self.target_dir}")

        if not self.target_dir.exists():
            logger.error(f"目录不存在: {self.target_dir}")
            return

        # 递归查找所有RAR文件
        rar_files = []
        for ext in self.RAR_EXTENSIONS:
            pattern = f"**/*{ext}"
            rar_files.extend(self.target_dir.glob(pattern))

        # 应用文件数量限制
        total_found = len(rar_files)
        if self.max_files and total_found > self.max_files:
            logger.info(f"找到 {total_found} 个RAR文件，限制扫描前 {self.max_files} 个")
            rar_files = rar_files[:self.max_files]
        else:
            logger.info(f"找到 {total_found} 个RAR文件")

        self.stats['total_rar_files'] = len(rar_files)

        # 分析每个RAR文件
        for idx, rar_path in enumerate(rar_files, 1):
            if idx % 10 == 0:
                logger.info(f"进度: {idx}/{len(rar_files)}")

            try:
                rar_info = self._analyze_rar_file(rar_path)
                self.rar_files.append(rar_info)

                # 更新统计
                self.stats['total_size'] += rar_info.file_size
                if rar_info.is_nested:
                    self.stats['nested_rar_files'] += 1
                if rar_info.nesting_level > self.stats['max_nesting_level']:
                    self.stats['max_nesting_level'] = rar_info.nesting_level
                if rar_info.has_japanese_tags:
                    self.stats['files_with_japanese_tags'] += 1
                if rar_info.needs_cleaning:
                    self.stats['files_needing_cleaning'] += 1
                if rar_info.analysis_errors:
                    self.stats['analysis_errors'] += 1

                # 更新文件类型统计
                for file_type, count in rar_info.file_types.items():
                    self.file_type_stats[file_type] += count

            except Exception as e:
                logger.error(f"分析文件失败 {rar_path}: {e}")
                self.stats['analysis_errors'] += 1

        logger.info("扫描完成")

    def _analyze_rar_file(self, rar_path: Path, current_depth: int = 0) -> RARFileInfo:
        """
        分析单个RAR文件

        Args:
            rar_path: RAR文件路径
            current_depth: 当前嵌套深度

        Returns:
            RARFileInfo对象
        """
        file_size = rar_path.stat().st_size
        inner_files = []
        inner_rar_count = 0
        file_types = defaultdict(int)
        errors = []

        try:
            with rarfile.RarFile(str(rar_path)) as rf:
                for member in rf.infolist():
                    if member.is_dir():
                        continue

                    # 获取文件信息
                    file_info = {
                        'name': member.filename,
                        'size': member.file_size,
                        'compress_size': member.compress_size,
                        'is_rar': False
                    }

                    # 检查文件类型
                    file_ext = Path(member.filename).suffix.lower()
                    file_types[file_ext] += 1

                    # 检查是否是嵌套的RAR
                    if file_ext in self.RAR_EXTENSIONS:
                        inner_rar_count += 1
                        file_info['is_rar'] = True

                    inner_files.append(file_info)

        except Exception as e:
            error_msg = f"无法读取RAR文件: {e}"
            logger.error(f"{rar_path}: {error_msg}")
            errors.append(error_msg)

        # 分析文件名
        file_name = rar_path.name
        has_japanese_tags = False
        japanese_tags = []

        for pattern in self.JAPANESE_TAG_PATTERNS:
            matches = re.findall(pattern, file_name)
            if matches:
                has_japanese_tags = True
                japanese_tags.extend(matches)

        # 提取系列名和卷号
        series_name, volume_info = self._extract_series_and_volume(file_name)

        # 判断是否需要清理
        needs_cleaning = has_japanese_tags or inner_rar_count > 0

        # 计算嵌套层级
        nesting_level = 1 if inner_rar_count > 0 else 0

        return RARFileInfo(
            file_path=str(rar_path),
            file_size=file_size,
            is_nested=inner_rar_count > 0,
            nesting_level=nesting_level,
            inner_rar_count=inner_rar_count,
            inner_files=inner_files,
            total_inner_files=len(inner_files),
            file_types=dict(file_types),
            has_japanese_tags=has_japanese_tags,
            japanese_tags=japanese_tags,
            series_name=series_name,
            volume_info=volume_info,
            needs_cleaning=needs_cleaning,
            analysis_errors=errors if errors else None
        )

    def _extract_series_and_volume(self, filename: str) -> Tuple[Optional[str], Optional[str]]:
        """
        从文件名提取系列名和卷号

        Args:
            filename: 文件名

        Returns:
            (系列名, 卷号)元组
        """
        # 移除扩展名
        name = Path(filename).stem

        # 移除日文标记
        for pattern in self.JAPANESE_TAG_PATTERNS:
            name = re.sub(pattern, '', name)

        # 尝试提取卷号
        volume = None
        for pattern in self.VOLUME_PATTERNS:
            match = re.search(pattern, name)
            if match:
                volume = match.group(1)
                # 移除卷号部分，剩下的是系列名
                name = re.sub(pattern, '', name)
                break

        # 清理系列名
        series_name = name.strip(' -_「」『』[]【】')

        return series_name if series_name else None, volume

    def generate_report(self, output_file: Optional[str] = None, mode: str = 'detailed') -> Dict:
        """
        生成探测报告

        Args:
            output_file: 输出文件路径（JSON格式）
            mode: 报告模式 ('simple' 或 'detailed')

        Returns:
            报告字典
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_directory': str(self.target_dir),
            'statistics': self.stats,
            'file_type_distribution': dict(self.file_type_stats),
        }

        if mode == 'detailed':
            # 详细模式：包含所有文件信息
            report['files'] = [asdict(rar_info) for rar_info in self.rar_files]
        else:
            # 简单模式：只包含需要处理的文件
            nested_files = [
                {
                    'file_path': rar_info.file_path,
                    'file_size': rar_info.file_size,
                    'inner_rar_count': rar_info.inner_rar_count,
                    'has_japanese_tags': rar_info.has_japanese_tags,
                    'series_name': rar_info.series_name,
                }
                for rar_info in self.rar_files
                if rar_info.needs_cleaning
            ]
            report['files_needing_processing'] = nested_files

        # 保存到文件
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"报告已保存到: {output_path}")

        return report

    def print_summary(self) -> None:
        """打印摘要报告"""
        print("\n" + "=" * 80)
        print("RAR文件探测报告")
        print("=" * 80)
        print(f"目标目录: {self.target_dir}")
        print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n统计信息:")
        print(f"  总RAR文件数: {self.stats['total_rar_files']}")
        print(f"  嵌套RAR文件数: {self.stats['nested_rar_files']}")
        print(f"  最大嵌套层级: {self.stats['max_nesting_level']}")
        print(f"  总大小: {self._format_size(self.stats['total_size'])}")
        print(f"  包含日文标记: {self.stats['files_with_japanese_tags']}")
        print(f"  需要处理的文件: {self.stats['files_needing_cleaning']}")
        print(f"  分析错误数: {self.stats['analysis_errors']}")

        if self.file_type_stats:
            print("\n内部文件类型分布:")
            for file_type, count in sorted(self.file_type_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {file_type or '(无扩展名)'}: {count}")

        # 显示示例文件
        if self.rar_files:
            print("\n嵌套RAR示例（前5个）:")
            nested_examples = [f for f in self.rar_files if f.is_nested][:5]
            for idx, rar_info in enumerate(nested_examples, 1):
                print(f"\n  [{idx}] {Path(rar_info.file_path).name}")
                print(f"      路径: {rar_info.file_path}")
                print(f"      大小: {self._format_size(rar_info.file_size)}")
                print(f"      内部RAR数: {rar_info.inner_rar_count}")
                print(f"      内部文件数: {rar_info.total_inner_files}")
                if rar_info.has_japanese_tags:
                    print(f"      日文标记: {', '.join(rar_info.japanese_tags)}")
                if rar_info.series_name:
                    print(f"      系列名: {rar_info.series_name}")
                if rar_info.volume_info:
                    print(f"      卷号: {rar_info.volume_info}")

        print("\n" + "=" * 80)

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
    parser = argparse.ArgumentParser(description='RAR文件结构探测工具')
    parser.add_argument('--dir', '-d', required=True, help='目标目录路径')
    parser.add_argument('--mode', '-m', choices=['simple', 'detailed'], default='simple',
                        help='报告模式: simple(简单) 或 detailed(详细)')
    parser.add_argument('--output', '-o', help='输出JSON报告文件路径')
    parser.add_argument('--max-depth', type=int, default=10, help='最大嵌套深度（默认10）')
    parser.add_argument('--max-files', '-n', type=int, help='最大扫描文件数（用于测试）')

    args = parser.parse_args()

    # 创建探测器
    inspector = RARInspector(args.dir, max_depth=args.max_depth, max_files=args.max_files)

    # 扫描目录
    inspector.scan_directory()

    # 打印摘要
    inspector.print_summary()

    # 生成报告
    if args.output:
        inspector.generate_report(output_file=args.output, mode=args.mode)

    logger.info("探测完成")


if __name__ == '__main__':
    main()
