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

# 2. 配置 Gemini (使用新版 API)
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

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

def fetch_single_feed(feed_conf, retry_count=3):
    """
    抓取单个 RSS 源（带重试机制、日期过滤、数据验证）
    
    Args:
        feed_conf: RSS 源配置
        retry_count: 重试次数
    
    Returns:
        str: 格式化的内容文本，失败返回 None
    """
    feed_name = feed_conf['name']
    feed_url = feed_conf['url']
    max_items = feed_conf.get('max_items', 3)
    is_arxiv = feed_conf.get('type') == 'arxiv' or 'arxiv' in feed_url.lower()
    
    # 检查缓存
    cache_key = hashlib.md5(feed_url.encode()).hexdigest()
    cached_data = load_cache(cache_key, max_age_hours=6)  # 6小时缓存
    if cached_data:
        print(f"  📦 {feed_name} 使用缓存数据")
        return cached_data
    
    for attempt in range(retry_count):
        try:
            if attempt > 0:
                # 指数退避：第1次重试等1秒，第2次等2秒，第3次等4秒
                wait_time = 2 ** (attempt - 1)
                print(f"  - 重试 {feed_name} (第 {attempt + 1}/{retry_count} 次，等待 {wait_time}秒)...")
                time.sleep(wait_time)
            
            # 使用 requests 先下载，设置超时
            print(f"正在抓取: {feed_name}...")
            response = requests.get(
                feed_url, 
                headers=HEADERS,
                timeout=(10, 30),  # (连接超时, 读取超时) 单位：秒
                allow_redirects=True
            )
            response.raise_for_status()  # 检查 HTTP 状态码
            
            # 尝试不同的编码
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                # 尝试检测编码
                response.encoding = response.apparent_encoding or 'utf-8'
            
            # 解析 RSS/Atom
            feed = feedparser.parse(response.content)
            
            # 检查解析错误
            if feed.bozo and not is_arxiv:
                if attempt < retry_count - 1:
                    print(f"  - 警告: {feed_name} 格式解析错误，将重试...")
                    continue
                else:
                    print(f"  - 警告: {feed_name} 格式可能有问题，但已是最后一次尝试，继续处理...")
            
            # 检查是否有内容
            if not feed.entries:
                print(f"  - 警告: {feed_name} 没有找到任何条目")
                return None
            
            # 获取配置的时间窗口（小时）
            time_window_hours = config.get('crawler_settings', {}).get('content_freshness_hours', 48)
            
            # 提取和过滤内容
            section_text = f"\n\n--- 来源：{feed_name} ---\n"
            valid_items = 0
            filtered_by_date = 0
            filtered_by_validation = 0
            
            for item in feed.entries[:max_items * 2]:  # 多抓一些，因为要过滤
                if valid_items >= max_items:
                    break
                
                # 日期过滤
                if not is_content_fresh(item, hours=time_window_hours):
                    filtered_by_date += 1
                    continue
                
                # 特殊处理 Arxiv
                if is_arxiv:
                    title, link, desc = parse_arxiv_entry(item)
                else:
                    title = item.get('title', '无标题')
                    link = item.get('link', '')
                    desc = item.get('description', item.get('summary', ''))
                
                # 清理 HTML 标签（使用高级清理函数）
                clean_desc = clean_html_content(desc)
                
                # 限制长度
                if len(clean_desc) > 300:
                    clean_desc = clean_desc[:300] + "..."
                elif not clean_desc:
                    clean_desc = "无摘要"
                
                # 数据验证
                if not validate_item_content(title, link, clean_desc):
                    filtered_by_validation += 1
                    continue
                
                section_text += f"标题: {title}\n链接: {link}\n摘要: {clean_desc}\n\n"
                valid_items += 1
            
            if valid_items == 0:
                print(f"  - 警告: {feed_name} 所有内容都被过滤掉了（日期过滤: {filtered_by_date}, 验证失败: {filtered_by_validation}）")
                return None
            
            status_msg = f"  ✓ {feed_name} 抓取成功 ({valid_items} 条有效"
            if filtered_by_date > 0 or filtered_by_validation > 0:
                status_msg += f", 过滤: 日期{filtered_by_date}+验证{filtered_by_validation}"
            status_msg += ")"
            print(status_msg)
            
            # 保存到缓存
            save_cache(cache_key, section_text)
            
            return section_text
            
        except requests.exceptions.Timeout:
            print(f"  - 超时: {feed_name} (尝试 {attempt + 1}/{retry_count})")
            if attempt == retry_count - 1:
                print(f"  ✗ {feed_name} 抓取失败：连接超时")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"  - 网络错误: {feed_name} - {str(e)} (尝试 {attempt + 1}/{retry_count})")
            if attempt == retry_count - 1:
                print(f"  ✗ {feed_name} 抓取失败：{str(e)}")
                return None
                
        except Exception as e:
            print(f"  - 未知错误: {feed_name} - {str(e)} (尝试 {attempt + 1}/{retry_count})")
            if attempt == retry_count - 1:
                print(f"  ✗ {feed_name} 抓取失败：{str(e)}")
                return None
    
    return None


def fetch_feeds():
    """
    并发抓取所有 RSS 源并合并为文本
    使用线程池实现并发，提高抓取效率
    """
    print("开始抓取数据...")
    print(f"共有 {len(config['feeds'])} 个数据源")
    
    combined_content = []
    feeds_config = config['feeds']
    
    # 获取配置的并发数和速率限制
    max_workers = config.get('crawler_settings', {}).get('max_workers', 5)
    rate_limit = config.get('crawler_settings', {}).get('rate_limit_seconds', 0.5)
    
    # 使用线程池并发抓取
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_feed = {
            executor.submit(fetch_single_feed, feed_conf): feed_conf 
            for feed_conf in feeds_config
        }
        
        # 处理完成的任务
        for i, future in enumerate(as_completed(future_to_feed)):
            feed_conf = future_to_feed[future]
            try:
                result = future.result()
                if result:
                    combined_content.append(result)
                
                # 速率限制：每抓取完一个源，等待一段时间（避免过快请求）
                if i < len(feeds_config) - 1:  # 最后一个不需要等待
                    time.sleep(rate_limit)
                    
            except Exception as e:
                print(f"  ✗ {feed_conf['name']} 处理失败: {str(e)}")
    
    print(f"\n抓取完成: 成功 {len(combined_content)}/{len(feeds_config)} 个数据源")
    return "".join(combined_content)

def generate_summary(content):
    """调用 Gemini 生成 HTML 早报"""
    print("正在调用 Gemini 进行总结 (可能需要十几秒)...")
    full_prompt = config['prompt'] + "\n" + content
    
    try:
        # 使用新版 API - 不需要 "models/" 前缀，直接使用模型名称
        response = client.models.generate_content(
            model=config['gemini']['model_name'],
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini API 调用失败: {e}")
        # 尝试使用备用方法
        try:
            print("尝试使用备用 API 格式...")
            from google.generativeai import GenerativeModel, configure
            configure(api_key=os.environ["GOOGLE_API_KEY"])
            backup_model = GenerativeModel(config['gemini']['model_name'])
            backup_response = backup_model.generate_content(full_prompt)
            return backup_response.text
        except Exception as e2:
            print(f"备用方法也失败: {e2}")
            return None

def send_email(html_content):
    """发送邮件"""
    print("正在发送邮件...")
    try:
        user = os.environ["EMAIL_USER"]
        password = os.environ["EMAIL_PASSWORD"]
        receiver = config['email_settings']['receiver']
        subject = f"{config['email_settings']['subject']} ({datetime.now().strftime('%Y-%m-%d')})"
        smtp_host = config['email_settings'].get('smtp_host', 'smtp.gmail.com')
        
        yag = yagmail.SMTP(user=user, password=password, host=smtp_host)
        yag.send(
            to=receiver,
            subject=subject,
            contents=[html_content] # yagmail 自动识别 HTML
        )
        print("邮件发送成功！")
    except Exception as e:
        print(f"邮件发送失败: {e}")

# 主程序
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 AI 每日新闻摘要 - 开始运行")
    print("=" * 60)
    
    # 生成今天的缓存键
    today = datetime.now().strftime('%Y-%m-%d')
    raw_data_cache_key = f"raw_data_{today}"
    summary_cache_key = f"summary_{today}"
    
    # 1. 抓取（优先使用缓存）
    raw_data = load_cache(raw_data_cache_key, max_age_hours=12)
    if raw_data:
        print("\n📦 使用缓存的原始数据")
    else:
        raw_data = fetch_feeds()
        if raw_data:
            save_cache(raw_data_cache_key, raw_data)
    
    if not raw_data or len(raw_data.strip()) < 100:
        print("\n❌ 没有抓取到足够的数据，终止运行。")
        exit(1)
    
    print(f"\n📊 数据统计: 共 {len(raw_data)} 字符")
        
    # 2. 总结（优先使用缓存）
    summary_html = load_cache(summary_cache_key, max_age_hours=12)
    if summary_html:
        print("\n📦 使用缓存的摘要数据")
    else:
        summary_html = generate_summary(raw_data)
        if summary_html:
            save_cache(summary_cache_key, summary_html)
    
    # 3. 发送
    if summary_html:
        send_email(summary_html)
        print("\n" + "=" * 60)
        print("✅ 任务完成！")
        print("=" * 60)
    else:
        print("\n❌ 生成总结失败，未发送邮件。")
        exit(1)