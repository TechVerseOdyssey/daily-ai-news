# Copyright 2024 Daily AI News Project
# Licensed under the MIT License

"""
邮件发送模块
负责邮件发送，支持多收件人、自动 SMTP 配置检测
"""

import os
import re
from datetime import datetime
import yagmail


# 常用邮箱服务商 SMTP 配置
SMTP_CONFIGS = {
    'qq.com': {'host': 'smtp.qq.com', 'port': 465},
    'foxmail.com': {'host': 'smtp.qq.com', 'port': 465},
    'gmail.com': {'host': 'smtp.gmail.com', 'port': 587},
    'googlemail.com': {'host': 'smtp.gmail.com', 'port': 587},
    '163.com': {'host': 'smtp.163.com', 'port': 465},
    '126.com': {'host': 'smtp.126.com', 'port': 465},
    'yeah.net': {'host': 'smtp.yeah.net', 'port': 465},
    'sina.com': {'host': 'smtp.sina.com', 'port': 465},
    'sina.cn': {'host': 'smtp.sina.cn', 'port': 465},
    'sohu.com': {'host': 'smtp.sohu.com', 'port': 465},
    'aliyun.com': {'host': 'smtp.aliyun.com', 'port': 465},
    'outlook.com': {'host': 'smtp.office365.com', 'port': 587},
    'hotmail.com': {'host': 'smtp.office365.com', 'port': 587},
    'live.com': {'host': 'smtp.office365.com', 'port': 587},
    'yahoo.com': {'host': 'smtp.mail.yahoo.com', 'port': 465},
}


def is_valid_email(email):
    """
    校验邮箱地址是否有效
    
    Args:
        email: 邮箱地址字符串
    
    Returns:
        bool: 是否有效
    """
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def parse_email_receivers(receiver_str):
    """
    解析收件人字符串，支持多种分隔符
    
    Args:
        receiver_str: 收件人字符串，支持 ',' ';' 或空格分隔
    
    Returns:
        list: 有效的邮箱地址列表
    """
    if not receiver_str:
        return []
    
    normalized = receiver_str.replace(';', ',').replace(' ', ',')
    candidates = [email.strip() for email in normalized.split(',')]
    
    valid_emails = []
    invalid_emails = []
    
    for email in candidates:
        if not email:
            continue
        if is_valid_email(email):
            valid_emails.append(email)
        else:
            invalid_emails.append(email)
    
    if invalid_emails:
        print(f"  ⚠️  以下邮箱地址无效，已跳过: {', '.join(invalid_emails)}")
    
    return valid_emails


def get_smtp_config(sender_email):
    """
    根据发件人邮箱自动获取 SMTP 配置
    
    Args:
        sender_email: 发件人邮箱地址
    
    Returns:
        tuple: (smtp_host, smtp_port)
    """
    if not sender_email or '@' not in sender_email:
        return 'smtp.gmail.com', 587
    
    domain = sender_email.split('@')[-1].lower()
    
    if domain in SMTP_CONFIGS:
        smtp_config = SMTP_CONFIGS[domain]
        return smtp_config['host'], smtp_config['port']
    
    parts = domain.split('.')
    if len(parts) > 2:
        parent_domain = '.'.join(parts[-2:])
        if parent_domain in SMTP_CONFIGS:
            smtp_config = SMTP_CONFIGS[parent_domain]
            return smtp_config['host'], smtp_config['port']
    
    print(f"  ⚠️  未知邮箱域名 '{domain}'，尝试使用 smtp.{domain}:465")
    return f'smtp.{domain}', 465


def get_email_credentials():
    """
    获取邮件凭证和收件人，带有友好的错误提示
    
    Returns:
        tuple: (user, password, receivers) 或 (None, None, None) 如果缺失
    """
    user = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver_str = os.environ.get("EMAIL_RECEIVER", "")
    
    errors = []
    
    if not user:
        errors.append("EMAIL_USER (发件人邮箱)")
    if not password:
        errors.append("EMAIL_PASSWORD (邮箱授权码/密码)")
    if not receiver_str:
        errors.append("EMAIL_RECEIVER (收件人邮箱)")
    
    if errors:
        print("=" * 60)
        print("❌ 错误: 缺少必要的环境变量")
        print("=" * 60)
        print(f"\n缺失的环境变量: {', '.join(errors)}")
        print("\n请设置以下环境变量:")
        print("  export EMAIL_USER='your-email@example.com'")
        print("  export EMAIL_PASSWORD='your-password-or-app-token'")
        print("  export EMAIL_RECEIVER='receiver1@example.com,receiver2@example.com'")
        print("\n提示:")
        print("  - EMAIL_RECEIVER 支持多个收件人，用 ',' ';' 或空格分隔")
        print("  - QQ邮箱需要使用授权码，而非登录密码")
        print("  - Gmail 需要使用应用专用密码")
        print("=" * 60)
        return None, None, None
    
    receivers = parse_email_receivers(receiver_str)
    
    if not receivers:
        print("=" * 60)
        print("❌ 错误: 没有有效的收件人邮箱")
        print("=" * 60)
        print(f"\n环境变量 EMAIL_RECEIVER 的值: '{receiver_str}'")
        print("请检查邮箱地址格式是否正确")
        print("=" * 60)
        return None, None, None
    
    return user, password, receivers


class EmailSender:
    """邮件发送器类"""
    
    def __init__(self, config):
        """
        初始化邮件发送器
        
        Args:
            config: 配置字典
        """
        self.config = config
    
    def send(self, html_content):
        """
        发送邮件，支持多收件人
        
        Args:
            html_content: HTML 格式的邮件内容
        
        Returns:
            bool: 是否发送成功
        """
        print("正在准备发送邮件...")
        
        user, password, receivers = get_email_credentials()
        if not user or not receivers:
            return False
        
        smtp_host, smtp_port = get_smtp_config(user)
        
        email_settings = self.config.get('email_settings', {})
        subject_prefix = email_settings.get('subject', '🤖 AI 每日早报')
        subject = f"{subject_prefix} ({datetime.now().strftime('%Y-%m-%d')})"
        
        print(f"  发件人: {user}")
        print(f"  收件人: {', '.join(receivers)}")
        print(f"  SMTP: {smtp_host}:{smtp_port}")
        
        try:
            yag = yagmail.SMTP(user=user, password=password, host=smtp_host, port=smtp_port)
            yag.send(
                to=receivers,
                subject=subject,
                contents=[html_content]
            )
            print(f"  ✅ 邮件发送成功！共 {len(receivers)} 个收件人")
            return True
        except Exception as e:
            print(f"  ❌ 邮件发送失败: {e}")
            return False
