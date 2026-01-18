#!/bin/bash
# 快速测试设置脚本

echo "=========================================="
echo "Daily AI News - 测试环境设置"
echo "=========================================="

# 检查 Python 版本
echo ""
echo "1. 检查 Python 版本..."
python --version || python3 --version

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo ""
    echo "⚠️  警告: 未检测到虚拟环境"
    echo "   建议先创建虚拟环境:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate  # macOS/Linux"
    echo ""
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 安装依赖
echo ""
echo "2. 安装依赖..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装成功"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

# 运行测试
echo ""
echo "=========================================="
echo "3. 运行测试 (跳过网络测试)"
echo "=========================================="
python tests/run_all_tests.py --skip-network

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ 测试设置完成"
else
    echo "⚠️  部分测试失败，但环境已设置"
fi

exit $exit_code
