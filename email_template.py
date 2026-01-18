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
    
    html_parts = []
    html_parts.append(f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
            position: relative;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" fill="none"/><circle cx="10" cy="10" r="2" fill="rgba(255,255,255,0.1)"/></svg>');
            opacity: 0.5;
        }}
        
        .header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
            position: relative;
            z-index: 1;
        }}
        
        .header .date {{
            font-size: 16px;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }}
        
        .stats {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 10px;
        }}
        
        .stat-number {{
            font-size: 28px;
            font-weight: bold;
            display: block;
        }}
        
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
            margin-top: 5px;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .source-section {{
            margin-bottom: 40px;
        }}
        
        .source-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}
        
        .source-icon {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            font-size: 20px;
        }}
        
        .source-title {{
            font-size: 22px;
            font-weight: 600;
            color: #2d3748;
        }}
        
        .news-list {{
            list-style: none;
        }}
        
        .news-item {{
            background: #f7fafc;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .news-item:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }}
        
        .news-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
            line-height: 1.4;
        }}
        
        .news-title a {{
            color: #2d3748;
            text-decoration: none;
            transition: color 0.3s ease;
        }}
        
        .news-title a:hover {{
            color: #667eea;
        }}
        
        .news-summary {{
            color: #718096;
            font-size: 14px;
            line-height: 1.6;
            margin-top: 8px;
        }}
        
        .read-more {{
            display: inline-block;
            margin-top: 10px;
            color: #667eea;
            font-size: 14px;
            font-weight: 500;
            text-decoration: none;
        }}
        
        .read-more::after {{
            content: ' →';
            transition: transform 0.3s ease;
            display: inline-block;
        }}
        
        .read-more:hover::after {{
            transform: translateX(5px);
        }}
        
        .footer {{
            background: #f7fafc;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}
        
        .footer-text {{
            color: #718096;
            font-size: 13px;
            margin: 5px 0;
        }}
        
        .footer-icon {{
            font-size: 24px;
            margin-bottom: 10px;
        }}
        
        @media (max-width: 600px) {{
            .header h1 {{
                font-size: 24px;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            .source-title {{
                font-size: 18px;
            }}
            
            .news-title {{
                font-size: 16px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI 每日新闻摘要</h1>
            <div class="date">{today} {weekday}</div>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <span class="stat-number">{len(sources_data)}</span>
                <span class="stat-label">数据源</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{sum(len(source['items']) for source in sources_data)}</span>
                <span class="stat-label">新闻条数</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">24h</span>
                <span class="stat-label">时效性</span>
            </div>
        </div>
        
        <div class="content">
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
            <div class="source-section">
                <div class="source-header">
                    <div class="source-icon">{icon}</div>
                    <div class="source-title">{source['source']}</div>
                </div>
                <ul class="news-list">
""")
        
        for item in source['items']:
            html_parts.append(f"""
                    <li class="news-item">
                        <div class="news-title">
                            <a href="{item['link']}" target="_blank">{item['title']}</a>
                        </div>
                        <div class="news-summary">{item['summary']}</div>
                        <a href="{item['link']}" target="_blank" class="read-more">阅读全文</a>
                    </li>
""")
        
        html_parts.append("""
                </ul>
            </div>
""")
    
    html_parts.append(f"""
        </div>
        
        <div class="footer">
            <div class="footer-icon">🤖</div>
            <p class="footer-text">本邮件由 AI 新闻摘要系统自动生成</p>
            <p class="footer-text">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p class="footer-text" style="margin-top: 15px; color: #a0aec0;">
                ⚡ 智能抓取 · 自动过滤 · 精准推送
            </p>
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
    # 提取 body 内容部分
    body_start = basic_html.find('<div class="content">')
    body_end = basic_html.find('</div>', basic_html.find('<div class="footer">'))
    
    # 构建 AI 增强版邮件
    enhanced_html = basic_html[:body_start] + f"""
        <div class="ai-summary-section" style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); padding: 30px; margin: 0;">
            <div style="max-width: 800px; margin: 0 auto;">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div style="width: 50px; height: 50px; background: rgba(255,255,255,0.9); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-right: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        ✨
                    </div>
                    <h2 style="margin: 0; color: #2d3748; font-size: 24px; font-weight: 700;">AI 智能总结</h2>
                </div>
                <div style="background: rgba(255,255,255,0.95); padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); color: #2d3748; line-height: 1.8; font-size: 15px;">
                    {ai_summary}
                </div>
            </div>
        </div>
        """ + basic_html[body_start:]
    
    return enhanced_html
