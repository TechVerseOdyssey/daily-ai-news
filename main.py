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
import html
import re
import json
import hashlib
from email_template import generate_basic_html, wrap_with_ai_summary

# 1. 加载配置
def get_config_path():
    """获取配置文件的绝对路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'config.yaml')

with open(get_config_path(), 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 2. 配置 Gemini (使用 google-genai 新版 API)
def get_genai_client():
    """
    获取 Gemini API 客户端，带有友好的错误提示
    
    Returns:
        genai.Client: Gemini API 客户端
    
    Raises:
        SystemExit: 当环境变量缺失时退出程序
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("=" * 60)
        print("❌ 错误: 环境变量 GOOGLE_API_KEY 未设置")
        print("=" * 60)
        print("\n请设置 GOOGLE_API_KEY 环境变量:")
        print("  Linux/Mac: export GOOGLE_API_KEY='your-api-key'")
        print("  Windows:   set GOOGLE_API_KEY=your-api-key")
        print("\n获取 API Key: https://aistudio.google.com/app/apikey")
        print("=" * 60)
        exit(1)
    return genai.Client(api_key=api_key)

client = get_genai_client()


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

# 3. 请求头配置 - 模拟美国浏览器客户端
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, application/atom+xml, text/xml, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'X-Timezone': 'America/New_York',
    'Sec-CH-UA-Platform': '"macOS"',
    'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
}

# 4. 缓存目录初始化
def init_cache_dir():
    """
    初始化缓存目录，按优先级尝试多个位置
    
    Returns:
        str or None: 可用的缓存目录路径，如果都不可用返回 None
    """
    # 候选缓存目录（按优先级排序）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, '.cache'),  # 项目目录下的 .cache
        os.path.join(os.path.expanduser('~'), '.daily-ai-news-cache'),  # 用户主目录
        os.path.join(os.environ.get('TMPDIR', '/tmp'), 'daily-ai-news-cache'),  # 临时目录
    ]
    
    for cache_dir in candidates:
        try:
            os.makedirs(cache_dir, exist_ok=True)
            # 测试写入权限
            test_file = os.path.join(cache_dir, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return cache_dir
        except (OSError, PermissionError, IOError):
            continue
    
    # 所有候选目录都不可用
    print("  ⚠️  警告: 无法创建缓存目录，缓存功能已禁用")
    return None

CACHE_DIR = init_cache_dir()
CACHE_ENABLED = CACHE_DIR is not None


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


def calculate_keyword_score(title, summary):
    """
    计算文章的关键词相关度分数
    
    Args:
        title: 文章标题
        summary: 文章摘要
    
    Returns:
        int: 关键词相关度分数（越高越相关）
    """
    text = f"{title} {summary}".lower()
    score = 0
    
    # 从配置读取关键词权重
    keyword_weights = config.get('keyword_weights', [])
    
    if not keyword_weights:
        # 默认关键词权重（如果配置中没有）
        keyword_weights = [
            {'keywords': ['GPT-5', 'GPT-4', 'Claude', 'Gemini', 'OpenAI', 'Anthropic', 'AGI'], 'weight': 10},
            {'keywords': ['LLM', 'ChatGPT', 'GPT', '大模型', 'Large Language Model'], 'weight': 8},
            {'keywords': ['Transformer', 'RLHF', 'RAG', 'Fine-tuning', 'Prompt', 'Agent'], 'weight': 6},
            {'keywords': ['Neural Network', 'Deep Learning', 'Machine Learning', 'NLP'], 'weight': 4},
            {'keywords': ['AI', 'Artificial Intelligence', 'ML', 'Research'], 'weight': 2},
        ]
    
    for group in keyword_weights:
        keywords = group.get('keywords', [])
        weight = group.get('weight', 1)
        for keyword in keywords:
            if keyword.lower() in text:
                score += weight
    
    return score


def sort_and_limit_items(sources_data, max_total_items=100):
    """
    对所有文章按关键词相关度排序，并限制总数量
    
    Args:
        sources_data: 原始数据源列表
        max_total_items: 最大文章总数
    
    Returns:
        list: 排序并限制后的数据源列表
    """
    # 1. 收集所有文章并计算分数
    all_items = []
    for source in sources_data:
        source_name = source['source']
        for item in source['items']:
            score = calculate_keyword_score(item['title'], item['summary'])
            all_items.append({
                'source': source_name,
                'item': item,
                'score': score
            })
    
    # 2. 按分数降序排序
    all_items.sort(key=lambda x: x['score'], reverse=True)
    
    # 3. 限制总数量
    if len(all_items) > max_total_items:
        print(f"  ⚠️  文章数量 ({len(all_items)}) 超过上限 ({max_total_items})，已截取前 {max_total_items} 条")
        all_items = all_items[:max_total_items]
    
    # 4. 重新按数据源分组
    source_items_map = {}
    for entry in all_items:
        source_name = entry['source']
        if source_name not in source_items_map:
            source_items_map[source_name] = []
        source_items_map[source_name].append(entry['item'])
    
    # 5. 转换回原格式，保持分数高的源在前面
    result = []
    seen_sources = set()
    for entry in all_items:
        source_name = entry['source']
        if source_name not in seen_sources:
            seen_sources.add(source_name)
            result.append({
                'source': source_name,
                'items': source_items_map[source_name]
            })
    
    return result


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
    if not CACHE_ENABLED:
        return
    
    try:
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                # 使用 UTC 时间戳确保跨时区一致性
                'timestamp': datetime.now(timezone.utc).isoformat(),
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
    if not CACHE_ENABLED:
        return None
    
    try:
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        if not os.path.exists(cache_file):
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 检查缓存是否过期（使用 UTC 时间确保跨时区一致性）
        cache_time_str = cache_data['timestamp']
        # 兼容旧缓存（无时区信息）和新缓存（有时区信息）
        cache_time = datetime.fromisoformat(cache_time_str)
        if cache_time.tzinfo is None:
            # 旧缓存没有时区信息，假设为本地时间并转换为 UTC
            cache_time = cache_time.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
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
    
    # 从配置读取超时和缓存设置
    crawler_settings = config.get('crawler_settings', {})
    connect_timeout = crawler_settings.get('connect_timeout', 10)
    read_timeout = crawler_settings.get('read_timeout', 30)
    cache_max_age = crawler_settings.get('cache_max_age_hours', 6)
    
    # 检查缓存
    cache_key = hashlib.md5(feed_url.encode()).hexdigest()
    cached_data = load_cache(cache_key + '_structured', max_age_hours=cache_max_age)
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
                timeout=(connect_timeout, read_timeout),
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
    
    # 获取配置的并发数（速率限制通过控制 max_workers 实现）
    max_workers = config.get('crawler_settings', {}).get('max_workers', 5)
    
    # 使用线程池并发抓取
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_feed = {
            executor.submit(fetch_single_feed_structured, feed_conf): feed_conf 
            for feed_conf in feeds_config
        }
        
        # 处理完成的任务
        for future in as_completed(future_to_feed):
            feed_conf = future_to_feed[future]
            try:
                result = future.result()
                if result and result['items']:
                    all_sources.append(result)
            except Exception as e:
                print(f"  ✗ {feed_conf['name']} 处理失败: {str(e)}")
    
    print(f"\n抓取完成: 成功 {len(all_sources)}/{len(feeds_config)} 个数据源")
    return all_sources


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
    
    total_items_before = sum(len(source['items']) for source in sources_data)
    print(f"\n📊 原始数据: {len(sources_data)} 个数据源，共 {total_items_before} 条新闻")
    
    # 2. 按关键词相关度排序并限制总数量
    max_total_items = config.get('crawler_settings', {}).get('max_total_items', 100)
    print(f"\n🔄 正在按关键词相关度排序（上限 {max_total_items} 条）...")
    sources_data = sort_and_limit_items(sources_data, max_total_items)
    
    total_items_after = sum(len(source['items']) for source in sources_data)
    print(f"  ✅ 排序完成: {len(sources_data)} 个数据源，共 {total_items_after} 条新闻")
    
    # 3. 生成基础 HTML 内容（必须成功，作为后备）
    print("\n正在生成基础 HTML 内容...")
    freshness_hours = config.get('crawler_settings', {}).get('content_freshness_hours', 24)
    basic_html = generate_basic_html(sources_data, freshness_hours=freshness_hours)
    print("  ✅ 基础内容生成成功")
    
    # 4. 尝试用 AI 增强内容（根据配置决定是否启用）
    enable_ai_summary = config.get('gemini', {}).get('enable_ai_summary', True)
    ai_summary = None
    
    if enable_ai_summary:
        print("\n正在尝试使用 AI 生成智能总结...")
        print("  ⏳ 等待大模型响应（这可能需要10-30秒）...")
        ai_summary = try_enhance_with_ai(sources_data)
    else:
        print("\n⏭️  AI 总结已禁用（可在 config.yaml 中设置 enable_ai_summary: true 启用）")
    
    # 5. 准备最终邮件内容
    if ai_summary:
        # 如果有 AI 总结，使用模板包装
        final_html = wrap_with_ai_summary(basic_html, ai_summary)
        print("  ✅ AI 总结生成成功，将使用增强版邮件")
    else:
        final_html = basic_html
        if enable_ai_summary:
            print("  ⚠️  AI 总结生成失败，将使用基础版邮件（仍包含完整内容）")
    
    # 6. 发送邮件（必须成功）
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
