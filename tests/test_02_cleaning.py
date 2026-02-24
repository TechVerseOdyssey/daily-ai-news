#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 2: HTML 清理和数据验证
测试 NewsFetcher.clean_html_content 和 NewsFetcher.validate_item_content 静态方法
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_fetcher import NewsFetcher

# 使用静态方法引用
clean_html_content = NewsFetcher.clean_html_content
validate_item_content = NewsFetcher.validate_item_content

def test_html_cleaning():
    """测试 HTML 清理功能"""
    print("=" * 60)
    print("测试 2A: HTML 清理功能")
    print("=" * 60)
    
    test_cases = [
        # (输入, 期望包含, 描述)
        ("<p>Hello&nbsp;World</p>", "Hello World", "HTML 实体解码"),
        ("<script>alert('x')</script><p>Text</p>", "Text", "移除 script 标签"),
        ("<style>body{}</style><p>Content</p>", "Content", "移除 style 标签"),
        ("Normal   text   with   spaces", "Normal text with spaces", "清理多余空白"),
        ("Line1\n\n\nLine2", "Line1", "清理多余换行"),
        ("<p>中文&amp;测试</p>", "中文&测试", "中文和实体"),
        ("<div><p>Nested <b>tags</b></p></div>", "Nested tags", "嵌套标签"),
        ("", "", "空字符串处理"),
    ]
    
    passed = 0
    failed = 0
    
    for i, (input_html, expected_contains, description) in enumerate(test_cases, 1):
        try:
            result = clean_html_content(input_html)
            
            # 检查是否包含期望的文本
            if expected_contains in result or (not expected_contains and not result):
                print(f"✅ 测试 {i}: {description}")
                print(f"   输入: {input_html[:50]}")
                print(f"   输出: {result[:50]}")
                passed += 1
            else:
                print(f"❌ 测试 {i}: {description}")
                print(f"   输入: {input_html[:50]}")
                print(f"   期望包含: {expected_contains}")
                print(f"   实际输出: {result[:50]}")
                failed += 1
        except Exception as e:
            print(f"❌ 测试 {i}: {description} - 异常: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"HTML 清理测试: 通过 {passed}/{passed+failed}")
    print("=" * 60)
    
    return failed == 0


def test_content_validation():
    """测试内容验证功能"""
    print("\n" + "=" * 60)
    print("测试 2B: 内容验证功能")
    print("=" * 60)
    
    test_cases = [
        # (标题, 链接, 描述, 期望结果, 描述)
        ("Good Title", "https://example.com", "Good description text", True, "正常内容"),
        ("AB", "https://example.com", "Good description", False, "标题太短"),
        ("Good Title", "invalid-url", "Description", False, "无效链接"),
        ("Good Title", "ftp://example.com", "Description", False, "非 HTTP 链接"),
        ("广告标题", "https://example.com", "Description", False, "包含广告关键词"),
        ("推广内容", "https://example.com", "Description", False, "包含推广关键词"),
        ("Normal Title", "https://example.com", "AB", False, "描述太短"),
        ("无标题", "https://example.com", "Description", False, "无标题"),
        ("   ", "https://example.com", "Description", False, "空白标题"),
        ("Great Article", "https://example.com", "无摘要", True, "无摘要但其他正常"),
    ]
    
    passed = 0
    failed = 0
    
    for i, (title, link, desc, expected, description) in enumerate(test_cases, 1):
        try:
            result = validate_item_content(title, link, desc)
            
            if result == expected:
                status = "✅"
                passed += 1
            else:
                status = "❌"
                failed += 1
            
            print(f"{status} 测试 {i}: {description}")
            print(f"   标题: {title[:30]}")
            print(f"   链接: {link[:40]}")
            print(f"   结果: {result} (期望: {expected})")
        except Exception as e:
            print(f"❌ 测试 {i}: {description} - 异常: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"内容验证测试: 通过 {passed}/{passed+failed}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    result1 = test_html_cleaning()
    result2 = test_content_validation()
    
    if result1 and result2:
        print("\n✅ 所有测试通过")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)
