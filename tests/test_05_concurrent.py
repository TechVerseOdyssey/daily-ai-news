#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 5: 并发抓取
测试 NewsFetcher.fetch_all 方法的并发性能
"""

import sys
import os
import time
import yaml

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_fetcher import NewsFetcher

def test_concurrent_fetch():
    """测试并发抓取功能"""
    print("=" * 60)
    print("测试 5: 并发抓取性能")
    print("=" * 60)
    
    # 加载配置
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ 找不到 config.yaml 文件")
        return False
    
    feed_count = len(config.get('feeds', []))
    max_workers = config.get('crawler_settings', {}).get('max_workers', 5)
    
    print(f"\n配置信息:")
    print(f"  RSS 源数量: {feed_count}")
    print(f"  并发线程数: {max_workers}")
    
    print("\n开始并发抓取测试...")
    print("=" * 60)
    
    fetcher = NewsFetcher(config)
    start_time = time.time()
    
    try:
        sources_data = fetcher.fetch_all()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("抓取完成")
        print("=" * 60)
        
        # 性能统计
        total_items = sum(len(s.get('items', [])) for s in sources_data) if sources_data else 0
        print(f"\n⏱️  总耗时: {duration:.2f} 秒")
        print(f"📊 数据源数: {len(sources_data) if sources_data else 0}")
        print(f"📊 新闻条目数: {total_items}")
        
        # 性能评估
        print("\n性能评估:")
        
        # 预期时间：串行约 5-10 秒/源，并发应该显著缩短
        expected_serial_time = feed_count * 7  # 假设每个源 7 秒
        expected_concurrent_time = expected_serial_time / max_workers * 1.5  # 考虑开销
        
        checks = []
        
        # 1. 基本成功检查
        if sources_data and total_items > 0:
            checks.append(("✅", "成功抓取数据"))
        else:
            checks.append(("❌", "抓取数据不足"))
        
        # 2. 时间检查
        if duration < expected_serial_time * 0.6:  # 比串行快至少 40%
            checks.append(("✅", f"并发加速明显 (预期串行: ~{expected_serial_time:.0f}秒)"))
        elif duration < expected_serial_time:
            checks.append(("⚠️", f"有加速但不明显 (预期串行: ~{expected_serial_time:.0f}秒)"))
        else:
            checks.append(("❌", f"耗时过长 (预期串行: ~{expected_serial_time:.0f}秒)"))
        
        # 3. 绝对时间检查
        max_reasonable_time = 120  # 120 秒内应该完成（考虑速率限制）
        if duration < max_reasonable_time:
            checks.append(("✅", f"总耗时合理 (< {max_reasonable_time}秒)"))
        else:
            checks.append(("⚠️", f"总耗时较长 (> {max_reasonable_time}秒，可能网络较慢)"))
        
        for status, message in checks:
            print(f"  {status} {message}")
        
        # 内容质量检查
        if sources_data:
            print("\n内容质量:")
            quality_checks = [
                ("包含多个来源", len(sources_data) >= 2),
                ("包含新闻条目", total_items >= 3),
                ("每个来源有名称", all(s.get('source') for s in sources_data)),
            ]
            
            all_passed = True
            for check_name, check_result in quality_checks:
                status = "✅" if check_result else "❌"
                print(f"  {status} {check_name}")
                if not check_result:
                    all_passed = False
            
            # 预览
            print("\n数据预览:")
            print("-" * 60)
            for source in sources_data[:3]:
                print(f"\n来源: {source.get('source', 'N/A')}")
                for item in source.get('items', [])[:2]:
                    print(f"  - {item.get('title', 'N/A')[:60]}")
            print("-" * 60)
            
            if all_passed and checks[0][0] == "✅":
                print("\n" + "=" * 60)
                print("✅ 并发抓取测试通过")
                print("=" * 60)
                return True
            else:
                print("\n⚠️  测试完成但部分检查未通过")
                return False
        else:
            print("\n❌ 未抓取到任何数据")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_concurrent_fetch()
    sys.exit(0 if success else 1)
