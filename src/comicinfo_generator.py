#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComicInfo.xml生成器
用于Komga等漫画阅读器
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import zipfile
import logging
import re
from pathlib import Path
from typing import Optional
from metadata_bangumi import MangaMetadata

logger = logging.getLogger(__name__)


class ComicInfoGenerator:
    """ComicInfo.xml生成器"""

    @staticmethod
    def _add_element(parent: ET.Element, tag: str, text: Optional[str]):
        """
        添加XML元素

        Args:
            parent: 父元素
            tag: 标签名
            text: 文本内容
        """
        if text:
            element = ET.SubElement(parent, tag)
            element.text = str(text)

    @staticmethod
    def _prettify(elem: ET.Element) -> str:
        """
        格式化XML

        Args:
            elem: XML元素

        Returns:
            格式化后的XML字符串
        """
        rough_string = ET.tostring(elem, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')

    @classmethod
    def generate(cls, metadata: MangaMetadata, volume_number: Optional[int] = None) -> str:
        """
        生成ComicInfo.xml内容

        Args:
            metadata: 漫画元数据
            volume_number: 卷号（可选）

        Returns:
            XML字符串
        """
        root = ET.Element('ComicInfo')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')

        # 基本信息
        cls._add_element(root, 'Series', metadata.title_zh or metadata.title)

        if metadata.title_ja:
            cls._add_element(root, 'LocalizedSeries', metadata.title_ja)

        if metadata.title_en:
            cls._add_element(root, 'AlternateSeries', metadata.title_en)

        if volume_number:
            cls._add_element(root, 'Number', str(volume_number))
            cls._add_element(root, 'Volume', str(volume_number))

        if metadata.total_volumes:
            cls._add_element(root, 'Count', str(metadata.total_volumes))

        # 作者信息
        if metadata.author:
            cls._add_element(root, 'Writer', metadata.author)

        if metadata.artist:
            cls._add_element(root, 'Penciller', metadata.artist)
            cls._add_element(root, 'Inker', metadata.artist)
            cls._add_element(root, 'Colorist', metadata.artist)
            cls._add_element(root, 'CoverArtist', metadata.artist)

        # 出版信息
        if metadata.publisher:
            cls._add_element(root, 'Publisher', metadata.publisher)

        if metadata.publish_date:
            # 提取年月日
            parts = metadata.publish_date.split('-')
            if len(parts) >= 1:
                cls._add_element(root, 'Year', parts[0])
            if len(parts) >= 2:
                cls._add_element(root, 'Month', parts[1])
            if len(parts) >= 3:
                cls._add_element(root, 'Day', parts[2])

        # 简介
        if metadata.summary:
            # 移除HTML标签
            summary_clean = re.sub(r'<[^>]+>', '', metadata.summary)
            summary_clean = re.sub(r'\n+', '\n', summary_clean).strip()
            cls._add_element(root, 'Summary', summary_clean)

        # 标签
        if metadata.tags:
            cls._add_element(root, 'Tags', ', '.join(metadata.tags))

        # 语言
        cls._add_element(root, 'LanguageISO', 'ja')  # 日文

        # 类型
        cls._add_element(root, 'Manga', 'Yes')

        # 来源信息
        if metadata.source and metadata.source_id:
            notes = f"Source: {metadata.source}, ID: {metadata.source_id}"
            cls._add_element(root, 'Notes', notes)

        return cls._prettify(root)

    @classmethod
    def embed_into_cbz(cls, cbz_path: Path, comicinfo_xml: str) -> bool:
        """
        将ComicInfo.xml嵌入CBZ文件

        Args:
            cbz_path: CBZ文件路径
            comicinfo_xml: ComicInfo.xml内容

        Returns:
            是否成功
        """
        try:
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
