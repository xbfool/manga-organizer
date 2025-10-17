#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检查脚本 - 测试所需依赖和工具是否可用
"""

import sys
import os

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 7:
        print("✓ Python版本符合要求 (>=3.7)")
        return True
    else:
        print("✗ Python版本过低，需要3.7或更高版本")
        return False

def check_modules():
    """检查必需的Python模块"""
    required_modules = {
        'zipfile': '处理ZIP/CBZ文件',
        'rarfile': '处理RAR/CBR文件',
        'pathlib': '路径处理',
        'json': 'JSON处理',
        'logging': '日志记录',
        'shutil': '文件操作',
        're': '正则表达式',
        'dataclasses': '数据类',
    }

    all_ok = True
    print("\n检查Python模块:")
    for module, desc in required_modules.items():
        try:
            __import__(module)
            print(f"✓ {module:20s} - {desc}")
        except ImportError:
            print(f"✗ {module:20s} - {desc} [缺失]")
            all_ok = False

    return all_ok

def check_unrar():
    """检查UnRAR工具"""
    print("\n检查UnRAR工具:")

    try:
        import rarfile
        from pathlib import Path

        # 配置UnRAR工具路径（与主脚本保持一致）
        rarfile.UNRAR_TOOL = r"C:\Program Files\UnRAR\UnRAR.exe"

        unrar_path = Path(rarfile.UNRAR_TOOL)
        print(f"配置的UnRAR路径: {unrar_path}")

        # 检查文件是否存在
        if unrar_path.exists():
            print(f"✓ 找到UnRAR: {unrar_path}")
            return True
        else:
            print("✗ UnRAR工具不存在于配置的路径")
            print(f"  当前配置路径: {unrar_path}")
            print("\n请确认UnRAR.exe已放置在该位置")
            print("  下载: https://www.rarlab.com/rar_add.htm")
            return False

    except Exception as e:
        print(f"✗ 检查UnRAR时出错: {e}")
        return False

def check_disk_space():
    """检查磁盘空间"""
    print("\n检查磁盘空间:")
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")

        print(f"总空间: {total // (2**30)} GB")
        print(f"已使用: {used // (2**30)} GB")
        print(f"可用: {free // (2**30)} GB")

        if free > 10 * (2**30):  # 10GB
            print("✓ 磁盘空间充足")
            return True
        else:
            print("⚠ 磁盘空间可能不足，建议至少有10GB可用空间")
            return False
    except Exception as e:
        print(f"✗ 检查磁盘空间时出错: {e}")
        return False

def test_basic_operations():
    """测试基本操作"""
    print("\n测试基本操作:")

    try:
        from pathlib import Path
        import tempfile
        import zipfile

        # 创建临时测试文件
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)

            # 测试1: 创建目录
            test_subdir = test_dir / "test_dir"
            test_subdir.mkdir()
            print("✓ 创建目录")

            # 测试2: 创建文件
            test_file = test_subdir / "test.txt"
            test_file.write_text("测试内容", encoding='utf-8')
            print("✓ 创建文件")

            # 测试3: 创建ZIP文件
            zip_file = test_dir / "test.zip"
            with zipfile.ZipFile(zip_file, 'w') as zf:
                zf.write(test_file, "test.txt")
            print("✓ 创建ZIP文件")

            # 测试4: 解压ZIP文件
            extract_dir = test_dir / "extract"
            extract_dir.mkdir()
            with zipfile.ZipFile(zip_file, 'r') as zf:
                zf.extractall(extract_dir)
            print("✓ 解压ZIP文件")

        return True

    except Exception as e:
        print(f"✗ 基本操作测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("漫画整理工具 - 环境检查")
    print("=" * 60)

    results = []

    results.append(("Python版本", check_python_version()))
    results.append(("Python模块", check_modules()))
    results.append(("UnRAR工具", check_unrar()))
    results.append(("磁盘空间", check_disk_space()))
    results.append(("基本操作", test_basic_operations()))

    print("\n" + "=" * 60)
    print("检查结果汇总:")
    print("=" * 60)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s}: {status}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有检查通过，环境准备就绪！")
        print("\n下一步：运行 python manga_organizer.py")
    else:
        print("✗ 部分检查未通过，请按照上述提示解决问题")
        print("\n注意：UnRAR工具对于处理RAR/CBR文件是必需的")
    print("=" * 60)

if __name__ == '__main__':
    main()
