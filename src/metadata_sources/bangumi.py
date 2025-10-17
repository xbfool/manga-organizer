#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bangumi API客户端
中文元数据源
"""

import requests
import time
import logging
from typing import Optional
from .base import MetadataSource, MangaMetadata

logger = logging.getLogger(__name__)


class BangumiSource(MetadataSource):
    """Bangumi API数据源（中文优先）"""

    API_URL = "https://api.bgm.tv"

    # 漫画类型ID
    SUBJECT_TYPE_BOOK = 1

    def __init__(self, config=None):
        super().__init__(config)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'manga-organizer/1.0 (https://github.com/xbfool/manga-organizer)'
        })
        self.rate_limit_delay = 1  # 秒

    def search(self, title: str, **kwargs) -> Optional[MangaMetadata]:
        """
        搜索漫画

        Args:
            title: 漫画标题
            **kwargs: 其他参数

        Returns:
            MangaMetadata或None
        """
        try:
            # 搜索
            search_url = f"{self.API_URL}/search/subject/{title}"
            params = {
                'type': self.SUBJECT_TYPE_BOOK,  # 书籍类型
                'responseGroup': 'small'
            }

            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get('list', [])

            if not results:
                logger.info(f"Bangumi: 未找到 '{title}'")
                return None

            # 取第一个结果
            subject = results[0]
            subject_id = subject.get('id')

            # 获取详细信息
            return self.get_by_id(str(subject_id))

        except Exception as e:
            logger.error(f"Bangumi搜索失败 '{title}': {e}")
            return None

    def get_by_id(self, subject_id: str) -> Optional[MangaMetadata]:
        """
        通过ID获取详细信息

        Args:
            subject_id: Bangumi subject ID

        Returns:
            MangaMetadata或None
        """
        try:
            # 获取详细信息
            detail_url = f"{self.API_URL}/v0/subjects/{subject_id}"
            response = self.session.get(detail_url, timeout=10)
            response.raise_for_status()

            subject = response.json()

            # 解析元数据
            metadata = self._parse_subject(subject)

            time.sleep(self.rate_limit_delay)
            return metadata

        except Exception as e:
            logger.error(f"Bangumi获取详情失败 ID={subject_id}: {e}")
            return None

    def _parse_subject(self, subject: dict) -> MangaMetadata:
        """解析Bangumi subject数据"""

        metadata = MangaMetadata()

        # 标题
        metadata.title_zh = subject.get('name_cn') or subject.get('name')
        metadata.title_native = subject.get('name')  # 原名（可能是日文）

        # 创作者
        persons = subject.get('infobox', [])
        for item in persons:
            key = item.get('key', '').lower()
            value = item.get('value')

            if not value:
                continue

            # 处理值（可能是字符串或列表）
            if isinstance(value, list):
                names = [v.get('v', '') if isinstance(v, dict) else str(v) for v in value]
            else:
                names = [str(value)]

            # 根据key分类
            if '作者' in key or 'author' in key or '原作' in key:
                metadata.authors.extend(names)
            elif '作画' in key or 'artist' in key or '漫画' in key:
                metadata.artists.extend(names)
            elif '出版社' in key or 'publisher' in key:
                metadata.publisher = names[0] if names else None
            elif '话数' in key or 'chapter' in key:
                try:
                    metadata.chapters = int(names[0]) if names else None
                except:
                    pass
            elif '卷数' in key or 'volume' in key:
                try:
                    metadata.volumes = int(names[0]) if names else None
                except:
                    pass

        # 日期
        date_str = subject.get('date')  # 格式: YYYY-MM-DD
        if date_str:
            try:
                parts = date_str.split('-')
                metadata.year = int(parts[0]) if len(parts) > 0 else None
                metadata.month = int(parts[1]) if len(parts) > 1 else None
            except:
                pass

        # 简介
        summary = subject.get('summary')
        if summary:
            metadata.summary_zh = summary

        # 标签
        tags = subject.get('tags', [])
        metadata.tags = [tag.get('name', '') for tag in tags if tag.get('name')]

        # 评分
        rating = subject.get('rating', {})
        score = rating.get('score')
        if score:
            metadata.rating = float(score)

        # 封面
        images = subject.get('images', {})
        cover_url = images.get('large') or images.get('medium') or images.get('small')
        if cover_url:
            metadata.cover_url = cover_url

        # 元信息
        metadata.source = 'Bangumi'
        metadata.source_id = str(subject.get('id'))
        metadata.language = 'zh'

        return metadata

    def is_available(self) -> bool:
        """检查API是否可用"""
        try:
            response = self.session.get(f"{self.API_URL}/", timeout=5)
            return response.status_code == 200
        except:
            return False
