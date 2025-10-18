#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bangumi元数据API客户端
https://bangumi.tv / https://api.bgm.tv
"""

import requests
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MangaMetadata:
    """漫画元数据"""
    title: str  # 标题
    title_zh: Optional[str] = None  # 中文标题
    title_ja: Optional[str] = None  # 日文标题
    title_en: Optional[str] = None  # 英文标题
    author: Optional[str] = None  # 作者
    artist: Optional[str] = None  # 画师
    publisher: Optional[str] = None  # 出版社
    summary: Optional[str] = None  # 简介
    tags: Optional[List[str]] = None  # 标签
    total_volumes: Optional[int] = None  # 总卷数
    publish_date: Optional[str] = None  # 发布日期
    cover_url: Optional[str] = None  # 封面URL
    source: str = "bangumi"  # 来源
    source_id: Optional[str] = None  # 来源ID


class BangumiAPI:
    """Bangumi API客户端"""

    BASE_URL = "https://api.bgm.tv"
    USER_AGENT = "manga-organizer/1.0 (https://github.com/user/manga-organizer)"

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
            'Accept': 'application/json'
        })

    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        发送API请求

        Args:
            endpoint: API端点
            params: 请求参数

        Returns:
            响应数据
        """
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Bangumi API请求失败: {e}")
            return None

    def search(self, query: str, subject_type: int = 1) -> Optional[List[Dict[str, Any]]]:
        """
        搜索条目

        Args:
            query: 搜索关键词
            subject_type: 条目类型 (1=书籍/漫画, 2=动画, 3=音乐, 4=游戏, 6=真人)

        Returns:
            搜索结果列表
        """
        params = {
            'type': subject_type,
            'responseGroup': 'small'
        }

        # Bangumi v0 API 搜索
        result = self._request(f"/search/subject/{query}", params)

        if result and 'list' in result:
            return result['list']

        return None

    def get_subject(self, subject_id: int) -> Optional[Dict[str, Any]]:
        """
        获取条目详情

        Args:
            subject_id: 条目ID

        Returns:
            条目详情
        """
        return self._request(f"/v0/subjects/{subject_id}")

    def parse_metadata(self, subject_data: Dict[str, Any]) -> MangaMetadata:
        """
        解析条目数据为元数据对象

        Args:
            subject_data: Bangumi条目数据

        Returns:
            元数据对象
        """
        # 提取标题
        title = subject_data.get('name', '')
        title_zh = subject_data.get('name_cn')
        title_ja = subject_data.get('name')

        # 提取作者和画师
        author = None
        artist = None
        infobox = subject_data.get('infobox', [])
        for item in infobox:
            key = item.get('key', '')
            value = item.get('value', '')

            # 处理value可能是列表的情况
            if isinstance(value, list):
                value = ', '.join([v.get('v', '') if isinstance(v, dict) else str(v) for v in value])

            if key in ['作者', '漫画作者']:
                author = value
            elif key in ['作画', '画师']:
                artist = value

        # 如果没找到artist，使用author
        if not artist and author:
            artist = author

        # 提取出版社
        publisher = None
        for item in infobox:
            if item.get('key') in ['出版社', '连载杂志']:
                value = item.get('value', '')
                if isinstance(value, list):
                    value = ', '.join([v.get('v', '') if isinstance(v, dict) else str(v) for v in value])
                publisher = value
                break

        # 提取总卷数
        total_volumes = None
        for item in infobox:
            if item.get('key') == '话数':
                try:
                    total_volumes = int(item.get('value', 0))
                except (ValueError, TypeError):
                    pass
                break

        # 提取发布日期
        publish_date = subject_data.get('date')

        # 提取标签
        tags = []
        for tag in subject_data.get('tags', []):
            tags.append(tag.get('name', ''))

        # 提取封面
        images = subject_data.get('images', {})
        cover_url = images.get('large') or images.get('common') or images.get('medium')

        return MangaMetadata(
            title=title,
            title_zh=title_zh,
            title_ja=title_ja,
            author=author,
            artist=artist,
            publisher=publisher,
            summary=subject_data.get('summary'),
            tags=tags[:10] if tags else None,  # 限制标签数量
            total_volumes=total_volumes,
            publish_date=publish_date,
            cover_url=cover_url,
            source="bangumi",
            source_id=str(subject_data.get('id'))
        )

    def search_manga(self, title: str, author: Optional[str] = None) -> Optional[MangaMetadata]:
        """
        搜索漫画并返回最佳匹配

        Args:
            title: 漫画标题
            author: 作者名（可选，用于验证）

        Returns:
            元数据对象或None
        """
        logger.info(f"Bangumi搜索: {title}")

        # 搜索
        results = self.search(title, subject_type=1)

        if not results:
            logger.warning(f"Bangumi未找到结果: {title}")
            return None

        # 取第一个结果（通常最相关）
        first_result = results[0]
        subject_id = first_result.get('id')

        if not subject_id:
            return None

        # 获取详细信息
        subject_data = self.get_subject(subject_id)

        if not subject_data:
            return None

        # 解析元数据
        metadata = self.parse_metadata(subject_data)

        logger.info(f"Bangumi找到: {metadata.title_zh or metadata.title}")

        return metadata
