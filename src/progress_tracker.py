#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度跟踪模块
功能：记录处理进度，支持断点续传
使用JSON格式，易于阅读和调试
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileProgress:
    """单个文件的处理进度"""
    file_path: str
    status: str  # pending, processing, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    output_files: List[str] = None
    retry_count: int = 0

    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, progress_file: str = ".progress/processing_progress.json"):
        """
        初始化进度跟踪器

        Args:
            progress_file: 进度文件路径
        """
        self.progress_file = Path(progress_file)
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.progress_data = self._load_or_create()

    def _load_or_create(self) -> Dict:
        """加载或创建进度文件"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"加载现有进度文件: {self.progress_file}")
                    return data
            except Exception as e:
                logger.error(f"加载进度文件失败: {e}，创建新文件")

        # 创建新的进度数据结构
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "sessions": [],
            "current_session": None,
            "files": {},
            "statistics": {
                "total_files": 0,
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            }
        }

    def start_session(self, total_files: int, session_name: Optional[str] = None) -> str:
        """
        开始新的处理会话

        Args:
            total_files: 总文件数
            session_name: 会话名称

        Returns:
            会话ID
        """
        session = {
            "session_id": self.session_id,
            "session_name": session_name or f"Session_{self.session_id}",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "total_files": total_files,
            "processed_files": 0,
            "status": "running"
        }

        self.progress_data["current_session"] = session
        self.progress_data["sessions"].append(session)
        self.save()

        logger.info(f"开始新会话: {session['session_name']} (ID: {self.session_id})")
        return self.session_id

    def add_file(self, file_path: str) -> None:
        """
        添加文件到待处理列表

        Args:
            file_path: 文件路径
        """
        if file_path not in self.progress_data["files"]:
            self.progress_data["files"][file_path] = asdict(FileProgress(
                file_path=file_path,
                status="pending"
            ))
            self.progress_data["statistics"]["total_files"] += 1
            self.progress_data["statistics"]["pending"] += 1

    def add_files(self, file_paths: List[str]) -> None:
        """
        批量添加文件

        Args:
            file_paths: 文件路径列表
        """
        for file_path in file_paths:
            self.add_file(file_path)
        self.save()
        logger.info(f"添加 {len(file_paths)} 个文件到处理队列")

    def start_processing(self, file_path: str) -> None:
        """
        标记文件开始处理

        Args:
            file_path: 文件路径
        """
        if file_path in self.progress_data["files"]:
            file_data = self.progress_data["files"][file_path]
            old_status = file_data["status"]

            file_data["status"] = "processing"
            file_data["started_at"] = datetime.now().isoformat()

            # 更新统计
            if old_status == "pending":
                self.progress_data["statistics"]["pending"] -= 1
            elif old_status == "failed":
                self.progress_data["statistics"]["failed"] -= 1

            self.progress_data["statistics"]["processing"] += 1

    def mark_completed(self, file_path: str, output_files: List[str]) -> None:
        """
        标记文件处理完成

        Args:
            file_path: 文件路径
            output_files: 输出文件列表
        """
        if file_path in self.progress_data["files"]:
            file_data = self.progress_data["files"][file_path]

            file_data["status"] = "completed"
            file_data["completed_at"] = datetime.now().isoformat()
            file_data["output_files"] = output_files
            file_data["error"] = None

            # 更新统计
            self.progress_data["statistics"]["processing"] -= 1
            self.progress_data["statistics"]["completed"] += 1

            # 更新会话进度
            if self.progress_data["current_session"]:
                self.progress_data["current_session"]["processed_files"] += 1

    def mark_failed(self, file_path: str, error: str) -> None:
        """
        标记文件处理失败

        Args:
            file_path: 文件路径
            error: 错误信息
        """
        if file_path in self.progress_data["files"]:
            file_data = self.progress_data["files"][file_path]

            file_data["status"] = "failed"
            file_data["completed_at"] = datetime.now().isoformat()
            file_data["error"] = error
            file_data["retry_count"] += 1

            # 更新统计
            self.progress_data["statistics"]["processing"] -= 1
            self.progress_data["statistics"]["failed"] += 1

            # 更新会话进度
            if self.progress_data["current_session"]:
                self.progress_data["current_session"]["processed_files"] += 1

    def end_session(self, status: str = "completed") -> None:
        """
        结束当前会话

        Args:
            status: 会话状态 (completed, interrupted, error)
        """
        if self.progress_data["current_session"]:
            self.progress_data["current_session"]["completed_at"] = datetime.now().isoformat()
            self.progress_data["current_session"]["status"] = status
            self.save()

            logger.info(f"会话结束: {self.progress_data['current_session']['session_name']} (状态: {status})")

    def get_pending_files(self) -> List[str]:
        """
        获取所有待处理的文件

        Returns:
            待处理文件列表
        """
        pending = []
        for file_path, file_data in self.progress_data["files"].items():
            if file_data["status"] == "pending":
                pending.append(file_path)
        return pending

    def get_failed_files(self, max_retries: int = 3) -> List[str]:
        """
        获取所有失败的文件（未超过最大重试次数）

        Args:
            max_retries: 最大重试次数

        Returns:
            失败文件列表
        """
        failed = []
        for file_path, file_data in self.progress_data["files"].items():
            if file_data["status"] == "failed" and file_data["retry_count"] < max_retries:
                failed.append(file_path)
        return failed

    def is_file_processed(self, file_path: str) -> bool:
        """
        检查文件是否已处理

        Args:
            file_path: 文件路径

        Returns:
            是否已处理
        """
        if file_path in self.progress_data["files"]:
            return self.progress_data["files"][file_path]["status"] == "completed"
        return False

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        stats = self.progress_data["statistics"].copy()

        # 计算进度百分比
        total = stats["total_files"]
        if total > 0:
            stats["progress_percentage"] = (stats["completed"] / total) * 100
            stats["failed_percentage"] = (stats["failed"] / total) * 100
        else:
            stats["progress_percentage"] = 0
            stats["failed_percentage"] = 0

        return stats

    def save(self) -> None:
        """保存进度到文件"""
        self.progress_data["last_updated"] = datetime.now().isoformat()

        try:
            # 先写入临时文件
            temp_file = self.progress_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, ensure_ascii=False, indent=2)

            # 原子性替换
            temp_file.replace(self.progress_file)

        except Exception as e:
            logger.error(f"保存进度文件失败: {e}")

    def print_summary(self) -> None:
        """打印进度摘要"""
        stats = self.get_statistics()

        print("\n" + "="*60)
        print("处理进度摘要")
        print("="*60)
        print(f"总文件数: {stats['total_files']}")
        print(f"待处理: {stats['pending']}")
        print(f"处理中: {stats['processing']}")
        print(f"已完成: {stats['completed']} ({stats['progress_percentage']:.1f}%)")
        print(f"失败: {stats['failed']} ({stats['failed_percentage']:.1f}%)")

        if self.progress_data["current_session"]:
            session = self.progress_data["current_session"]
            print(f"\n当前会话: {session['session_name']}")
            print(f"开始时间: {session['started_at']}")
            print(f"已处理: {session['processed_files']}/{session['total_files']}")

        print("="*60)

    def export_summary(self, output_file: str) -> None:
        """
        导出可读的摘要报告

        Args:
            output_file: 输出文件路径
        """
        stats = self.get_statistics()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("处理进度报告\n")
            f.write("="*80 + "\n\n")

            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"进度文件: {self.progress_file}\n\n")

            f.write("统计信息:\n")
            f.write(f"  总文件数: {stats['total_files']}\n")
            f.write(f"  待处理: {stats['pending']}\n")
            f.write(f"  处理中: {stats['processing']}\n")
            f.write(f"  已完成: {stats['completed']} ({stats['progress_percentage']:.1f}%)\n")
            f.write(f"  失败: {stats['failed']} ({stats['failed_percentage']:.1f}%)\n\n")

            # 会话历史
            if self.progress_data["sessions"]:
                f.write("会话历史:\n")
                for session in self.progress_data["sessions"]:
                    f.write(f"\n  会话: {session['session_name']}\n")
                    f.write(f"    ID: {session['session_id']}\n")
                    f.write(f"    开始: {session['started_at']}\n")
                    if session['completed_at']:
                        f.write(f"    结束: {session['completed_at']}\n")
                    f.write(f"    状态: {session['status']}\n")
                    f.write(f"    处理文件: {session['processed_files']}/{session['total_files']}\n")

            # 失败文件列表
            failed_files = [
                (path, data) for path, data in self.progress_data["files"].items()
                if data["status"] == "failed"
            ]

            if failed_files:
                f.write("\n\n失败文件列表:\n")
                f.write("-"*80 + "\n")
                for file_path, file_data in failed_files:
                    f.write(f"\n  文件: {Path(file_path).name}\n")
                    f.write(f"    路径: {file_path}\n")
                    f.write(f"    错误: {file_data['error']}\n")
                    f.write(f"    重试次数: {file_data['retry_count']}\n")

            f.write("\n" + "="*80 + "\n")

        logger.info(f"摘要报告已导出: {output_file}")

    def reset(self) -> None:
        """重置进度（慎用）"""
        logger.warning("重置进度跟踪器")
        self.progress_data = self._load_or_create()
        self.save()

    def cleanup_old_sessions(self, keep_last_n: int = 10) -> None:
        """
        清理旧会话记录

        Args:
            keep_last_n: 保留最近N个会话
        """
        if len(self.progress_data["sessions"]) > keep_last_n:
            removed = len(self.progress_data["sessions"]) - keep_last_n
            self.progress_data["sessions"] = self.progress_data["sessions"][-keep_last_n:]
            logger.info(f"清理了 {removed} 个旧会话记录")
            self.save()


def main():
    """测试和演示"""
    import argparse

    parser = argparse.ArgumentParser(description='进度跟踪器工具')
    parser.add_argument('--file', '-f', default='.progress/processing_progress.json',
                        help='进度文件路径')
    parser.add_argument('--action', '-a', choices=['summary', 'export', 'reset'],
                        default='summary', help='操作类型')
    parser.add_argument('--output', '-o', help='导出文件路径')

    args = parser.parse_args()

    tracker = ProgressTracker(args.file)

    if args.action == 'summary':
        tracker.print_summary()
    elif args.action == 'export':
        output_file = args.output or 'progress_summary.txt'
        tracker.export_summary(output_file)
        print(f"摘要已导出到: {output_file}")
    elif args.action == 'reset':
        confirm = input("确认重置进度？这将清除所有记录 (yes/no): ")
        if confirm.lower() == 'yes':
            tracker.reset()
            print("进度已重置")
        else:
            print("已取消")


if __name__ == '__main__':
    main()
