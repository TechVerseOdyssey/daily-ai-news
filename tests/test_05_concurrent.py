#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 5: 并发抓取
测试 fetch_feeds 函数的并发性能
"""

import sys
import os
import time
import yaml

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import fetch_feeds

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
    
    start_time = time.time()
    
    try:
        result = fetch_feeds()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("抓取完成")
        print("=" * 60)
        
        # 性能统计
        print(f"\n⏱️  总耗时: {duration:.2f} 秒")
        print(f"📊 数据长度: {len(result) if result else 0} 字符")
        
        if result:
            print(f"📈 平均速度: {len(result) / duration:.0f} 字符/秒")
        
        # 性能评估
        print("\n性能评估:")
        
        # 预期时间：串行约 5-10 秒/源，并发应该显著缩短
        expected_serial_time = feed_count * 7  # 假设每个源 7 秒
        expected_concurrent_time = expected_serial_time / max_workers * 1.5  # 考虑开销
        
        checks = []
        
        # 1. 基本成功检查
        if result and len(result) > 500:
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
        max_reasonable_time = 60  # 60 秒内应该完成
        if duration < max_reasonable_time:
            checks.append(("✅", f"总耗时合理 (< {max_reasonable_time}秒)"))
        else:
            checks.append(("⚠️", f"总耗时较长 (> {max_reasonable_time}秒，可能网络较慢)"))
        
        for status, message in checks:
            print(f"  {status} {message}")
        
        # 内容质量检查
        if result:
            print("\n内容质量:")
            quality_checks = [
                ("包含多个来源", result.count("来源：") >= 2),
                ("包含标题信息", result.count("标题:") >= 3),
                ("包含链接信息", result.count("http") >= 5),
                ("数据量充足", len(result) > 1000),
            ]
            
            all_passed = True
            for check_name, check_result in quality_checks:
                status = "✅" if check_result else "❌"
                print(f"  {status} {check_name}")
                if not check_result:
                    all_passed = False
            
            print("\n前 500 字符预览:")
            print("-" * 60)
            print(result[:500])
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
