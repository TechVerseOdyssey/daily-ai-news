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
    
    # 使用内联样式避免CSS解析问题
    html_parts = []
    html_parts.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:15px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;background:#f0f2f5;line-height:1.6;">
    <div style="max-width:700px;margin:0 auto;background:#ffffff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);overflow:hidden;">
        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:24px 20px;text-align:center;">
            <h1 style="font-size:24px;font-weight:700;margin:0 0 6px 0;">🤖 AI 每日新闻摘要</h1>
            <div style="font-size:14px;opacity:0.9;">{today} {weekday}</div>
        </div>
        <table style="width:100%;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;" cellpadding="0" cellspacing="0">
            <tr>
                <td style="width:33.33%;text-align:center;padding:12px 8px;"><div style="font-size:22px;font-weight:bold;">{len(sources_data)}</div><div style="font-size:12px;opacity:0.9;margin-top:2px;">数据源</div></td>
                <td style="width:33.33%;text-align:center;padding:12px 8px;border-left:1px solid rgba(255,255,255,0.2);border-right:1px solid rgba(255,255,255,0.2);"><div style="font-size:22px;font-weight:bold;">{sum(len(source['items']) for source in sources_data)}</div><div style="font-size:12px;opacity:0.9;margin-top:2px;">新闻条数</div></td>
                <td style="width:33.33%;text-align:center;padding:12px 8px;"><div style="font-size:22px;font-weight:bold;">24h</div><div style="font-size:12px;opacity:0.9;margin-top:2px;">时效性</div></td>
            </tr>
        </table>
        <div style="padding:20px;">
""")
    
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
        
        html_parts.append(f"""
            <div style="margin-bottom:24px;">
                <div style="margin-bottom:12px;padding-bottom:10px;border-bottom:2px solid #667eea;">
                    <span style="display:inline-block;width:28px;height:28px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:6px;text-align:center;line-height:28px;font-size:14px;margin-right:10px;vertical-align:middle;">{icon}</span>
                    <span style="font-size:18px;font-weight:600;color:#2d3748;vertical-align:middle;">{source['source']}</span>
                </div>
                <ul style="list-style:none;margin:0;padding:0;">
""")
        
        for item in source['items']:
            html_parts.append(f"""
                    <li style="background:#f8f9fa;border-radius:8px;padding:14px 16px;margin-bottom:10px;border-left:3px solid #667eea;">
                        <div style="font-size:15px;font-weight:600;line-height:1.4;margin-bottom:6px;">
                            <a href="{item['link']}" target="_blank" style="color:#2d3748;text-decoration:none;">{item['title']}</a>
                        </div>
                        <div style="color:#666;font-size:13px;line-height:1.5;">{item['summary']}</div>
                        <a href="{item['link']}" target="_blank" style="display:inline-block;margin-top:8px;color:#667eea;font-size:12px;font-weight:500;text-decoration:none;">阅读全文 →</a>
                    </li>
""")
        
        html_parts.append("""
                </ul>
            </div>
""")
    
    html_parts.append(f"""
        </div>
        <div style="background:#f8f9fa;padding:16px;text-align:center;border-top:1px solid #e9ecef;">
            <p style="color:#888;font-size:12px;margin:0;">🤖 AI 新闻摘要 · {datetime.now().strftime('%Y-%m-%d %H:%M')} · ⚡ 智能抓取</p>
        </div>
    </div>
</body>
</html>
""")
    
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
    # 查找内容区域的开始位置（padding:20px 的 div）
    content_marker = '<div style="padding:20px;">'
    body_start = basic_html.find(content_marker)
    
    if body_start == -1:
        # 如果找不到，直接返回原始HTML
        return basic_html
    
    # 构建 AI 增强版邮件：在内容区域前插入AI总结
    ai_summary_html = f"""
        <div style="background:linear-gradient(135deg,#fff3e0 0%,#ffe0b2 100%);padding:16px 20px;border-bottom:1px solid #ffcc80;">
            <div style="margin-bottom:10px;">
                <span style="display:inline-block;width:24px;height:24px;background:#ff9800;border-radius:6px;text-align:center;line-height:24px;font-size:12px;margin-right:8px;vertical-align:middle;">✨</span>
                <span style="color:#e65100;font-size:16px;font-weight:600;vertical-align:middle;">AI 智能总结</span>
            </div>
            <div style="background:rgba(255,255,255,0.9);padding:14px;border-radius:8px;color:#333;line-height:1.7;font-size:14px;">
                {ai_summary}
            </div>
        </div>
        """
    
    enhanced_html = basic_html[:body_start] + ai_summary_html + basic_html[body_start:]
    
    return enhanced_html
