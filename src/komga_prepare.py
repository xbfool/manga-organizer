#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Komga准备工具
本地完成元数据获取和目录整理，输出Komga就绪的目录结构
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import shutil
import json
import zipfile
import tempfile
import rarfile

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置UnRAR工具路径
rarfile.UNRAR_TOOL = r"C:\Program Files\UnRAR\UnRAR.exe"

from metadata_sources import (
    MangaMetadata,
    BangumiSource,
    TraceMoeSource,
    AniListSource,
    ComicVineSource
)
from comicinfo_generator import ComicInfoGenerator
from cover_manager import CoverManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('komga_prepare.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class VolumeFile:
    """卷文件信息"""
    path: Path
    volume_num: int
    file_size: int


@dataclass
class SeriesInfo:
    """系列信息"""
    name: str
    category: str  # 日漫/美漫/港漫
    volumes: List[VolumeFile]
    metadata: Optional[MangaMetadata] = None


class KomgaPreparer:
    """Komga准备器"""

    def __init__(self, config: Dict):
        self.config = config
        self.output_dir = Path(config['output_dir'])
        self.language_priority = config.get('language_priority', ['zh', 'ja', 'romaji', 'en'])
        self.temp_dir = Path(config.get('temp_directory', '.temp_conversion'))

        # 初始化元数据源
        self.metadata_sources = []
        sources_config = config.get('metadata_sources', {})

        # Bangumi（中文）
        if sources_config.get('bangumi', {}).get('enabled', True):
            self.metadata_sources.append(BangumiSource())

        # trace.moe（中文翻译）
        if sources_config.get('trace_moe', {}).get('enabled', True):
            self.metadata_sources.append(TraceMoeSource())

        # AniList（日文/英文）
        if sources_config.get('anilist', {}).get('enabled', True):
            self.metadata_sources.append(AniListSource())

        # ComicVine（美漫）
        comicvine_config = sources_config.get('comicvine', {})
        if comicvine_config.get('enabled') and comicvine_config.get('api_key'):
            self.metadata_sources.append(ComicVineSource(comicvine_config))

        # 初始化工具
        self.comicinfo_gen = ComicInfoGenerator()
        self.cover_mgr = CoverManager()

        # 统计
        self.stats = {
            'total_series': 0,
            'processed_series': 0,
            'total_volumes': 0,
            'processed_volumes': 0,
            'metadata_found': 0,
            'metadata_not_found': 0,
            'converted': 0,
            'errors': 0
        }

    def prepare_all(self, source_dirs: List[str]):
        """
        准备所有漫画

        Args:
            source_dirs: 源目录列表
        """
        logger.info("=" * 60)
        logger.info("Komga准备工具")
        logger.info("=" * 60)

        # 扫描所有系列
        all_series = []
        for source_dir in source_dirs:
            series_list = self.scan_directory(Path(source_dir))
            all_series.extend(series_list)

        self.stats['total_series'] = len(all_series)
        self.stats['total_volumes'] = sum(len(s.volumes) for s in all_series)

        logger.info(f"\n找到 {len(all_series)} 个系列，共 {self.stats['total_volumes']} 卷")

        # 处理每个系列
        for i, series in enumerate(all_series, 1):
            logger.info(f"\n[{i}/{len(all_series)}] 处理: {series.name}")
            self.process_series(series)

        # 输出统计
        self.print_stats()

        # 生成传输清单
        self.generate_transfer_manifest()

    def scan_directory(self, source_dir: Path) -> List[SeriesInfo]:
        """
        扫描目录，识别系列

        Args:
            source_dir: 源目录

        Returns:
            系列列表
        """
        logger.info(f"扫描目录: {source_dir}")

        series_dict = {}

        # 递归查找所有漫画文件
        supported_formats = ['.cbz', '.cbr', '.zip', '.rar', '.7z', '.pdf']
        for file_path in source_dir.rglob('*'):
            if file_path.suffix.lower() in supported_formats:
                # 提取系列名（使用父目录名）
                raw_series_name = file_path.parent.name
                series_name = self._clean_series_name(raw_series_name)

                # 提取卷号
                volume_num = self._extract_volume_number(file_path.name)

                if series_name not in series_dict:
                    category = self._detect_category(file_path)
                    series_dict[series_name] = SeriesInfo(
                        name=series_name,
                        category=category,
                        volumes=[]
                    )

                series_dict[series_name].volumes.append(VolumeFile(
                    path=file_path,
                    volume_num=volume_num or 0,
                    file_size=file_path.stat().st_size
                ))

        # 排序卷
        for series in series_dict.values():
            series.volumes.sort(key=lambda v: v.volume_num)

        return list(series_dict.values())

    def process_series(self, series: SeriesInfo):
        """
        处理单个系列

        Args:
            series: 系列信息
        """
        try:
            # 1. 获取元数据
            metadata = self.fetch_metadata(series.name, series.category)
            series.metadata = metadata

            if metadata:
                self.stats['metadata_found'] += 1
                logger.info(f"  ✓ 获取元数据: {metadata.get_best_title()}")
            else:
                self.stats['metadata_not_found'] += 1
                logger.warning(f"  ✗ 未找到元数据")
                # 创建基础元数据
                metadata = MangaMetadata(title_zh=series.name)
                series.metadata = metadata

            # 2. 确定输出目录
            output_series_dir = self.get_output_dir(series, metadata)
            output_series_dir.mkdir(parents=True, exist_ok=True)

            # 3. 下载封面
            if metadata.cover_url:
                self.cover_mgr.save_as_series_cover(metadata.cover_url, output_series_dir)

            # 4. 处理每一卷
            for volume in series.volumes:
                self.process_volume(volume, series, metadata, output_series_dir)

            self.stats['processed_series'] += 1

        except Exception as e:
            logger.error(f"处理系列失败 {series.name}: {e}")
            self.stats['errors'] += 1

    def fetch_metadata(self, title: str, category: str) -> Optional[MangaMetadata]:
        """
        从多个源获取元数据

        Args:
            title: 标题
            category: 分类

        Returns:
            合并的元数据
        """
        final_metadata = None

        for source in self.metadata_sources:
            try:
                metadata = source.search(title)
                if metadata:
                    if final_metadata is None:
                        final_metadata = metadata
                    else:
                        final_metadata.merge(metadata)
            except Exception as e:
                logger.warning(f"  {source.source_name} 查询失败: {e}")

        return final_metadata

    def process_volume(self, volume: VolumeFile, series: SeriesInfo,
                       metadata: MangaMetadata, output_dir: Path):
        """
        处理单卷

        Args:
            volume: 卷文件
            series: 系列信息
            metadata: 元数据
            output_dir: 输出目录
        """
        try:
            # 生成标准文件名
            title = metadata.get_best_title(self.language_priority)
            if volume.volume_num > 0:
                filename = f"{title} v{volume.volume_num:02d}.cbz"
            else:
                filename = f"{title}.cbz"

            output_path = output_dir / filename

            # 检查是否需要处理
            if output_path.exists():
                logger.info(f"    跳过（已存在）: {filename}")
            else:
                # 转换文件为CBZ格式
                file_ext = volume.path.suffix.lower()
                if file_ext == '.pdf':
                    # PDF保持原样
                    output_path = output_path.with_suffix('.pdf')
                    logger.info(f"    复制PDF: {filename}")
                    shutil.copy2(volume.path, output_path)
                elif file_ext in ['.rar', '.cbr', '.7z']:
                    # 需要转换
                    logger.info(f"    转换: {filename}")
                    if not self._convert_to_cbz(volume.path, output_path):
                        logger.error(f"    转换失败: {filename}")
                        return
                    self.stats['converted'] += 1
                else:
                    # ZIP/CBZ直接复制
                    logger.info(f"    复制: {filename}")
                    if not self._convert_to_cbz(volume.path, output_path):
                        logger.error(f"    复制失败: {filename}")
                        return

            # 生成并嵌入ComicInfo.xml (仅CBZ格式)
            if output_path.suffix.lower() in ['.cbz', '.zip']:
                comicinfo_xml = self.comicinfo_gen.generate(
                    metadata,
                    volume_num=volume.volume_num,
                    total_volumes=len(series.volumes)
                )

                self.comicinfo_gen.embed_into_cbz(output_path, comicinfo_xml)

            self.stats['processed_volumes'] += 1

        except Exception as e:
            logger.error(f"    处理卷失败 {volume.path.name}: {e}")
            self.stats['errors'] += 1

    def get_output_dir(self, series: SeriesInfo, metadata: MangaMetadata) -> Path:
        """
        获取输出目录

        Args:
            series: 系列信息
            metadata: 元数据

        Returns:
            输出目录路径
        """
        # 根据分类和语言组织目录
        if series.category == '日漫':
            # 判断语言版本
            if metadata.language == 'zh' or metadata.title_zh:
                library = '日漫-中文版'
            elif metadata.language == 'ja':
                library = '日漫-日文版'
            else:
                library = '日漫-其他'

            # 按作者分类（如果有）
            if metadata.authors:
                author = metadata.authors[0]
                return self.output_dir / library / author / metadata.get_best_title(self.language_priority)
            else:
                return self.output_dir / library / metadata.get_best_title(self.language_priority)

        elif series.category == '美漫':
            return self.output_dir / '美漫' / metadata.get_best_title(self.language_priority)

        elif series.category == '港漫':
            return self.output_dir / '港漫' / metadata.get_best_title(self.language_priority)

        else:
            return self.output_dir / '其他' / metadata.get_best_title(self.language_priority)

    def _clean_series_name(self, name: str) -> str:
        """
        清理系列名，移除方括号标记

        Args:
            name: 原始系列名

        Returns:
            清理后的系列名

        Examples:
            神兵前传III[7][未] -> 神兵前传III
            灌篮高手[完] -> 灌篮高手
            海贼王 [1-100] -> 海贼王
        """
        import re

        # 移除方括号及其内容：[7][未]、[完]、[1-100] 等
        cleaned = re.sub(r'\s*\[[^\]]*\]', '', name)

        # 移除圆括号及其内容（可选，如果需要也清理圆括号）
        # cleaned = re.sub(r'\s*\([^\)]*\)', '', cleaned)

        # 清理多余的空格
        cleaned = ' '.join(cleaned.split())

        # 移除首尾空格
        cleaned = cleaned.strip()

        return cleaned

    def _extract_volume_number(self, filename: str) -> Optional[int]:
        """提取卷号"""
        import re

        patterns = [
            r'v(\d+)',
            r'vol[\._\s]*(\d+)',
            r'第(\d+)[卷集册]',
            r'[_\s](\d{2,3})[_\s\.]',
        ]

        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def _detect_category(self, file_path: Path) -> str:
        """检测分类"""
        path_str = str(file_path).lower()

        if any(k in path_str for k in ['日漫', 'japanese', 'manga', 'jp']):
            return '日漫'
        elif any(k in path_str for k in ['美漫', 'american', 'comics', 'marvel', 'dc']):
            return '美漫'
        elif any(k in path_str for k in ['港漫', 'hongkong', 'hk']):
            return '港漫'

        return '其他'

    def _convert_to_cbz(self, source_path: Path, target_path: Path) -> bool:
        """
        转换文件为CBZ格式

        Args:
            source_path: 源文件路径
            target_path: 目标CBZ路径

        Returns:
            是否成功
        """
        file_ext = source_path.suffix.lower()

        try:
            # ZIP格式直接重命名
            if file_ext == '.zip':
                shutil.copy2(source_path, target_path)
                return True

            # CBZ格式直接复制
            elif file_ext == '.cbz':
                shutil.copy2(source_path, target_path)
                return True

            # PDF格式保持不变
            elif file_ext == '.pdf':
                # PDF不转换，直接复制
                pdf_target = target_path.with_suffix('.pdf')
                shutil.copy2(source_path, pdf_target)
                return True

            # RAR/CBR/7z需要真实转换
            elif file_ext in ['.rar', '.cbr', '.7z']:
                return self._extract_and_repack(source_path, target_path)

            else:
                logger.warning(f"不支持的格式: {file_ext}")
                return False

        except Exception as e:
            logger.error(f"转换失败 {source_path}: {e}")
            return False

    def _extract_and_repack(self, source_path: Path, target_path: Path) -> bool:
        """
        解压RAR/CBR/7z并重新打包为CBZ

        Args:
            source_path: 源文件路径
            target_path: 目标CBZ路径

        Returns:
            是否成功
        """
        temp_extract_dir = None

        try:
            # 创建临时解压目录
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            temp_extract_dir = tempfile.mkdtemp(dir=self.temp_dir)
            temp_extract_path = Path(temp_extract_dir)

            # 解压文件
            logger.info(f"    解压: {source_path.name}")

            file_ext = source_path.suffix.lower()

            if file_ext in ['.rar', '.cbr']:
                # 解压RAR
                with rarfile.RarFile(source_path) as rf:
                    rf.extractall(temp_extract_path)

            elif file_ext == '.7z':
                # 解压7z (需要py7zr库)
                try:
                    import py7zr
                    with py7zr.SevenZipFile(source_path, mode='r') as z:
                        z.extractall(temp_extract_path)
                except ImportError:
                    logger.error("需要安装py7zr库: pip install py7zr")
                    return False

            # 重新打包为CBZ (ZIP)
            logger.info(f"    打包: {target_path.name}")
            with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file in sorted(temp_extract_path.rglob('*')):
                    if file.is_file():
                        # 使用相对路径
                        arcname = file.relative_to(temp_extract_path)
                        zf.write(file, arcname)

            return True

        except Exception as e:
            logger.error(f"解压重打包失败 {source_path}: {e}")
            return False

        finally:
            # 清理临时目录
            if temp_extract_dir and Path(temp_extract_dir).exists():
                try:
                    shutil.rmtree(temp_extract_dir)
                except Exception as e:
                    logger.warning(f"清理临时目录失败 {temp_extract_dir}: {e}")

    def print_stats(self):
        """打印统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("处理统计")
        logger.info("=" * 60)
        logger.info(f"系列总数: {self.stats['total_series']}")
        logger.info(f"已处理系列: {self.stats['processed_series']}")
        logger.info(f"卷总数: {self.stats['total_volumes']}")
        logger.info(f"已处理卷: {self.stats['processed_volumes']}")
        logger.info(f"格式转换: {self.stats['converted']}")
        logger.info(f"元数据找到: {self.stats['metadata_found']}")
        logger.info(f"元数据未找到: {self.stats['metadata_not_found']}")
        logger.info(f"错误: {self.stats['errors']}")
        logger.info("=" * 60)

    def generate_transfer_manifest(self):
        """生成传输清单"""
        manifest_path = self.output_dir / "TRANSFER_MANIFEST.txt"

        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("Komga传输清单\n")
                f.write("=" * 60 + "\n\n")

                f.write(f"输出目录: {self.output_dir}\n")
                f.write(f"系列数: {self.stats['processed_series']}\n")
                f.write(f"文件数: {self.stats['processed_volumes']}\n\n")

                f.write("传输命令示例:\n\n")

                f.write("# Windows → Linux (rsync)\n")
                f.write(f'rsync -avz --progress "{self.output_dir}/" user@server:/data/komga/comics/\n\n')

                f.write("# Windows共享\n")
                f.write(f'robocopy "{self.output_dir}" "\\\\server\\komga\\comics" /E /MT:8\n\n')

                f.write("# 直接拷贝到NAS\n")
                f.write(f'xcopy "{self.output_dir}" "\\\\NAS\\comics\\" /E /H /C /I\n\n')

                f.write("=" * 60 + "\n")

            logger.info(f"\n传输清单已生成: {manifest_path}")

        except Exception as e:
            logger.error(f"生成传输清单失败: {e}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Komga准备工具')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    args = parser.parse_args()

    # 读取配置
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    komga_config = config.get('komga_prepare', {})

    # 初始化准备器
    preparer = KomgaPreparer(komga_config)

    # 执行准备
    source_dirs = komga_config.get('source_dirs', [])
    preparer.prepare_all(source_dirs)

    logger.info("\n✓ 完成！")


if __name__ == '__main__':
    main()
