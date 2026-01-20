# AI 每日新闻摘要

自动抓取 AI 领域最新资讯，通过 Gemini 生成智能总结，定时发送精美邮件。

## 功能特性

- **多源 RSS 抓取** - OpenAI、Google AI、Arxiv、DeepMind、MIT News 等
- **智能排序** - 基于关键词权重的相关度排序
- **AI 总结** - Gemini 生成智能摘要（可配置开关）
- **自动 SMTP** - 根据发件邮箱自动选择 SMTP 配置
- **多收件人** - 支持多个收件人，逗号/分号/空格分隔
- **并发抓取** - 多线程并发提高效率
- **缓存机制** - 避免重复抓取

## 项目结构

```
daily-ai-news/
├── main.py              # 主程序入口
├── news_fetcher.py      # 新闻抓取模块
├── ai_summarizer.py     # AI 总结模块
├── email_sender.py      # 邮件发送模块
├── email_template.py    # 邮件模板
├── config.yaml          # 配置文件
├── requirements.txt     # 依赖
└── .github/workflows/   # GitHub Actions
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
# 邮箱配置（必需）
export EMAIL_USER='your-email@qq.com'
export EMAIL_PASSWORD='your-smtp-password'
export EMAIL_RECEIVER='receiver@example.com'  # 支持多个：a@qq.com,b@163.com

# Gemini API（启用 AI 总结时需要）
export GOOGLE_API_KEY='your-google-api-key'
```

**获取授权码**:
- QQ邮箱: 设置 → 账户 → POP3/SMTP服务 → 开启并获取授权码
- Gmail: 开启两步验证后创建应用专用密码

**获取 Gemini API Key**: https://aistudio.google.com/app/apikey

### 3. 运行

```bash
python main.py
```

## 配置文件 (config.yaml)

### 邮件设置

```yaml
email_settings:
  subject: "🤖 AI 每日早报"
```
> SMTP 配置会根据 `EMAIL_USER` 自动选择，支持 QQ/Gmail/163/126/Outlook/新浪/阿里云/Yahoo

### AI 总结

```yaml
gemini:
  model_name: "gemini-2.0-flash"
  enable_ai_summary: false  # true 启用 / false 禁用
```

### 爬虫设置

```yaml
crawler_settings:
  max_workers: 5              # 并发线程数
  content_freshness_hours: 168  # 内容时效（小时）
  max_total_items: 100        # 文章总数上限
```

### 数据源

```yaml
feeds:
  - name: "OpenAI Blog"
    url: "https://openai.com/blog/rss.xml"
    max_items: 5
```

### 关键词权重

```yaml
keyword_weights:
  - keywords: ["GPT-5", "Claude", "Agent"]
    weight: 10
  - keywords: ["LLM", "ChatGPT"]
    weight: 8
```

## GitHub Actions

项目已配置每日自动运行（北京时间 08:30）。

在仓库 **Settings → Secrets and variables → Actions** 添加：

| Secret | 说明 |
|--------|------|
| `EMAIL_USER` | 发件人邮箱 |
| `EMAIL_PASSWORD` | 邮箱授权码 |
| `EMAIL_RECEIVER` | 收件人邮箱 |
| `GOOGLE_API_KEY` | Gemini API Key（启用 AI 总结时需要） |

## 技术栈

- Python 3.8+
- feedparser - RSS 解析
- google-genai - Gemini API
- yagmail - 邮件发送
- beautifulsoup4 - HTML 处理

## 许可证

MIT License
