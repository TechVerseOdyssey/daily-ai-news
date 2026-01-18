# 🤖 AI 每日新闻摘要

一个基于 GitHub Actions 的自动化工具，每天自动抓取 AI 领域的最新动态，使用 Google Gemini API 生成精美的中文摘要，并通过邮件发送。

## ✨ 功能特点

- 📰 自动抓取多个 AI 相关 RSS 源（Hugging Face、GitHub Trending、OpenAI Blog、Google AI Blog、Arxiv 等）
- 🤖 使用 Google Gemini AI 智能总结和分类新闻
- 📧 自动发送 HTML 格式的精美邮件
- ⏰ 每天定时运行（北京时间 08:30）
- 🔧 支持手动触发运行

## 🚀 快速开始

### 1. Fork 本项目

点击右上角的 "Fork" 按钮，将本项目复制到你的 GitHub 账号下。

### 2. 配置环境变量

在你 Fork 的仓库中，进入 `Settings` → `Secrets and variables` → `Actions`，添加以下 3 个 Secrets：

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `GOOGLE_API_KEY` | Google Gemini API 密钥 | 从 [Google AI Studio](https://makersuite.google.com/app/apikey) 获取 |
| `EMAIL_USER` | 发件邮箱地址 | your_email@qq.com |
| `EMAIL_PASSWORD` | 邮箱授权码（非登录密码） | 从邮箱设置中获取授权码 |

#### 如何获取邮箱授权码？

**QQ 邮箱：**
1. 登录 [QQ 邮箱](https://mail.qq.com/)
2. 点击"设置" → "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启"POP3/SMTP服务"或"IMAP/SMTP服务"
5. 点击"生成授权码"，将生成的授权码保存（这就是 `EMAIL_PASSWORD`）

**Gmail：**
1. 开启两步验证
2. 访问 [App passwords](https://myaccount.google.com/apppasswords)
3. 生成应用专用密码

**163/126 邮箱：**
1. 登录邮箱 → 设置 → POP3/SMTP/IMAP
2. 开启服务并生成授权码

### 3. 修改配置文件

编辑 `config.yaml` 文件：

```yaml
email_settings:
  receiver: "your_email@example.com"  # 修改为你的收件邮箱
  smtp_host: "smtp.qq.com"  # 根据发件邮箱类型修改
```

**常用 SMTP 服务器：**
- QQ 邮箱：`smtp.qq.com`
- Gmail：`smtp.gmail.com`
- 163 邮箱：`smtp.163.com`
- 126 邮箱：`smtp.126.com`
- Outlook：`smtp.office365.com`

### 4. 启用 GitHub Actions

1. 进入你 Fork 的仓库
2. 点击 `Actions` 标签页
3. 如果看到提示，点击"I understand my workflows, go ahead and enable them"
4. 点击左侧的 "Daily AI News Digest"
5. 点击右侧的 "Enable workflow"

### 5. 测试运行

点击 "Run workflow" → "Run workflow" 按钮，手动触发一次运行，检查是否正常工作。

## 📋 项目结构

```
daily-ai-news/
├── .github/
│   └── workflows/
│       └── daily.yml        # GitHub Actions 工作流配置
├── config.yaml              # 配置文件（RSS 源、邮件设置等）
├── main.py                  # 主程序
├── requirements.txt         # Python 依赖
└── README.md               # 说明文档
```

## ⚙️ 自定义配置

### 修改 RSS 源

在 `config.yaml` 中的 `feeds` 部分添加或删除 RSS 源：

```yaml
feeds:
  - name: "你的RSS源名称"
    url: "https://example.com/rss.xml"
    max_items: 5  # 每次抓取的最大条目数
```

### 修改定时时间

在 `.github/workflows/daily.yml` 中修改 cron 表达式：

```yaml
schedule:
  - cron: '30 0 * * *'  # UTC 00:30 = 北京时间 08:30
```

### 自定义提示词

在 `config.yaml` 中修改 `prompt` 部分，调整 AI 生成摘要的风格和格式。

## 🐛 常见问题

### 为什么没有收到邮件？

1. 检查 GitHub Actions 的运行日志是否有错误
2. 确认邮箱授权码配置正确（不是登录密码）
3. 检查 `config.yaml` 中的 `receiver` 邮箱地址是否正确
4. 查看垃圾邮件文件夹

### Gemini API 调用失败？

1. 确认 API Key 是否正确配置
2. 检查 API 配额是否用完（免费版有限制）
3. 尝试切换到 `gemini-1.5-flash`（更快且免费）

### RSS 源抓取失败？

- 某些 RSS 源可能在某些地区无法访问
- 可以在 `config.yaml` 中删除无法访问的源
- 或使用 RSSHub 等镜像服务

## 📦 依赖说明

- `google-generativeai`: Google Gemini API 客户端
- `feedparser`: RSS/Atom 解析库
- `yagmail`: 简化的邮件发送库
- `pyyaml`: YAML 配置文件解析
- `beautifulsoup4`: HTML 内容清理
- `requests`: HTTP 请求库

## 📝 开发说明

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export GOOGLE_API_KEY="your_api_key"
export EMAIL_USER="your_email@qq.com"
export EMAIL_PASSWORD="your_auth_code"

# 运行
python main.py
```

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⭐ Star History

如果这个项目对你有帮助，欢迎点个 Star ⭐！
