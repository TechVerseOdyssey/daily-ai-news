# Copyright 2026 Daily AI News Project
# Licensed under the MIT License

"""
新闻抓取模块
负责从 RSS 源抓取新闻数据，包括并发抓取、内容过滤、缓存等功能
"""

import os
import re
import json
import html
import time
import hashlib
import requests
import feedparser
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup


# 请求头配置 - 模拟美国浏览器客户端
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


class NewsFetcher:
    """新闻抓取器类"""
    
    def __init__(self, config):
        """
        初始化新闻抓取器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.cache_dir = self._init_cache_dir()
        self.cache_enabled = self.cache_dir is not None
    
    def _init_cache_dir(self):
        """
        初始化缓存目录，按优先级尝试多个位置
        
        Returns:
            str or None: 可用的缓存目录路径，如果都不可用返回 None
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(script_dir, '.cache'),
            os.path.join(os.path.expanduser('~'), '.daily-ai-news-cache'),
            os.path.join(os.environ.get('TMPDIR', '/tmp'), 'daily-ai-news-cache'),
        ]
        
        for cache_dir in candidates:
            try:
                os.makedirs(cache_dir, exist_ok=True)
                test_file = os.path.join(cache_dir, '.write_test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                return cache_dir
            except (OSError, PermissionError, IOError):
                continue
        
        print("  ⚠️  警告: 无法创建缓存目录，缓存功能已禁用")
        return None
    
    def _save_cache(self, cache_key, data):
        """保存数据到缓存"""
        if not self.cache_enabled:
            return
        
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'data': data
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"缓存保存失败: {e}")
    
    def _load_cache(self, cache_key, max_age_hours=24):
        """从缓存加载数据"""
        if not self.cache_enabled:
            return None
        
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_time_str = cache_data['timestamp']
            cache_time = datetime.fromisoformat(cache_time_str)
            if cache_time.tzinfo is None:
                cache_time = cache_time.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            if (now - cache_time).total_seconds() > max_age_hours * 3600:
                return None
            
            return cache_data['data']
        except Exception as e:
            print(f"缓存加载失败: {e}")
            return None
    
    @staticmethod
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
        
        soup = BeautifulSoup(html_text, "html.parser")
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        text = text.strip()
        
        return text
    
    @staticmethod
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
        if not title or title == '无标题' or len(title.strip()) < 3:
            return False
        
        if not link or not link.startswith('http'):
            return False
        
        if description and len(description.strip()) < 10:
            if description.strip() not in ['无摘要', '']:
                return False
        
        spam_keywords = ['广告', '推广', 'AD', 'sponsored', 'advertisement']
        title_lower = title.lower()
        for keyword in spam_keywords:
            if keyword.lower() in title_lower:
                return False
        
        return True
    
    @staticmethod
    def is_content_fresh(item, hours=24):
        """
        检查内容是否是最近发布的（日期过滤）
        
        Args:
            item: feedparser 的 entry 对象
            hours: 时间窗口（小时），默认24小时
        
        Returns:
            bool: 是否是新鲜内容
        """
        published_time = None
        
        for time_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if hasattr(item, time_field):
                time_struct = getattr(item, time_field)
                if time_struct:
                    try:
                        published_time = datetime(*time_struct[:6], tzinfo=timezone.utc)
                        break
                    except Exception:
                        continue
        
        if not published_time:
            return True
        
        now = datetime.now(timezone.utc)
        time_diff = now - published_time
        
        return time_diff.total_seconds() <= hours * 3600
    
    @staticmethod
    def parse_arxiv_entry(item):
        """
        特殊处理 Arxiv API 返回的条目格式
        
        Args:
            item: feedparser entry
        
        Returns:
            tuple: (title, link, description)
        """
        title = item.get('title', '').replace('\n', ' ').strip()
        link = item.get('id', item.get('link', ''))
        description = item.get('summary', '')
        
        authors = []
        if 'authors' in item:
            for author in item['authors']:
                if 'name' in author:
                    authors.append(author['name'])
        
        if authors:
            author_str = ', '.join(authors[:3])
            if len(authors) > 3:
                author_str += ' et al.'
            description = f"作者: {author_str}. {description}"
        
        return title, link, description
    
    def calculate_keyword_score(self, title, summary):
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
        
        keyword_weights = self.config.get('keyword_weights', [])
        
        if not keyword_weights:
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
    
    def sort_and_limit_items(self, sources_data, max_total_items=100):
        """
        对所有文章按关键词相关度排序，并限制总数量
        
        Args:
            sources_data: 原始数据源列表
            max_total_items: 最大文章总数
        
        Returns:
            list: 排序并限制后的数据源列表
        """
        all_items = []
        for source in sources_data:
            source_name = source['source']
            for item in source['items']:
                score = self.calculate_keyword_score(item['title'], item['summary'])
                all_items.append({
                    'source': source_name,
                    'item': item,
                    'score': score
                })
        
        all_items.sort(key=lambda x: x['score'], reverse=True)
        
        if len(all_items) > max_total_items:
            print(f"  ⚠️  文章数量 ({len(all_items)}) 超过上限 ({max_total_items})，已截取前 {max_total_items} 条")
            all_items = all_items[:max_total_items]
        
        source_items_map = {}
        for entry in all_items:
            source_name = entry['source']
            if source_name not in source_items_map:
                source_items_map[source_name] = []
            source_items_map[source_name].append(entry['item'])
        
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
    
    def _fetch_single_feed(self, feed_conf, retry_count=3):
        """
        抓取单个 RSS 源并返回结构化数据
        
        Returns:
            dict: {'source': '数据源名称', 'items': [{'title': '...', 'link': '...', 'summary': '...'}]}
        """
        feed_name = feed_conf['name']
        feed_url = feed_conf['url']
        max_items = feed_conf.get('max_items', 3)
        is_arxiv = feed_conf.get('type') == 'arxiv' or 'arxiv' in feed_url.lower()
        
        crawler_settings = self.config.get('crawler_settings', {})
        connect_timeout = crawler_settings.get('connect_timeout', 10)
        read_timeout = crawler_settings.get('read_timeout', 30)
        cache_max_age = crawler_settings.get('cache_max_age_hours', 6)
        
        cache_key = hashlib.md5(feed_url.encode()).hexdigest()
        cached_data = self._load_cache(cache_key + '_structured', max_age_hours=cache_max_age)
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
                                                  crawler_settings.get('content_freshness_hours', 168))
                
                items = []
                filtered_by_date = 0
                filtered_by_validation = 0
                
                for item in feed.entries[:max_items * 2]:
                    if len(items) >= max_items:
                        break
                    
                    if not self.is_content_fresh(item, hours=time_window_hours):
                        filtered_by_date += 1
                        continue
                    
                    if is_arxiv:
                        title, link, desc = self.parse_arxiv_entry(item)
                    else:
                        title = item.get('title', '无标题')
                        link = item.get('link', '')
                        desc = item.get('description', item.get('summary', ''))
                    
                    clean_desc = self.clean_html_content(desc)
                    if len(clean_desc) > 300:
                        clean_desc = clean_desc[:300] + "..."
                    elif not clean_desc:
                        clean_desc = "无摘要"
                    
                    if not self.validate_item_content(title, link, clean_desc):
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
                
                self._save_cache(cache_key + '_structured', result)
                
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
    
    def fetch_all(self):
        """
        并发抓取所有 RSS 源并返回结构化数据
        
        Returns:
            list: 包含每个源的字典列表
        """
        print("开始抓取数据...")
        feeds_config = self.config.get('feeds', [])
        print(f"共有 {len(feeds_config)} 个数据源")
        
        all_sources = []
        max_workers = self.config.get('crawler_settings', {}).get('max_workers', 5)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_feed = {
                executor.submit(self._fetch_single_feed, feed_conf): feed_conf
                for feed_conf in feeds_config
            }
            
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
