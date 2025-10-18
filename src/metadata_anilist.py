#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AniList元数据API客户端（备用）
https://anilist.co
"""

import requests
import time
import logging
from typing import Optional, Dict, Any, List
from metadata_bangumi import MangaMetadata

logger = logging.getLogger(__name__)


class AniListAPI:
    """AniList API客户端"""

    API_URL = "https://graphql.anilist.co"
    USER_AGENT = "manga-organizer/1.0"

    def __init__(self, rate_limit_delay: float = 1.0):
        """
        初始化API客户端

        Args:
            rate_limit_delay: 请求间隔（秒）
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _request(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """
        发送GraphQL请求

        Args:
            query: GraphQL查询
            variables: 查询变量

        Returns:
            响应数据
        """
        self._rate_limit()

        try:
            response = self.session.post(
                self.API_URL,
                json={'query': query, 'variables': variables or {}},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if 'errors' in data:
                logger.warning(f"AniList API错误: {data['errors']}")
                return None

            return data.get('data')
        except requests.exceptions.RequestException as e:
            logger.warning(f"AniList API请求失败: {e}")
            return None

    def search_manga(self, title: str) -> Optional[MangaMetadata]:
        """
        搜索漫画

        Args:
            title: 漫画标题

        Returns:
            元数据对象或None
        """
        logger.info(f"AniList搜索: {title}")

        query = '''
        query ($search: String, $type: MediaType) {
          Media(search: $search, type: $type, format: MANGA) {
            id
            title {
              romaji
              english
              native
            }
            description
            volumes
            chapters
            coverImage {
              large
              medium
            }
            staff {
              edges {
                node {
                  name {
                    full
                  }
                }
                role
              }
            }
            tags {
              name
            }
            startDate {
              year
              month
              day
            }
          }
        }
        '''

        variables = {
            'search': title,
            'type': 'MANGA'
        }

        data = self._request(query, variables)

        if not data or 'Media' not in data:
            logger.warning(f"AniList未找到结果: {title}")
            return None

        media = data['Media']

        # 解析元数据
        titles = media.get('title', {})
        title_en = titles.get('english')
        title_ja = titles.get('native')
        title_romaji = titles.get('romaji')

        # 提取作者
        author = None
        artist = None
        staff_edges = media.get('staff', {}).get('edges', [])
        for edge in staff_edges:
            role = edge.get('role', '').lower()
            name = edge.get('node', {}).get('name', {}).get('full')

            if 'story' in role or 'author' in role:
                author = name
            elif 'art' in role:
                artist = name

        # 如果没有artist，使用author
        if not artist and author:
            artist = author

        # 提取标签
        tags = [tag.get('name') for tag in media.get('tags', [])[:10]]

        # 提取日期
        start_date = media.get('startDate', {})
        publish_date = None
        if start_date.get('year'):
            year = start_date.get('year')
            month = start_date.get('month', 1)
            day = start_date.get('day', 1)
            publish_date = f"{year}-{month:02d}-{day:02d}"

        # 提取封面
        cover_image = media.get('coverImage', {})
        cover_url = cover_image.get('large') or cover_image.get('medium')

        metadata = MangaMetadata(
            title=title_romaji or title_en or title_ja or title,
            title_zh=None,  # AniList没有中文标题
            title_ja=title_ja,
            title_en=title_en,
            author=author,
            artist=artist,
            summary=media.get('description'),
            tags=tags if tags else None,
            total_volumes=media.get('volumes'),
            publish_date=publish_date,
            cover_url=cover_url,
            source="anilist",
            source_id=str(media.get('id'))
        )

        logger.info(f"AniList找到: {metadata.title}")

        return metadata
