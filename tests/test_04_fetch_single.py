#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 4: 单个 RSS 源抓取
测试 fetch_single_feed 函数
"""

import sys
import os
import yaml

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import fetch_single_feed

def test_single_feed():
    """测试单个 RSS 源抓取"""
    print("=" * 60)
    print("测试 4: 单个 RSS 源抓取")
    print("=" * 60)
    
    # 加载配置
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ 找不到 config.yaml 文件")
        return False
    
    if not config.get('feeds'):
        print("❌ 配置文件中没有 RSS 源")
        return False
    
    # 测试第一个 RSS 源
    feed_conf = config['feeds'][0]
    feed_name = feed_conf['name']
    
    print(f"\n正在测试 RSS 源: {feed_name}")
    print(f"URL: {feed_conf['url']}")
    print(f"最大条目: {feed_conf.get('max_items', 3)}")
    print("\n" + "-" * 60)
    
    try:
        result = fetch_single_feed(feed_conf, retry_count=2)
        
        if result:
            print("\n" + "-" * 60)
            print("✅ 抓取成功")
            print(f"\n内容长度: {len(result)} 字符")
            print(f"\n前 800 字符预览:")
            print("=" * 60)
            print(result[:800])
            print("=" * 60)
            
            # 验证内容质量
            checks = []
            checks.append(("包含来源标记", "来源：" in result))
            checks.append(("包含标题", "标题:" in result))
            checks.append(("包含链接", "链接:" in result or "http" in result))
            checks.append(("内容长度合理", len(result) > 100))
            
            print("\n内容质量检查:")
            all_passed = True
            for check_name, check_result in checks:
                status = "✅" if check_result else "❌"
                print(f"  {status} {check_name}")
                if not check_result:
                    all_passed = False
            
            if all_passed:
                print("\n" + "=" * 60)
                print("✅ 单个源抓取测试通过")
                print("=" * 60)
                return True
            else:
                print("\n⚠️  抓取成功但内容质量检查未完全通过")
                return False
        else:
            print("\n❌ 抓取失败：未返回任何内容")
            print("\n可能的原因:")
            print("  1. 网络连接问题")
            print("  2. RSS 源暂时不可用")
            print("  3. 内容被过滤（日期/验证）")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_single_feed()
    sys.exit(0 if success else 1)
