# AI 每日新闻摘要

自动抓取 AI 领域最新资讯，通过 AI 大模型生成智能总结，定时发送精美邮件。

## 功能特性

- **多源 RSS 抓取** - OpenAI、Google AI、Arxiv、DeepMind、MIT News、VentureBeat、The Verge
- **智能排序** - 基于关键词权重的相关度排序
- **AI 双后端总结** - OpenRouter（主）+ Gemini（备），自动回退，429 限流自动重试
- **模型可配置** - 通过 `config.yaml` 切换 AI 模型，无需改代码
- **自动 SMTP** - 根据发件邮箱自动选择 SMTP 配置（QQ/Gmail/163/Outlook 等）
- **多收件人** - 支持多个收件人，逗号/分号/空格分隔
- **并发抓取** - 多线程并发提高效率
- **缓存机制** - 避免重复抓取，可配置缓存过期时间
- **本地开发友好** - 支持 `.env` 文件加载环境变量，无邮件凭证时仅控制台输出

## 项目结构

```
daily-ai-news/
├── main.py              # 主程序入口
├── news_fetcher.py      # 新闻抓取模块（并发、缓存、去重）
├── ai_summarizer.py     # AI 总结模块（OpenRouter + Gemini 双后端）
├── email_sender.py      # 邮件发送模块（自动 SMTP、多收件人）
├── email_template.py    # 邮件模板（HTML 生成、AI 内容安全过滤）
├── config.yaml          # 配置文件（数据源、模型、关键词、爬虫参数）
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量模板
├── .github/workflows/   # GitHub Actions 定时任务
└── tests/               # 测试套件（6 组测试）
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制模板并填入真实值：

```bash
cp .env.example .env
```

编辑 `.env`：

```bash
# OpenRouter API Key（主要 AI 后端）
OPENROUTER_API_KEY=your-openrouter-api-key

# Google Gemini API Key（备用 AI 后端，可选）
GOOGLE_API_KEY=your-google-api-key

# 邮件配置（可选，不配置则仅控制台输出）
EMAIL_USER=your-email@qq.com
EMAIL_PASSWORD=your-smtp-password
EMAIL_RECEIVER=receiver@example.com
```

**获取 API Key**:
- OpenRouter: https://openrouter.ai/keys
- Gemini: https://aistudio.google.com/app/apikey

**获取邮箱授权码**:
- QQ邮箱: 设置 → 账户 → POP3/SMTP服务 → 开启并获取授权码
- Gmail: 开启两步验证后创建应用专用密码

### 3. 运行

```bash
python main.py
```

运行流程：抓取新闻 → 关键词排序 → AI 生成总结 → 打印 HTML 到控制台 → 发送邮件（如已配置）

## 配置文件 (config.yaml)

### AI 总结

```yaml
ai_summary:
  enabled: true  # true 启用 / false 禁用

# OpenRouter（主要后端）
openrouter:
  model: "z-ai/glm-4.5-air:free"  # 可切换为其他 OpenRouter 模型

# Gemini（备用后端）
gemini:
  model_name: "gemini-2.0-flash"
```

### 爬虫设置

```yaml
crawler_settings:
  max_workers: 5              # 并发线程数
  content_freshness_hours: 25 # 内容时效（小时）
  cache_max_age_hours: 6      # 缓存有效期（小时）
  max_total_items: 100        # 文章总数上限
```

### 数据源

```yaml
feeds:
  - name: "OpenAI Blog"
    url: "https://openai.com/blog/rss.xml"
    max_items: 5
  - name: "Google AI Blog"
    url: "http://googleaiblog.blogspot.com/atom.xml"
    max_items: 10
    custom_freshness_hours: 168  # 可单独覆盖时效
```

### 关键词权重

```yaml
keyword_weights:
  - keywords: ["GPT-5", "Claude", "Agent", "AGI"]
    weight: 10
  - keywords: ["LLM", "ChatGPT", "AI Coding"]
    weight: 8
```

## GitHub Actions

项目已配置每日自动运行（北京时间 08:30），也支持手动触发。

在仓库 **Settings → Secrets and variables → Actions** 添加：

| Secret | 说明 | 必需 |
|--------|------|------|
| `OPENROUTER_API_KEY` | OpenRouter API Key | AI 总结启用时需要 |
| `GOOGLE_API_KEY` | Gemini API Key | 备用，可选 |
| `EMAIL_USER` | 发件人邮箱 | 是 |
| `EMAIL_PASSWORD` | 邮箱授权码 | 是 |
| `EMAIL_RECEIVER` | 收件人邮箱 | 是 |

## 测试

```bash
# 运行全部测试
python tests/run_all_tests.py

# 运行单个测试
python tests/test_06_ai_summary.py
```

| 测试 | 说明 |
|------|------|
| test_01_config | 配置文件加载 |
| test_02_cleaning | 数据清洗 |
| test_03_cache | 缓存机制 |
| test_04_fetch_single | 单源抓取 |
| test_05_concurrent | 并发抓取 |
| test_06_ai_summary | AI 总结（实际调用 API） |

## 技术栈

- Python 3.8+
- openai - OpenRouter API 调用
- google-genai - Gemini API（备用）
- feedparser - RSS/Atom 解析
- yagmail - 邮件发送
- beautifulsoup4 - HTML 处理
- PyYAML - 配置文件

## 许可证

MIT License
