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
from matplotlib.patches import Ellipse
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.colors as mcolors
import matplotlib.font_manager as fm

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
        # 准备颜色列表
        self.colors = list(mcolors.TABLEAU_COLORS.values())  # 使用matplotlib内置的TABLEAU颜色
    
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
        
        # 为连接的房间添加边
        for connection in constraints["soft_constraints"]["connection"]["constraints"]:
            if "room pair" in connection:
                room_pair = connection["room pair"]
                G.add_edge(room_pair[0], room_pair[1])
        
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
        
        # 创建房间约束表格数据
        room_table = []
        for room in rooms:
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
            
            connections = []
            for connection in constraints["soft_constraints"]["connection"]["constraints"]:
                if "room pair" in connection:
                    room_pair = connection["room pair"]
                    if room in room_pair:
                        other_room = room_pair[0] if room_pair[1] == room else room_pair[1]
                        connections.append(other_room)
            
            repulsions = []
            for repulsion in constraints["soft_constraints"]["repulsion"]["constraints"]:
                if repulsion.get("room1") == room:
                    repulsions.append(repulsion.get("room2"))
                elif repulsion.get("room2") == room:
                    repulsions.append(repulsion.get("room1"))
            
            # 添加到表格数据
            room_table.append({
                "房间": room,
                "面积": area,
                "朝向": orientation,
                "窗户": window_access,
                "长宽比": aspect_ratio,
                "连接": ", ".join(connections) if connections else "无",
                "排斥": ", ".join(repulsions) if repulsions else "无"
            })
        
        # 绘制图形
        if output_path:
            # 创建一个更大的图形
            plt.figure(figsize=(14, 10))
            
            # 设置节点位置，使用spring_layout算法
            pos = nx.spring_layout(G, seed=42)
            
            # 绘制边（连接关系）
            nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7, edge_color='gray')
            
            # 为每个房间分配一个颜色
            room_colors = {}
            for i, room in enumerate(rooms):
                room_colors[room] = self.colors[i % len(self.colors)]
            
            # 绘制椭圆形状的节点，大小基于面积，形状基于长宽比，颜色为唯一的房间颜色
            ax = plt.gca()
            for node, (x, y) in pos.items():
                area = room_areas[node]
                aspect_ratio = room_aspect_ratios[node]
                
                # 计算椭圆的宽度和高度
                width = np.sqrt(area * aspect_ratio) * 0.05
                height = np.sqrt(area / aspect_ratio) * 0.05
                
                # 创建椭圆
                ellipse = Ellipse((x, y), width, height, fill=True, alpha=0.7, 
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
                plt.Line2D([0], [0], color='gray', lw=1.5, label='房间连接关系')
            ]
            
            # 为每个房间添加一个图例项
            for room in rooms:
                legend_elements.append(
                    plt.Line2D([0], [0], marker='o', color='w', label=room,
                              markerfacecolor=room_colors[room], markersize=10)
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
        
        # 计算连接关系
        connections = {}
        for room in rooms:
            connections[room] = []
        
        for connection in constraints["soft_constraints"]["connection"]["constraints"]:
            if "room pair" in connection:
                room_pair = connection["room pair"]
                connections[room_pair[0]].append(room_pair[1])
                connections[room_pair[1]].append(room_pair[0])
        
        # 生成描述文本
        description = "约束条件概述：\n\n"
        description += f"总共包含 {len(rooms)} 个房间：{', '.join(rooms)}\n\n"
        
        # 描述每个房间的主要约束
        description += "各房间的主要约束：\n"
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
            
            # 连接关系
            if connections[room]:
                description += f"  连接：{', '.join(connections[room])}\n"
            else:
                description += "  连接：无\n"
        
        return description