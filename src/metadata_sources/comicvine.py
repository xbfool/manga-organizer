#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComicVine API客户端（重构版）
"""

import requests
import time
import logging
import re
from typing import Optional
from .base import MetadataSource, MangaMetadata

logger = logging.getLogger(__name__)


class ComicVineSource(MetadataSource):
    """ComicVine API数据源（美漫）"""

    API_URL = "https://comicvine.gamespot.com/api"

    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = config.get('api_key') if config else None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MangaOrganizer/1.0'})
        self.rate_limit_delay = 1

    def search(self, title: str, **kwargs) -> Optional[MangaMetadata]:
        """搜索漫画"""

        if not self.api_key:
            logger.warning("ComicVine API密钥未配置")
            return None

        try:
            search_url = f"{self.API_URL}/search/"
            params = {
                'api_key': self.api_key,
                'format': 'json',
                'query': title,
                'resources': 'volume',
                'limit': 1
            }

            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data['status_code'] != 1:
                logger.error(f"ComicVine API错误: {data.get('error')}")
                return None

            results = data.get('results', [])
            if not results:
                logger.info(f"ComicVine: 未找到 '{title}'")
                return None

            # 获取详细信息
            volume_id = results[0]['id']
            return self.get_by_id(str(volume_id))

        except Exception as e:
            logger.error(f"ComicVine搜索失败 '{title}': {e}")
            return None

    def get_by_id(self, volume_id: str) -> Optional[MangaMetadata]:
        """通过ID获取详细信息"""

        try:
            detail_url = f"{self.API_URL}/volume/4050-{volume_id}/"
            params = {
                'api_key': self.api_key,
                'format': 'json'
            }

            response = self.session.get(detail_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            volume = data.get('results', {})

            metadata = self._parse_volume(volume)
            time.sleep(self.rate_limit_delay)
            return metadata

        except Exception as e:
            logger.error(f"ComicVine获取失败 ID={volume_id}: {e}")
            return None

    def _parse_volume(self, volume: dict) -> MangaMetadata:
        """解析volume数据"""
        metadata = MangaMetadata()

        metadata.title_english = volume.get('name')

        # 创作者
        persons = volume.get('people', [])
        for person in persons:
            name = person.get('name')
            if name:
                metadata.authors.append(name)

        # 出版社
        publisher = volume.get('publisher')
        if publisher:
            metadata.publisher = publisher.get('name')

        metadata.year = volume.get('start_year')
        metadata.volumes = volume.get('count_of_issues')

        # 简介
        description = volume.get('description')
        if description:
            description = re.sub(r'<[^>]+>', '', description)
            metadata.summary_en = description.strip()

        metadata.cover_url = volume.get('image', {}).get('medium_url')
        metadata.source = 'ComicVine'
        metadata.source_id = str(volume.get('id'))
        metadata.language = 'en'

        return metadata
