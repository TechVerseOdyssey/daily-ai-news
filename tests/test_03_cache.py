#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 3: 缓存机制
测试 save_cache 和 load_cache 函数
"""

import sys
import os
import shutil
import time

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import save_cache, load_cache, CACHE_DIR

def test_cache():
    """测试缓存功能"""
    print("=" * 60)
    print("测试 3: 缓存机制")
    print("=" * 60)
    
    # 清理测试缓存
    test_cache_dir = '.cache_test'
    if os.path.exists(test_cache_dir):
        shutil.rmtree(test_cache_dir)
    
    # 临时修改缓存目录
    import main
    original_cache_dir = main.CACHE_DIR
    main.CACHE_DIR = test_cache_dir
    os.makedirs(test_cache_dir, exist_ok=True)
    
    try:
        # 测试 1: 保存和加载缓存
        print("\n✓ 测试 1: 保存和加载缓存...")
        test_data = "This is test data 测试数据 🚀"
        test_key = "test_key_1"
        
        save_cache(test_key, test_data)
        
        if os.path.exists(os.path.join(test_cache_dir, f"{test_key}.json")):
            print("  ✅ 缓存文件已创建")
        else:
            print("  ❌ 缓存文件未创建")
            return False
        
        loaded = load_cache(test_key, max_age_hours=1)
        if loaded == test_data:
            print("  ✅ 缓存数据加载成功")
        else:
            print(f"  ❌ 缓存数据不匹配")
            print(f"     期望: {test_data}")
            print(f"     实际: {loaded}")
            return False
        
        # 测试 2: 缓存过期
        print("\n✓ 测试 2: 缓存过期机制...")
        save_cache("expire_test", "old data")
        time.sleep(1)
        
        # max_age_hours=0 应该使其立即过期
        expired = load_cache("expire_test", max_age_hours=0)
        if expired is None:
            print("  ✅ 过期缓存正确返回 None")
        else:
            print("  ❌ 过期缓存未正确处理")
            return False
        
        # 测试 3: 不存在的缓存
        print("\n✓ 测试 3: 不存在的缓存...")
        missing = load_cache("nonexistent_key_12345")
        if missing is None:
            print("  ✅ 不存在的缓存正确返回 None")
        else:
            print("  ❌ 不存在的缓存处理错误")
            return False
        
        # 测试 4: 中文和特殊字符
        print("\n✓ 测试 4: 中文和特殊字符...")
        chinese_data = "测试中文内容：你好世界！🌍\n多行\n数据"
        save_cache("chinese_test", chinese_data)
        loaded_chinese = load_cache("chinese_test")
        
        if loaded_chinese == chinese_data:
            print("  ✅ 中文和特殊字符正确处理")
        else:
            print("  ❌ 中文和特殊字符处理错误")
            return False
        
        # 测试 5: 大数据
        print("\n✓ 测试 5: 大数据缓存...")
        large_data = "x" * 100000  # 100KB
        save_cache("large_test", large_data)
        loaded_large = load_cache("large_test")
        
        if loaded_large == large_data:
            print(f"  ✅ 大数据缓存成功 ({len(large_data)} 字符)")
        else:
            print("  ❌ 大数据缓存失败")
            return False
        
        print("\n" + "=" * 60)
        print("✅ 缓存测试通过")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 恢复原始缓存目录
        main.CACHE_DIR = original_cache_dir
        
        # 清理测试缓存
        if os.path.exists(test_cache_dir):
            shutil.rmtree(test_cache_dir)
            print("\n✓ 测试缓存已清理")


if __name__ == "__main__":
    success = test_cache()
    sys.exit(0 if success else 1)
