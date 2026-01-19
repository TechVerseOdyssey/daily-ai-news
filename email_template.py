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
<body style="margin:0;padding:20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);line-height:1.6;">
    <div style="max-width:800px;margin:0 auto;background:#ffffff;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.3);overflow:hidden;">
        <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:40px 30px;text-align:center;">
            <h1 style="font-size:32px;font-weight:700;margin:0 0 10px 0;">🤖 AI 每日新闻摘要</h1>
            <div style="font-size:16px;opacity:0.9;">{today} {weekday}</div>
        </div>
        <div style="background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;padding:20px 30px;text-align:center;">
            <span style="display:inline-block;text-align:center;padding:10px 20px;"><span style="font-size:28px;font-weight:bold;">{len(sources_data)}</span><br><span style="font-size:14px;opacity:0.9;">数据源</span></span>
            <span style="display:inline-block;text-align:center;padding:10px 20px;"><span style="font-size:28px;font-weight:bold;">{sum(len(source['items']) for source in sources_data)}</span><br><span style="font-size:14px;opacity:0.9;">新闻条数</span></span>
            <span style="display:inline-block;text-align:center;padding:10px 20px;"><span style="font-size:28px;font-weight:bold;">24h</span><br><span style="font-size:14px;opacity:0.9;">时效性</span></span>
        </div>
        <div style="padding:30px;">
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
            <div style="margin-bottom:40px;">
                <div style="display:flex;align-items:center;margin-bottom:20px;padding-bottom:15px;border-bottom:3px solid #667eea;">
                    <div style="width:40px;height:40px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:10px;display:flex;align-items:center;justify-content:center;margin-right:15px;font-size:20px;">{icon}</div>
                    <div style="font-size:22px;font-weight:600;color:#2d3748;">{source['source']}</div>
                </div>
                <ul style="list-style:none;margin:0;padding:0;">
""")
        
        for item in source['items']:
            html_parts.append(f"""
                    <li style="background:#f7fafc;border-radius:12px;padding:20px;margin-bottom:15px;border-left:4px solid #667eea;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size:18px;font-weight:600;margin-bottom:10px;line-height:1.4;">
                            <a href="{item['link']}" target="_blank" style="color:#2d3748;text-decoration:none;">{item['title']}</a>
                        </div>
                        <div style="color:#718096;font-size:14px;line-height:1.6;margin-top:8px;">{item['summary']}</div>
                        <a href="{item['link']}" target="_blank" style="display:inline-block;margin-top:10px;color:#667eea;font-size:14px;font-weight:500;text-decoration:none;">阅读全文 →</a>
                    </li>
""")
        
        html_parts.append("""
                </ul>
            </div>
""")
    
    html_parts.append(f"""
        </div>
        <div style="background:#f7fafc;padding:30px;text-align:center;border-top:1px solid #e2e8f0;">
            <div style="font-size:24px;margin-bottom:10px;">🤖</div>
            <p style="color:#718096;font-size:13px;margin:5px 0;">本邮件由 AI 新闻摘要系统自动生成</p>
            <p style="color:#718096;font-size:13px;margin:5px 0;">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="color:#a0aec0;font-size:13px;margin:15px 0 5px 0;">⚡ 智能抓取 · 自动过滤 · 精准推送</p>
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
    # 查找内容区域的开始位置（padding:30px 的 div）
    content_marker = '<div style="padding:30px;">'
    body_start = basic_html.find(content_marker)
    
    if body_start == -1:
        # 如果找不到，直接返回原始HTML
        return basic_html
    
    # 构建 AI 增强版邮件：在内容区域前插入AI总结
    ai_summary_html = f"""
        <div style="background:linear-gradient(135deg,#ffecd2 0%,#fcb69f 100%);padding:30px;margin:0;">
            <div style="max-width:800px;margin:0 auto;">
                <div style="margin-bottom:20px;">
                    <span style="display:inline-block;width:50px;height:50px;background:rgba(255,255,255,0.9);border-radius:12px;text-align:center;line-height:50px;font-size:24px;margin-right:15px;box-shadow:0 4px 6px rgba(0,0,0,0.1);vertical-align:middle;">✨</span>
                    <span style="color:#2d3748;font-size:24px;font-weight:700;vertical-align:middle;">AI 智能总结</span>
                </div>
                <div style="background:rgba(255,255,255,0.95);padding:25px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1);color:#2d3748;line-height:1.8;font-size:15px;">
                    {ai_summary}
                </div>
            </div>
        </div>
        """
    
    enhanced_html = basic_html[:body_start] + ai_summary_html + basic_html[body_start:]
    
    return enhanced_html
