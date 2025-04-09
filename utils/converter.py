"""
约束条件格式转换工具类，实现不同格式约束条件之间的转换
"""
import json
import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONSTRAINT_CONVERTER_PROMPT
from config import CONSTRAINT_QUANTIFICATION_MODEL  # 使用约束量化模块的模型

class ConstraintConverter:
    """
    约束条件格式转换工具类，用于在all格式和rooms格式之间转换
    """
    
    def __init__(self):
        """初始化约束条件格式转换工具类
        """
        pass
    
    def all_to_rooms(self, constraints_all):
        """将all格式的约束条件转换为rooms格式
        
        Args:
            constraints_all (dict): all格式的约束条件
        
        Returns:
            dict: rooms格式的约束条件
        """
        # 如果输入无效，返回空的rooms格式
        if not constraints_all or "hard_constraints" not in constraints_all or "soft_constraints" not in constraints_all:
            return {"rooms": {}}
        
        # 初始化结果
        constraints_rooms = {"rooms": {}}
        
        # 获取房间列表
        room_list = constraints_all["hard_constraints"]["room_list"]
        
        # 为每个房间创建约束条件
        for room in room_list:
            constraints_rooms["rooms"][room] = {
                "connection": [],
                "area": {},
                "orientation": "",
                "window_access": False,
                "aspect_ratio": {},
                "repulsion": []
            }
        
        # 转换connection约束
        for connection_constraint in constraints_all["soft_constraints"]["connection"]["constraints"]:
            if "room pair" in connection_constraint and len(connection_constraint["room pair"]) == 2:
                room1, room2 = connection_constraint["room pair"]
                if room1 in constraints_rooms["rooms"] and room2 in constraints_rooms["rooms"]:
                    if room2 not in constraints_rooms["rooms"][room1]["connection"]:
                        constraints_rooms["rooms"][room1]["connection"].append(room2)
                    if room1 not in constraints_rooms["rooms"][room2]["connection"]:
                        constraints_rooms["rooms"][room2]["connection"].append(room1)
        
        # 转换area约束
        for area_constraint in constraints_all["soft_constraints"]["area"]["constraints"]:
            if "room" in area_constraint and area_constraint["room"] in constraints_rooms["rooms"]:
                room = area_constraint["room"]
                if "min" in area_constraint:
                    constraints_rooms["rooms"][room]["area"]["min"] = area_constraint["min"]
                if "max" in area_constraint:
                    constraints_rooms["rooms"][room]["area"]["max"] = area_constraint["max"]
        
        # 转换orientation约束
        for orientation_constraint in constraints_all["soft_constraints"]["orientation"]["constraints"]:
            if "room" in orientation_constraint and "direction" in orientation_constraint:
                room = orientation_constraint["room"]
                if room in constraints_rooms["rooms"]:
                    constraints_rooms["rooms"][room]["orientation"] = orientation_constraint["direction"]
        
        # 转换window_access约束
        for window_constraint in constraints_all["soft_constraints"]["window_access"]["constraints"]:
            if "room" in window_constraint:
                room = window_constraint["room"]
                if room in constraints_rooms["rooms"]:
                    constraints_rooms["rooms"][room]["window_access"] = True
        
        # 转换aspect_ratio约束
        for aspect_constraint in constraints_all["soft_constraints"]["aspect_ratio"]["constraints"]:
            if "room" in aspect_constraint and aspect_constraint["room"] in constraints_rooms["rooms"]:
                room = aspect_constraint["room"]
                if "min" in aspect_constraint:
                    constraints_rooms["rooms"][room]["aspect_ratio"]["min"] = aspect_constraint["min"]
                if "max" in aspect_constraint:
                    constraints_rooms["rooms"][room]["aspect_ratio"]["max"] = aspect_constraint["max"]
        
        # 转换repulsion约束
        for repulsion_constraint in constraints_all["soft_constraints"]["repulsion"]["constraints"]:
            if "room1" in repulsion_constraint and "room2" in repulsion_constraint:
                room1 = repulsion_constraint["room1"]
                room2 = repulsion_constraint["room2"]
                if room1 in constraints_rooms["rooms"] and room2 in constraints_rooms["rooms"]:
                    if room2 not in constraints_rooms["rooms"][room1]["repulsion"]:
                        constraints_rooms["rooms"][room1]["repulsion"].append(room2)
                    if room1 not in constraints_rooms["rooms"][room2]["repulsion"]:
                        constraints_rooms["rooms"][room2]["repulsion"].append(room1)
        
        return constraints_rooms
    
    def rooms_to_all(self, constraints_rooms, original_all=None):
        """将rooms格式的约束条件转换为all格式
        
        Args:
            constraints_rooms (dict): rooms格式的约束条件
            original_all (dict, optional): 原始的all格式约束条件，用于保留结构信息
        
        Returns:
            dict: all格式的约束条件
        """
        # 如果输入无效，返回空的all格式
        if not constraints_rooms or "rooms" not in constraints_rooms:
            return {
                "hard_constraints": {"room_list": []},
                "soft_constraints": {
                    "connection": {"weight": 0.5, "constraints": []},
                    "area": {"weight": 0.5, "constraints": []},
                    "orientation": {"weight": 0.5, "constraints": []},
                    "window_access": {"weight": 0.5, "constraints": []},
                    "aspect_ratio": {"weight": 0.5, "constraints": []},
                    "repulsion": {"weight": 0.5, "constraints": []}
                }
            }
        
        # 创建默认的all格式，使用固定的默认权重
        constraints_all = {
            "hard_constraints": {"room_list": []},
            "soft_constraints": {
                "connection": {"weight": 0.5, "constraints": []},
                "area": {"weight": 0.5, "constraints": []},
                "orientation": {"weight": 0.5, "constraints": []},
                "window_access": {"weight": 0.5, "constraints": []},
                "aspect_ratio": {"weight": 0.5, "constraints": []},
                "repulsion": {"weight": 0.5, "constraints": []}
            }
        }
        
        # 如果有原始all格式，保留其权重设置
        if original_all and "soft_constraints" in original_all:
            for constraint_type in constraints_all["soft_constraints"]:
                if constraint_type in original_all["soft_constraints"] and "weight" in original_all["soft_constraints"][constraint_type]:
                    constraints_all["soft_constraints"][constraint_type]["weight"] = original_all["soft_constraints"][constraint_type]["weight"]
        
        # 获取房间列表
        room_list = list(constraints_rooms["rooms"].keys())
        constraints_all["hard_constraints"]["room_list"] = room_list
        
        # 处理已处理的connection对，避免重复
        processed_connections = set()
        
        # 转换各类约束条件
        for room, room_constraints in constraints_rooms["rooms"].items():
            # 转换connection约束
            for connected_room in room_constraints["connection"]:
                # 创建房间对的标识符（按字母顺序排序以确保唯一性）
                connection_pair = tuple(sorted([room, connected_room]))
                
                # 如果该连接还未处理，添加到all格式中
                if connection_pair not in processed_connections:
                    constraints_all["soft_constraints"]["connection"]["constraints"].append({
                        "room pair": [connection_pair[0], connection_pair[1]],
                        "room_weight": 0.5  # 固定默认权重
                    })
                    processed_connections.add(connection_pair)
            
            # 转换area约束
            if room_constraints["area"]:
                area_constraint = {"room": room, "room_weight": 0.5}  # 固定默认权重
                if "min" in room_constraints["area"]:
                    area_constraint["min"] = room_constraints["area"]["min"]
                if "max" in room_constraints["area"]:
                    area_constraint["max"] = room_constraints["area"]["max"]
                if len(area_constraint) > 2:  # 如果有除room和room_weight之外的字段
                    constraints_all["soft_constraints"]["area"]["constraints"].append(area_constraint)
            
            # 转换orientation约束
            if room_constraints["orientation"]:
                constraints_all["soft_constraints"]["orientation"]["constraints"].append({
                    "room": room,
                    "direction": room_constraints["orientation"],
                    "room_weight": 0.5  # 固定默认权重
                })
            
            # 转换window_access约束
            if room_constraints["window_access"]:
                constraints_all["soft_constraints"]["window_access"]["constraints"].append({
                    "room": room,
                    "room_weight": 0.5  # 固定默认权重
                })
            
            # 转换aspect_ratio约束
            if room_constraints["aspect_ratio"]:
                aspect_constraint = {"room": room, "room_weight": 0.5}  # 固定默认权重
                if "min" in room_constraints["aspect_ratio"]:
                    aspect_constraint["min"] = room_constraints["aspect_ratio"]["min"]
                if "max" in room_constraints["aspect_ratio"]:
                    aspect_constraint["max"] = room_constraints["aspect_ratio"]["max"]
                if len(aspect_constraint) > 2:  # 如果有除room和room_weight之外的字段
                    constraints_all["soft_constraints"]["aspect_ratio"]["constraints"].append(aspect_constraint)
        
        # 处理已处理的repulsion对，避免重复
        processed_repulsions = set()
        
        # 转换repulsion约束
        for room, room_constraints in constraints_rooms["rooms"].items():
            for repulsed_room in room_constraints["repulsion"]:
                # 创建房间对的标识符（按字母顺序排序以确保唯一性）
                repulsion_pair = tuple(sorted([room, repulsed_room]))
                
                # 如果该repulsion还未处理，添加到all格式中
                if repulsion_pair not in processed_repulsions:
                    constraints_all["soft_constraints"]["repulsion"]["constraints"].append({
                        "room1": repulsion_pair[0],
                        "room2": repulsion_pair[1],
                        "min_distance": 2,  # 默认最小距离
                        "room_weight": 0.5  # 固定默认权重
                    })
                    processed_repulsions.add(repulsion_pair)
        
        return constraints_all