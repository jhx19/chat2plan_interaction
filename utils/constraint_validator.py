"""
约束条件验证工具：检查约束条件的有效性，包括可达性检查
"""
import networkx as nx

class ConstraintValidator:
    """
    约束条件验证工具类，用于检查约束条件的有效性
    """
    
    def __init__(self):
        """初始化约束条件验证工具"""
        pass
    
    def validate_connectivity(self, constraints):
        """验证所有房间的可达性，确保所有房间都能从entrance通过path到达
        
        如果存在无法到达的房间，会添加path-该房间的连接关系
        
        Args:
            constraints (dict): 约束条件（all格式）
        
        Returns:
            dict: 修复后的约束条件（如果有修改）
            bool: 是否进行了修改
        """
        # 复制一份约束条件，避免直接修改原始数据
        fixed_constraints = constraints.copy()
        
        # 检查是否启用了path和entrance
        special_spaces = fixed_constraints.get("special_spaces", {})
        if not special_spaces.get("path", False) or not special_spaces.get("entrance", False):
            # 如果未启用path或entrance，则启用它们
            fixed_constraints["special_spaces"] = {"path": True, "entrance": True}
        
        # 获取房间列表
        rooms = fixed_constraints["hard_constraints"]["room_list"]
        
        # 创建房间连接图（包括path和entrance）
        G = nx.Graph()
        
        # 添加所有节点
        for room in rooms:
            G.add_node(room)
        
        # 添加path和entrance节点
        G.add_node("path")
        G.add_node("entrance")
        
        # 添加path和entrance的默认连接
        G.add_edge("path", "entrance")
        
        # 添加现有的连接关系
        for connection in fixed_constraints["soft_constraints"]["connection"]["constraints"]:
            if "room pair" in connection:
                room_pair = connection["room pair"]
                G.add_edge(room_pair[0], room_pair[1])
        
        # 检查每个房间是否可以从entrance到达
        modified = False
        
        # 从entrance开始的可达节点
        reachable_nodes = set(nx.node_connected_component(G, "entrance"))
        
        # 找出不可达的房间
        unreachable_rooms = [room for room in rooms if room not in reachable_nodes]
        
        # 如果有不可达的房间，添加path-该房间的连接
        if unreachable_rooms:
            modified = True
            
            for room in unreachable_rooms:
                # 添加到图中
                G.add_edge("path", room)
                
                # 添加到约束条件中
                new_connection = {
                    "room pair": ["path", room],
                    "room_weight": 0.8  # 设置较高的权重以确保连接
                }
                
                fixed_constraints["soft_constraints"]["connection"]["constraints"].append(new_connection)
        
        # 确保connection的权重适当
        if fixed_constraints["soft_constraints"]["connection"]["weight"] < 0.5:
            fixed_constraints["soft_constraints"]["connection"]["weight"] = 0.7
            modified = True
        
        return fixed_constraints, modified
    
    def validate_and_add_path_entrance(self, constraints):
        """确保约束条件中包含path和entrance，并添加默认的path-entrance连接
        
        Args:
            constraints (dict): 约束条件（all格式）
            
        Returns:
            dict: 修复后的约束条件
            bool: 是否进行了修改
        """
        # 复制一份约束条件，避免直接修改原始数据
        fixed_constraints = constraints.copy()
        modified = False
        
        # 确保special_spaces字段存在
        if "special_spaces" not in fixed_constraints:
            fixed_constraints["special_spaces"] = {"path": True, "entrance": True}
            modified = True
        elif "path" not in fixed_constraints["special_spaces"] or "entrance" not in fixed_constraints["special_spaces"]:
            fixed_constraints["special_spaces"]["path"] = True
            fixed_constraints["special_spaces"]["entrance"] = True
            modified = True
        
        # 检查是否已有path-entrance连接
        has_path_entrance_connection = False
        for connection in fixed_constraints["soft_constraints"]["connection"]["constraints"]:
            if "room pair" in connection:
                room_pair = connection["room pair"]
                if ("path" in room_pair and "entrance" in room_pair):
                    has_path_entrance_connection = True
                    break
        
        # 如果没有path-entrance连接，添加它
        if not has_path_entrance_connection:
            new_connection = {
                "room pair": ["path", "entrance"],
                "room_weight": 1.0  # 最高权重，表示必要连接
            }
            
            fixed_constraints["soft_constraints"]["connection"]["constraints"].append(new_connection)
            modified = True
        
        return fixed_constraints, modified