#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComicInfo.xml生成器
符合Anansi Project v2.0标准，兼容Komga
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import zipfile
import logging
from pathlib import Path
from typing import Optional
from metadata_sources.base import MangaMetadata

logger = logging.getLogger(__name__)


class ComicInfoGenerator:
    """ComicInfo.xml生成器"""

    def generate(self, metadata: MangaMetadata, volume_num: int = None,
                 total_volumes: int = None) -> str:
        """
        生成ComicInfo.xml内容

        Args:
            metadata: 漫画元数据
            volume_num: 当前卷号
            total_volumes: 总卷数

        Returns:
            XML字符串
        """

        root = ET.Element("ComicInfo")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")

        # 系列信息
        title = metadata.get_best_title()
        if title:
            self._add_element(root, "Series", title)

        if volume_num is not None:
            self._add_element(root, "Number", str(volume_num))

        if total_volumes or metadata.volumes:
            count = total_volumes or metadata.volumes
            self._add_element(root, "Count", str(count))

        # 创作者
        if metadata.authors:
            self._add_element(root, "Writer", ", ".join(metadata.authors))

        if metadata.artists:
            self._add_element(root, "Penciller", ", ".join(metadata.artists))

        if metadata.translators:
            self._add_element(root, "Translator", ", ".join(metadata.translators))

        # 出版信息
        if metadata.publisher:
            self._add_element(root, "Publisher", metadata.publisher)

        if metadata.year:
            self._add_element(root, "Year", str(metadata.year))

        if metadata.month:
            self._add_element(root, "Month", str(metadata.month))

        # 内容描述
        summary = metadata.get_best_summary()
        if summary:
            self._add_element(root, "Summary", summary)

        if metadata.genres:
            self._add_element(root, "Genre", ", ".join(metadata.genres))

        # 漫画特定
        self._add_element(root, "Manga", "Yes")

        # 语言（ISO 639-1）
        language_code = self._get_language_code(metadata.language or 'zh')
        self._add_element(root, "LanguageISO", language_code)

        # 评分（转换为社区评分格式：0-5）
        if metadata.rating:
            # 假设rating是0-10，转换为0-5
            community_rating = metadata.rating / 2.0
            self._add_element(root, "CommunityRating", f"{community_rating:.2f}")

        # 标签
        if metadata.tags:
            self._add_element(root, "Tags", ", ".join(metadata.tags))

        # 元数据来源（作为Notes）
        if metadata.source:
            notes = f"Metadata from {metadata.source}"
            if metadata.source_id:
                notes += f" (ID: {metadata.source_id})"
            self._add_element(root, "Notes", notes)

        # 格式化XML
        return self._prettify(root)

    def _add_element(self, parent: ET.Element, tag: str, text: str):
        """添加子元素"""
        if text:
            elem = ET.SubElement(parent, tag)
            elem.text = str(text)

    def _get_language_code(self, language: str) -> str:
        """获取ISO 639-1语言代码"""
        language_map = {
            'zh': 'zh',
            'ja': 'ja',
            'en': 'en',
            'ko': 'ko',
            'chinese': 'zh',
            'japanese': 'ja',
            'english': 'en',
            'korean': 'ko'
        }
        return language_map.get(language.lower(), 'zh')

    def _prettify(self, elem: ET.Element) -> str:
        """格式化XML"""
        rough_string = ET.tostring(elem, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')

    def embed_into_cbz(self, cbz_path: Path, comicinfo_xml: str) -> bool:
        """
        将ComicInfo.xml嵌入CBZ文件

        Args:
            cbz_path: CBZ文件路径
            comicinfo_xml: ComicInfo.xml内容

        Returns:
            是否成功
        """
        try:
            # CBZ本质上是ZIP文件
            temp_path = cbz_path.with_suffix('.tmp')

            # 读取原文件，添加ComicInfo.xml
            with zipfile.ZipFile(cbz_path, 'r') as zip_read:
                with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zip_write:
                    # 复制所有现有文件（跳过旧的ComicInfo.xml）
                    for item in zip_read.infolist():
                        if item.filename != 'ComicInfo.xml':
                            data = zip_read.read(item.filename)
                            zip_write.writestr(item, data)

                    # 添加新的ComicInfo.xml到根目录
                    zip_write.writestr('ComicInfo.xml', comicinfo_xml.encode('utf-8'))

            # 替换原文件
            temp_path.replace(cbz_path)
            logger.info(f"已嵌入ComicInfo.xml: {cbz_path.name}")
            return True

        except Exception as e:
            logger.error(f"嵌入ComicInfo.xml失败 {cbz_path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return False

    def extract_from_cbz(self, cbz_path: Path) -> Optional[str]:
        """
        从CBZ提取ComicInfo.xml

        Args:
            cbz_path: CBZ文件路径

        Returns:
            ComicInfo.xml内容或None
        """
        try:
            with zipfile.ZipFile(cbz_path, 'r') as zf:
                if 'ComicInfo.xml' in zf.namelist():
                    return zf.read('ComicInfo.xml').decode('utf-8')
            return None

        except Exception as e:
            logger.error(f"提取ComicInfo.xml失败 {cbz_path}: {e}")
            return None

    def create_series_comicinfo(self, metadata: MangaMetadata, output_path: Path) -> bool:
        """
        创建系列级ComicInfo.xml文件

        Args:
            metadata: 系列元数据
            output_path: 输出路径（系列目录）

        Returns:
            是否成功
        """
        try:
            comicinfo_xml = self.generate(metadata)
            comicinfo_path = output_path / "ComicInfo.xml"

            with open(comicinfo_path, 'w', encoding='utf-8') as f:
                f.write(comicinfo_xml)

            logger.info(f"已创建系列ComicInfo.xml: {comicinfo_path}")
            return True

        except Exception as e:
            logger.error(f"创建系列ComicInfo.xml失败: {e}")
            return False
