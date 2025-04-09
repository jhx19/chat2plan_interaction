"""
约束条件可视化模块：生成图形表示的约束条件，便于用户直观理解
"""
import sys
import os
import json
import matplotlib.pyplot as plt
import matplotlib
import networkx as nx
import numpy as np
from matplotlib.patches import Ellipse, Rectangle
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.colors as mcolors
import matplotlib.font_manager as fm
from collections import defaultdict

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ConstraintVisualization:
    """
    约束条件可视化模块类，负责将约束条件转化为图形表示
    """
    
    def __init__(self):
        """初始化约束条件可视化模块"""
        # 设置支持中文显示的字体
        self._setup_chinese_font()
        
        # 艺术审美色卡 - 选择柔和、美观的配色方案
        self.colors = [
            "#E63946",  # 红色调
            "#457B9D",  # 蓝色调
            "#F4A261",  # 橙色调
            "#2A9D8F",  # 绿松石色
            "#F1FAEE",  # 淡奶油色
            "#E9C46A",  # 金黄色
            "#264653",  # 深青色
            "#A8DADC",  # 淡蓝色
            "#B5838D",  # 淡玫瑰色
            "#FFB4A2",  # 淡珊瑚色
            "#6D6875",  # 蓝灰色
            "#CB997E",  # 棕褐色
            "#FFCDB2",  # 淡橙色
            "#B5838D",  # 玫瑰褐色
            "#E5989B",  # 粉红色
        ]
    
    def _setup_chinese_font(self):
        """设置支持中文的字体"""
        # 尝试设置支持中文的字体
        font_dirs = []
        font_files = fm.findSystemFonts(fontpaths=font_dirs)
        
        # 尝试一些常见的支持中文的字体
        chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'FangSong', 'KaiTi', 
                         'STXihei', 'STKaiti', 'STSong', 'STFangsong', 'Heiti SC',
                         'Hiragino Sans GB', 'WenQuanYi Zen Hei', 'WenQuanYi Micro Hei',
                         'Noto Sans CJK SC', 'Noto Sans SC', 'Source Han Sans CN']
        
        # 设置默认字体
        self.chinese_font = None
        for font_name in chinese_fonts:
            try:
                matplotlib.rc('font', family=font_name)
                self.chinese_font = font_name
                print(f"使用中文字体: {font_name}")
                break
            except:
                continue
        
        if not self.chinese_font:
            print("警告：未能找到支持中文的字体，可能导致中文显示为方块")
            # 尝试使用默认sans-serif字体
            matplotlib.rc('font', family='sans-serif')
    
    def visualize_constraints(self, constraints, output_path=None):
        """生成约束条件的可视化图形
        
        Args:
            constraints (dict): 约束条件（all格式）
            output_path (str, optional): 输出图像的保存路径
        
        Returns:
            tuple: (room_graph, room_table) 房间连接图和房间约束表格
        """
        # 从约束条件中提取房间列表
        rooms = constraints["hard_constraints"]["room_list"]
        
        # 创建一个图表示房间之间的连接关系
        G = nx.Graph()
        
        # 为每个房间添加节点
        for room in rooms:
            G.add_node(room)
        
        # 添加特殊节点：path和entrance（如果存在）
        special_spaces = constraints.get("special_spaces", {})
        if special_spaces.get("path", False):
            G.add_node("path")
        if special_spaces.get("entrance", False):
            G.add_node("entrance")
        
        # 存储连接和邻接关系，用于后续绘图
        connection_edges = []
        adjacency_edges = []
        
        # 为连接的房间添加边
        for connection in constraints["soft_constraints"]["connection"]["constraints"]:
            if "room pair" in connection:
                room_pair = connection["room pair"]
                G.add_edge(room_pair[0], room_pair[1])
                connection_edges.append((room_pair[0], room_pair[1]))
        
        # 为邻接的房间添加边（不同样式）
        for adjacency in constraints["soft_constraints"].get("adjacency", {}).get("constraints", []):
            if "room pair" in adjacency:
                room_pair = adjacency["room pair"]
                if not G.has_edge(room_pair[0], room_pair[1]):  # 避免重复边
                    G.add_edge(room_pair[0], room_pair[1])
                    adjacency_edges.append((room_pair[0], room_pair[1]))
        
        # 为每个房间计算面积和长宽比
        room_areas = {}
        room_aspect_ratios = {}
        
        for area_constraint in constraints["soft_constraints"]["area"]["constraints"]:
            if "room" in area_constraint:
                room = area_constraint["room"]
                min_area = area_constraint.get("min", 10)  # 默认最小面积为10
                max_area = area_constraint.get("max", 20)  # 默认最大面积为20
                avg_area = (min_area + max_area) / 2
                room_areas[room] = avg_area
        
        for ratio_constraint in constraints["soft_constraints"]["aspect_ratio"]["constraints"]:
            if "room" in ratio_constraint:
                room = ratio_constraint["room"]
                min_ratio = ratio_constraint.get("min", 0.5)  # 默认最小长宽比为0.5
                max_ratio = ratio_constraint.get("max", 2.0)  # 默认最大长宽比为2.0
                avg_ratio = (min_ratio + max_ratio) / 2
                room_aspect_ratios[room] = avg_ratio
        
        # 为没有指定面积和长宽比的房间设置默认值
        for room in rooms:
            if room not in room_areas:
                room_areas[room] = 15  # 默认面积为15
            if room not in room_aspect_ratios:
                room_aspect_ratios[room] = 1.0  # 默认长宽比为1.0
        
        # 创建房间约束表格数据（不包含path和entrance）
        room_table = []
        for room in rooms:  # 只处理正式房间，排除special spaces
            # 获取该房间的约束条件
            area = "未指定"
            for area_constraint in constraints["soft_constraints"]["area"]["constraints"]:
                if area_constraint.get("room") == room:
                    min_area = area_constraint.get("min", "")
                    max_area = area_constraint.get("max", "")
                    area = f"{min_area}-{max_area}平方米" if min_area and max_area else "未指定"
            
            orientation = "未指定"
            for orient_constraint in constraints["soft_constraints"]["orientation"]["constraints"]:
                if orient_constraint.get("room") == room:
                    orientation = orient_constraint.get("direction", "未指定")
            
            window_access = "否"
            for window_constraint in constraints["soft_constraints"]["window_access"]["constraints"]:
                if window_constraint.get("room") == room:
                    window_access = "是"
            
            aspect_ratio = "未指定"
            for ratio_constraint in constraints["soft_constraints"]["aspect_ratio"]["constraints"]:
                if ratio_constraint.get("room") == room:
                    min_ratio = ratio_constraint.get("min", "")
                    max_ratio = ratio_constraint.get("max", "")
                    aspect_ratio = f"{min_ratio}-{max_ratio}" if min_ratio and max_ratio else "未指定"
            
            # 获取直接连接的房间（排除path和entrance）
            connections = []
            for connection in constraints["soft_constraints"]["connection"]["constraints"]:
                if "room pair" in connection:
                    room_pair = connection["room pair"]
                    if room in room_pair:
                        other_room = room_pair[0] if room_pair[1] == room else room_pair[1]
                        if other_room in rooms:  # 只包含正式房间
                            connections.append(other_room)
            
            # 获取邻接的房间（排除path和entrance）
            adjacencies = []
            for adjacency in constraints["soft_constraints"].get("adjacency", {}).get("constraints", []):
                if "room pair" in adjacency:
                    room_pair = adjacency["room pair"]
                    if room in room_pair:
                        other_room = room_pair[0] if room_pair[1] == room else room_pair[1]
                        if other_room in rooms:  # 只包含正式房间
                            adjacencies.append(other_room)
            
            # 获取排斥的房间（排除path和entrance）
            repulsions = []
            for repulsion in constraints["soft_constraints"]["repulsion"]["constraints"]:
                if repulsion.get("room1") == room:
                    repulsed_room = repulsion.get("room2")
                    if repulsed_room in rooms:  # 只包含正式房间
                        repulsions.append(repulsed_room)
                elif repulsion.get("room2") == room:
                    repulsed_room = repulsion.get("room1")
                    if repulsed_room in rooms:  # 只包含正式房间
                        repulsions.append(repulsed_room)
            
            # 添加到表格数据
            room_table.append({
                "房间": room,
                "面积": area,
                "朝向": orientation,
                "窗户": window_access,
                "长宽比": aspect_ratio,
                "直接连接": ", ".join(connections) if connections else "无",
                "空间邻接": ", ".join(adjacencies) if adjacencies else "无",
                "排斥": ", ".join(repulsions) if repulsions else "无"
            })
        
        # 绘制图形
        if output_path:
            # 创建一个更大的图形
            plt.figure(figsize=(14, 10))
            
            # 设置节点位置，使用spring_layout算法，更加紧凑
            pos = nx.spring_layout(G, seed=42, k=0.15)  # 较小的k值会使布局更紧凑
            
            # 先绘制边，以便节点能覆盖它们
            # 绘制连接关系边（实线）
            nx.draw_networkx_edges(
                G, pos, 
                edgelist=connection_edges,
                width=1.5, 
                alpha=0.7, 
                edge_color='gray'
            )
            
            # 绘制邻接关系边（更加稀疏的虚线）
            nx.draw_networkx_edges(
                G, pos, 
                edgelist=adjacency_edges,
                width=1.2, 
                alpha=0.7, 
                edge_color='blue',
                style='dashed',
                #dashes=(2, 5)  # 控制虚线样式，使其更加稀疏
            )
            
            # 为每个房间分配一个颜色
            room_colors = {}
            for i, room in enumerate(rooms):
                room_colors[room] = self.colors[i % len(self.colors)]
            
            # 为特殊节点设置颜色
            if "path" in G.nodes():
                room_colors["path"] = "#9B2226"  # 深红色
            if "entrance" in G.nodes():
                room_colors["entrance"] = "#006D77"  # 青蓝色
            
            # 绘制节点（放在边之后以便覆盖边）
            ax = plt.gca()
            for node, (x, y) in pos.items():
                # 特殊处理path和entrance（使用矩形）
                if node == "path":
                    # Path使用矩形
                    rect = Rectangle((x-0.12, y-0.08), 0.24, 0.16, 
                                   angle=0, fill=True, alpha=0.8,
                                   color=room_colors[node], edgecolor='black', linewidth=1.5)
                    ax.add_patch(rect)
                    continue
                elif node == "entrance":
                    # Entrance使用矩形
                    rect = Rectangle((x-0.10, y-0.10), 0.20, 0.20, 
                                   angle=0, fill=True, alpha=0.8,
                                   color=room_colors[node], edgecolor='black', linewidth=1.5)
                    ax.add_patch(rect)
                    continue
                
                # 普通房间节点使用椭圆
                if node in room_areas and node in room_aspect_ratios:
                    area = room_areas[node]
                    aspect_ratio = room_aspect_ratios[node]
                    
                    # 计算椭圆的宽度和高度
                    width = np.sqrt(area * aspect_ratio) * 0.05
                    height = np.sqrt(area / aspect_ratio) * 0.05
                    
                    # 创建椭圆
                    ellipse = Ellipse((x, y), width, height, fill=True, alpha=0.8, 
                                    color=room_colors[node], edgecolor='black', linewidth=1.5)
                    ax.add_patch(ellipse)
            
            # 绘制节点标签（房间名称）
            nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold", font_color="black")
            
            # 设置图形标题和边距
            plt.title("房间连接关系图", fontsize=18)
            plt.axis("off")
            plt.tight_layout()
            
            # 添加图例说明
            legend_elements = [
                plt.Line2D([0], [0], color='gray', lw=1.5, label='直接连接'),
                plt.Line2D([0], [0], color='blue', lw=1.2, linestyle='dashed', dashes=(2, 5), label='空间邻接')
            ]
            
            # 为每个房间添加一个图例项
            for room in rooms:
                legend_elements.append(
                    plt.Line2D([0], [0], marker='o', color='w', label=room,
                              markerfacecolor=room_colors[room], markersize=10)
                )
                
            # 为特殊空间添加图例（如果存在）
            if "path" in G.nodes():
                legend_elements.append(
                    plt.Line2D([0], [0], marker='s', color='w', label='流线空间(path)',
                              markerfacecolor=room_colors["path"], markersize=10)
                )
            if "entrance" in G.nodes():
                legend_elements.append(
                    plt.Line2D([0], [0], marker='s', color='w', label='入口(entrance)',
                              markerfacecolor=room_colors["entrance"], markersize=10)
                )
            
            plt.legend(handles=legend_elements, loc='best', fontsize=10)
            
            # 保存图形
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # 将表格保存为图片
            table_image_path = output_path.replace('.png', '_table.png')
            self.save_table_as_image(room_table, table_image_path)
        
        return {
            "room_graph": G,
            "room_table": room_table
        }
    
    def save_table_as_image(self, table_data, output_path):
        """将表格保存为图片
        
        Args:
            table_data (list): 表格数据
            output_path (str): 输出图像的保存路径
        """
        if not table_data:
            return
        
        # 获取所有列
        columns = list(table_data[0].keys())
        
        # 准备表格数据
        cell_text = []
        for row in table_data:
            cell_text.append([str(row[col]) for col in columns])
        
        # 创建图形和轴
        fig = plt.figure(figsize=(12, len(table_data) + 2))
        ax = fig.add_subplot(111)
        
        # 隐藏轴
        ax.axis('tight')
        ax.axis('off')
        
        # 创建表格
        table = ax.table(cellText=cell_text,
                         colLabels=columns,
                         loc='center',
                         cellLoc='center')
        
        # 设置表格样式
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        # 为表头设置样式
        for (i, j), cell in table.get_celld().items():
            if i == 0:  # 表头行
                cell.set_text_props(fontproperties=dict(weight='bold'))
                cell.set_facecolor('lightgray')
        
        # 保存图形
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def print_room_table(self, room_table):
        """打印房间约束表格
        
        Args:
            room_table (list): 房间约束表格数据
        """
        # 获取所有列
        if not room_table:
            print("没有约束条件数据")
            return
            
        columns = list(room_table[0].keys())
        
        # 获取每列的最大宽度
        col_widths = {col: len(col) for col in columns}
        for row in room_table:
            for col in columns:
                col_widths[col] = max(col_widths[col], len(str(row[col])))
        
        # 打印表头
        header = "┌"
        for col in columns:
            header += "─" * (col_widths[col] + 2) + "┬"
        header = header[:-1] + "┐"
        print(header)
        
        header_row = "│"
        for col in columns:
            header_row += f" {col.center(col_widths[col])} │"
        print(header_row)
        
        separator = "├"
        for col in columns:
            separator += "─" * (col_widths[col] + 2) + "┼"
        separator = separator[:-1] + "┤"
        print(separator)
        
        # 打印表格内容
        for row in room_table:
            row_str = "│"
            for col in columns:
                row_str += f" {str(row[col]).ljust(col_widths[col])} │"
            print(row_str)
        
        # 打印表格底部
        footer = "└"
        for col in columns:
            footer += "─" * (col_widths[col] + 2) + "┴"
        footer = footer[:-1] + "┘"
        print(footer)
    
    def describe_visualization(self, constraints):
        """生成对约束条件可视化的文本描述
        
        Args:
            constraints (dict): 约束条件（all格式）
        
        Returns:
            str: 约束条件的文本描述
        """
        # 从约束条件中提取房间列表
        rooms = constraints["hard_constraints"]["room_list"]
        
        # 计算直接连接关系
        connections = {}
        for room in rooms:
            connections[room] = []
        
        for connection in constraints["soft_constraints"]["connection"]["constraints"]:
            if "room pair" in connection:
                room_pair = connection["room pair"]
                # 排除特殊空间path和entrance
                if room_pair[0] in rooms and room_pair[1] in rooms:
                    connections[room_pair[0]].append(room_pair[1])
                    connections[room_pair[1]].append(room_pair[0])
        
        # 计算邻接关系
        adjacencies = {}
        for room in rooms:
            adjacencies[room] = []
        
        for adjacency in constraints["soft_constraints"].get("adjacency", {}).get("constraints", []):
            if "room pair" in adjacency:
                room_pair = adjacency["room pair"]
                # 排除特殊空间path和entrance
                if room_pair[0] in rooms and room_pair[1] in rooms:
                    adjacencies[room_pair[0]].append(room_pair[1])
                    adjacencies[room_pair[1]].append(room_pair[0])
        
        # 检查流线和入口是否存在
        special_spaces = constraints.get("special_spaces", {})
        has_path = special_spaces.get("path", False)
        has_entrance = special_spaces.get("entrance", False)
        
        # 查找与path相连的房间
        path_connections = []
        if has_path:
            for connection in constraints["soft_constraints"]["connection"]["constraints"]:
                if "room pair" in connection:
                    room_pair = connection["room pair"]
                    if "path" in room_pair:
                        other_room = room_pair[0] if room_pair[1] == "path" else room_pair[1]
                        if other_room in rooms:  # 只添加正式房间，不包括entrance
                            path_connections.append(other_room)
        
        # 生成描述文本
        description = "约束条件概述：\n\n"
        description += f"总共包含 {len(rooms)} 个房间：{', '.join(rooms)}\n"
        
        if has_path and has_entrance:
            description += "\n使用流线空间(path)连接入口(entrance)和其他房间"
            if path_connections:
                description += f"\n流线直接连接的房间: {', '.join(path_connections)}\n"
        
        # 描述每个房间的主要约束
        description += "\n各房间的主要约束：\n"
        for room in rooms:
            description += f"- {room}：\n"
            
            # 面积约束
            area_desc = "  面积：未指定"
            for area_constraint in constraints["soft_constraints"]["area"]["constraints"]:
                if area_constraint.get("room") == room:
                    min_area = area_constraint.get("min", "")
                    max_area = area_constraint.get("max", "")
                    if min_area and max_area:
                        area_desc = f"  面积：{min_area}-{max_area}平方米"
                    elif min_area:
                        area_desc = f"  面积：最小{min_area}平方米"
                    elif max_area:
                        area_desc = f"  面积：最大{max_area}平方米"
            description += area_desc + "\n"
            
            # 朝向约束
            orientation_desc = "  朝向：未指定"
            for orient_constraint in constraints["soft_constraints"]["orientation"]["constraints"]:
                if orient_constraint.get("room") == room:
                    orientation = orient_constraint.get("direction", "")
                    if orientation:
                        orientation_desc = f"  朝向：{orientation}"
            description += orientation_desc + "\n"
            
            # 直接连接关系
            if connections[room]:
                description += f"  直接连接：{', '.join(connections[room])}\n"
            else:
                description += "  直接连接：无\n"
            
            # 邻接关系
            if adjacencies[room]:
                description += f"  空间邻接：{', '.join(adjacencies[room])}\n"
            
            # 与path的连接（如果有）
            if has_path and room in path_connections:
                description += "  通过流线空间连接：是\n"
        
        return description
        
    def compare_constraints(self, old_constraints, new_constraints, output_path=None):
        """比较两个约束条件，生成差异表格
        
        Args:
            old_constraints (dict): 原约束条件（all格式）
            new_constraints (dict): 新约束条件（all格式）
            output_path (str, optional): 输出图像的保存路径
            
        Returns:
            list: 差异表格数据
        """
        diff_table = []
        
        # 比较房间列表
        old_rooms = set(old_constraints["hard_constraints"]["room_list"])
        new_rooms = set(new_constraints["hard_constraints"]["room_list"])
        
        # 添加/删除的房间
        added_rooms = new_rooms - old_rooms
        removed_rooms = old_rooms - new_rooms
        
        if added_rooms:
            diff_table.append({
                "约束类型": "房间列表",
                "修改类型": "添加房间",
                "原值": "无",
                "新值": ", ".join(added_rooms)
            })
            
        if removed_rooms:
            diff_table.append({
                "约束类型": "房间列表",
                "修改类型": "删除房间",
                "原值": ", ".join(removed_rooms),
                "新值": "无"
            })
        
        # 比较软约束
        for constraint_type in ["connection", "adjacency", "area", "orientation", "window_access", "aspect_ratio", "repulsion"]:
            self._compare_constraint_type(old_constraints, new_constraints, constraint_type, diff_table)
        
        # 保存差异表格为图片
        if output_path and diff_table:
            self.save_table_as_image(diff_table, output_path)
            
        return diff_table
    
    def _compare_constraint_type(self, old_constraints, new_constraints, constraint_type, diff_table):
        """比较特定类型的约束条件
        
        Args:
            old_constraints (dict): 原约束条件
            new_constraints (dict): 新约束条件
            constraint_type (str): 约束类型
            diff_table (list): 差异表格数据
        """
        # 检查约束类型权重是否变化
        old_weight = old_constraints["soft_constraints"].get(constraint_type, {}).get("weight", 0)
        new_weight = new_constraints["soft_constraints"].get(constraint_type, {}).get("weight", 0)
        
        if old_weight != new_weight:
            diff_table.append({
                "约束类型": constraint_type,
                "修改类型": "权重变化",
                "原值": str(old_weight),
                "新值": str(new_weight)
            })
        
        # 获取约束列表
        old_constraints_list = old_constraints["soft_constraints"].get(constraint_type, {}).get("constraints", [])
        new_constraints_list = new_constraints["soft_constraints"].get(constraint_type, {}).get("constraints", [])
        
        # 为不同类型的约束使用不同的比较方法
        if constraint_type in ["connection", "adjacency"]:
            self._compare_pair_constraints(old_constraints_list, new_constraints_list, constraint_type, diff_table)
        elif constraint_type == "repulsion":
            self._compare_repulsion_constraints(old_constraints_list, new_constraints_list, diff_table)
        else:
            self._compare_single_room_constraints(old_constraints_list, new_constraints_list, constraint_type, diff_table)
    
    def _compare_pair_constraints(self, old_list, new_list, constraint_type, diff_table):
        """比较房间对约束（connection, adjacency）
        
        Args:
            old_list (list): 原约束列表
            new_list (list): 新约束列表
            constraint_type (str): 约束类型
            diff_table (list): 差异表格
        """
        # 提取房间对
        old_pairs = set()
        for item in old_list:
            if "room pair" in item and len(item["room pair"]) == 2:
                # 对房间对进行排序，确保相同对的顺序一致
                pair = tuple(sorted(item["room pair"]))
                old_pairs.add(pair)
        
        new_pairs = set()
        for item in new_list:
            if "room pair" in item and len(item["room pair"]) == 2:
                pair = tuple(sorted(item["room pair"]))
                new_pairs.add(pair)
        
        # 添加新的房间对
        added_pairs = new_pairs - old_pairs
        if added_pairs:
            for pair in added_pairs:
                diff_table.append({
                    "约束类型": constraint_type,
                    "修改类型": "新增连接关系",
                    "原值": "无",
                    "新值": f"{pair[0]} - {pair[1]}"
                })
        
        # 删除的房间对
        removed_pairs = old_pairs - new_pairs
        if removed_pairs:
            for pair in removed_pairs:
                diff_table.append({
                    "约束类型": constraint_type,
                    "修改类型": "删除连接关系",
                    "原值": f"{pair[0]} - {pair[1]}",
                    "新值": "无"
                })
    
    def _compare_repulsion_constraints(self, old_list, new_list, diff_table):
        """比较排斥约束
        
        Args:
            old_list (list): 原约束列表
            new_list (list): 新约束列表
            diff_table (list): 差异表格
        """
        # 提取房间对
        old_pairs = set()
        for item in old_list:
            if "room1" in item and "room2" in item:
                # 对房间对进行排序，确保相同对的顺序一致
                pair = tuple(sorted([item["room1"], item["room2"]]))
                old_pairs.add(pair)
        
        new_pairs = set()
        for item in new_list:
            if "room1" in item and "room2" in item:
                pair = tuple(sorted([item["room1"], item["room2"]]))
                new_pairs.add(pair)
        
        # 添加新的排斥关系
        added_pairs = new_pairs - old_pairs
        if added_pairs:
            for pair in added_pairs:
                diff_table.append({
                    "约束类型": "repulsion",
                    "修改类型": "新增排斥关系",
                    "原值": "无",
                    "新值": f"{pair[0]} - {pair[1]}"
                })
        
        # 删除的排斥关系
        removed_pairs = old_pairs - new_pairs
        if removed_pairs:
            for pair in removed_pairs:
                diff_table.append({
                    "约束类型": "repulsion",
                    "修改类型": "删除排斥关系",
                    "原值": f"{pair[0]} - {pair[1]}",
                    "新值": "无"
                })
                
        # 最小距离变化
        for old_item in old_list:
            if "room1" in old_item and "room2" in old_item and "min_distance" in old_item:
                room1, room2 = old_item["room1"], old_item["room2"]
                old_min_distance = old_item["min_distance"]
                
                # 查找新列表中对应项
                for new_item in new_list:
                    if (new_item.get("room1") == room1 and new_item.get("room2") == room2) or \
                       (new_item.get("room1") == room2 and new_item.get("room2") == room1):
                        if "min_distance" in new_item and new_item["min_distance"] != old_min_distance:
                            diff_table.append({
                                "约束类型": "repulsion",
                                "修改类型": f"最小距离变化 ({room1}-{room2})",
                                "原值": str(old_min_distance),
                                "新值": str(new_item["min_distance"])
                            })
    
    def _compare_single_room_constraints(self, old_list, new_list, constraint_type, diff_table):
        """比较单个房间约束（area, orientation, window_access, aspect_ratio）
        
        Args:
            old_list (list): 原约束列表
            new_list (list): 新约束列表
            constraint_type (str): 约束类型
            diff_table (list): 差异表格
        """
        # 按房间名组织约束
        old_room_constraints = {}
        for item in old_list:
            if "room" in item:
                old_room_constraints[item["room"]] = item
                
        new_room_constraints = {}
        for item in new_list:
            if "room" in item:
                new_room_constraints[item["room"]] = item
        
        # 检查新增的房间约束
        for room in new_room_constraints:
            if room not in old_room_constraints:
                constraint_desc = self._format_constraint_value(new_room_constraints[room], constraint_type)
                diff_table.append({
                    "约束类型": constraint_type,
                    "修改类型": f"新增{room}约束",
                    "原值": "无",
                    "新值": constraint_desc
                })
            else:
                # 比较约束值是否变化
                old_item = old_room_constraints[room]
                new_item = new_room_constraints[room]
                
                if constraint_type == "area":
                    # 比较面积范围
                    old_min = old_item.get("min", "未指定")
                    old_max = old_item.get("max", "未指定")
                    new_min = new_item.get("min", "未指定")
                    new_max = new_item.get("max", "未指定")
                    
                    if old_min != new_min or old_max != new_max:
                        diff_table.append({
                            "约束类型": "area",
                            "修改类型": f"{room}面积变化",
                            "原值": f"min:{old_min}, max:{old_max}",
                            "新值": f"min:{new_min}, max:{new_max}"
                        })
                        
                elif constraint_type == "aspect_ratio":
                    # 比较长宽比范围
                    old_min = old_item.get("min", "未指定")
                    old_max = old_item.get("max", "未指定")
                    new_min = new_item.get("min", "未指定")
                    new_max = new_item.get("max", "未指定")
                    
                    if old_min != new_min or old_max != new_max:
                        diff_table.append({
                            "约束类型": "aspect_ratio",
                            "修改类型": f"{room}长宽比变化",
                            "原值": f"min:{old_min}, max:{old_max}",
                            "新值": f"min:{new_min}, max:{new_max}"
                        })
                        
                elif constraint_type == "orientation":
                    # 比较朝向
                    old_direction = old_item.get("direction", "未指定")
                    new_direction = new_item.get("direction", "未指定")
                    
                    if old_direction != new_direction:
                        diff_table.append({
                            "约束类型": "orientation",
                            "修改类型": f"{room}朝向变化",
                            "原值": old_direction,
                            "新值": new_direction
                        })
        
        # 检查删除的房间约束
        for room in old_room_constraints:
            if room not in new_room_constraints:
                constraint_desc = self._format_constraint_value(old_room_constraints[room], constraint_type)
                diff_table.append({
                    "约束类型": constraint_type,
                    "修改类型": f"删除{room}约束",
                    "原值": constraint_desc,
                    "新值": "无"
                })
    
    def _format_constraint_value(self, constraint, constraint_type):
        """格式化约束值描述
        
        Args:
            constraint (dict): 约束条件
            constraint_type (str): 约束类型
            
        Returns:
            str: 格式化的约束值描述
        """
        if constraint_type == "area":
            min_area = constraint.get("min", "未指定")
            max_area = constraint.get("max", "未指定")
            return f"min:{min_area}, max:{max_area}"
            
        elif constraint_type == "aspect_ratio":
            min_ratio = constraint.get("min", "未指定")
            max_ratio = constraint.get("max", "未指定")
            return f"min:{min_ratio}, max:{max_ratio}"
            
        elif constraint_type == "orientation":
            return constraint.get("direction", "未指定")
            
        elif constraint_type == "window_access":
            return "需要窗户"
            
        return str(constraint)