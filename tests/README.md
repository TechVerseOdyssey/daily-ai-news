# 测试文档

这个目录包含了项目的自动化测试脚本。

## 📋 测试清单

### 1. 配置文件验证 (`test_01_config.py`)
- ✅ YAML 格式验证
- ✅ 必需字段检查
- ✅ RSS 源配置验证
- ✅ 邮件设置检查
- ✅ 爬虫参数验证

**运行：**
```bash
python tests/test_01_config.py
```

### 2. HTML 清理和数据验证 (`test_02_cleaning.py`)
- ✅ HTML 标签清理
- ✅ 实体编码解码
- ✅ 空白字符处理
- ✅ 标题验证
- ✅ 链接验证
- ✅ 广告过滤

**运行：**
```bash
python tests/test_02_cleaning.py
```

### 3. 缓存机制 (`test_03_cache.py`)
- ✅ 缓存保存和加载
- ✅ 缓存过期处理
- ✅ 不存在的缓存处理
- ✅ 中文和特殊字符
- ✅ 大数据缓存

**运行：**
```bash
python tests/test_03_cache.py
```

### 4. 单个 RSS 源抓取 (`test_04_fetch_single.py`)
- ✅ RSS 源连接
- ✅ 内容抓取
- ✅ 重试机制
- ✅ 内容质量验证

**运行（需要网络）：**
```bash
python tests/test_04_fetch_single.py
```

### 5. 并发抓取性能 (`test_05_concurrent.py`)
- ✅ 多线程并发
- ✅ 性能测试
- ✅ 数据完整性
- ✅ 耗时统计

**运行（需要网络）：**
```bash
python tests/test_05_concurrent.py
```

## 🚀 快速开始

### 运行所有测试
```bash
# 在项目根目录运行
python tests/run_all_tests.py
```

### 跳过网络测试
```bash
# 只运行不需要网络的测试
python tests/run_all_tests.py --skip-network
```

### 单独运行某个测试
```bash
python tests/test_01_config.py
python tests/test_02_cleaning.py
python tests/test_03_cache.py
# ... 等等
```

## 📊 测试输出示例

```
======================================================================
🧪 Daily AI News - 自动化测试套件
======================================================================

======================================================================
运行测试: 配置文件验证
======================================================================
✅ 配置文件验证 - 通过

======================================================================
运行测试: HTML清理和验证
======================================================================
✅ HTML清理和验证 - 通过

...

======================================================================
📊 测试总结
======================================================================

总计: 5 个测试
✅ 通过: 5
❌ 失败: 0

详细结果:
  ✅ 通过 - 配置文件验证
  ✅ 通过 - HTML清理和验证
  ✅ 通过 - 缓存机制
  ✅ 通过 - 单源抓取
  ✅ 通过 - 并发抓取

======================================================================
✅ 所有测试通过！
======================================================================
```

## 🔧 故障排查

### 测试失败常见原因

1. **配置文件问题**
   ```bash
   # 检查 config.yaml 是否存在
   ls -la config.yaml
   
   # 验证 YAML 格式
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. **网络连接问题**
   ```bash
   # 测试网络连接
   curl -I https://huggingface.co/papers/daily_papers.rss
   
   # 使用代理（如果需要）
   export http_proxy=http://proxy:port
   export https_proxy=http://proxy:port
   ```

3. **依赖问题**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt
   ```

4. **权限问题**
   ```bash
   # 确保测试脚本有执行权限
   chmod +x tests/*.py
   ```

## 📝 添加新测试

创建新测试文件的模板：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 X: 测试名称
测试描述
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import your_function

def test_your_feature():
    """测试你的功能"""
    print("=" * 60)
    print("测试 X: 测试名称")
    print("=" * 60)
    
    try:
        # 你的测试代码
        result = your_function()
        
        if result:
            print("✅ 测试通过")
            return True
        else:
            print("❌ 测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    success = test_your_feature()
    sys.exit(0 if success else 1)
```

然后在 `run_all_tests.py` 的 `TESTS` 列表中添加：
```python
("测试名称", "test_0X_yourtest.py", requires_network_bool),
```

## 🎯 持续集成

这些测试可以集成到 GitHub Actions 中：

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python tests/run_all_tests.py --skip-network
```

## 📞 获取帮助

如果测试遇到问题：
1. 查看测试输出的详细错误信息
2. 检查项目 README.md 的环境配置部分
3. 提交 Issue 时附上完整的测试输出
