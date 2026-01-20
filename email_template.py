"""
邮件模板模块
负责生成美观的 HTML 邮件内容
"""

from datetime import datetime


def generate_basic_html(sources_data):
    """
    生成基础 HTML 邮件内容（不依赖大模型）
    
    Args:
        sources_data: list of dict, [{'source': '...', 'items': [{'title': '...', 'link': '...', 'summary': '...'}]}]
    
    Returns:
        str: HTML 格式的邮件内容
    """
    today = datetime.now().strftime('%Y年%m月%d日')
    weekday = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][datetime.now().weekday()]
    
    # 使用内联样式避免CSS解析问题，紧凑HTML避免空白
    html_parts = []
    total_news = sum(len(source['items']) for source in sources_data)
    html_parts.append(f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>')
    html_parts.append(f'<body style="margin:0;padding:10px;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',\'PingFang SC\',sans-serif;background:#f0f2f5;line-height:1.5;">')
    html_parts.append(f'<div style="max-width:640px;margin:0 auto;background:#fff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.08);overflow:hidden;">')
    # 头部
    html_parts.append(f'<div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:16px;text-align:center;">')
    html_parts.append(f'<div style="font-size:20px;font-weight:700;margin-bottom:4px;">🤖 AI 每日新闻摘要</div>')
    html_parts.append(f'<div style="font-size:13px;opacity:0.9;">{today} {weekday}</div></div>')
    # 统计栏
    html_parts.append(f'<table style="width:100%;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:#fff;" cellpadding="0" cellspacing="0"><tr>')
    html_parts.append(f'<td style="width:33%;text-align:center;padding:10px 5px;"><b style="font-size:20px;">{len(sources_data)}</b><div style="font-size:11px;opacity:0.9;">数据源</div></td>')
    html_parts.append(f'<td style="width:34%;text-align:center;padding:10px 5px;border-left:1px solid rgba(255,255,255,0.2);border-right:1px solid rgba(255,255,255,0.2);"><b style="font-size:20px;">{total_news}</b><div style="font-size:11px;opacity:0.9;">新闻条数</div></td>')
    html_parts.append(f'<td style="width:33%;text-align:center;padding:10px 5px;"><b style="font-size:20px;">24h</b><div style="font-size:11px;opacity:0.9;">时效性</div></td>')
    html_parts.append(f'</tr></table>')
    # 内容区域
    html_parts.append(f'<div style="padding:12px 16px;">')
    
    # 数据源图标映射
    source_icons = {
        'OpenAI': '🚀',
        'Google': '🔍',
        'Arxiv': '📚',
        'MIT': '🎓',
        'DeepMind': '🧠',
        'VentureBeat': '💼',
        'Verge': '📱'
    }
    
    for source in sources_data:
        # 根据源名称选择图标
        icon = '📰'
        for key, emoji in source_icons.items():
            if key.lower() in source['source'].lower():
                icon = emoji
                break
        
        # 数据源标题
        html_parts.append(f'<div style="margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #667eea;">')
        html_parts.append(f'<span style="display:inline-block;width:22px;height:22px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:4px;text-align:center;line-height:22px;font-size:12px;margin-right:6px;vertical-align:middle;">{icon}</span>')
        html_parts.append(f'<span style="font-size:15px;font-weight:600;color:#2d3748;vertical-align:middle;">{source["source"]}</span></div>')
        
        for item in source['items']:
            html_parts.append(f'<div style="background:#f8f9fa;border-radius:6px;padding:10px 12px;margin-bottom:8px;border-left:3px solid #667eea;">')
            html_parts.append(f'<div style="font-size:14px;font-weight:600;line-height:1.3;margin-bottom:4px;"><a href="{item["link"]}" target="_blank" style="color:#2d3748;text-decoration:none;">{item["title"]}</a></div>')
            html_parts.append(f'<div style="color:#666;font-size:12px;line-height:1.4;">{item["summary"]}</div>')
            html_parts.append(f'<a href="{item["link"]}" target="_blank" style="display:inline-block;margin-top:6px;color:#667eea;font-size:11px;font-weight:500;text-decoration:none;">阅读全文 →</a></div>')
        
        # 数据源分隔
        html_parts.append('<div style="margin-bottom:12px;"></div>')
    
    # 页脚
    html_parts.append('</div>')
    html_parts.append(f'<div style="background:#f8f9fa;padding:10px;text-align:center;border-top:1px solid #e9ecef;">')
    html_parts.append(f'<span style="color:#888;font-size:11px;">🤖 AI新闻摘要 · {datetime.now().strftime("%Y-%m-%d %H:%M")} · ⚡智能抓取</span></div>')
    html_parts.append('</div></body></html>')
    
    return "".join(html_parts)


def wrap_with_ai_summary(basic_html, ai_summary):
    """
    将 AI 总结嵌入到基础 HTML 邮件中
    
    Args:
        basic_html: 基础 HTML 邮件内容
        ai_summary: AI 生成的总结内容
    
    Returns:
        str: 包含 AI 总结的完整 HTML 邮件
    """
    # 查找内容区域的开始位置
    content_marker = '<div style="padding:12px 16px;">'
    body_start = basic_html.find(content_marker)
    
    if body_start == -1:
        return basic_html
    
    # 构建 AI 增强版邮件：在内容区域前插入AI总结（紧凑格式）
    ai_summary_html = '<div style="background:linear-gradient(135deg,#fff3e0,#ffe0b2);padding:12px 16px;border-bottom:1px solid #ffcc80;">'
    ai_summary_html += '<div style="margin-bottom:8px;"><span style="display:inline-block;width:20px;height:20px;background:#ff9800;border-radius:4px;text-align:center;line-height:20px;font-size:10px;margin-right:6px;vertical-align:middle;">✨</span>'
    ai_summary_html += '<span style="color:#e65100;font-size:14px;font-weight:600;vertical-align:middle;">AI 智能总结</span></div>'
    ai_summary_html += f'<div style="background:rgba(255,255,255,0.9);padding:10px;border-radius:6px;color:#333;line-height:1.6;font-size:13px;">{ai_summary}</div></div>'
    
    enhanced_html = basic_html[:body_start] + ai_summary_html + basic_html[body_start:]
    
    return enhanced_html
