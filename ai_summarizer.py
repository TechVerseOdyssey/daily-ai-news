# Copyright 2026 Daily AI News Project
# Licensed under the MIT License

"""
AI 总结模块
支持 OpenRouter（主要）和 Gemini（备用）两种 API 生成新闻智能总结
"""

import os

# 延迟导入，避免在未安装时报错
genai = None


class AISummarizer:
    """AI 总结生成器类，支持 OpenRouter 和 Gemini 双后端"""
    
    def __init__(self, config):
        """
        初始化 AI 总结器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self._openrouter_client = None
        self._gemini_client = None
        self._initialized_openrouter = False
        self._initialized_gemini = False
        self._cached_gemini_model = None
    
    # ==================== OpenRouter 后端 ====================
    
    def _ensure_openrouter(self):
        """确保 OpenRouter 客户端已初始化"""
        if self._initialized_openrouter:
            return self._openrouter_client is not None
        
        self._initialized_openrouter = True
        
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("  ⚠️  环境变量 OPENROUTER_API_KEY 未设置，OpenRouter 不可用")
            return False
        
        try:
            from openai import OpenAI
            self._openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            return True
        except ImportError:
            print("  ⚠️  openai 库未安装，OpenRouter 不可用（pip install openai）")
            return False
        except Exception as e:
            print(f"  ⚠️  OpenRouter 客户端初始化失败: {e}")
            return False
    
    def _generate_via_openrouter(self, content):
        """
        通过 OpenRouter API 生成总结（带 429 重试）
        
        Args:
            content: 要总结的内容文本
        
        Returns:
            str or None: 生成的总结，失败返回 None
        """
        import time
        
        openrouter_config = self.config.get('openrouter', {})
        model = openrouter_config.get('model')
        if not model:
            print("  ⚠️  config.yaml 中未配置 openrouter.model，OpenRouter 不可用")
            return None
        prompt = self.config.get('prompt', '')
        max_retries = openrouter_config.get('max_retries', 3)
        
        print(f"  🔗 使用 OpenRouter (模型: {model})...")
        
        for attempt in range(max_retries):
            try:
                response = self._openrouter_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": content},
                    ],
                )
                result = response.choices[0].message.content
                if result:
                    print("  ✅ OpenRouter 总结生成成功")
                return result
            except Exception as e:
                error_str = str(e)
                # 429 限流：等待后重试
                if '429' in error_str and attempt < max_retries - 1:
                    wait = 15 * (attempt + 1)
                    print(f"  ⚠️  触发速率限制，等待 {wait} 秒后重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(wait)
                    continue
                print(f"  ❌ OpenRouter API 调用失败: {e}")
                return None
        
        return None
    
    # ==================== Gemini 后端（备用） ====================
    
    def _ensure_gemini(self):
        """确保 Gemini 客户端已初始化"""
        global genai
        
        if self._initialized_gemini:
            return self._gemini_client is not None
        
        self._initialized_gemini = True
        
        if genai is None:
            try:
                from google import genai as _genai
                genai = _genai
            except ImportError:
                print("  ⚠️  google-genai 库未安装，Gemini 备用方案不可用")
                return False
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("  ⚠️  环境变量 GOOGLE_API_KEY 未设置，Gemini 备用方案不可用")
            return False
        
        try:
            self._gemini_client = genai.Client(api_key=api_key)
            return True
        except Exception as e:
            print(f"  ⚠️  Gemini 客户端初始化失败: {e}")
            return False
    
    def _get_gemini_model(self):
        """获取可用的 Gemini 模型（带缓存）"""
        if self._cached_gemini_model:
            return self._cached_gemini_model
        
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
            available_models = []
            for model in self._gemini_client.models.list():
                name = model.name
                if name.startswith('models/'):
                    name = name[7:]
                available_models.append(name)
            
            for preferred in preferred_models:
                if preferred in available_models:
                    self._cached_gemini_model = preferred
                    return preferred
                for available in available_models:
                    if available.startswith(preferred):
                        self._cached_gemini_model = available
                        return available
            
            for available in available_models:
                if 'flash' in available.lower():
                    self._cached_gemini_model = available
                    return available
        except Exception as e:
            print(f"  ⚠️  获取 Gemini 模型列表失败: {e}")
        
        fallback = self.config.get('gemini', {}).get('model_name', 'gemini-2.0-flash')
        self._cached_gemini_model = fallback
        return fallback
    
    def _generate_via_gemini(self, content):
        """
        通过 Gemini API 生成总结（备用）
        
        Args:
            content: 要总结的内容文本
        
        Returns:
            str or None: 生成的总结，失败返回 None
        """
        model_name = self._get_gemini_model()
        full_prompt = self.config.get('prompt', '') + "\n" + content
        
        print(f"  🔗 使用 Gemini 备用方案 (模型: {model_name})...")
        
        try:
            response = self._gemini_client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            result = response.text
            if result:
                print("  ✅ Gemini 总结生成成功")
            return result
        except Exception as e:
            print(f"  ❌ Gemini API 调用失败: {e}")
            # 尝试旧版 API
            try:
                import google.generativeai as genai_old
                api_key = os.environ.get("GOOGLE_API_KEY")
                if not api_key:
                    return None
                genai_old.configure(api_key=api_key)
                backup_model = genai_old.GenerativeModel(model_name)
                backup_response = backup_model.generate_content(full_prompt)
                return backup_response.text
            except Exception as e2:
                print(f"  ❌ Gemini 旧版 API 也失败: {e2}")
                return None
    
    # ==================== 统一接口 ====================
    
    def _generate_summary(self, content):
        """
        生成 AI 总结：先尝试 OpenRouter，失败后回退到 Gemini
        
        Args:
            content: 要总结的内容文本
        
        Returns:
            str or None: 生成的总结，失败返回 None
        """
        print("正在调用 AI 进行总结 (可能需要十几秒)...")
        
        # 1. 主要方案：OpenRouter
        if self._ensure_openrouter():
            result = self._generate_via_openrouter(content)
            if result:
                return result
            print("  ⚠️  OpenRouter 失败，尝试 Gemini 备用方案...")
        else:
            print("  ⚠️  OpenRouter 不可用，尝试 Gemini 备用方案...")
        
        # 2. 备用方案：Gemini
        if self._ensure_gemini():
            result = self._generate_via_gemini(content)
            if result:
                return result
        
        print("  ❌ 所有 AI 后端均不可用")
        return None
    
    def is_enabled(self):
        """
        检查 AI 总结功能是否启用
        
        Returns:
            bool: 是否启用
        """
        return self.config.get('ai_summary', {}).get('enabled',
               self.config.get('gemini', {}).get('enable_ai_summary', True))
    
    def enhance_with_ai(self, sources_data):
        """
        尝试用大模型增强内容
        
        Args:
            sources_data: 结构化的数据源列表
        
        Returns:
            str or None: AI 生成的总结（HTML 格式），失败返回 None
        """
        if not self.is_enabled():
            print("\n⏭️  AI 总结已禁用（可在 config.yaml 中设置 ai_summary.enabled: true 启用）")
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
