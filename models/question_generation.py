"""
提问生成模块：根据用户需求猜测和关键问题列表，生成下一个问题，引导用户提供更多信息
"""
import sys
import os
import json
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import QUESTION_GENERATION_PROMPT, QUESTION_GENERATION_TEMPERATURE
from config import QUESTION_GENERATION_MODEL

class QuestionGeneration:
    """
    提问生成模块类，负责生成下一个问题
    """
    
    def __init__(self, openai_client):
        """初始化提问生成模块
        
        Args:
            openai_client: OpenAI API客户端实例
        """
        self.openai_client = openai_client
    
    def generate_question(self, current_requirement_guess, key_questions):
        """生成下一个问题并更新关键问题状态
        
        Args:
            current_requirement_guess (str): 当前的用户需求猜测
            key_questions (list): 关键问题列表（按类别组织）
        
        Returns:
            str: 生成的下一个问题
        """
        # 如果没有用户需求猜测，生成初始问题
        if not current_requirement_guess or current_requirement_guess == "目前没有关于用户需求的猜测。":
            return "请您先告诉我您的建筑项目的基本情况和需求。"
        
        # 格式化关键问题列表，便于提供给LLM
        key_questions_formatted = self._format_key_questions(key_questions)
        
        # 准备提示词
        prompt = QUESTION_GENERATION_PROMPT.format(
            current_requirement_guess=current_requirement_guess,
            key_questions_formatted=key_questions_formatted
        )
        
        # 调用API生成下一个问题并同时更新关键问题状态，使用指定模型
        response = self.openai_client.generate_completion(
            prompt=prompt,
            model_name=QUESTION_GENERATION_MODEL,  # 使用为问题生成指定的模型
            temperature=QUESTION_GENERATION_TEMPERATURE
        )
        
        # 如果API调用失败或返回为空，则使用默认问题
        if not response:
            return "能否再详细描述一下您对这个建筑设计的期望和需求？"
        
        # 尝试解析JSON响应
        try:
            result = json.loads(response)
            if "question" in result:
                # 如果响应中包含categories信息，则更新关键问题状态
                if "categories" in result:
                    for category_result in result["categories"]:
                        category_name = category_result.get("category")
                        status = category_result.get("status")
                        
                        # 查找对应的类别并更新状态
                        for category in key_questions:
                            if category["category"] == category_name and status == "已知":
                                category["status"] = "已知"
                
                return result["question"]
        except json.JSONDecodeError:
            # 如果不是JSON格式，则按照原来的方式处理
            pass
            
        # 返回生成的问题
        return response.strip()
    
    def _format_key_questions(self, key_questions):
        """格式化关键问题列表，便于提供给LLM
        
        Args:
            key_questions (list): 关键问题列表（按类别组织）
        
        Returns:
            str: 格式化后的关键问题列表
        """
        formatted_questions = ""
        
        for category in key_questions:
            formatted_questions += f"类别：{category['category']}\n"
            for question in category['questions']:
                formatted_questions += f"- {question['question']} (状态：{question['status']})\n"
            formatted_questions += "\n"
        
        return formatted_questions