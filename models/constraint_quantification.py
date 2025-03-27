"""
约束条件量化模块：将用户需求猜测转化为软约束条件，进行冲突检测和用户确认
"""
import sys
import os
import json
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONSTRAINT_QUANTIFICATION_PROMPT, CONSTRAINT_QUANTIFICATION_TEMPERATURE, CONSTRAINT_ROOMS_OPTIMIZATION_PROMPT
from config import BASE_PROMPT, TEMPLATE_CONSTRAINTS_ALL_PATH, TEMPLATE_CONSTRAINTS_ROOMS_PATH
from config import CONSTRAINT_QUANTIFICATION_MODEL

class ConstraintQuantification:
    """
    约束条件量化模块类，负责将用户需求猜测转化为约束条件
    """
    
    def __init__(self, openai_client):
        """初始化约束条件量化模块
        
        Args:
            openai_client: OpenAI API客户端实例
        """
        self.openai_client = openai_client
    
    def generate_constraints(self, user_requirement_guess, spatial_understanding):
        """生成约束条件
        
        Args:
            user_requirement_guess (str): 用户需求猜测
            spatial_understanding (str): 空间理解记录
        
        Returns:
            dict: 生成的约束条件（JSON格式）
        """
        # 加载约束条件模板
        constraint_template_all = self._load_constraint_template(TEMPLATE_CONSTRAINTS_ALL_PATH)
        
        # 如果没有用户需求猜测或空间理解记录，返回空约束条件
        if not user_requirement_guess or user_requirement_guess == "目前没有关于用户需求的猜测。":
            return constraint_template_all
        
        # 步骤1: 生成all格式的约束条件
        # 准备提示词，使用带注释的模板
        with open("prompt_template_constraints_all.txt", 'r', encoding='utf-8') as f:
            template_all_with_comments = f.read()
        
        prompt_all = CONSTRAINT_QUANTIFICATION_PROMPT.format(
            base_prompt=BASE_PROMPT,
            user_requirement_guess=user_requirement_guess,
            spatial_understanding=spatial_understanding,
            constraint_template=template_all_with_comments
        )
        
        # 调用API生成all格式约束条件
        response_all = self.openai_client.generate_completion(
            prompt=prompt_all,
            model_name=CONSTRAINT_QUANTIFICATION_MODEL,
            temperature=CONSTRAINT_QUANTIFICATION_TEMPERATURE
        )
        
        # 如果API调用失败或返回为空，则返回空约束条件
        if not response_all:
            return constraint_template_all
        
        # 处理API返回的JSON响应
        try:
            result_all = json.loads(response_all)
            # 处理多出的"constraints"嵌套层问题
            if "constraints" in result_all:
                constraints_all = result_all["constraints"]
            else:
                constraints_all = result_all
        except (json.JSONDecodeError, TypeError):
            # 如果解析失败，使用空模板
            constraints_all = constraint_template_all
        
        # 步骤2: 将all格式转换为rooms格式
        from utils.converter import ConstraintConverter
        converter = ConstraintConverter()
        constraints_rooms = converter.all_to_rooms(constraints_all)
        
        # 步骤3: 优化rooms格式的约束条件
        # 准备提示词，使用带注释的模板
        with open("prompt_template_constraints_rooms.txt", 'r', encoding='utf-8') as f:
            template_rooms_with_comments = f.read()
        
        # 使用config中定义的优化rooms格式的提示词
        prompt_rooms = CONSTRAINT_ROOMS_OPTIMIZATION_PROMPT.format(
            user_requirement_guess=user_requirement_guess,
            spatial_understanding=spatial_understanding,
            constraints_rooms=json.dumps(constraints_rooms, ensure_ascii=False, indent=2),
            template_rooms_with_comments=template_rooms_with_comments
        )
        
        # 调用API优化rooms格式约束条件
        response_rooms = self.openai_client.generate_completion(
            prompt=prompt_rooms,
            model_name=CONSTRAINT_QUANTIFICATION_MODEL,
            temperature=CONSTRAINT_QUANTIFICATION_TEMPERATURE
        )
        
        # 如果API调用失败或返回为空，则使用转换得到的rooms格式
        if not response_rooms:
            optimized_constraints_rooms = constraints_rooms
        else:
            # 处理API返回的JSON响应
            try:
                result_rooms = json.loads(response_rooms)
                # 处理多出的"constraints"嵌套层问题
                if "constraints" in result_rooms and "rooms" in result_rooms["constraints"]:
                    optimized_constraints_rooms = {"rooms": result_rooms["constraints"]["rooms"]}
                else:
                    optimized_constraints_rooms = result_rooms.get("constraints", constraints_rooms)
            except (json.JSONDecodeError, TypeError):
                # 如果解析失败，使用转换得到的rooms格式
                optimized_constraints_rooms = constraints_rooms
        
        # 步骤4: 将优化后的rooms格式同步回all格式
        final_constraints_all = converter.rooms_to_all(optimized_constraints_rooms, constraints_all)
        
        return final_constraints_all
    
    def _load_constraint_template(self, template_path):
        """加载约束条件模板
        
        Args:
            template_path (str): 模板文件路径
        
        Returns:
            dict: 约束条件模板
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或解析失败，返回一个空的模板
            if template_path == TEMPLATE_CONSTRAINTS_ALL_PATH:
                return {
                    "hard_constraints": {"room_list": []},
                    "soft_constraints": {
                        "connection": {"weight": 0.0, "constraints": []},
                        "area": {"weight": 0.0, "constraints": []},
                        "orientation": {"weight": 0.0, "constraints": []},
                        "window_access": {"weight": 0.0, "constraints": []},
                        "aspect_ratio": {"weight": 0.0, "constraints": []},
                        "repulsion": {"weight": 0.0, "constraints": []}
                    }
                }
            else:  # TEMPLATE_CONSTRAINTS_ROOMS_PATH
                return {"rooms": {}}
    
    def _extract_json(self, text):
        """从文本中提取JSON部分
        
        Args:
            text (str): 包含JSON的文本
        
        Returns:
            str: 提取的JSON字符串
        """
        # 尝试找到JSON的开始和结束位置
        start_idx = text.find('{')
        if start_idx == -1:
            return "{}"
        
        # 计算括号的嵌套深度，找到对应的结束括号
        depth = 0
        for i in range(start_idx, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i+1]
        
        # 如果没有找到匹配的结束括号，返回空JSON
        return "{}"