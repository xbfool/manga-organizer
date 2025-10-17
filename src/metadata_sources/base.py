#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元数据基础类
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from abc import ABC, abstractmethod


@dataclass
class MangaMetadata:
    """漫画元数据统一模型"""

    # 标题（多语言）
    title_zh: Optional[str] = None        # 中文标题
    title_native: Optional[str] = None    # 原语言标题（日文等）
    title_romaji: Optional[str] = None    # 罗马音
    title_english: Optional[str] = None   # 英文标题

    # 创作者
    authors: List[str] = field(default_factory=list)      # 作者
    artists: List[str] = field(default_factory=list)      # 画师
    translators: List[str] = field(default_factory=list)  # 翻译

    # 出版信息
    publisher: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    status: Optional[str] = None  # 连载中/已完结

    # 内容信息
    volumes: Optional[int] = None
    chapters: Optional[int] = None
    summary_zh: Optional[str] = None      # 中文简介
    summary_en: Optional[str] = None      # 英文简介
    genres: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # 评分
    rating: Optional[float] = None

    # 资源
    cover_url: Optional[str] = None

    # 元信息
    source: Optional[str] = None          # 数据来源
    source_id: Optional[str] = None       # 源ID
    language: Optional[str] = None        # zh/ja/en

    def get_best_title(self, priority: List[str] = None) -> str:
        """
        根据优先级获取最佳标题

        Args:
            priority: 语言优先级列表，如 ['zh', 'ja', 'romaji', 'en']

        Returns:
            最佳标题
        """
        if priority is None:
            priority = ['zh', 'ja', 'romaji', 'en']

        title_map = {
            'zh': self.title_zh,
            'ja': self.title_native,
            'romaji': self.title_romaji,
            'en': self.title_english
        }

        for lang in priority:
            title = title_map.get(lang)
            if title:
                return title

        # 如果都没有，返回第一个非空标题
        for title in [self.title_zh, self.title_native, self.title_romaji, self.title_english]:
            if title:
                return title

        return "Unknown"

    def get_best_summary(self, priority: List[str] = None) -> Optional[str]:
        """获取最佳简介"""
        if priority is None:
            priority = ['zh', 'en']

        summary_map = {
            'zh': self.summary_zh,
            'en': self.summary_en
        }

        for lang in priority:
            summary = summary_map.get(lang)
            if summary:
                return summary

        return None

    def merge(self, other: 'MangaMetadata'):
        """
        合并另一个元数据对象
        保留非空值，优先保留当前对象的值
        """
        if not self.title_zh and other.title_zh:
            self.title_zh = other.title_zh
        if not self.title_native and other.title_native:
            self.title_native = other.title_native
        if not self.title_romaji and other.title_romaji:
            self.title_romaji = other.title_romaji
        if not self.title_english and other.title_english:
            self.title_english = other.title_english

        # 合并作者列表
        self.authors = list(set(self.authors + other.authors))
        self.artists = list(set(self.artists + other.artists))

        # 合并标签
        self.genres = list(set(self.genres + other.genres))
        self.tags = list(set(self.tags + other.tags))

        # 其他字段
        if not self.publisher and other.publisher:
            self.publisher = other.publisher
        if not self.year and other.year:
            self.year = other.year
        if not self.volumes and other.volumes:
            self.volumes = other.volumes
        if not self.summary_zh and other.summary_zh:
            self.summary_zh = other.summary_zh
        if not self.summary_en and other.summary_en:
            self.summary_en = other.summary_en
        if not self.cover_url and other.cover_url:
            self.cover_url = other.cover_url


class MetadataSource(ABC):
    """元数据源抽象基类"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.source_name = self.__class__.__name__

    @abstractmethod
    def search(self, title: str, **kwargs) -> Optional[MangaMetadata]:
        """
        搜索漫画元数据

        Args:
            title: 漫画标题
            **kwargs: 其他搜索参数

        Returns:
            MangaMetadata对象或None
        """
        pass

    @abstractmethod
    def get_by_id(self, source_id: str) -> Optional[MangaMetadata]:
        """
        通过ID获取元数据

        Args:
            source_id: 源ID

        Returns:
            MangaMetadata对象或None
        """
        pass

    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return True
