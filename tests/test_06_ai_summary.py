#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 06: AI 总结功能（实际调用 OpenRouter API）

从 .env 文件读取 OPENROUTER_API_KEY，实际调用 API 验证：
1. API Key 有效性
2. OpenRouter 客户端初始化
3. API 调用 + HTML 结构 + 中文内容（合并为一次调用，减少限流风险）
4. enhance_with_ai 完整链路
5. AI 禁用时的行为
"""

import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 重试配置
MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 15


def load_env():
    """从项目根目录的 .env 文件加载环境变量"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(project_root, '.env')

    if not os.path.exists(env_file):
        print(f"❌ 未找到 .env 文件: {env_file}")
        print("   请复制 .env.example 为 .env 并填入 API Key:")
        print(f"   cp {os.path.join(project_root, '.env.example')} {env_file}")
        return False

    loaded = 0
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                if value:
                    os.environ[key] = value
                    loaded += 1

    print(f"  ✅ 从 .env 加载了 {loaded} 个环境变量")
    return True


def load_config():
    """加载项目配置"""
    import yaml
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def call_with_retry(func, description):
    """带重试的 API 调用封装，处理 429 限流"""
    for attempt in range(MAX_RETRIES):
        result = func()
        if result is not None:
            return result
        if attempt < MAX_RETRIES - 1:
            wait = RETRY_WAIT_SECONDS * (attempt + 1)
            print(f"  🔄 {description} 第 {attempt + 1} 次失败，等待 {wait} 秒后重试...")
            time.sleep(wait)
    return None


# 模拟的新闻数据
MOCK_SOURCES_DATA = [
    {
        'source': 'OpenAI Blog',
        'items': [
            {
                'title': 'Introducing GPT-5: A New Era of AI',
                'link': 'https://openai.com/blog/gpt-5',
                'summary': 'OpenAI announces GPT-5 with breakthrough capabilities in reasoning.'
            },
        ]
    },
    {
        'source': 'DeepMind Blog',
        'items': [
            {
                'title': 'AlphaFold 3: Predicting All Molecular Structures',
                'link': 'https://deepmind.google/blog/alphafold3',
                'summary': 'AlphaFold 3 predicts the structure of all life molecules.'
            }
        ]
    }
]


def test_openrouter_api_key():
    """测试 1: 验证 OPENROUTER_API_KEY 已设置"""
    print("\n--- 测试 1: 验证 API Key ---")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    assert api_key, "OPENROUTER_API_KEY 未设置，请在 .env 文件中填入"
    assert len(api_key) > 10, f"API Key 太短 ({len(api_key)} 字符)"
    print(f"  ✅ API Key 已设置 (长度: {len(api_key)}, 前缀: {api_key[:8]}...)")
    return True


def test_openrouter_init():
    """测试 2: 验证 OpenRouter 客户端初始化"""
    print("\n--- 测试 2: OpenRouter 客户端初始化 ---")
    from ai_summarizer import AISummarizer

    config = load_config()
    config.setdefault('ai_summary', {})['enabled'] = True

    summarizer = AISummarizer(config)
    result = summarizer._ensure_openrouter()
    assert result, "OpenRouter 客户端初始化失败"
    assert summarizer._openrouter_client is not None, "客户端对象为 None"
    print("  ✅ OpenRouter 客户端初始化成功")
    return True


def test_api_call_and_content():
    """测试 3: 实际 API 调用 + HTML 结构 + 中文验证（合并为一次调用）"""
    print("\n--- 测试 3: 实际 API 调用 & 内容验证 ---")
    from ai_summarizer import AISummarizer

    config = load_config()
    config.setdefault('ai_summary', {})['enabled'] = True

    summarizer = AISummarizer(config)

    test_content = """
--- 来源：OpenAI Blog ---
标题: Introducing GPT-5
链接: https://openai.com/blog/gpt-5
摘要: OpenAI announces GPT-5 with breakthrough capabilities.

--- 来源：Arxiv ---
标题: Attention Is All You Need v2
链接: https://arxiv.org/abs/2025.12345
摘要: Transformer 架构的重大改进论文
"""

    result = call_with_retry(
        lambda: summarizer._generate_summary(test_content),
        "API 调用"
    )
    assert result is not None, f"API 在 {MAX_RETRIES} 次重试后仍返回 None（可能是限流）"
    assert len(result) > 50, f"总结内容太短 ({len(result)} 字符)"
    print(f"  ✅ API 调用成功，返回 {len(result)} 字符")

    # 验证 HTML 标签
    has_html = any(tag in result for tag in ['<h3>', '<ul>', '<li>', '<b>', '<a '])
    if has_html:
        print("  ✅ 包含 HTML 标签")
    else:
        print("  ⚠️  未检测到 HTML 标签（模型可能返回了纯文本，不影响功能）")

    # 验证中文内容
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in result)
    assert has_chinese, "总结中没有中文内容，翻译可能未生效"
    print("  ✅ 包含中文内容")

    print(f"  📄 预览: {result[:200]}...")
    return True


def test_enhance_with_ai_full_chain():
    """测试 4: enhance_with_ai 完整链路"""
    print("\n--- 测试 4: enhance_with_ai 完整链路 ---")
    from ai_summarizer import AISummarizer

    config = load_config()
    config.setdefault('ai_summary', {})['enabled'] = True

    summarizer = AISummarizer(config)

    result = call_with_retry(
        lambda: summarizer.enhance_with_ai(MOCK_SOURCES_DATA),
        "enhance_with_ai"
    )

    assert result is not None, f"enhance_with_ai 在 {MAX_RETRIES} 次重试后仍返回 None"
    assert len(result) > 100, f"总结内容太短 ({len(result)} 字符)"
    print(f"  ✅ 完整链路测试通过，总结 {len(result)} 字符")
    return True


def test_ai_disabled():
    """测试 5: AI 禁用时的行为"""
    print("\n--- 测试 5: AI 禁用行为 ---")
    from ai_summarizer import AISummarizer

    config = load_config()
    config.setdefault('ai_summary', {})['enabled'] = False

    summarizer = AISummarizer(config)
    assert not summarizer.is_enabled(), "is_enabled() 应该返回 False"

    result = summarizer.enhance_with_ai(MOCK_SOURCES_DATA)
    assert result is None, "AI 禁用时应返回 None"
    print("  ✅ AI 禁用时正确返回 None")
    return True


def main():
    print("=" * 60)
    print("🧪 测试 06: AI 总结功能（实际 API 调用）")
    print("=" * 60)

    if not load_env():
        sys.exit(1)

    tests = [
        ("API Key 验证", test_openrouter_api_key),
        ("客户端初始化", test_openrouter_init),
        ("API 调用 & 内容验证", test_api_call_and_content),
        ("完整链路测试", test_enhance_with_ai_full_chain),
        ("AI 禁用行为", test_ai_disabled),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ 断言失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"📊 结果: {passed} 通过, {failed} 失败 (共 {passed + failed} 个测试)")
    print(f"{'=' * 60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
