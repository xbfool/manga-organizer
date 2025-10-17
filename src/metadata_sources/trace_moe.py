#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trace.moe AniList代理客户端
提供中文翻译的AniList数据
"""

import requests
import time
import logging
from typing import Optional
from .base import MetadataSource, MangaMetadata

logger = logging.getLogger(__name__)


class TraceMoeSource(MetadataSource):
    """trace.moe AniList代理（中文翻译）"""

    # 使用trace.moe提供的AniList代理
    API_URL = "https://trace.moe/anilist/"

    def __init__(self, config=None):
        super().__init__(config)
        self.session = requests.Session()
        self.rate_limit_delay = 1

    def search(self, title: str, **kwargs) -> Optional[MangaMetadata]:
        """
        搜索漫画（使用GraphQL）

        Args:
            title: 漫画标题
            **kwargs: 其他参数

        Returns:
            MangaMetadata或None
        """

        query = '''
        query ($search: String) {
            Media (search: $search, type: MANGA) {
                id
                title {
                    romaji
                    english
                    native
                    chinese
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
                                native
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

        variables = {
            'search': title
        }

        try:
            response = self.session.post(
                self.API_URL,
                json={'query': query, 'variables': variables},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if 'errors' in data:
                logger.error(f"trace.moe API错误: {data['errors']}")
                return None

            media = data.get('data', {}).get('Media')
            if not media:
                logger.info(f"trace.moe: 未找到 '{title}'")
                return None

            metadata = self._parse_media(media)

            time.sleep(self.rate_limit_delay)
            return metadata

        except Exception as e:
            logger.error(f"trace.moe搜索失败 '{title}': {e}")
            return None

    def get_by_id(self, anilist_id: str) -> Optional[MangaMetadata]:
        """
        通过AniList ID获取

        Args:
            anilist_id: AniList ID

        Returns:
            MangaMetadata或None
        """

        query = '''
        query ($id: Int) {
            Media (id: $id, type: MANGA) {
                id
                title {
                    romaji
                    english
                    native
                    chinese
                }
                startDate {
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
                                native
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
            variables = {'id': int(anilist_id)}

            response = self.session.post(
                self.API_URL,
                json={'query': query, 'variables': variables},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            media = data.get('data', {}).get('Media')

            if not media:
                return None

            return self._parse_media(media)

        except Exception as e:
            logger.error(f"trace.moe获取失败 ID={anilist_id}: {e}")
            return None

    def _parse_media(self, media: dict) -> MangaMetadata:
        """解析media数据"""

        metadata = MangaMetadata()

        # 标题（包含中文！）
        titles = media.get('title', {})
        metadata.title_zh = titles.get('chinese')  # 中文标题
        metadata.title_native = titles.get('native')  # 日文
        metadata.title_romaji = titles.get('romaji')  # 罗马音
        metadata.title_english = titles.get('english')  # 英文

        # 创作者
        staff_edges = media.get('staff', {}).get('edges', [])
        for edge in staff_edges:
            role = edge.get('role', '').lower()
            node = edge.get('node', {})
            name = node.get('name', {}).get('full')

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

        # 卷数章节
        metadata.volumes = media.get('volumes')
        metadata.chapters = media.get('chapters')

        # 标签
        metadata.genres = media.get('genres', [])

        # 简介（可能包含HTML）
        description = media.get('description')
        if description:
            # 简单清理HTML
            import re
            description = re.sub(r'<br\s*/?>', '\n', description)
            description = re.sub(r'<[^>]+>', '', description)
            metadata.summary_en = description.strip()

        # 评分（0-100转为0-10）
        score = media.get('averageScore')
        if score:
            metadata.rating = score / 10.0

        # 状态
        status = media.get('status')
        status_map = {
            'FINISHED': '已完结',
            'RELEASING': '连载中',
            'NOT_YET_RELEASED': '未发布',
            'CANCELLED': '已取消'
        }
        metadata.status = status_map.get(status, status)

        # 封面
        cover = media.get('coverImage', {})
        metadata.cover_url = cover.get('large')

        # 元信息
        metadata.source = 'trace.moe/AniList'
        metadata.source_id = str(media.get('id'))
        metadata.language = 'zh' if metadata.title_zh else 'ja'

        return metadata

    def is_available(self) -> bool:
        """检查API是否可用"""
        try:
            response = self.session.post(
                self.API_URL,
                json={'query': '{ Media(id: 1) { id } }'},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
