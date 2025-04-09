"""
约束条件优化模块：根据用户反馈，优化调整约束条件
"""
import sys
import os
import json
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONSTRAINT_REFINEMENT_PROMPT, CONSTRAINT_QUANTIFICATION_MODEL, BASE_PROMPT

class ConstraintRefinement:
    """
    约束条件优化模块类，负责根据用户反馈优化约束条件
    """
    
    def __init__(self, openai_client):
        """初始化约束条件优化模块
        
        Args:
            openai_client: OpenAI API客户端实例
        """
        self.openai_client = openai_client
    
    def refine_constraints(self, constraints, user_feedback, spatial_understanding, model_name=None):
        """根据用户反馈优化约束条件
        
        Args:
            constraints (dict): 当前的约束条件（all格式）
            user_feedback (str): 用户的反馈意见
            spatial_understanding (str): 空间理解记录
            model_name (str, optional): 使用的模型名称
        
        Returns:
            dict: 优化后的约束条件
        """
        # 如果未指定模型，使用约束量化模块的默认模型
        if not model_name:
            model_name = CONSTRAINT_QUANTIFICATION_MODEL
            
        # 准备提示词
        prompt = CONSTRAINT_REFINEMENT_PROMPT.format(
            base_prompt=BASE_PROMPT,
            current_constraints=json.dumps(constraints, ensure_ascii=False, indent=2),
            user_feedback=user_feedback,
            spatial_understanding=spatial_understanding
        )
        
        # 调用API优化约束条件
        response = self.openai_client.generate_completion(
            prompt=prompt,
            model_name=model_name,
            temperature=0.5  # 使用较低温度以获得更精确的结果
        )
        
        # 如果API调用失败或返回为空，则返回原约束条件
        if not response:
            return constraints
        
        # 处理API返回的JSON响应
        try:
            result = json.loads(response)
            
            # 处理多出的"constraints"嵌套层问题
            if "refined_constraints" in result:
                refined_constraints = result["refined_constraints"]
            else:
                refined_constraints = result
            
            # 检查refined_constraints的格式是否符合预期
            if not self._validate_constraints(refined_constraints):
                print("优化后的约束条件格式不符合预期，将使用原约束条件。")
                return constraints
            
            return refined_constraints
        
        except (json.JSONDecodeError, TypeError) as e:
            print(f"解析优化后的约束条件时出错: {str(e)}")
            return constraints
    
    def _validate_constraints(self, constraints):
        """验证约束条件的格式是否符合预期
        
        Args:
            constraints (dict): 要验证的约束条件
        
        Returns:
            bool: 约束条件是否有效
        """
        # 检查基本结构
        if not isinstance(constraints, dict):
            return False
        
        # 检查是否有硬约束和软约束
        if "hard_constraints" not in constraints or "soft_constraints" not in constraints:
            return False
        
        # 检查硬约束中是否有房间列表
        if "room_list" not in constraints["hard_constraints"]:
            return False
        
        # 检查软约束中是否有各类约束
        required_constraints = ["connection", "area", "orientation", "window_access", "aspect_ratio", "repulsion"]
        for constraint_type in required_constraints:
            if constraint_type not in constraints["soft_constraints"]:
                return False
            
            # 检查每种约束是否有weight和constraints字段
            if "weight" not in constraints["soft_constraints"][constraint_type] or \
               "constraints" not in constraints["soft_constraints"][constraint_type]:
                return False
        
        return True