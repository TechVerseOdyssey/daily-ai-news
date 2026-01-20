# AI 每日新闻摘要

自动抓取 AI 领域最新资讯，生成精美邮件并定时发送。

## 功能特性

- **多源 RSS 抓取**: 支持 OpenAI、Google AI、Arxiv、MIT News、DeepMind、VentureBeat、The Verge 等
- **智能排序**: 基于关键词权重对新闻进行相关度排序
- **AI 增强**: 可选使用 Gemini 生成智能总结（可在配置中启用/禁用）
- **精美邮件**: 响应式 HTML 邮件模板，支持移动端
- **并发抓取**: 多线程并发，提高抓取效率
- **缓存机制**: 避免重复抓取，支持多级缓存目录
- **内容过滤**: 日期过滤 + 内容验证，确保新闻质量

## 项目结构

```
daily-ai-news/
├── main.py              # 主程序
├── email_template.py    # 邮件模板生成
├── config.yaml          # 配置文件
├── requirements.txt     # 依赖包
└── tests/               # 测试文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# Gemini API Key（必需）
export GOOGLE_API_KEY='your-google-api-key'

# 邮箱配置（必需）
export EMAIL_USER='your-email@qq.com'
export EMAIL_PASSWORD='your-smtp-password'
```

**获取 API Key**: https://aistudio.google.com/app/apikey

**获取邮箱授权码**:
- QQ邮箱: 设置 → 账户 → POP3/SMTP服务 → 开启并获取授权码
- Gmail: 开启两步验证后创建应用专用密码

### 3. 修改配置文件

编辑 `config.yaml`：

```yaml
email_settings:
  receiver: "your-email@example.com"  # 接收邮箱
  smtp_host: "smtp.qq.com"            # SMTP 服务器
  smtp_port: 465                      # SMTP 端口

gemini:
  enable_ai_summary: true  # 是否启用 AI 总结
```

### 4. 运行

```bash
python main.py
```

## 配置说明

### 爬虫设置

```yaml
crawler_settings:
  max_workers: 5              # 并发线程数
  connect_timeout: 10         # 连接超时（秒）
  read_timeout: 30            # 读取超时（秒）
  content_freshness_hours: 168  # 内容时效性（小时）
  cache_max_age_hours: 6      # 缓存有效期（小时）
  max_total_items: 100        # 文章总数上限
```

### 关键词权重

```yaml
keyword_weights:
  - keywords: ["GPT-5", "Claude", "Gemini", "Agent"]
    weight: 10
  - keywords: ["LLM", "ChatGPT", "大模型"]
    weight: 8
```

### 数据源配置

```yaml
feeds:
  - name: "OpenAI Blog"
    url: "https://openai.com/blog/rss.xml"
    max_items: 5
    custom_freshness_hours: 168  # 可选，覆盖全局时效性设置
```

## GitHub Actions 自动运行

项目已配置 GitHub Actions，每天自动运行。需要在仓库 Settings → Secrets 中添加：

- `GOOGLE_API_KEY`
- `EMAIL_USER`
- `EMAIL_PASSWORD`

## 测试

```bash
# 运行所有测试
cd tests && python run_all_tests.py

# 运行单个测试
python tests/test_01_config.py
```

## 技术栈

- **Python 3.8+**
- **feedparser**: RSS/Atom 解析
- **google-genai**: Gemini API
- **yagmail**: 邮件发送
- **beautifulsoup4**: HTML 内容清理
- **requests**: HTTP 请求

## 许可证

MIT License
