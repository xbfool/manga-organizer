#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元数据源模块
支持多个元数据API源
"""

from .base import MetadataSource, MangaMetadata
from .anilist import AniListSource
from .bangumi import BangumiSource
from .trace_moe import TraceMoeSource
from .comicvine import ComicVineSource

__all__ = [
    'MetadataSource',
    'MangaMetadata',
    'AniListSource',
    'BangumiSource',
    'TraceMoeSource',
    'ComicVineSource',
]
