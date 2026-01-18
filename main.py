import os
import yaml
import feedparser
import yagmail
from google import genai
from datetime import datetime, timedelta, timezone
import time
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import html
import re
import json
import hashlib

# 1. 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 2. 配置 Gemini (使用 google-genai 新版 API)
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


def get_available_model():
    """
    获取可用的免费 Gemini 模型
    优先使用配置文件中指定的模型，如果不可用则自动选择
    
    Returns:
        str: 可用的模型名称
    """
    # 优先尝试的模型列表（按优先级排序）
    preferred_models = [
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro',
    ]
    
    # 如果配置文件中指定了模型，优先尝试
    config_model = config.get('gemini', {}).get('model_name', '')
    if config_model and config_model not in preferred_models:
        preferred_models.insert(0, config_model)
    
    try:
        # 获取可用模型列表
        print("正在获取可用的 Gemini 模型...")
        available_models = []
        
        for model in client.models.list():
            model_name = model.name
            # 模型名称格式: models/gemini-2.0-flash -> gemini-2.0-flash
            if model_name.startswith('models/'):
                model_name = model_name[7:]
            available_models.append(model_name)
        
        print(f"  发现 {len(available_models)} 个可用模型")
        
        # 按优先级选择模型
        for preferred in preferred_models:
            # 精确匹配
            if preferred in available_models:
                print(f"  ✓ 选择模型: {preferred}")
                return preferred
            # 前缀匹配（如 gemini-2.0-flash 匹配 gemini-2.0-flash-exp）
            for available in available_models:
                if available.startswith(preferred):
                    print(f"  ✓ 选择模型: {available}")
                    return available
        
        # 如果都没有，选择第一个包含 'flash' 的模型（通常是免费的）
        for available in available_models:
            if 'flash' in available.lower():
                print(f"  ✓ 选择模型: {available}")
                return available
        
        # 最后兜底：返回第一个 gemini 模型
        for available in available_models:
            if 'gemini' in available.lower():
                print(f"  ✓ 选择模型: {available}")
                return available
        
        # 如果实在找不到，返回配置的默认值
        print(f"  ⚠ 未找到可用模型，使用配置默认值: {config_model}")
        return config_model
        
    except Exception as e:
        print(f"  ⚠ 获取模型列表失败: {e}")
        # 返回配置的默认值
        fallback = config.get('gemini', {}).get('model_name', 'gemini-2.0-flash')
        print(f"  使用默认模型: {fallback}")
        return fallback

# 3. 请求头配置 - 模拟真实浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, application/atom+xml, text/xml, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0'
}

# 4. 缓存目录
CACHE_DIR = '.cache'
os.makedirs(CACHE_DIR, exist_ok=True)


def clean_html_content(html_text):
    """
    高级 HTML 清理函数
    
    Args:
        html_text: 原始 HTML 文本
    
    Returns:
        str: 清理后的纯文本
    """
    if not html_text:
        return ""
    
    # 1. 使用 BeautifulSoup 移除 HTML 标签
    soup = BeautifulSoup(html_text, "html.parser")
    
    # 2. 移除 script 和 style 标签
    for script in soup(["script", "style"]):
        script.decompose()
    
    # 3. 获取文本
    text = soup.get_text()
    
    # 4. HTML 实体解码
    text = html.unescape(text)
    
    # 5. 清理多余的空白字符和换行
    text = re.sub(r'\s+', ' ', text)  # 多个空白符替换为单个空格
    text = re.sub(r'\n\s*\n', '\n', text)  # 多个连续换行替换为单个换行
    
    # 6. 去除首尾空白
    text = text.strip()
    
    return text


def validate_item_content(title, link, description):
    """
    验证抓取的单条内容是否有效
    
    Args:
        title: 标题
        link: 链接
        description: 描述
    
    Returns:
        bool: 内容是否有效
    """
    # 1. 标题检查
    if not title or title == '无标题' or len(title.strip()) < 3:
        return False
    
    # 2. 链接检查
    if not link or not link.startswith('http'):
        return False
    
    # 3. 描述检查（可以为空，但如果有应该有一定长度）
    if description and len(description.strip()) < 10:
        # 描述过短，可能是无意义内容
        if description.strip() not in ['无摘要', '']:
            return False
    
    # 4. 过滤广告关键词
    spam_keywords = ['广告', '推广', 'AD', 'sponsored', 'advertisement']
    title_lower = title.lower()
    for keyword in spam_keywords:
        if keyword.lower() in title_lower:
            return False
    
    return True


def is_content_fresh(item, hours=24):
    """
    检查内容是否是最近发布的（日期过滤）
    
    Args:
        item: feedparser 的 entry 对象
        hours: 时间窗口（小时），默认24小时
    
    Returns:
        bool: 是否是新鲜内容
    """
    # 尝试获取发布时间
    published_time = None
    
    # 尝试不同的时间字段
    for time_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
        if hasattr(item, time_field):
            time_struct = getattr(item, time_field)
            if time_struct:
                try:
                    # 转换为 datetime
                    published_time = datetime(*time_struct[:6], tzinfo=timezone.utc)
                    break
                except:
                    continue
    
    # 如果没有时间信息，默认认为是新内容（保留）
    if not published_time:
        return True
    
    # 计算时间差
    now = datetime.now(timezone.utc)
    time_diff = now - published_time
    
    # 检查是否在时间窗口内
    return time_diff.total_seconds() <= hours * 3600


def parse_arxiv_entry(item):
    """
    特殊处理 Arxiv API 返回的条目格式
    
    Args:
        item: feedparser entry
    
    Returns:
        tuple: (title, link, description)
    """
    # Arxiv 特殊格式处理
    title = item.get('title', '').replace('\n', ' ').strip()
    
    # Arxiv 的链接通常在 id 字段或 link 字段
    link = item.get('id', item.get('link', ''))
    
    # Arxiv 的摘要在 summary 字段
    description = item.get('summary', '')
    
    # Arxiv 可能还有作者信息
    authors = []
    if 'authors' in item:
        for author in item['authors']:
            if 'name' in author:
                authors.append(author['name'])
    
    # 如果有作者，添加到描述中
    if authors:
        author_str = ', '.join(authors[:3])  # 只取前3个作者
        if len(authors) > 3:
            author_str += ' et al.'
        description = f"作者: {author_str}. {description}"
    
    return title, link, description


def save_cache(cache_key, data):
    """
    保存数据到缓存
    
    Args:
        cache_key: 缓存键
        data: 要缓存的数据
    """
    try:
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'data': data
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"缓存保存失败: {e}")


def load_cache(cache_key, max_age_hours=24):
    """
    从缓存加载数据
    
    Args:
        cache_key: 缓存键
        max_age_hours: 缓存最大年龄（小时）
    
    Returns:
        缓存的数据，如果不存在或过期返回 None
    """
    try:
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        if not os.path.exists(cache_file):
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 检查缓存是否过期
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        now = datetime.now()
        if (now - cache_time).total_seconds() > max_age_hours * 3600:
            return None
        
        return cache_data['data']
    except Exception as e:
        print(f"缓存加载失败: {e}")
        return None

def fetch_single_feed_structured(feed_conf, retry_count=3):
    """
    抓取单个 RSS 源并返回结构化数据（用于新架构）
    
    Returns:
        dict: {'source': '数据源名称', 'items': [{'title': '...', 'link': '...', 'summary': '...'}]}
    """
    feed_name = feed_conf['name']
    feed_url = feed_conf['url']
    max_items = feed_conf.get('max_items', 3)
    is_arxiv = feed_conf.get('type') == 'arxiv' or 'arxiv' in feed_url.lower()
    
    # 检查缓存
    cache_key = hashlib.md5(feed_url.encode()).hexdigest()
    cached_data = load_cache(cache_key + '_structured', max_age_hours=6)
    if cached_data:
        print(f"  📦 {feed_name} 使用缓存数据")
        return cached_data
    
    for attempt in range(retry_count):
        try:
            if attempt > 0:
                wait_time = 2 ** (attempt - 1)
                print(f"  - 重试 {feed_name} (第 {attempt + 1}/{retry_count} 次，等待 {wait_time}秒)...")
                time.sleep(wait_time)
            
            print(f"正在抓取: {feed_name}...")
            response = requests.get(
                feed_url, 
                headers=HEADERS,
                timeout=(10, 30),
                allow_redirects=True
            )
            response.raise_for_status()
            
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                response.encoding = response.apparent_encoding or 'utf-8'
            
            feed = feedparser.parse(response.content)
            
            if feed.bozo and not is_arxiv:
                if attempt < retry_count - 1:
                    print(f"  - 警告: {feed_name} 格式解析错误，将重试...")
                    continue
            
            if not feed.entries:
                print(f"  - 警告: {feed_name} 没有找到任何条目")
                return None
            
            time_window_hours = feed_conf.get('custom_freshness_hours', 
                                             config.get('crawler_settings', {}).get('content_freshness_hours', 168))
            
            items = []
            filtered_by_date = 0
            filtered_by_validation = 0
            
            for item in feed.entries[:max_items * 2]:
                if len(items) >= max_items:
                    break
                
                if not is_content_fresh(item, hours=time_window_hours):
                    filtered_by_date += 1
                    continue
                
                if is_arxiv:
                    title, link, desc = parse_arxiv_entry(item)
                else:
                    title = item.get('title', '无标题')
                    link = item.get('link', '')
                    desc = item.get('description', item.get('summary', ''))
                
                clean_desc = clean_html_content(desc)
                if len(clean_desc) > 300:
                    clean_desc = clean_desc[:300] + "..."
                elif not clean_desc:
                    clean_desc = "无摘要"
                
                if not validate_item_content(title, link, clean_desc):
                    filtered_by_validation += 1
                    continue
                
                items.append({
                    'title': title,
                    'link': link,
                    'summary': clean_desc
                })
            
            if not items:
                print(f"  - 警告: {feed_name} 所有内容都被过滤掉了（日期过滤: {filtered_by_date}, 验证失败: {filtered_by_validation}）")
                return None
            
            status_msg = f"  ✓ {feed_name} 抓取成功 ({len(items)} 条有效"
            if filtered_by_date > 0 or filtered_by_validation > 0:
                status_msg += f", 过滤: 日期{filtered_by_date}+验证{filtered_by_validation}"
            status_msg += ")"
            print(status_msg)
            
            result = {
                'source': feed_name,
                'items': items
            }
            
            # 保存到缓存
            save_cache(cache_key + '_structured', result)
            
            return result
            
        except requests.exceptions.Timeout:
            if attempt == retry_count - 1:
                print(f"  ✗ {feed_name} 抓取失败：连接超时")
                return None
        except requests.exceptions.RequestException as e:
            if attempt == retry_count - 1:
                print(f"  ✗ {feed_name} 抓取失败：{str(e)}")
                return None
        except Exception as e:
            if attempt == retry_count - 1:
                print(f"  ✗ {feed_name} 抓取失败：{str(e)}")
                return None
    
    return None


def fetch_feeds():
    """
    并发抓取所有 RSS 源并返回结构化数据
    使用线程池实现并发，提高抓取效率
    
    Returns:
        list: 包含每个源的字典列表 [{'source': '...', 'items': [{'title': '...', 'link': '...', 'summary': '...'}]}]
    """
    print("开始抓取数据...")
    print(f"共有 {len(config['feeds'])} 个数据源")
    
    all_sources = []
    feeds_config = config['feeds']
    
    # 获取配置的并发数和速率限制
    max_workers = config.get('crawler_settings', {}).get('max_workers', 5)
    rate_limit = config.get('crawler_settings', {}).get('rate_limit_seconds', 0.5)
    
    # 使用线程池并发抓取
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_feed = {
            executor.submit(fetch_single_feed_structured, feed_conf): feed_conf 
            for feed_conf in feeds_config
        }
        
        # 处理完成的任务
        for i, future in enumerate(as_completed(future_to_feed)):
            feed_conf = future_to_feed[future]
            try:
                result = future.result()
                if result and result['items']:
                    all_sources.append(result)
                
                # 速率限制：每抓取完一个源，等待一段时间（避免过快请求）
                if i < len(feeds_config) - 1:  # 最后一个不需要等待
                    time.sleep(rate_limit)
                    
            except Exception as e:
                print(f"  ✗ {feed_conf['name']} 处理失败: {str(e)}")
    
    print(f"\n抓取完成: 成功 {len(all_sources)}/{len(feeds_config)} 个数据源")
    return all_sources

def generate_basic_html(sources_data):
    """
    生成基础 HTML 邮件内容（不依赖大模型）
    
    Args:
        sources_data: list of dict, [{'source': '...', 'items': [{'title': '...', 'link': '...', 'summary': '...'}]}]
    
    Returns:
        str: HTML 格式的邮件内容
    """
    today = datetime.now().strftime('%Y年%m月%d日')
    
    html_parts = []
    html_parts.append(f"""
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333; }}
        h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h3 {{ color: #34495e; margin-top: 30px; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin: 15px 0; padding: 10px; background: #f8f9fa; border-left: 3px solid #3498db; }}
        a {{ color: #2980b9; text-decoration: none; font-weight: bold; }}
        a:hover {{ text-decoration: underline; }}
        p {{ margin: 5px 0; color: #666; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <h2>🤖 AI 每日新闻摘要 - {today}</h2>
""")
    
    total_items = sum(len(source['items']) for source in sources_data)
    html_parts.append(f"<p>📊 今日共抓取 <b>{len(sources_data)}</b> 个数据源，<b>{total_items}</b> 条新闻</p>")
    html_parts.append("<hr>")
    
    for source in sources_data:
        html_parts.append(f"\n<h3>📰 {source['source']}</h3>")
        html_parts.append("<ul>")
        
        for item in source['items']:
            html_parts.append(f"""
    <li>
        <a href="{item['link']}" target="_blank">{item['title']}</a>
        <p>{item['summary']}</p>
    </li>
""")
        
        html_parts.append("</ul>")
    
    html_parts.append(f"""
    <div class="footer">
        <p>本邮件由 AI 新闻摘要系统自动生成</p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
""")
    
    return "".join(html_parts)


def generate_summary(content):
    """调用 Gemini 生成 HTML 早报"""
    print("正在调用 Gemini 进行总结 (可能需要十几秒)...")
    full_prompt = config['prompt'] + "\n" + content
    
    # 自动获取可用模型
    model_name = get_available_model()
    
    try:
        # 使用 google-genai 新版 API (主要方式)
        print(f"使用模型: {model_name}")
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini API 调用失败: {e}")
        # 尝试使用备用方法 (google-generativeai 旧版 API)
        try:
            print("尝试使用备用 API 格式 (google-generativeai)...")
            import google.generativeai as genai_old
            genai_old.configure(api_key=os.environ["GOOGLE_API_KEY"])
            backup_model = genai_old.GenerativeModel(model_name)
            backup_response = backup_model.generate_content(full_prompt)
            return backup_response.text
        except Exception as e2:
            print(f"备用方法也失败: {e2}")
            return None


def try_enhance_with_ai(sources_data):
    """
    尝试用大模型增强内容（可选功能，失败不影响主流程）
    
    Args:
        sources_data: 结构化的数据源列表
    
    Returns:
        str or None: AI 生成的总结（HTML 格式），失败返回 None
    """
    try:
        # 将结构化数据转为文本用于大模型
        content_parts = []
        for source in sources_data:
            content_parts.append(f"\n\n--- 来源：{source['source']} ---")
            for item in source['items']:
                content_parts.append(f"\n标题: {item['title']}")
                content_parts.append(f"链接: {item['link']}")
                content_parts.append(f"摘要: {item['summary']}\n")
        
        content_text = "\n".join(content_parts)
        
        # 调用 AI 生成总结
        ai_summary = generate_summary(content_text)
        
        if ai_summary:
            print("  ✅ AI 总结生成成功")
            return ai_summary
        else:
            print("  ⚠️  AI 总结生成失败，将使用基础版本")
            return None
            
    except Exception as e:
        print(f"  ⚠️  AI 增强功能异常: {e}")
        return None

def send_email(html_content):
    """发送邮件，返回是否成功"""
    print("正在发送邮件...")
    try:
        user = os.environ["EMAIL_USER"]
        password = os.environ["EMAIL_PASSWORD"]
        receiver = config['email_settings']['receiver']
        subject = f"{config['email_settings']['subject']} ({datetime.now().strftime('%Y-%m-%d')})"
        smtp_host = config['email_settings'].get('smtp_host', 'smtp.gmail.com')
        smtp_port = config['email_settings'].get('smtp_port', 465)  # QQ邮箱默认465
        
        yag = yagmail.SMTP(user=user, password=password, host=smtp_host, port=smtp_port)
        yag.send(
            to=receiver,
            subject=subject,
            contents=[html_content] # yagmail 自动识别 HTML
        )
        print("邮件发送成功！")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

# 主程序
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 AI 每日新闻摘要 - 开始运行")
    print("=" * 60)
    
    # 1. 抓取数据（结构化）
    sources_data = fetch_feeds()
    
    if not sources_data or len(sources_data) == 0:
        print("\n❌ 没有抓取到任何数据，终止运行。")
        exit(1)
    
    total_items = sum(len(source['items']) for source in sources_data)
    print(f"\n📊 数据统计: {len(sources_data)} 个数据源，共 {total_items} 条新闻")
    
    # 2. 生成基础 HTML 内容（必须成功，作为后备）
    print("\n正在生成基础 HTML 内容...")
    basic_html = generate_basic_html(sources_data)
    print("  ✅ 基础内容生成成功")
    
    # 3. 尝试用 AI 增强内容（等待结果，但失败不终止）
    print("\n正在尝试使用 AI 生成智能总结...")
    print("  ⏳ 等待大模型响应（这可能需要10-30秒）...")
    ai_summary = try_enhance_with_ai(sources_data)
    
    # 4. 准备最终邮件内容
    if ai_summary:
        # 如果有 AI 总结，将其放在邮件顶部
        final_html = f"""
<html>
<head><meta charset="UTF-8"></head>
<body>
    <h2>🌟 AI 智能总结</h2>
    <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin-bottom: 30px;">
        {ai_summary}
    </div>
    <hr>
    <h2>📰 详细内容</h2>
    {basic_html[basic_html.find('<body>') + 6:basic_html.find('</body>')]}
</body>
</html>
"""
        print("  ✅ AI 总结生成成功，将使用增强版邮件")
    else:
        final_html = basic_html
        print("  ⚠️  AI 总结生成失败，将使用基础版邮件（仍包含完整内容）")
    
    # 5. 发送邮件（必须成功）
    print("\n开始发送邮件...")
    email_sent = send_email(final_html)
    
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
        exit(1)
