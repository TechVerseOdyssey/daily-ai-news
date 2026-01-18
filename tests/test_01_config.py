#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 1: 配置文件验证
验证 config.yaml 格式和必需字段
"""

import yaml
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_config_file():
    """测试配置文件"""
    print("=" * 60)
    print("测试 1: 配置文件验证")
    print("=" * 60)
    
    try:
        # 1. 加载 YAML 文件
        print("\n✓ 步骤 1: 加载配置文件...")
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("✅ YAML 文件格式正确")
        
        # 2. 检查必需字段
        print("\n✓ 步骤 2: 检查必需字段...")
        required_fields = ['feeds', 'email_settings', 'gemini', 'crawler_settings', 'prompt']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"缺少必需字段: {field}")
            print(f"  ✅ {field}")
        
        # 3. 检查 feeds 结构
        print("\n✓ 步骤 3: 检查 RSS 源配置...")
        if not isinstance(config['feeds'], list):
            raise ValueError("feeds 必须是列表类型")
        
        print(f"  ✅ 配置了 {len(config['feeds'])} 个 RSS 源")
        
        for i, feed in enumerate(config['feeds']):
            name = feed.get('name', f'未命名-{i}')
            url = feed.get('url', '')
            if not url:
                print(f"  ⚠️  {name}: 缺少 URL")
            else:
                print(f"  ✅ {name}: {url[:50]}...")
        
        # 4. 检查邮件设置
        print("\n✓ 步骤 4: 检查邮件设置...")
        email_settings = config['email_settings']
        
        if 'receiver' not in email_settings:
            raise ValueError("缺少 receiver 配置")
        
        if '@example.com' in email_settings['receiver']:
            print("  ⚠️  警告: receiver 仍然是示例邮箱，请修改")
        else:
            print(f"  ✅ receiver: {email_settings['receiver']}")
        
        if 'smtp_host' not in email_settings:
            print("  ⚠️  警告: 未配置 smtp_host，将使用默认值")
        else:
            print(f"  ✅ smtp_host: {email_settings['smtp_host']}")
        
        # 5. 检查爬虫设置
        print("\n✓ 步骤 5: 检查爬虫设置...")
        crawler_settings = config.get('crawler_settings', {})
        
        settings_to_check = {
            'max_workers': (1, 20),
            'rate_limit_seconds': (0, 5),
            'content_freshness_hours': (1, 168),
        }
        
        for setting, (min_val, max_val) in settings_to_check.items():
            value = crawler_settings.get(setting)
            if value is None:
                print(f"  ⚠️  {setting}: 未配置")
            elif not (min_val <= value <= max_val):
                print(f"  ⚠️  {setting}: {value} (建议范围: {min_val}-{max_val})")
            else:
                print(f"  ✅ {setting}: {value}")
        
        print("\n" + "=" * 60)
        print("✅ 配置文件验证通过")
        print("=" * 60)
        return True
        
    except FileNotFoundError:
        print("❌ 错误: 找不到 config.yaml 文件")
        return False
    except yaml.YAMLError as e:
        print(f"❌ 错误: YAML 格式错误 - {e}")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


if __name__ == "__main__":
    success = test_config_file()
    sys.exit(0 if success else 1)
