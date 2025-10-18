#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的进度跟踪器
只记录已完成文件列表，不需要复杂状态
"""

import json
import os
from pathlib import Path
from typing import Set, Optional
from datetime import datetime


class SimpleTracker:
    """简化的进度跟踪器"""

    def __init__(self, tracking_file: str = ".progress/completed.json"):
        """
        初始化跟踪器

        Args:
            tracking_file: 跟踪文件路径
        """
        self.tracking_file = Path(tracking_file)
        self.completed: Set[str] = set()
        self.started_at: Optional[str] = None
        self.last_updated: Optional[str] = None

        # 确保目录存在
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)

        # 加载已完成列表
        self._load()

    def _load(self):
        """加载已完成列表"""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.completed = set(data.get('completed', []))
                    self.started_at = data.get('started_at')
                    self.last_updated = data.get('last_updated')
            except Exception as e:
                print(f"Warning: Failed to load tracking file: {e}")
                self.completed = set()

    def _save(self):
        """保存已完成列表"""
        data = {
            'started_at': self.started_at or datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'total_completed': len(self.completed),
            'completed': sorted(list(self.completed))
        }

        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.last_updated = data['last_updated']
        if not self.started_at:
            self.started_at = data['started_at']

    def is_completed(self, file_path: str) -> bool:
        """
        检查文件是否已完成

        Args:
            file_path: 文件路径

        Returns:
            是否已完成
        """
        # 使用文件名作为键（因为路径可能变化）
        file_name = Path(file_path).name
        return file_name in self.completed

    def mark_completed(self, file_path: str):
        """
        标记文件为已完成

        Args:
            file_path: 文件路径
        """
        file_name = Path(file_path).name
        self.completed.add(file_name)
        self._save()

    def get_stats(self) -> dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            'total_completed': len(self.completed),
            'started_at': self.started_at,
            'last_updated': self.last_updated
        }

    def reset(self):
        """重置跟踪记录"""
        self.completed.clear()
        self.started_at = None
        self.last_updated = None
        if self.tracking_file.exists():
            self.tracking_file.unlink()
