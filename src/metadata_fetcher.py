#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
漫画元数据获取模块
支持从多个API源获取漫画信息
"""

import requests
import json
import time
from typing import Optional, Dict, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MangaMetadata:
    """漫画元数据"""
    title: str
    title_english: Optional[str] = None
    title_romaji: Optional[str] = None
    author: Optional[str] = None
    artist: Optional[str] = None
    publisher: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    volumes: Optional[int] = None
    chapters: Optional[int] = None
    genres: List[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    source: Optional[str] = None  # API来源
    source_id: Optional[str] = None  # 源数据库ID


class AniListFetcher:
    """AniList API 查询器（日漫）"""

    API_URL = "https://graphql.anilist.co"

    def __init__(self):
        self.session = requests.Session()
        self.rate_limit_delay = 1  # 秒

    def search_manga(self, title: str) -> Optional[MangaMetadata]:
        """搜索漫画信息"""

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
                logger.error(f"AniList API错误: {data['errors']}")
                return None

            media = data.get('data', {}).get('Media')
            if not media:
                logger.warning(f"未找到漫画: {title}")
                return None

            # 提取作者信息
            author = None
            artist = None
            for edge in media.get('staff', {}).get('edges', []):
                role = edge.get('role', '').lower()
                name = edge.get('node', {}).get('name', {}).get('full')
                if 'story' in role or 'original' in role:
                    author = name
                elif 'art' in role:
                    artist = name

            # 格式化日期
            start_date = self._format_date(media.get('startDate'))
            end_date = self._format_date(media.get('endDate'))

            metadata = MangaMetadata(
                title=media['title'].get('native') or media['title'].get('romaji'),
                title_english=media['title'].get('english'),
                title_romaji=media['title'].get('romaji'),
                author=author,
                artist=artist,
                start_date=start_date,
                end_date=end_date,
                volumes=media.get('volumes'),
                chapters=media.get('chapters'),
                genres=media.get('genres', []),
                description=self._clean_html(media.get('description')),
                cover_url=media.get('coverImage', {}).get('large'),
                source='AniList',
                source_id=str(media.get('id'))
            )

            time.sleep(self.rate_limit_delay)
            return metadata

        except Exception as e:
            logger.error(f"AniList查询失败 '{title}': {e}")
            return None

    def _format_date(self, date_obj: Optional[Dict]) -> Optional[str]:
        """格式化日期对象"""
        if not date_obj:
            return None

        year = date_obj.get('year')
        month = date_obj.get('month')
        day = date_obj.get('day')

        if year:
            if month and day:
                return f"{year}-{month:02d}-{day:02d}"
            elif month:
                return f"{year}-{month:02d}"
            else:
                return str(year)
        return None

    def _clean_html(self, text: Optional[str]) -> Optional[str]:
        """清理HTML标签"""
        if not text:
            return None

        import re
        # 简单的HTML标签清理
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()


class ComicVineFetcher:
    """ComicVine API 查询器（美漫）"""

    API_URL = "https://comicvine.gamespot.com/api"

    def __init__(self, api_key: str):
        """
        初始化

        Args:
            api_key: ComicVine API密钥，从 https://comicvine.gamespot.com/api/ 获取
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MangaOrganizer/1.0'
        })
        self.rate_limit_delay = 1

    def search_comic(self, title: str) -> Optional[MangaMetadata]:
        """搜索漫画信息"""

        if not self.api_key:
            logger.error("ComicVine API密钥未配置")
            return None

        # 第一步：搜索系列
        search_url = f"{self.API_URL}/search/"
        params = {
            'api_key': self.api_key,
            'format': 'json',
            'query': title,
            'resources': 'volume',
            'limit': 1
        }

        try:
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data['status_code'] != 1:
                logger.error(f"ComicVine API错误: {data.get('error')}")
                return None

            results = data.get('results', [])
            if not results:
                logger.warning(f"未找到漫画: {title}")
                return None

            volume = results[0]

            # 第二步：获取详细信息
            volume_id = volume['id']
            detail_url = f"{self.API_URL}/volume/4050-{volume_id}/"
            params = {
                'api_key': self.api_key,
                'format': 'json',
                'field_list': 'name,start_year,publisher,count_of_issues,description,image,authors'
            }

            response = self.session.get(detail_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            volume_detail = data.get('results', {})

            # 提取作者信息
            authors = []
            if 'authors' in volume_detail and volume_detail['authors']:
                authors = [person['name'] for person in volume_detail['authors']]

            metadata = MangaMetadata(
                title=volume_detail.get('name'),
                publisher=volume_detail.get('publisher', {}).get('name') if volume_detail.get('publisher') else None,
                start_date=str(volume_detail.get('start_year')) if volume_detail.get('start_year') else None,
                volumes=volume_detail.get('count_of_issues'),
                description=self._clean_html(volume_detail.get('description')),
                cover_url=volume_detail.get('image', {}).get('medium_url'),
                author=', '.join(authors) if authors else None,
                source='ComicVine',
                source_id=str(volume_id)
            )

            time.sleep(self.rate_limit_delay)
            return metadata

        except Exception as e:
            logger.error(f"ComicVine查询失败 '{title}': {e}")
            return None

    def _clean_html(self, text: Optional[str]) -> Optional[str]:
        """清理HTML标签"""
        if not text:
            return None

        import re
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()


class MetadataFetcherManager:
    """元数据获取管理器"""

    def __init__(self, comicvine_api_key: Optional[str] = None):
        self.anilist = AniListFetcher()
        self.comicvine = ComicVineFetcher(comicvine_api_key) if comicvine_api_key else None

    def fetch_metadata(self, title: str, category: str = 'auto') -> Optional[MangaMetadata]:
        """
        获取漫画元数据

        Args:
            title: 漫画标题
            category: 分类 ('日漫', '美漫', 'auto')

        Returns:
            MangaMetadata对象或None
        """

        # 根据分类选择API
        if category == '日漫' or category == 'auto':
            logger.info(f"尝试从AniList查询: {title}")
            metadata = self.anilist.search_manga(title)
            if metadata:
                return metadata

        if category == '美漫' and self.comicvine:
            logger.info(f"尝试从ComicVine查询: {title}")
            metadata = self.comicvine.search_comic(title)
            if metadata:
                return metadata

        logger.warning(f"未找到元数据: {title}")
        return None

    def batch_fetch(self, titles: List[str], category: str = 'auto') -> Dict[str, Optional[MangaMetadata]]:
        """
        批量获取元数据

        Args:
            titles: 标题列表
            category: 分类

        Returns:
            标题到元数据的映射
        """
        results = {}

        for i, title in enumerate(titles):
            logger.info(f"处理 {i+1}/{len(titles)}: {title}")
            results[title] = self.fetch_metadata(title, category)

        return results


def main():
    """测试函数"""

    logging.basicConfig(level=logging.INFO)

    # 初始化管理器
    manager = MetadataFetcherManager()

    # 测试日漫查询
    print("=" * 60)
    print("测试1: 查询日漫 - 灌篮高手")
    print("=" * 60)

    metadata = manager.fetch_metadata("SLAM DUNK", category='日漫')
    if metadata:
        print(f"\n标题: {metadata.title}")
        print(f"英文标题: {metadata.title_english}")
        print(f"罗马音: {metadata.title_romaji}")
        print(f"作者: {metadata.author}")
        print(f"开始时间: {metadata.start_date}")
        print(f"结束时间: {metadata.end_date}")
        print(f"卷数: {metadata.volumes}")
        print(f"类型: {', '.join(metadata.genres) if metadata.genres else 'N/A'}")
        print(f"封面: {metadata.cover_url}")
        print(f"\n简介: {metadata.description[:200]}..." if metadata.description else "")

    print("\n" + "=" * 60)
    print("测试2: 查询日漫 - 神兵玄奇")
    print("=" * 60)

    metadata = manager.fetch_metadata("神兵玄奇", category='日漫')
    if metadata:
        print(f"\n标题: {metadata.title}")
        print(f"作者: {metadata.author}")
    else:
        print("未找到（港漫可能不在AniList数据库中）")

    # 如果有ComicVine API key，可以测试美漫
    # 获取key: https://comicvine.gamespot.com/api/

    print("\n" + "=" * 60)
    print("提示: 要查询美漫，需要在 https://comicvine.gamespot.com/api/ 注册获取API key")
    print("=" * 60)


if __name__ == '__main__':
    main()
