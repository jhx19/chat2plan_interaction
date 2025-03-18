"""
LLM API客户端，封装各种模型的API调用
"""
import os
import sys
import time
import json
import requests
import openai
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AVAILABLE_MODELS

class OpenAIClient:
    """
    LLM API客户端类，封装不同模型的API调用
    """
    
    def __init__(self):
        """初始化LLM API客户端
        
        从环境变量加载所有可能的API密钥并验证常用模型
        """
        # 检查环境变量中的API密钥
        self._check_api_keys()
        
        # 初始化模型客户端
        self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        
        # 缓存获取的访问令牌
        self.access_tokens = {}
        
        # 记录token使用量
        self.session_manager = None
    
    def set_session_manager(self, session_manager):
        """设置会话记录管理器
        
        Args:
            session_manager: SessionManager实例
        """
        self.session_manager = session_manager
    
    def _record_api_call(self, model_name, prompt, response, tokens_used):
        """记录API调用信息
        
        Args:
            model_name (str): 使用的模型名称
            prompt (str): 发送的提示词
            response (str): 收到的回应
            tokens_used (dict): 使用的token数量
        """
        if self.session_manager:
            self.session_manager.add_api_call(model_name, prompt, response, tokens_used)
    
    def _check_api_keys(self):
        """检查环境变量中的API密钥"""
        # 收集所有需要的API密钥环境变量
        required_env_vars = set()
        for model_name, model_config in AVAILABLE_MODELS.items():
            if "api_key_env" in model_config:
                required_env_vars.add(model_config["api_key_env"])
            if "secret_key_env" in model_config:
                required_env_vars.add(model_config["secret_key_env"])
        
        # 检查缺少的环境变量并发出警告
        missing_env_vars = [env_var for env_var in required_env_vars if env_var not in os.environ]
        if missing_env_vars:
            print(f"警告: 以下环境变量未设置，某些模型可能无法使用: {', '.join(missing_env_vars)}")
    
    def _get_model_config(self, model_name):
        """获取模型配置
        
        Args:
            model_name (str): 模型名称
        
        Returns:
            dict: 模型配置
        """
        if model_name in AVAILABLE_MODELS:
            return AVAILABLE_MODELS[model_name]
        else:
            raise ValueError(f"不支持的模型: {model_name}，请在config.py的AVAILABLE_MODELS中添加配置")

    
    def generate_completion(self, prompt, model_name=None, temperature=None, max_tokens=None):
        """生成文本补全，根据不同模型调用不同的API
        
        Args:
            prompt (str): 提示词
            model_name (str, optional): 使用的模型名称。如果为None，则使用默认模型。
            temperature (float, optional): 温度参数，控制随机性。如果为None，则使用配置中的默认值。
            max_tokens (int, optional): 最大生成令牌数。如果为None，则使用配置中的默认值。
        
        Returns:
            str: 生成的文本
        """
        # 如果未指定模型，使用默认的OpenAI模型
        if not model_name:
            model_name = "gpt-4o"
        
        # 获取模型配置
        try:
            model_config = self._get_model_config(model_name)
        except ValueError as e:
            print(str(e))
            # 回退到默认模型
            model_name = "gpt-4o"
            model_config = self._get_model_config(model_name)
        
        # 使用配置中的默认值（如果未提供）
        temperature = temperature if temperature is not None else model_config.get("temperature", 0.7)
        max_tokens = max_tokens if max_tokens is not None else model_config.get("max_tokens", 2000)
        
        # 根据模型类型选择不同的API调用方式
        model_type = model_config.get("type", "openai")
        
        try:
            if model_type == "openai":
                return self._call_openai_api(prompt, model_config, temperature, max_tokens)
            elif model_type == "anthropic":
                return self._call_anthropic_api(prompt, model_config, temperature, max_tokens)
            elif model_type == "zhipu":
                return self._call_zhipu_api(prompt, model_config, temperature, max_tokens)
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
        
        except Exception as e:
            print(f"调用{model_name} API时发生错误: {str(e)}")
            
            # 如果是速率限制错误，等待一段时间后重试
            if "rate_limit" in str(e).lower():
                print(f"达到API速率限制，等待10秒后重试...")
                time.sleep(10)
                return self.generate_completion(prompt, model_name, temperature, max_tokens)
            
            # 其他错误，返回空字符串
            return ""
    
    def _call_openai_api(self, prompt, model_config, temperature, max_tokens):
        """调用OpenAI兼容API
        
        Args:
            prompt (str): 提示词
            model_config (dict): 模型配置
            temperature (float): 温度参数
            max_tokens (int): 最大生成令牌数
        
        Returns:
            str: 生成的文本
        """
        # 设置自定义的API基础URL和API密钥
        base_url = model_config.get("base_url")
        api_key = os.environ.get(model_config.get("api_key_env", "OPENAI_API_KEY"), "")
        
        # 创建新的客户端实例（如果需要）
        if base_url and base_url != "https://api.openai.com/v1" or api_key != os.environ.get("OPENAI_API_KEY", ""):
            client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
        else:
            client = self.openai_client
        
        # 添加重试逻辑
        max_retries = 3
        retry_delay = 2
        
        # 导入配置参数，用于控制是否强制输出JSON格式
        from config import FORCE_JSON_OUTPUT, RESPONSE_FORMAT
        
        for attempt in range(max_retries):
            try:
                # 创建API调用参数
                api_params = {
                    "model": model_config.get("model", "gpt-3.5-turbo"),
                    "messages": [
                        {"role": "system", "content": "你是一个专业的建筑设计师助手，帮助用户设计建筑布局。你的回答应该基于专业知识，并考虑用户的个性化需求。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                
                # 如果需要强制输出JSON格式
                if FORCE_JSON_OUTPUT:
                    api_params["response_format"] = {"type": RESPONSE_FORMAT}
                
                response = client.chat.completions.create(**api_params)
                return response.choices[0].message.content
                
            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # 指数退避
                    print(f"达到API速率限制，等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                raise  # 重新抛出其他类型的异常
    
    def _call_anthropic_api(self, prompt, model_config, temperature, max_tokens):
        """调用Anthropic API
        
        Args:
            prompt (str): 提示词
            model_config (dict): 模型配置
            temperature (float): 温度参数
            max_tokens (int): 最大生成令牌数
        
        Returns:
            str: 生成的文本
        """
        api_key = os.environ.get(model_config.get("api_key_env", "ANTHROPIC_API_KEY"))
        model = model_config.get("model", "claude-instant-1.2")
        api_version = model_config.get("api_version", "2023-06-01")
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": api_version,
            "content-type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        else:
            raise Exception(f"Anthropic API错误: {response.status_code}, {response.text}")

    def _call_zhipu_api(self, prompt, model_config, temperature, max_tokens):
        """调用智谱AI API
        
        Args:
            prompt (str): 提示词
            model_config (dict): 模型配置
            temperature (float): 温度参数
            max_tokens (int): 最大生成令牌数
        
        Returns:
            str: 生成的文本
        """
        api_key = os.environ.get(model_config.get("api_key_env", "ZHIPU_API_KEY"))
        model = model_config.get("model", "glm-4")
        base_url = model_config.get("base_url", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的建筑设计师助手，帮助用户设计建筑布局。你的回答应该基于专业知识，并考虑用户的个性化需求。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(base_url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception(f"智谱AI API返回错误: {result}")
        else:
            raise Exception(f"智谱AI API错误: {response.status_code}, {response.text}")
        
