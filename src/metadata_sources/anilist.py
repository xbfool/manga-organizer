#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AniList API客户端（重构版）
"""

import requests
import time
import logging
import re
from typing import Optional
from .base import MetadataSource, MangaMetadata

logger = logging.getLogger(__name__)


class AniListSource(MetadataSource):
    """AniList API数据源"""

    API_URL = "https://graphql.anilist.co"

    def __init__(self, config=None):
        super().__init__(config)
        self.session = requests.Session()
        self.rate_limit_delay = 1

    def search(self, title: str, **kwargs) -> Optional[MangaMetadata]:
        """搜索漫画"""

        query = '''
        query ($search: String) {
            Media (search: $search, type: MANGA) {
                id
                title {
                    romaji
                    english
                    native
                }
                startDate {
                    year
                    month
                    day
                }
                endDate {
                    year
                    month
                    day
                }
                volumes
                chapters
                staff {
                    edges {
                        role
                        node {
                            name {
                                full
                            }
                        }
                    }
                }
                genres
                description
                coverImage {
                    large
                }
                averageScore
                status
            }
        }
        '''

        try:
            variables = {'search': title}
            response = self.session.post(
                self.API_URL,
                json={'query': query, 'variables': variables},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            if 'errors' in data:
                logger.error(f"AniList API错误: {data['errors']}")
                return None

            media = data.get('data', {}).get('Media')
            if not media:
                logger.info(f"AniList: 未找到 '{title}'")
                return None

            metadata = self._parse_media(media)
            time.sleep(self.rate_limit_delay)
            return metadata

        except Exception as e:
            logger.error(f"AniList搜索失败 '{title}': {e}")
            return None

    def get_by_id(self, anilist_id: str) -> Optional[MangaMetadata]:
        """通过ID获取"""
        # 实现与search类似，使用id查询
        pass

    def _parse_media(self, media: dict) -> MangaMetadata:
        """解析media数据"""
        metadata = MangaMetadata()

        # 标题
        titles = media.get('title', {})
        metadata.title_native = titles.get('native')
        metadata.title_romaji = titles.get('romaji')
        metadata.title_english = titles.get('english')

        # 创作者
        staff_edges = media.get('staff', {}).get('edges', [])
        for edge in staff_edges:
            role = edge.get('role', '').lower()
            name = edge.get('node', {}).get('name', {}).get('full')
            if name:
                if 'story' in role or 'original' in role:
                    metadata.authors.append(name)
                elif 'art' in role:
                    metadata.artists.append(name)

        # 日期
        start_date = media.get('startDate', {})
        if start_date:
            metadata.year = start_date.get('year')
            metadata.month = start_date.get('month')

        metadata.volumes = media.get('volumes')
        metadata.chapters = media.get('chapters')
        metadata.genres = media.get('genres', [])

        # 简介
        description = media.get('description')
        if description:
            description = re.sub(r'<br\s*/?>', '\n', description)
            description = re.sub(r'<[^>]+>', '', description)
            metadata.summary_en = description.strip()

        # 评分
        score = media.get('averageScore')
        if score:
            metadata.rating = score / 10.0

        metadata.cover_url = media.get('coverImage', {}).get('large')
        metadata.source = 'AniList'
        metadata.source_id = str(media.get('id'))
        metadata.language = 'ja'

        return metadata
