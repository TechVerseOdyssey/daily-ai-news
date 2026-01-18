#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行所有测试脚本

使用方法:
    python tests/run_all_tests.py

可选参数:
    --skip-network  跳过需要网络的测试
"""

import sys
import os
import subprocess
import argparse

# 测试脚本列表 (测试名称, 文件名, 是否需要网络)
TESTS = [
    ("配置文件验证", "test_01_config.py", False),
    ("HTML清理和验证", "test_02_cleaning.py", False),
    ("缓存机制", "test_03_cache.py", False),
    ("单源抓取", "test_04_fetch_single.py", True),
    ("并发抓取", "test_05_concurrent.py", True),
]


def run_test(test_file, test_name):
    """运行单个测试"""
    print(f"\n{'=' * 70}")
    print(f"运行测试: {test_name}")
    print(f"{'=' * 70}")
    
    test_path = os.path.join("tests", test_file)
    
    try:
        result = subprocess.run(
            [sys.executable, test_path],
            capture_output=False,
            text=True,
            timeout=120  # 2分钟超时
        )
        
        if result.returncode == 0:
            print(f"\n✅ {test_name} - 通过")
            return True
        else:
            print(f"\n❌ {test_name} - 失败 (退出码: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n⏱️  {test_name} - 超时")
        return False
    except Exception as e:
        print(f"\n❌ {test_name} - 异常: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="运行所有测试")
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="跳过需要网络连接的测试"
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("🧪 Daily AI News - 自动化测试套件")
    print("=" * 70)
    
    # 检查是否在项目根目录
    if not os.path.exists("config.yaml"):
        print("\n❌ 错误: 请在项目根目录运行此脚本")
        print("   cd /path/to/daily-ai-news")
        print("   python tests/run_all_tests.py")
        sys.exit(1)
    
    results = []
    skipped = []
    
    for test_name, test_file, requires_network in TESTS:
        if requires_network and args.skip_network:
            print(f"\n⏭️  跳过 {test_name} (需要网络)")
            skipped.append(test_name)
            continue
        
        success = run_test(test_file, test_name)
        results.append((test_name, success))
    
    # 打印总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    total = len(results)
    
    print(f"\n总计: {total} 个测试")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    
    if skipped:
        print(f"⏭️  跳过: {len(skipped)}")
        for name in skipped:
            print(f"   - {name}")
    
    print("\n详细结果:")
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status} - {test_name}")
    
    print("\n" + "=" * 70)
    
    if failed == 0:
        print("✅ 所有测试通过！")
        print("=" * 70)
        return 0
    else:
        print(f"⚠️  有 {failed} 个测试失败")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
