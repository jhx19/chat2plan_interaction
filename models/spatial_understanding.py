"""
空间理解模块：负责解析用户输入的建筑边界和环境信息，提取空间信息
"""
import sys
import os
import json
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BASE_PROMPT, SPATIAL_UNDERSTANDING_PROMPT, SPATIAL_UNDERSTANDING_TEMPERATURE, SPATIAL_UNDERSTANDING_MODEL

class SpatialUnderstanding:
    """
    空间理解模块类，负责解析用户输入的建筑边界和环境信息
    """
    
    def __init__(self, openai_client):
        """初始化空间理解模块
        
        Args:
            openai_client: OpenAI API客户端实例
        """
        self.openai_client = openai_client
    
    def process(self, user_input, current_spatial_understanding):
        """处理用户输入，提取空间信息
        
        Args:
            user_input (str): 用户输入的文本
            current_spatial_understanding (str): 当前的空间理解记录
        
        Returns:
            dict: 包含更新后的空间理解记录和更新状态的JSON对象
        """
        # 如果当前没有空间理解记录，则初始化为空字符串
        if not current_spatial_understanding:
            current_spatial_understanding = "目前没有关于建筑边界和环境的信息。"
        
        # 准备提示词
        prompt = SPATIAL_UNDERSTANDING_PROMPT.format(
            base_prompt=BASE_PROMPT,
            user_input=user_input,
            current_spatial_understanding=current_spatial_understanding
        )
        
        # 调用OpenAI API获取更新后的空间理解记录，使用指定模型
        response = self.openai_client.generate_completion(
            prompt=prompt,
            model_name=SPATIAL_UNDERSTANDING_MODEL,  # 使用为此模块指定的模型
            temperature=SPATIAL_UNDERSTANDING_TEMPERATURE
        )
        
        # 如果API调用失败或返回为空，则保持原记录不变
        if not response:
            return {
                "content": current_spatial_understanding,
                "updated": False
            }
        
        # 解析API返回的JSON响应
        try:
            result = json.loads(response)
            updated_spatial_understanding = result.get("spatial_understanding", "")
            
            # 检查是否有实质性更新
            if not updated_spatial_understanding:
                return {
                    "content": current_spatial_understanding,
                    "updated": False
                }
            
            # 检查是否有实质性更新
            is_updated = updated_spatial_understanding != current_spatial_understanding
            
            return {
                "content": updated_spatial_understanding,
                "updated": is_updated
            }
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回原记录
            return {
                "content": current_spatial_understanding,
                "updated": False
            }
        
