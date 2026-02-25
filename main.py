# Copyright 2026 Daily AI News Project
# Licensed under the MIT License

"""
AI 每日新闻摘要 - 主程序
整合新闻抓取、AI 总结、邮件发送三个模块
"""

import os
import yaml

from news_fetcher import NewsFetcher
from ai_summarizer import AISummarizer
from email_sender import EmailSender
from email_template import generate_basic_html, wrap_with_ai_summary


def get_config_path():
    """获取配置文件的绝对路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'config.yaml')


def load_config():
    """加载配置文件"""
    with open(get_config_path(), 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_env():
    """从 .env 文件加载环境变量（不覆盖已有的）"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key, value = key.strip(), value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value


def main():
    """主程序入口"""
    print("=" * 60)
    print("🤖 AI 每日新闻摘要 - 开始运行")
    print("=" * 60)
    
    # 加载 .env 环境变量（本地开发用，CI 环境会被 secrets 覆盖）
    load_env()
    
    # 加载配置
    config = load_config()
    
    # 初始化各模块
    fetcher = NewsFetcher(config)
    summarizer = AISummarizer(config)
    email_sender = EmailSender(config)
    
    # 1. 抓取数据（结构化）
    sources_data = fetcher.fetch_all()
    
    if not sources_data:
        print("\n❌ 没有抓取到任何数据，终止运行。")
        raise SystemExit(1)
    
    total_items_before = sum(len(source['items']) for source in sources_data)
    print(f"\n📊 原始数据: {len(sources_data)} 个数据源，共 {total_items_before} 条新闻")
    
    # 2. 按关键词相关度排序并限制总数量
    max_total_items = config.get('crawler_settings', {}).get('max_total_items', 100)
    print(f"\n🔄 正在按关键词相关度排序（上限 {max_total_items} 条）...")
    sources_data = fetcher.sort_and_limit_items(sources_data, max_total_items)
    
    total_items_after = sum(len(source['items']) for source in sources_data)
    print(f"  ✅ 排序完成: {len(sources_data)} 个数据源，共 {total_items_after} 条新闻")
    
    # 3. 生成基础 HTML 内容（必须成功，作为后备）
    print("\n正在生成基础 HTML 内容...")
    freshness_hours = config.get('crawler_settings', {}).get('content_freshness_hours', 24)
    basic_html = generate_basic_html(sources_data, freshness_hours=freshness_hours)
    print("  ✅ 基础内容生成成功")
    
    # 4. 尝试用 AI 增强内容（根据配置决定是否启用）
    ai_summary = summarizer.enhance_with_ai(sources_data)
    
    # 5. 准备最终邮件内容
    if ai_summary:
        final_html = wrap_with_ai_summary(basic_html, ai_summary)
        print("  ✅ AI 总结生成成功，将使用增强版邮件")
    else:
        final_html = basic_html
        if summarizer.is_enabled():
            print("  ⚠️  AI 总结生成失败，将使用基础版邮件（仍包含完整内容）")
    
    # 6. 打印邮件内容到控制台
    print("\n" + "=" * 60)
    print("📄 邮件 HTML 内容预览:")
    print("=" * 60)
    print(final_html)
    print("=" * 60)
    
    # 7. 发送邮件（有邮件配置时才发送）
    email_user = os.environ.get("EMAIL_USER")
    email_password = os.environ.get("EMAIL_PASSWORD")
    email_receiver = os.environ.get("EMAIL_RECEIVER")
    
    if email_user and email_password and email_receiver:
        print("\n开始发送邮件...")
        email_sent = email_sender.send(final_html)
        
        if email_sent:
            print("\n" + "=" * 60)
            print("✅ 任务完成！邮件已发送")
            if ai_summary:
                print("   📧 邮件类型: AI 增强版（包含智能总结）")
            else:
                print("   📧 邮件类型: 基础版（包含所有原始内容）")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ 邮件发送失败！")
            print("=" * 60)
            raise SystemExit(1)
    else:
        print("\n⏭️  未配置邮件凭证（EMAIL_USER/EMAIL_PASSWORD/EMAIL_RECEIVER），跳过邮件发送")
        print("✅ 任务完成！（仅控制台输出）")


if __name__ == "__main__":
    main()
