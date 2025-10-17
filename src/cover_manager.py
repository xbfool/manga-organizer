#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
封面下载和管理
"""

import requests
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CoverManager:
    """封面下载管理器"""

    def __init__(self, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = timeout

    def download_cover(self, cover_url: str, output_path: Path) -> bool:
        """
        下载封面

        Args:
            cover_url: 封面URL
            output_path: 输出路径（文件路径）

        Returns:
            是否成功
        """
        try:
            logger.info(f"下载封面: {cover_url}")

            response = self.session.get(cover_url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            # 确保目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存文件
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"封面已保存: {output_path}")
            return True

        except Exception as e:
            logger.error(f"下载封面失败 {cover_url}: {e}")
            return False

    def save_as_series_cover(self, cover_url: str, series_dir: Path) -> bool:
        """
        下载并保存为系列封面

        Args:
            cover_url: 封面URL
            series_dir: 系列目录

        Returns:
            是否成功
        """
        if not cover_url:
            return False

        cover_path = series_dir / "cover.jpg"
        return self.download_cover(cover_url, cover_path)

    def extract_cover_from_cbz(self, cbz_path: Path, output_path: Path) -> bool:
        """
        从CBZ提取第一页作为封面

        Args:
            cbz_path: CBZ文件路径
            output_path: 输出路径

        Returns:
            是否成功
        """
        try:
            import zipfile
            from PIL import Image
            import io

            with zipfile.ZipFile(cbz_path, 'r') as zf:
                # 获取所有图片文件
                image_files = [f for f in zf.namelist()
                               if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]

                if not image_files:
                    return False

                # 按名称排序，取第一个
                image_files.sort()
                first_image = image_files[0]

                # 读取图片
                image_data = zf.read(first_image)
                img = Image.open(io.BytesIO(image_data))

                # 转换为RGB（如果是RGBA）
                if img.mode == 'RGBA':
                    img = img.convert('RGB')

                # 保存为JPEG
                img.save(output_path, 'JPEG', quality=90)

            logger.info(f"已提取封面: {output_path}")
            return True

        except Exception as e:
            logger.error(f"提取封面失败 {cbz_path}: {e}")
            return False
