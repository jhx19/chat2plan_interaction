"""
需求分析模块：根据用户输入和已有信息，推测用户需求，更新用户需求猜测
"""
import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import REQUIREMENT_ANALYSIS_PROMPT, REQUIREMENT_ANALYSIS_TEMPERATURE, CHECK_QUESTION_ANSWERED_PROMPT
from config import REQUIREMENT_ANALYSIS_MODEL

class RequirementAnalysis:
    """
    需求分析模块类，负责分析用户输入，推测用户需求
    """
    
    def __init__(self, openai_client):
        """初始化需求分析模块
        
        Args:
            openai_client: OpenAI API客户端实例
        """
        self.openai_client = openai_client
    
    def process(self, user_input, current_requirement_guess, spatial_understanding):
        """处理用户输入，更新用户需求猜测和空间理解
        
        Args:
            user_input (str): 用户输入的文本
            current_requirement_guess (str): 当前的用户需求猜测
            spatial_understanding (str): 当前的空间理解记录
        
        Returns:
            dict: 包含更新后的用户需求猜测、空间理解记录和更新状态的JSON对象
        """
        # 如果当前没有用户需求猜测，则初始化为空字符串
        if not current_requirement_guess:
            current_requirement_guess = "目前没有关于用户需求的猜测。"
        
        # 准备提示词
        prompt = REQUIREMENT_ANALYSIS_PROMPT.format(
            user_input=user_input,
            current_requirement_guess=current_requirement_guess,
            spatial_understanding=spatial_understanding
        )
        
        # 调用API获取更新后的用户需求猜测，使用指定模型
        response = self.openai_client.generate_completion(
            prompt=prompt,
            model_name=REQUIREMENT_ANALYSIS_MODEL,  # 使用为需求分析指定的模型
            temperature=REQUIREMENT_ANALYSIS_TEMPERATURE
        )
        
        # 如果API调用失败或返回为空，则保持原猜测不变
        if not response:
            return {
                "requirement": {
                    "content": current_requirement_guess,
                    "updated": False
                },
                "spatial_understanding": {
                    "content": spatial_understanding,
                    "updated": False
                }
            }
        
        # 尝试解析响应为JSON
        try:
            # 首先尝试直接解析为JSON
            result = json.loads(response)
            # 验证JSON结构是否符合预期
            if "spatial_updated" in result and "requirement_updated" in result:
                # 构建返回结果
                return {
                    "requirement": {
                        "content": result.get("requirement_guess", current_requirement_guess),
                        "updated": result.get("requirement_updated", False)
                    },
                    "spatial_understanding": {
                        "content": result.get("spatial_understanding", spatial_understanding),
                        "updated": result.get("spatial_updated", False)
                    }
                }
        except json.JSONDecodeError:
            # 如果不是JSON格式，则按照原来的方式处理
            pass
        
        # 处理并返回更新后的用户需求猜测
        updated_requirement_guess = response.strip()
        
        # 检查是否有实质性更新
        requirement_updated = updated_requirement_guess != current_requirement_guess
        if updated_requirement_guess == "目前没有关于用户需求的猜测。" and current_requirement_guess != updated_requirement_guess:
            requirement_updated = False
            updated_requirement_guess = current_requirement_guess
        
        # 返回JSON格式的结果
        return {
            "requirement": {
                "content": updated_requirement_guess,
                "updated": requirement_updated
            },
            "spatial_understanding": {
                "content": spatial_understanding,
                "updated": False
            }
        }
    
    def check_question_answered(self, question, requirement_guess):
        """检查问题是否已在用户需求猜测中得到回答
        
        Args:
            question (str): 要检查的问题
            requirement_guess (str): 当前的用户需求猜测
        
        Returns:
            bool: 问题是否已被回答
        """
        # 如果没有用户需求猜测，则问题未回答
        if not requirement_guess or requirement_guess == "目前没有关于用户需求的猜测。":
            return False
        
        # 准备提示词
        prompt = CHECK_QUESTION_ANSWERED_PROMPT.format(
            question=question,
            requirement_guess=requirement_guess
        )
        
        # 调用API判断问题是否已回答，使用与需求分析相同的模型
        response = self.openai_client.generate_completion(
            prompt=prompt,
            model_name=REQUIREMENT_ANALYSIS_MODEL,  # 使用相同的模型确保一致性
            temperature=0.0  # 使用较低的温度以获得确定性结果
        )
        
        # 如果API调用失败或返回为空，则默认为未回答
        if not response:
            return False
        
        # 尝试解析JSON响应
        try:
            result = json.loads(response)
            if "answered" in result:
                return result["answered"]
        except json.JSONDecodeError:
            # 如果不是JSON格式，则按照原来的方式处理
            response = response.strip().lower()
            return "是" in response