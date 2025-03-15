"""
JSON处理工具类，处理约束条件JSON数据
"""
import json
import os

class JsonHandler:
    """
    JSON处理工具类，用于处理约束条件JSON数据
    """
    
    def __init__(self):
        """初始化JSON处理工具类"""
        pass
    
    def load_json(self, file_path):
        """从文件加载JSON数据
        
        Args:
            file_path (str): JSON文件路径
        
        Returns:
            dict: 加载的JSON数据，如果加载失败则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载JSON文件失败: {str(e)}")
            return None
    
    def save_json(self, data, file_path):
        """将JSON数据保存到文件
        
        Args:
            data (dict): 要保存的JSON数据
            file_path (str): 保存的文件路径
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存JSON文件失败: {str(e)}")
            return False
    
    def validate_constraints_all(self, constraints):
        """验证all格式的约束条件是否有效
        
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
        
        # 检查软约束中是否有所有必需的约束类型
        required_constraint_types = [
            "connection", "area", "orientation", "window_access", "aspect_ratio", "repulsion"
        ]
        for constraint_type in required_constraint_types:
            if constraint_type not in constraints["soft_constraints"]:
                return False
            
            # 检查每种约束类型是否有权重和约束列表
            if "weight" not in constraints["soft_constraints"][constraint_type] or \
               "constraints" not in constraints["soft_constraints"][constraint_type]:
                return False
        
        return True
    
    def validate_constraints_rooms(self, constraints):
        """验证rooms格式的约束条件是否有效
        
        Args:
            constraints (dict): 要验证的约束条件
        
        Returns:
            bool: 约束条件是否有效
        """
        # 检查基本结构
        if not isinstance(constraints, dict):
            return False
        
        # 检查是否有rooms字段
        if "rooms" not in constraints:
            return False
        
        # 检查rooms是否是字典
        if not isinstance(constraints["rooms"], dict):
            return False
        
        # 检查每个房间的约束条件是否符合格式
        for room_name, room_constraints in constraints["rooms"].items():
            # 检查必需的字段
            required_fields = ["connection", "area", "orientation", "window_access", "aspect_ratio", "repulsion"]
            for field in required_fields:
                if field not in room_constraints:
                    return False
        
        return True 