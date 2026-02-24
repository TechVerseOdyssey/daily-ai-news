# Copyright 2026 Daily AI News Project
# Licensed under the MIT License

"""
AI 总结模块
负责调用 Gemini API 生成新闻智能总结
"""

import os

# 延迟导入 genai，避免在未安装时报错
genai = None


class AISummarizer:
    """AI 总结生成器类"""
    
    def __init__(self, config):
        """
        初始化 AI 总结器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.client = None
        self._initialized = False
        self._cached_model_name = None
    
    def _ensure_client(self):
        """确保 Gemini 客户端已初始化"""
        global genai
        
        if self._initialized:
            return self.client is not None
        
        self._initialized = True
        
        # 延迟导入
        if genai is None:
            try:
                from google import genai as _genai
                genai = _genai
            except ImportError:
                print("  ⚠️  google-genai 库未安装，AI 总结功能不可用")
                return False
        
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
            return False
        
        try:
            self.client = genai.Client(api_key=api_key)
            return True
        except Exception as e:
            print(f"初始化 Gemini 客户端失败: {e}")
            return False
    
    def _get_available_model(self):
        """
        获取可用的免费 Gemini 模型（带缓存，避免重复查询）
        
        Returns:
            str: 可用的模型名称
        """
        if self._cached_model_name:
            return self._cached_model_name
        
        preferred_models = [
            'gemini-2.0-flash',
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro',
        ]
        
        config_model = self.config.get('gemini', {}).get('model_name', '')
        if config_model and config_model not in preferred_models:
            preferred_models.insert(0, config_model)
        
        try:
            print("正在获取可用的 Gemini 模型...")
            available_models = []
            
            for model in self.client.models.list():
                model_name = model.name
                if model_name.startswith('models/'):
                    model_name = model_name[7:]
                available_models.append(model_name)
            
            print(f"  发现 {len(available_models)} 个可用模型")
            
            for preferred in preferred_models:
                if preferred in available_models:
                    print(f"  ✓ 选择模型: {preferred}")
                    self._cached_model_name = preferred
                    return preferred
                for available in available_models:
                    if available.startswith(preferred):
                        print(f"  ✓ 选择模型: {available}")
                        self._cached_model_name = available
                        return available
            
            for available in available_models:
                if 'flash' in available.lower():
                    print(f"  ✓ 选择模型: {available}")
                    self._cached_model_name = available
                    return available
            
            for available in available_models:
                if 'gemini' in available.lower():
                    print(f"  ✓ 选择模型: {available}")
                    self._cached_model_name = available
                    return available
            
            print(f"  ⚠ 未找到可用模型，使用配置默认值: {config_model}")
            return config_model
            
        except Exception as e:
            print(f"  ⚠ 获取模型列表失败: {e}")
            fallback = self.config.get('gemini', {}).get('model_name', 'gemini-2.0-flash')
            print(f"  使用默认模型: {fallback}")
            return fallback
    
    def _generate_summary(self, content):
        """
        调用 Gemini 生成总结
        
        Args:
            content: 要总结的内容文本
        
        Returns:
            str or None: 生成的总结，失败返回 None
        """
        print("正在调用 Gemini 进行总结 (可能需要十几秒)...")
        full_prompt = self.config.get('prompt', '') + "\n" + content
        
        model_name = self._get_available_model()
        
        try:
            print(f"使用模型: {model_name}")
            response = self.client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini API 调用失败: {e}")
            try:
                print("尝试使用备用 API 格式 (google-generativeai)...")
                import google.generativeai as genai_old
                api_key = os.environ.get("GOOGLE_API_KEY")
                if not api_key:
                    print("备用方法失败: GOOGLE_API_KEY 环境变量未设置")
                    return None
                genai_old.configure(api_key=api_key)
                backup_model = genai_old.GenerativeModel(model_name)
                backup_response = backup_model.generate_content(full_prompt)
                return backup_response.text
            except Exception as e2:
                print(f"备用方法也失败: {e2}")
                return None
    
    def is_enabled(self):
        """
        检查 AI 总结功能是否启用
        
        Returns:
            bool: 是否启用
        """
        return self.config.get('gemini', {}).get('enable_ai_summary', True)
    
    def enhance_with_ai(self, sources_data):
        """
        尝试用大模型增强内容
        
        Args:
            sources_data: 结构化的数据源列表
        
        Returns:
            str or None: AI 生成的总结（HTML 格式），失败返回 None
        """
        if not self.is_enabled():
            print("\n⏭️  AI 总结已禁用（可在 config.yaml 中设置 enable_ai_summary: true 启用）")
            return None
        
        if not self._ensure_client():
            print("  ⚠️  Gemini 客户端初始化失败，跳过 AI 总结")
            return None
        
        try:
            print("\n正在尝试使用 AI 生成智能总结...")
            print("  ⏳ 等待大模型响应（这可能需要10-30秒）...")
            
            content_parts = []
            for source in sources_data:
                content_parts.append(f"\n\n--- 来源：{source['source']} ---")
                for item in source['items']:
                    content_parts.append(f"\n标题: {item['title']}")
                    content_parts.append(f"链接: {item['link']}")
                    content_parts.append(f"摘要: {item['summary']}\n")
            
            content_text = "\n".join(content_parts)
            
            ai_summary = self._generate_summary(content_text)
            
            if ai_summary:
                print("  ✅ AI 总结生成成功")
                return ai_summary
            else:
                print("  ⚠️  AI 总结生成失败，将使用基础版本")
                return None
                
        except Exception as e:
            print(f"  ⚠️  AI 增强功能异常: {e}")
            return None
