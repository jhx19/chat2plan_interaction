"""
约束条件量化模块：将用户需求猜测转化为软约束条件，进行冲突检测和用户确认
"""
import sys
import os
import json
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONSTRAINT_QUANTIFICATION_PROMPT, CONSTRAINT_QUANTIFICATION_TEMPERATURE
from config import TEMPLATE_CONSTRAINTS_ALL_PATH, TEMPLATE_CONSTRAINTS_ROOMS_PATH
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
        constraint_template = self._load_constraint_template(TEMPLATE_CONSTRAINTS_ALL_PATH)
        
        # 如果没有用户需求猜测或空间理解记录，返回空约束条件
        if not user_requirement_guess or user_requirement_guess == "目前没有关于用户需求的猜测。":
            return constraint_template
        
        # 准备提示词
        prompt = CONSTRAINT_QUANTIFICATION_PROMPT.format(
            user_requirement_guess=user_requirement_guess,
            spatial_understanding=spatial_understanding,
            constraint_template=json.dumps(constraint_template, ensure_ascii=False, indent=2)
        )
        
        # 调用API生成约束条件，使用指定模型
        response = self.openai_client.generate_completion(
            prompt=prompt,
            model_name=CONSTRAINT_QUANTIFICATION_MODEL,  # 使用为约束量化指定的模型
            temperature=CONSTRAINT_QUANTIFICATION_TEMPERATURE
        )
        
        # 如果API调用失败或返回为空，则返回空约束条件
        if not response:
            return constraint_template
        
        # 尝试解析响应为JSON
        try:
            # 首先尝试直接解析为JSON
            result = json.loads(response)
            # 检查是否包含constraints字段
            if "constraints" in result:
                return result["constraints"]
            else:
                # 尝试提取响应中的JSON部分（如果有）
                json_str = self._extract_json(response)
                constraints = json.loads(json_str)
                return constraints
        except json.JSONDecodeError:
            print("警告：无法解析生成的约束条件为JSON格式。使用默认约束条件。")
            return constraint_template
    
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