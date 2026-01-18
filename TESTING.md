# Daily AI News - 测试套件

## ✅ 已创建的测试文件

我已经为你创建了完整的自动化测试套件：

### 📁 测试文件结构

```
tests/
├── README.md                    # 测试文档
├── run_all_tests.py            # 测试运行器（主入口）
├── setup_and_test.sh           # 快速设置脚本
├── test_01_config.py           # 配置文件验证
├── test_02_cleaning.py         # HTML清理和数据验证
├── test_03_cache.py            # 缓存机制测试
├── test_04_fetch_single.py     # 单源抓取测试（需要网络）
└── test_05_concurrent.py       # 并发抓取测试（需要网络）
```

## 🚀 快速开始

### 方法 1：自动设置（推荐）

```bash
# 一键设置和测试
bash tests/setup_and_test.sh
```

这个脚本会：

1. 检查 Python 版本
2. 安装依赖
3. 运行所有不需要网络的测试

### 方法 2：手动设置

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行所有测试
python tests/run_all_tests.py

# 3. 或跳过网络测试
python tests/run_all_tests.py --skip-network

# 4. 或单独运行某个测试
python tests/test_01_config.py
```

## 📋 测试清单

### ✅ 不需要网络的测试（可随时运行）

1. **配置文件验证** (`test_01_config.py`)
   - YAML 格式检查
   - 必需字段验证
   - RSS 源配置检查
   - 邮件设置验证

2. **HTML 清理和验证** (`test_02_cleaning.py`)
   - HTML 标签清理
   - 实体编码解码
   - 数据质量验证
   - 广告关键词过滤

3. **缓存机制** (`test_03_cache.py`)
   - 缓存保存/加载
   - 过期处理
   - 中文支持
   - 大数据处理

### 🌐 需要网络的测试

1. **单源抓取** (`test_04_fetch_single.py`)
   - RSS 连接测试
   - 重试机制验证
   - 内容质量检查

2. **并发抓取** (`test_05_concurrent.py`)
   - 多线程性能测试
   - 抓取速度验证
   - 数据完整性检查

## 📊 预期输出示例

```
======================================================================
🧪 Daily AI News - 自动化测试套件
======================================================================

============================================================
测试 1: 配置文件验证
============================================================

✓ 步骤 1: 加载配置文件...
✅ YAML 文件格式正确

✓ 步骤 2: 检查必需字段...
  ✅ feeds
  ✅ email_settings
  ✅ gemini
  ✅ crawler_settings
  ✅ prompt

✓ 步骤 3: 检查 RSS 源配置...
  ✅ 配置了 6 个 RSS 源
  ✅ Hugging Face Daily Papers: https://huggingface.co/papers/daily_papers.rss...
  ...

============================================================
✅ 配置文件验证通过
============================================================

...

======================================================================
📊 测试总结
======================================================================

总计: 3 个测试
✅ 通过: 3
❌ 失败: 0
⏭️  跳过: 2
   - 单源抓取
   - 并发抓取

详细结果:
  ✅ 通过 - 配置文件验证
  ✅ 通过 - HTML清理和验证
  ✅ 通过 - 缓存机制

======================================================================
✅ 所有测试通过！
======================================================================
```

## 🔍 测试覆盖

这些测试覆盖了：

- ✅ 配置管理
- ✅ 数据清理
- ✅ 缓存系统
- ✅ RSS 抓取
- ✅ 并发处理
- ✅ 错误处理
- ✅ 重试机制
- ✅ 数据验证
- ✅ 性能基准

## 🐛 故障排查

### 依赖问题

```bash
pip install -r requirements.txt --upgrade
```

### 权限问题

```bash
chmod +x tests/*.py
chmod +x tests/*.sh
```

### 网络问题

```bash
# 只运行离线测试
python tests/run_all_tests.py --skip-network
```

## 📝 下一步

测试通过后，你可以：

1. **本地运行完整程序**

   ```bash
   export GOOGLE_API_KEY="your_key"
   export EMAIL_USER="your_email"
   export EMAIL_PASSWORD="your_password"
   python main.py
   ```

2. **配置 GitHub Actions**
   - 添加 Secrets (GOOGLE_API_KEY, EMAIL_USER, EMAIL_PASSWORD)
   - 修改 config.yaml 中的 receiver
   - 手动触发 workflow 测试

3. **持续监控**
   - 检查每日邮件
   - 查看 Actions 运行日志
   - 定期清理缓存

查看 `tests/README.md` 获取更详细的测试文档。
