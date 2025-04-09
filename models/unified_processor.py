
import sys
import os
import json
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BASE_PROMPT, DEFAULT_MODEL

class UnifiedProcessor:
    """
    统一处理模块类，负责处理用户输入，更新空间理解、用户需求猜测、关键问题列表，并生成下一个问题
    """
    
    def __init__(self, openai_client):
        """初始化统一处理模块
        
        Args:
            openai_client: OpenAI API客户端实例
        """
        self.openai_client = openai_client
    
    def process(self, user_input, current_spatial_understanding, current_requirement_guess, 
                current_key_questions, conversation_history):
        """处理用户输入，更新空间理解、用户需求猜测、关键问题列表，并生成下一个问题
        
        Args:
            user_input (str): 用户输入的文本
            current_spatial_understanding (str): 当前的空间理解记录
            current_requirement_guess (str): 当前的用户需求猜测
            current_key_questions (list): 当前的关键问题列表
            conversation_history (list): 系统与用户的问答记录
        
        Returns:
            dict: 包含更新后的空间理解、用户需求猜测、关键问题列表和下一个问题的JSON对象
        """
        # 如果当前没有空间理解记录，则初始化为空字符串
        if not current_spatial_understanding:
            current_spatial_understanding = "目前没有关于建筑边界和环境的信息。"
        
        # 如果当前没有用户需求猜测，则初始化为空字符串
        if not current_requirement_guess:
            current_requirement_guess = "目前没有关于用户需求的猜测。"
        
        # 格式化关键问题列表，便于提供给LLM
        key_questions_formatted = self._format_key_questions(current_key_questions)
        
        # 格式化对话历史
        conversation_history_formatted = self._format_conversation_history(conversation_history)
        
        # 准备提示词
        prompt = self._prepare_prompt(
            user_input=user_input,
            current_spatial_understanding=current_spatial_understanding,
            current_requirement_guess=current_requirement_guess,
            key_questions_formatted=key_questions_formatted,
            conversation_history_formatted=conversation_history_formatted
        )
        
        # 调用OpenAI API获取更新后的信息
        response = self.openai_client.generate_completion(
            prompt=prompt,
            model_name=DEFAULT_MODEL,
            temperature=0.7
        )
        
        # 如果API调用失败或返回为空，则保持原记录不变
        if not response:
            return {
                "thinking": "无法处理用户输入，请重试。",
                "user_requirements": {
                    "updated": False,
                    "content": current_requirement_guess
                },
                "spatial_understanding": {
                    "updated": False,
                    "content": current_spatial_understanding
                },
                "key_questions": {
                    "updated": False,
                    "content": current_key_questions
                },
                "next_question": "能否再详细描述一下您对这个建筑设计的期望和需求？"
            }
        
        # 解析API返回的JSON响应
        try:
            result = json.loads(response)
            
            # 提取思考内容
            thinking = result.get("thinking", "")
            
            # 提取用户需求猜测更新
            user_requirements_updated = result.get("user_requirements", {}).get("updated", False)
            user_requirements_content = result.get("user_requirements", {}).get("content", current_requirement_guess)
            
            # 提取空间理解更新
            spatial_understanding_updated = result.get("spatial_understanding", {}).get("updated", False)
            spatial_understanding_content = result.get("spatial_understanding", {}).get("content", current_spatial_understanding)
            
            # 提取关键问题列表更新
            key_questions_updated = result.get("key_questions", {}).get("updated", False)
            key_questions_content = result.get("key_questions", {}).get("content", current_key_questions)
            
            # 提取下一个问题
            next_question = result.get("next_question", "能否再详细描述一下您对这个建筑设计的期望和需求？")
            
            return {
                "thinking": thinking,
                "user_requirements": {
                    "updated": user_requirements_updated,
                    "content": user_requirements_content
                },
                "spatial_understanding": {
                    "updated": spatial_understanding_updated,
                    "content": spatial_understanding_content
                },
                "key_questions": {
                    "updated": key_questions_updated,
                    "content": key_questions_content
                },
                "next_question": next_question
            }
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回原记录
            return {
                "thinking": "处理用户输入时出现错误，无法解析响应。",
                "user_requirements": {
                    "updated": False,
                    "content": current_requirement_guess
                },
                "spatial_understanding": {
                    "updated": False,
                    "content": current_spatial_understanding
                },
                "key_questions": {
                    "updated": False,
                    "content": current_key_questions
                },
                "next_question": "能否再详细描述一下您对这个建筑设计的期望和需求？"
            }
    
    def _format_key_questions(self, key_questions):
        """格式化关键问题列表，便于提供给LLM
        
        Args:
            key_questions (Dict): 关键问题列表
        
        Returns:
            str: 格式化后的关键问题列表
        """
        formatted_questions = ""
        
        for question in key_questions:
            formatted_questions += f"{question["category"]}: {question["status"]}, {question["details"]}"
            formatted_questions += "\n"
        
        return formatted_questions
    
    def _format_conversation_history(self, conversation_history):
        """格式化对话历史，便于提供给LLM
        
        Args:
            conversation_history (list): 对话历史
        
        Returns:
            str: 格式化后的对话历史
        """
        formatted_history = ""
        
        for entry in conversation_history:
            role = entry.get('role', '')
            content = entry.get('content', '')
            
            if role == 'user':
                formatted_history += f"用户: {content}\n\n"
            elif role == 'system':
                formatted_history += f"系统: {content}\n\n"
        
        return formatted_history
    
    def _prepare_prompt(self, user_input, current_spatial_understanding, 
                       current_requirement_guess, key_questions_formatted, 
                       conversation_history_formatted):
        """准备提示词
        
        Args:
            user_input (str): 用户输入的文本
            current_spatial_understanding (str): 当前的空间理解记录
            current_requirement_guess (str): 当前的用户需求猜测
            key_questions_formatted (str): 格式化后的关键问题列表
            conversation_history_formatted (str): 格式化后的对话历史
        
        Returns:
            str: 准备好的提示词
        """
        prompt = f"""{BASE_PROMPT}

你的当前任务是处理最新的用户输入，更新空间理解、用户需求猜测、关键问题列表，并生成下一个问题。

请按照以下步骤进行：
1. 从整体任务上进行思考，分析用户输入的内容，判断是否需要更新空间理解、用户需求猜测或关键问题列表。
2. 分析用户输入，提取关于建筑边界和环境的信息，更新spatial_understanding，空间理解指的是建筑形状、面积、周围环境信息等。
3. 分析用户输入，推测用户的建筑设计需求和偏好，更新user_requirements。
4. 根据用户输入和已有信息，更新key_questions。
5. 生成下一个问题，引导用户提供更多信息。

当前空间理解记录：
{current_spatial_understanding}

当前用户需求猜测：
{current_requirement_guess}

当前关键问题列表：
{key_questions_formatted}

系统与用户的问答记录：
{conversation_history_formatted}

用户当前输入：
{user_input}

请以JSON格式返回以下内容：
{{
   "thinking": 对本次所有内容更新的思考,
   "user_requirements": {{
      "updated": (true/false),
      "content": "" //更新后的内容，string格式
   }},
   "spatial_understanding": {{
      "updated": (true/false),
      "content": "" //更新后的内容，string格式
   }},
   "key_questions": {{
      "updated": (true/false),
      "content": [
        {{
          "category": "" //问题类别,
          "status": "" //未知/已知,
          "details": "" //简要描述}}
      ] //更新的内容，格式严格按照关键问题列表的格式，list格式，要包含所有问题类别
   }},
   "next_question": 下一个问题（如果所有问题的状态都是已知，则为空字符串）
}}
注意：
- 下一个问题可以是根据关键问题列表中"未知"状态的问题产生的新问题，也可以是根据上一问答中未能解决或明确的问题继续提问
- 请确保返回的JSON格式正确，所有字段都必须存在，只返回json内容，不要包含任何解释或注释
- 如果某项内容没有更新，请保持原内容不变，并将updated设为false，content返回空字符串
- 哪怕是状态已知的问题，也可以在关键问题列表中更新details，以提供更详细的信息
- 房间数量和类型：要时刻注意更新调整；生活方式：从用户的日常生活习惯中提取设计可能用到的信息；空间使用偏好：可能涉及到空间的方位、采光、空间关系等；环境应对需求：考虑噪音、与周围环境的交互或排斥关系等。
"""
        
        return prompt