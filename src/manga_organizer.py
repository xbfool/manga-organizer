#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
漫画收藏标准化整理工具
功能：扫描、分析、转换、重组漫画文件
"""

import os
import re
import shutil
import zipfile
import rarfile
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# 配置UnRAR工具路径
rarfile.UNRAR_TOOL = r"C:\Program Files\UnRAR\UnRAR.exe"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('manga_organizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class MangaFile:
    """漫画文件信息"""
    original_path: str
    file_name: str
    file_size: int
    file_type: str  # zip, rar, cbz, cbr, pdf
    category: str  # 日漫, 美漫, 港漫, 连环画
    language: Optional[str] = None  # 中文版, 日文版, 双语版
    series_name: Optional[str] = None
    volume: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    needs_conversion: bool = False
    target_path: Optional[str] = None
    processed: bool = False
    error: Optional[str] = None


class MangaOrganizer:
    """漫画整理器主类"""

    # 支持的文件格式
    SUPPORTED_FORMATS = {'.zip', '.rar', '.cbz', '.cbr', '.pdf', '.7z'}

    # 分类关键词
    CATEGORY_KEYWORDS = {
        '日漫': ['日漫', '日本', 'japanese', 'manga', 'jp'],
        '美漫': ['美漫', '美国', 'american', 'comics', 'marvel', 'dc'],
        '港漫': ['港漫', '香港', 'hongkong', 'hk'],
        '连环画': ['连环画', '小人书']
    }

    # 语言版本关键词
    LANGUAGE_KEYWORDS = {
        '中文版': ['中文', '中译', '汉化', 'chinese', 'cn'],
        '日文版': ['日文', '日语', '原版', 'japanese', 'jp', 'raw'],
        '双语版': ['双语', '中日', '合版', 'bilingual']
    }

    def __init__(self, source_dir: str, target_dir: str = '漫画-已整理'):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(source_dir) / target_dir
        self.temp_dir = Path(source_dir) / '.temp_conversion'
        self.manga_files: List[MangaFile] = []
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'converted': 0,
            'errors': 0,
            'skipped': 0
        }

    def scan_files(self) -> List[MangaFile]:
        """扫描所有漫画文件"""
        logger.info(f"开始扫描目录: {self.source_dir}")

        manga_files = []
        for root, dirs, files in os.walk(self.source_dir):
            # 跳过目标目录和临时目录
            if self.target_dir.name in root or '.temp' in root:
                continue

            for file in files:
                file_path = Path(root) / file
                file_ext = file_path.suffix.lower()

                if file_ext in self.SUPPORTED_FORMATS:
                    try:
                        manga_file = self._analyze_file(file_path)
                        manga_files.append(manga_file)
                    except Exception as e:
                        logger.error(f"分析文件失败 {file_path}: {e}")

        self.manga_files = manga_files
        self.stats['total_files'] = len(manga_files)
        logger.info(f"扫描完成，共找到 {len(manga_files)} 个文件")
        return manga_files

    def _analyze_file(self, file_path: Path) -> MangaFile:
        """分析单个文件"""
        file_name = file_path.name
        file_size = file_path.stat().st_size
        file_type = file_path.suffix.lower().replace('.', '')

        # 判断分类
        category = self._detect_category(file_path)

        # 判断语言版本
        language = self._detect_language(file_path)

        # 提取系列名、卷号等信息
        series_name, volume = self._extract_series_info(file_name)

        # 提取作者信息
        author = self._extract_author(file_path)

        # 判断是否需要转换
        needs_conversion = file_type in ['rar', 'cbr', 'zip']

        return MangaFile(
            original_path=str(file_path),
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            category=category,
            language=language,
            series_name=series_name,
            volume=volume,
            author=author,
            needs_conversion=needs_conversion
        )

    def _detect_category(self, file_path: Path) -> str:
        """检测漫画分类"""
        path_str = str(file_path).lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in path_str:
                    return category

        return '未分类'

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """检测语言版本"""
        path_str = str(file_path).lower()

        for language, keywords in self.LANGUAGE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in path_str:
                    return language

        return None

    def _extract_series_info(self, file_name: str) -> Tuple[Optional[str], Optional[str]]:
        """提取系列名和卷号"""
        # 常见模式匹配
        patterns = [
            r'(.+?)[_\s-]+[Vv]ol[._\s]*(\d+)',
            r'(.+?)[_\s-]+第?(\d+)[卷集话]',
            r'(.+?)[_\s-]+(\d{2,3})',
            r'(.+?)[_\s]+(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, file_name)
            if match:
                series_name = match.group(1).strip()
                volume = match.group(2).zfill(3)  # 补零到3位
                return series_name, volume

        # 无法提取，返回文件名（去扩展名）
        series_name = Path(file_name).stem
        return series_name, None

    def _extract_author(self, file_path: Path) -> Optional[str]:
        """提取作者信息"""
        # 从路径中查找可能的作者名
        path_parts = file_path.parts

        # 检查是否在"名人"目录下
        if '名人' in path_parts:
            idx = path_parts.index('名人')
            if idx + 1 < len(path_parts):
                return path_parts[idx + 1]

        # 尝试从文件名中提取 【作者】格式
        match = re.search(r'【([^】]+)】', file_path.name)
        if match:
            return match.group(1)

        return None

    def convert_format(self, manga_file: MangaFile, target_format: str = 'cbz') -> bool:
        """转换压缩格式（真实转换，不是重命名）"""
        try:
            source_path = Path(manga_file.original_path)

            # 如果已经是目标格式，只需要重命名
            if manga_file.file_type == target_format:
                return True

            # 创建临时目录
            self.temp_dir.mkdir(exist_ok=True)
            temp_extract = self.temp_dir / f"extract_{source_path.stem}"
            temp_extract.mkdir(exist_ok=True)

            logger.info(f"转换格式: {manga_file.file_name} ({manga_file.file_type} -> {target_format})")

            # 解压原文件
            if manga_file.file_type in ['rar', 'cbr']:
                with rarfile.RarFile(source_path, 'r') as rf:
                    rf.extractall(temp_extract)
            elif manga_file.file_type in ['zip', 'cbz']:
                with zipfile.ZipFile(source_path, 'r') as zf:
                    zf.extractall(temp_extract)
            else:
                logger.warning(f"不支持的格式: {manga_file.file_type}")
                return False

            # 创建新的cbz文件
            target_path = temp_extract.parent / f"{source_path.stem}.cbz"
            with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(temp_extract):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_extract)
                        zf.write(file_path, arcname)

            # 更新文件信息
            manga_file.original_path = str(target_path)
            manga_file.file_type = target_format
            manga_file.file_name = target_path.name

            # 清理临时文件
            shutil.rmtree(temp_extract)

            self.stats['converted'] += 1
            return True

        except Exception as e:
            logger.error(f"格式转换失败 {manga_file.file_name}: {e}")
            manga_file.error = str(e)
            self.stats['errors'] += 1
            return False

    def generate_target_path(self, manga_file: MangaFile) -> Path:
        """生成目标路径"""
        # 根据分类生成路径
        if manga_file.category == '日漫':
            if manga_file.language:
                base_path = self.target_dir / '日漫' / manga_file.language
            else:
                base_path = self.target_dir / '日漫' / '未分类'

            # 按作者分类
            if manga_file.author:
                base_path = base_path / manga_file.author

            # 按系列分类
            if manga_file.series_name:
                base_path = base_path / manga_file.series_name

        elif manga_file.category == '美漫':
            # 美漫按系列分类
            base_path = self.target_dir / '美漫' / '未分类'
            if manga_file.series_name:
                base_path = self.target_dir / '美漫' / manga_file.series_name

        elif manga_file.category == '港漫':
            base_path = self.target_dir / '港漫'
            if manga_file.series_name:
                base_path = base_path / manga_file.series_name

        elif manga_file.category == '连环画':
            base_path = self.target_dir / '连环画'
            if manga_file.series_name:
                base_path = base_path / manga_file.series_name

        else:
            base_path = self.target_dir / '未分类'

        # 生成标准化文件名: 作品名 - 卷号 - 标题.cbz
        if manga_file.volume:
            file_name = f"{manga_file.series_name} - {manga_file.volume}.cbz"
        else:
            file_name = f"{manga_file.series_name}.cbz"

        return base_path / file_name

    def organize_file(self, manga_file: MangaFile, dry_run: bool = False) -> bool:
        """整理单个文件"""
        try:
            # 生成目标路径
            target_path = self.generate_target_path(manga_file)
            manga_file.target_path = str(target_path)

            if dry_run:
                logger.info(f"[预演] {manga_file.file_name} -> {target_path}")
                return True

            # 创建目标目录
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 转换格式（如需要）
            if manga_file.needs_conversion and manga_file.file_type != 'cbz':
                if not self.convert_format(manga_file):
                    return False

            # 复制文件到目标位置
            source_path = Path(manga_file.original_path)
            shutil.copy2(source_path, target_path)

            manga_file.processed = True
            self.stats['processed'] += 1
            logger.info(f"已处理: {manga_file.file_name} -> {target_path}")

            return True

        except Exception as e:
            logger.error(f"整理文件失败 {manga_file.file_name}: {e}")
            manga_file.error = str(e)
            self.stats['errors'] += 1
            return False

    def organize_all(self, dry_run: bool = False, batch_size: int = 100):
        """整理所有文件"""
        logger.info(f"开始整理，共 {len(self.manga_files)} 个文件")

        if dry_run:
            logger.info("=== 预演模式 ===")

        for i, manga_file in enumerate(self.manga_files):
            if i > 0 and i % batch_size == 0:
                logger.info(f"进度: {i}/{len(self.manga_files)}")

            self.organize_file(manga_file, dry_run=dry_run)

        logger.info("整理完成")
        self.print_stats()

    def print_stats(self):
        """打印统计信息"""
        logger.info("=== 整理统计 ===")
        logger.info(f"总文件数: {self.stats['total_files']}")
        logger.info(f"已处理: {self.stats['processed']}")
        logger.info(f"已转换: {self.stats['converted']}")
        logger.info(f"错误: {self.stats['errors']}")
        logger.info(f"跳过: {self.stats['skipped']}")

    def save_report(self, output_file: str = 'manga_report.json'):
        """保存整理报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'files': [asdict(f) for f in self.manga_files]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"报告已保存: {output_file}")

    def mark_processed_directories(self):
        """标记已处理的目录"""
        processed_dirs = set()

        for manga_file in self.manga_files:
            if manga_file.processed:
                original_dir = Path(manga_file.original_path).parent
                processed_dirs.add(original_dir)

        for dir_path in processed_dirs:
            new_name = f"[已处理]{dir_path.name}"
            new_path = dir_path.parent / new_name

            try:
                if not new_path.exists():
                    dir_path.rename(new_path)
                    logger.info(f"已标记目录: {dir_path} -> {new_path}")
            except Exception as e:
                logger.error(f"标记目录失败 {dir_path}: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("漫画收藏标准化整理工具")
    print("=" * 60)

    # 初始化
    source_dir = os.getcwd()
    organizer = MangaOrganizer(source_dir)

    # 扫描文件
    print("\n[1/4] 正在扫描文件...")
    organizer.scan_files()

    # 生成分析报告
    print("\n[2/4] 生成分析报告...")
    organizer.save_report('manga_analysis.json')

    # 询问是否继续
    print(f"\n找到 {organizer.stats['total_files']} 个文件")
    print(f"目标目录: {organizer.target_dir}")
    choice = input("\n是否开始整理？(y=开始/d=预演/n=取消) [d]: ").strip().lower()

    if choice == 'n':
        print("已取消")
        return

    dry_run = choice != 'y'

    # 开始整理
    print("\n[3/4] 开始整理文件...")
    organizer.organize_all(dry_run=dry_run)

    # 保存最终报告
    print("\n[4/4] 保存最终报告...")
    organizer.save_report('manga_final_report.json')

    # 标记已处理目录
    if not dry_run:
        print("\n标记已处理的目录...")
        organizer.mark_processed_directories()

    print("\n完成！")


if __name__ == '__main__':
    main()
