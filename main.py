import os
import sys
import json
import argparse
from dotenv import load_dotenv
from models.spatial_understanding import SpatialUnderstanding
from models.requirement_analysis import RequirementAnalysis
from models.question_generation import QuestionGeneration
from models.constraint_quantification import ConstraintQuantification
from models.constraint_visualization import ConstraintVisualization
from models.constraint_refinement import ConstraintRefinement
from models.solution_refinement import SolutionRefinement
from utils.openai_client import OpenAIClient
from utils.json_handler import JsonHandler
from utils.converter import ConstraintConverter
from utils.session_manager import SessionManager
from utils.workflow_manager import WorkflowManager
from models.unified_processor import UnifiedProcessor

# 加载环境变量（包括OpenAI API密钥）
load_dotenv()

class ArchitectureAISystem:
    """建筑布局设计AI系统的主类，控制整个交互流程"""
    
    def __init__(self, resume_session_path=None, input_file="input.json", if_rooms_constraints=False):
        """初始化系统各组件
        
        Args:
            resume_session_path (str, optional): 恢复会话的路径。如果提供，将从该路径恢复会话状态。
        """
        self.input_file = input_file
        self.if_rooms_constraints = if_rooms_constraints
        # 初始化会话记录管理器
        self.session_manager = SessionManager()
        
        # 初始化OpenAI客户端
        self.openai_client = OpenAIClient()
        
        # 设置会话记录管理器到OpenAI客户端
        self.openai_client.set_session_manager(self.session_manager)
        
        # 初始化各功能模块
        self.spatial_understanding = SpatialUnderstanding(self.openai_client)
        self.requirement_analysis = RequirementAnalysis(self.openai_client)
        self.question_generation = QuestionGeneration(self.openai_client)
        self.constraint_quantification = ConstraintQuantification(self.openai_client)
        
        # 初始化统一处理模块
        self.unified_processor = UnifiedProcessor(self.openai_client)

        # 初始化JSON处理工具和转换工具
        self.json_handler = JsonHandler()
        self.converter = ConstraintConverter()
        
        # 初始化工作流程管理器
        self.workflow_manager = WorkflowManager(self.session_manager)
        
        # 初始化约束条件可视化模块
        self.constraint_visualization = ConstraintVisualization()
        
        # 初始化约束条件优化模块
        self.constraint_refinement = ConstraintRefinement(self.openai_client)
        
        # 初始化布局方案优化模块
        self.solution_refinement = SolutionRefinement(self.openai_client)
        
        # 初始化系统状态
        self.initialize_system_state(resume_session_path)
        
    def initialize_system_state(self, resume_session_path=None):
        """初始化系统状态，包括关键问题列表、用户需求猜测和空间理解
        
        Args:
            resume_session_path (str, optional): 恢复会话的路径。如果提供，将从该路径恢复会话状态。
        """
        if resume_session_path and os.path.isdir(resume_session_path):
            # 从指定路径恢复会话状态
            self.resume_from_session(resume_session_path)
        else:
            # 初始化空间理解（空）
            self.spatial_understanding_record = ""
            
            # 初始化用户需求猜测（空）
            self.user_requirement_guess = ""
            
            # 加载预设的关键问题列表
            self.load_key_questions()
            
            # 初始化对话历史
            self.conversation_history = []
            
            # 初始化约束条件（空）
            self.constraints_all = self.load_template("templates/template_constraints_all.txt")
            self.constraints_rooms = self.load_template("templates/template_constraints_rooms.txt")
            
            # 初始化布局方案（空）
            self.current_solution = {"status": "not_generated", "message": "布局方案尚未生成"}
    
    def resume_from_session(self, session_path):
        """从指定的会话目录恢复系统状态
        
        Args:
            session_path (str): 会话目录路径
        """
        current_state_path = os.path.join(session_path, 'current_state.json')
        
        if not os.path.exists(current_state_path):
            print(f"错误：无法找到会话状态文件 {current_state_path}")
            # 初始化为默认状态
            self.initialize_system_state()
            return
        
        try:
            # 读取当前状态文件
            with open(current_state_path, 'r', encoding='utf-8') as f:
                current_state = json.load(f)
            
            print(f"正在从会话 {session_path} 恢复状态...")
            
            # 恢复空间理解记录
            spatial_understanding = current_state.get('spatial_understanding', {})
            self.spatial_understanding_record = spatial_understanding.get('content', "")
            print(f"已恢复空间理解记录: {self.spatial_understanding_record[:50]}...")
            
            # 恢复用户需求猜测
            user_requirements = current_state.get('user_requirements', {})
            self.user_requirement_guess = user_requirements.get('content', "")
            print(f"已恢复用户需求猜测: {self.user_requirement_guess[:50]}...")
            
            # 恢复关键问题列表
            key_questions = current_state.get('key_questions', {}).get('questions', [])
            if key_questions:
                self.key_questions = key_questions
                print(f"已恢复关键问题列表: {len(self.key_questions)} 个问题")
            else:
                # 如果没有恢复到关键问题列表，则加载默认列表
                self.load_key_questions()
                print("使用默认关键问题列表")
            
            # 恢复约束条件
            constraints = current_state.get('constraints', {})
            if 'all' in constraints:
                self.constraints_all = constraints['all']
                print("已恢复all格式约束条件")
            else:
                self.constraints_all = self.load_template("templates/template_constraints_all.txt")
                print("使用默认all格式约束条件模板")
                
            if 'rooms' in constraints:
                self.constraints_rooms = constraints['rooms']
                print("已恢复rooms格式约束条件")
            else:
                self.constraints_rooms = self.load_template("templates/template_constraints_rooms.txt")
                print("使用默认rooms格式约束条件模板")
            
            # 恢复布局方案
            # 查找最近的solution_generation记录
            solution_states = []
            for state in current_state.get('intermediate_states', []):
                if 'solution_generation' in state.get('name', ''):
                    solution_states.append(state)
            
            if solution_states:
                # 使用最新的方案
                latest_solution = sorted(solution_states, key=lambda x: x.get('timestamp', ''))[-1]
                self.current_solution = latest_solution.get('data', {}).get('solution', 
                                                                     {"status": "not_generated", 
                                                                      "message": "布局方案尚未生成"})
                print("已恢复最新布局方案")
            else:
                self.current_solution = {"status": "not_generated", "message": "布局方案尚未生成"}
                print("初始化为默认布局方案状态")
            
            # 确定应该进入哪个阶段
            self._determine_workflow_stage()
            
            print(f"会话状态恢复完成，当前阶段：{self.workflow_manager.get_current_stage()}")
            
        except Exception as e:
            print(f"恢复会话状态时出错: {str(e)}")
            # 初始化为默认状态
            self.initialize_system_state()
    
    def _determine_workflow_stage(self):
        """根据恢复的状态确定应该进入哪个工作流阶段"""
        # 更新工作流程管理器中的关键问题状态
        resolved_questions = sum(1 for q in self.key_questions if q["status"] == "已知")
        total_questions = len(self.key_questions)
        self.workflow_manager.set_key_questions_status(resolved_questions, total_questions)
        
        # 检查是否所有关键问题都已解决
        all_resolved = resolved_questions == total_questions
        
        # 检查是否已有约束条件
        has_constraints = False
        if self.constraints_all and "hard_constraints" in self.constraints_all:
            if self.constraints_all["hard_constraints"].get("room_list", []):
                has_constraints = True
        
        # 检查是否已有布局方案
        has_solution = self.current_solution.get("status") == "success"
        
        # 根据状态确定阶段
        if not all_resolved:
            # 如果有未解决的关键问题，进入需求收集阶段
            self.workflow_manager.current_stage = self.workflow_manager.STAGE_REQUIREMENT_GATHERING
        elif not has_constraints:
            # 如果所有关键问题都解决了，但没有约束条件，进入约束条件生成阶段
            self.workflow_manager.current_stage = self.workflow_manager.STAGE_CONSTRAINT_GENERATION
        elif not has_solution:
            # 如果有约束条件但没有布局方案，进入约束条件优化阶段
            self.workflow_manager.current_stage = self.workflow_manager.STAGE_CONSTRAINT_REFINEMENT
        else:
            # 如果有布局方案，进入布局方案优化阶段
            self.workflow_manager.current_stage = self.workflow_manager.STAGE_SOLUTION_REFINEMENT
    
    def load_key_questions(self):
        """加载预设的关键问题列表"""
        # 这里可以从文件加载或直接定义关键问题列表
        self.key_questions = [
            {
                "category": "房间数量和类型",
                "status": "未知",
                "details": ""
            },
            {
                "category": "住户信息",
                "status": "未知",
                "details": ""
            },
            {
                "category": "生活方式",
                "status": "未知",
                "details": ""
            },
            {
                "category": "空间使用偏好",
                "status": "未知",
                "details": ""
            },
            {
                "category": "环境应对要求",
                "status": "未知",
                "details": ""
            },
            {
                "category": "其他特殊需求",
                "status": "未知",
                "details": ""
            }
        ]
        
        # 更新工作流程管理器中的关键问题状态
        resolved_questions = sum(1 for q in self.key_questions if q["status"] == "已知")
        total_questions = len(self.key_questions)
        self.workflow_manager.set_key_questions_status(resolved_questions, total_questions)
    
    def load_template(self, template_name):
        """加载约束条件模板"""
        try:
            with open(template_name, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果文件不存在，返回一个空的模板
            if "template_constraints_all.txt" in template_name:
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
            else:  # template_constraints_rooms.txt
                return {"rooms": {}}
    
    def load_input_json(self):
        """从JSON文件加载初始输入数据
        
        Args:
            file_path (str): JSON文件路径
            
        Returns:
            dict: 包含spatial_info和user_requirement的字典，如果加载失败则返回None
        """
        file_path = self.input_file 
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载初始输入文件失败: {e}")
            return None
    
    def process_llm_result(self, result, user_input=None):
        """处理LLM返回的结果，更新系统状态
        
        Args:
            result (dict): LLM返回的结果
            user_input (str, optional): 用户输入，用于记录日志
            
        Returns:
            dict: 包含处理后的next_question和更新状态
        """
        # 更新用户需求猜测
        if result["user_requirements"]["updated"]:
            self.user_requirement_guess = result["user_requirements"]["content"]
            if user_input:
                self.session_manager.update_user_requirements(
                    {"content": self.user_requirement_guess},
                    user_input
                )
            print("用户需求已更新。")
        
        # 更新空间理解记录
        if result["spatial_understanding"]["updated"]:
            self.spatial_understanding_record = result["spatial_understanding"]["content"]
            if user_input:
                self.session_manager.update_spatial_understanding(
                    {"content": self.spatial_understanding_record},
                    user_input
                )
            print("空间理解已更新。")
        
        # 更新关键问题列表
        if result["key_questions"]["updated"]:
            self.key_questions = result["key_questions"]["content"]
            if user_input:
                self.session_manager.update_key_questions(
                    {"questions": self.key_questions},
                    user_input
                )
            
            # 更新工作流程管理器中的关键问题状态
            resolved_questions = sum(1 for q in self.key_questions if q["status"] == "已知")
            total_questions = len(self.key_questions)
            self.workflow_manager.set_key_questions_status(resolved_questions, total_questions)
        
        # 获取下一个问题
        next_question = result.get("next_question", "能否再详细描述一下您对这个建筑设计的期望和需求？")
        
        return next_question
    
    def start_interaction(self):
        """开始交互流程"""
        print("欢迎使用建筑布局设计AI系统！")
        
        # 如果不是从会话恢复，尝试从input.json加载初始输入
        if self.workflow_manager.get_current_stage() == self.workflow_manager.STAGE_REQUIREMENT_GATHERING and not self.user_requirement_guess:
            input_data = self.load_input_json()
            
            # 如果成功加载了初始输入
            if input_data and "spatial_info" in input_data and "user_requirement" in input_data:
                print("已从input.json加载初始输入数据。")
                
                # 合并空间信息和用户需求作为首次输入
                user_input = f"空间信息：{input_data['spatial_info']}\n\n用户需求：{input_data['user_requirement']}"
                
                # 记录用户输入
                self.session_manager.add_user_input(user_input)
            else:
                user_input = None
        else:
            user_input = None
        
        # 主交互循环
        while True:
            # 显示当前阶段
            current_stage = self.workflow_manager.get_current_stage()
            stage_description = self.workflow_manager.get_stage_description()
            print(f"\n{stage_description}")
            
            # 根据当前阶段处理交互
            if current_stage == self.workflow_manager.STAGE_REQUIREMENT_GATHERING:
                # 需求收集阶段
                if not user_input:
                    # 获取用户输入
                    user_input = input("用户: ")
                
                    # 记录用户输入
                    self.session_manager.add_user_input(user_input)
                
                # 检查是否退出
                if user_input.lower() in ["退出", "结束", "quit", "exit"]:
                    print("感谢使用！再见！")
                    break
                
                # 检查是否跳过到约束条件量化阶段
                if user_input.lower() in ["skip", "跳过"]:
                    print("您已选择跳过提问阶段，直接进入约束条件生成阶段。")
                    self.workflow_manager.advance_to_next_stage()
                    user_input = None
                    continue
                
                # 处理用户输入并获取回应
                response = self.process_user_input(user_input)
                user_input = None
                
                # 如果response是字典（包含question和explanation），则提取问题
                if isinstance(response, dict) and "question" in response:
                    question_text = response["question"]
                    # 输出系统回应
                    print(f"系统: {question_text}")
                else:
                    # 向后兼容，处理response是字符串的情况
                    print(f"系统: {response}")
                
                # 记录系统回应
                self.session_manager.add_system_response(response)
                
                # 检查是否所有关键问题已解决，可以进入约束条件量化阶段
                if self.workflow_manager.can_advance_to_constraint_generation():
                    print("所有关键问题已解决，即将进入约束条件生成阶段...")
                    self.workflow_manager.advance_to_next_stage()
            
            elif current_stage == self.workflow_manager.STAGE_CONSTRAINT_GENERATION:
                # 约束条件生成阶段
                print("正在生成约束条件...")
                constraints_json = self.finalize_constraints()
                print("\n根据我们的对话，我已经为您生成了设计约束条件。")
                
                # 保存最终结果
                self.session_manager.set_final_result({
                    "constraints": constraints_json,
                    "solver_status": "not_implemented"
                })
                
                # 进入约束条件可视化阶段
                self.workflow_manager.advance_to_next_stage()
            
            elif current_stage == self.workflow_manager.STAGE_CONSTRAINT_VISUALIZATION:
                # 约束条件可视化阶段
                print("正在可视化约束条件...")
                
                # 生成可视化
                viz_result = self.constraint_visualization.visualize_constraints(
                    self.constraints_all,
                    output_path=os.path.join(self.session_manager.get_session_dir(), "constraints_visualization.png")
                )
                
                # 打印约束条件表格
                print("\n房间约束条件表格：")
                self.constraint_visualization.print_room_table(viz_result["room_table"])
                
                # 打印约束条件描述
                print("\n")
                description = self.constraint_visualization.describe_visualization(self.constraints_all)
                print(description)
                
                # 提示查看可视化图像
                img_path = os.path.join(self.session_manager.get_session_dir(), 'constraints_visualization.png')
                table_path = os.path.join(self.session_manager.get_session_dir(), 'constraints_visualization_table.png')
                print(f"\n可视化图像已保存至：{img_path}")
                print(f"表格图像已保存至：{table_path}")
                
                # 记录可视化结果
                self.session_manager.add_intermediate_state(
                    "constraint_visualization", 
                    {"description": description}
                )
                
                # 进入约束条件优化阶段
                self.workflow_manager.advance_to_next_stage()
            
            elif current_stage == self.workflow_manager.STAGE_CONSTRAINT_REFINEMENT:
                # 约束条件优化阶段
                print("请提供关于约束条件的修改意见，或输入'skip'跳过此阶段：")
                
                # 获取用户输入
                user_input = input("用户: ")
                
                # 记录用户输入
                self.session_manager.add_user_input(user_input)
                
                # 检查是否退出
                if user_input.lower() in ["退出", "结束", "quit", "exit"]:
                    print("感谢使用！再见！")
                    break
                
                # 检查是否跳过到方案生成阶段
                if user_input.lower() in ["skip", "跳过"]:
                    print("您已选择跳过约束条件优化阶段，直接进入布局方案生成阶段。")
                    self.workflow_manager.advance_to_next_stage()
                    continue
                
                # 优化约束条件
                print("正在根据您的反馈优化约束条件...")
                refined_constraints, diff_table = self.constraint_refinement.refine_constraints(
                    self.constraints_all,
                    user_input,
                    self.spatial_understanding_record
                )
                
                # 更新约束条件
                self.constraints_all = refined_constraints
                self.constraints_rooms = self.converter.all_to_rooms(refined_constraints)
                
                # 记录约束条件状态
                self.session_manager.update_constraints(
                    {"all": self.constraints_all, "rooms": self.constraints_rooms}
                )
                
                # 如果有变化，显示变化表格
                if diff_table:
                    print("\n约束条件变化：")
                    diff_table_path = os.path.join(
                        self.session_manager.get_session_dir(), 
                        f"constraints_diff_{self.workflow_manager.current_iteration}.png"
                    )
                    self.constraint_visualization.save_table_as_image(diff_table, diff_table_path)
                    self.constraint_visualization.print_room_table(diff_table)
                    print(f"\n变化对比表格已保存至：{diff_table_path}")
                else:
                    print("\n约束条件未发生变化。")
                
                # 重新可视化和打印优化后的约束条件
                viz_result = self.constraint_visualization.visualize_constraints(
                    self.constraints_all,
                    output_path=os.path.join(
                        self.session_manager.get_session_dir(), 
                        f"constraints_visualization_refined_{self.workflow_manager.current_iteration}.png"
                    )
                )
                
                # 打印约束条件表格
                print("\n优化后的房间约束条件表格：")
                self.constraint_visualization.print_room_table(viz_result["room_table"])
                
                # 打印约束条件描述
                print("\n")
                description = self.constraint_visualization.describe_visualization(self.constraints_all)
                print(description)
                
                # 提示查看可视化图像
                img_path = os.path.join(self.session_manager.get_session_dir(), 
                                      f'constraints_visualization_refined_{self.workflow_manager.current_iteration}.png')
                table_path = os.path.join(self.session_manager.get_session_dir(), 
                                        f'constraints_visualization_refined_{self.workflow_manager.current_iteration}_table.png')
                print(f"\n优化后的可视化图像已保存至：{img_path}")
                print(f"优化后的表格图像已保存至：{table_path}")
                
                # 记录可视化结果
                self.session_manager.add_intermediate_state(
                    f"constraint_visualization_refined_{self.workflow_manager.current_iteration}", 
                    {"description": description}
                )
                
                # 增加迭代次数
                self.workflow_manager.current_iteration += 1
            
            elif current_stage == self.workflow_manager.STAGE_SOLUTION_GENERATION:
                # 布局方案生成阶段
                print("\n正在调用求解器生成布局方案...")
                
                # 调用求解器（只保留接口）
                self.current_solution = self.call_solver(self.constraints_all)
                
                # 记录解决方案
                self.session_manager.add_intermediate_state(
                    f"solution_generation_{self.workflow_manager.current_iteration}",
                    {"solution": self.current_solution}
                )
                
                # 打印布局方案
                print("\n生成的布局方案：")
                print(json.dumps(self.current_solution, ensure_ascii=False, indent=2))
                
                # 进入布局方案优化阶段
                self.workflow_manager.advance_to_next_stage()
            
            elif current_stage == self.workflow_manager.STAGE_SOLUTION_REFINEMENT:
                # 布局方案优化阶段
                print("请提供关于布局方案的修改意见，或输入'skip'跳过此阶段：")
                
                # 获取用户输入
                user_input = input("用户: ")
                
                # 记录用户输入
                self.session_manager.add_user_input(user_input)
                
                # 检查是否退出
                if user_input.lower() in ["退出", "结束", "quit", "exit"]:
                    print("感谢使用！再见！")
                    break
                
                # 检查是否跳过进入下一轮优化
                if user_input.lower() in ["skip", "跳过"]:
                    print("您已选择跳过布局方案优化阶段，进入下一轮方案生成。")
                    self.workflow_manager.advance_to_next_stage()
                    continue
                
                # 优化约束条件
                print("正在根据您的反馈优化约束条件...")
                refined_constraints, diff_table = self.solution_refinement.refine_solution(
                    self.constraints_all,
                    self.current_solution,
                    user_input,
                    self.spatial_understanding_record
                )
                
                # 更新约束条件
                self.constraints_all = refined_constraints
                self.constraints_rooms = self.converter.all_to_rooms(refined_constraints)
                
                # 记录约束条件状态
                self.session_manager.update_constraints(
                    {"all": self.constraints_all, "rooms": self.constraints_rooms}
                )
                
                # 如果有变化，显示变化表格
                if diff_table:
                    print("\n根据布局反馈优化的约束条件变化：")
                    diff_table_path = os.path.join(
                        self.session_manager.get_session_dir(), 
                        f"solution_constraints_diff_{self.workflow_manager.current_iteration}.png"
                    )
                    self.constraint_visualization.save_table_as_image(diff_table, diff_table_path)
                    self.constraint_visualization.print_room_table(diff_table)
                    print(f"\n变化对比表格已保存至：{diff_table_path}")
                else:
                    print("\n约束条件未发生变化。")
                
                # 重新可视化约束条件
                viz_result = self.constraint_visualization.visualize_constraints(
                    self.constraints_all,
                    output_path=os.path.join(
                        self.session_manager.get_session_dir(), 
                        f"constraints_visualization_solution_refined_{self.workflow_manager.current_iteration}.png"
                    )
                )

                # 打印约束条件表格
                print("\n基于反馈优化后的约束条件表格：")
                self.constraint_visualization.print_room_table(viz_result["room_table"])
                
                # 重新生成布局方案
                print("\n基于新的约束条件，重新生成布局方案...")
                self.workflow_manager.advance_to_next_stage()  # 返回到方案生成阶段
                
                # 增加迭代次数
                self.workflow_manager.current_iteration += 1
    
    def process_user_input(self, user_input):
        """处理用户输入，调用相应模块，返回系统回应"""
        
        # 获取当前对话历史
        conversation_history = self.session_manager.get_conversation_history()
        
        # 使用统一处理模块处理用户输入
        unified_result = self.unified_processor.process(
            user_input,
            self.spatial_understanding_record,
            self.user_requirement_guess,
            self.key_questions,
            conversation_history
        )
        
        # 使用统一的后处理函数处理LLM返回的结果
        next_question = self.process_llm_result(unified_result, user_input)
        
        return next_question
    
    def all_key_questions_resolved(self):
        """检查是否所有关键问题都已解决""" 
        # self.key_questions 是一个列表，每个元素是一个dict，包含category, status, details
        for question in self.key_questions:
            if question["status"] == "未知":
                return False
        return True
    
    # def finalize_constraints(self):
    #     """生成最终的约束条件"""
    #     # 使用约束条件量化模块将用户需求猜测转化为约束条件
    #     constraints_all = self.constraint_quantification.generate_constraints(
    #         self.user_requirement_guess, self.spatial_understanding_record
    #     )
        
    #     # 转换为rooms格式
    #     constraints_rooms = self.converter.all_to_rooms(constraints_all)
        
    #     # 保存约束条件
    #     self.constraints_all = constraints_all
    #     self.constraints_rooms = constraints_rooms
        
    #     # 记录约束条件状态
    #     self.session_manager.update_constraints(
    #         {"all": constraints_all, "rooms": constraints_rooms}
    #     )
        
    #     return constraints_all
    
    def call_solver(self, constraints):
        """调用布局求解器（仅保留接口）"""
        # 这里仅保留接口，实际实现会调用外部求解器
        print("模拟求解器生成布局方案...")
        
        # 创建一个假设的布局方案
        rooms = constraints["hard_constraints"]["room_list"]
        layout = {}
        
        # 为每个房间分配一个假设的位置和尺寸
        grid_size = int(len(rooms) ** 0.5) + 1
        for i, room in enumerate(rooms):
            row = i // grid_size
            col = i % grid_size
            
            # 从约束条件中获取房间面积（如果有）
            area = 15  # 默认面积
            for area_constraint in constraints["soft_constraints"]["area"]["constraints"]:
                if area_constraint.get("room") == room:
                    min_area = area_constraint.get("min", 10)
                    max_area = area_constraint.get("max", 20)
                    area = (min_area + max_area) / 2
            
            # 从约束条件中获取房间长宽比（如果有）
            aspect_ratio = 1.0  # 默认长宽比
            for ratio_constraint in constraints["soft_constraints"]["aspect_ratio"]["constraints"]:
                if ratio_constraint.get("room") == room:
                    min_ratio = ratio_constraint.get("min", 0.5)
                    max_ratio = ratio_constraint.get("max", 2.0)
                    aspect_ratio = (min_ratio + max_ratio) / 2
            
            # 计算房间尺寸
            width = (area * aspect_ratio) ** 0.5
            height = area / width
            
            # 分配位置和尺寸
            layout[room] = {
                "x": col * 10,
                "y": row * 10,
                "width": width,
                "height": height,
                "area": area
            }
        
        # 返回假设的布局方案
        return {
            "status": "success",
            "message": "布局方案生成成功",
            "layout": layout
        }
    
    def finalize_constraints(self):
        """生成最终的约束条件"""
        # 使用约束条件量化模块将用户需求猜测转化为约束条件
        constraints_all = self.constraint_quantification.generate_constraints(
            self.user_requirement_guess, self.spatial_understanding_record, self.if_rooms_constraints
        )
        
        # 检查并添加path和entrance
        from utils.constraint_validator import ConstraintValidator
        validator = ConstraintValidator()
        
        # 确保约束中包含path和entrance
        constraints_all, path_modified = validator.validate_and_add_path_entrance(constraints_all)
        
        # 检查所有房间的可达性，添加必要的path连接
        constraints_all, reachability_modified = validator.validate_connectivity(constraints_all)
        
        if path_modified or reachability_modified:
            print("已添加流线空间(path)和入口(entrance)，并确保所有房间可达性。")
        
        # 转换为rooms格式
        constraints_rooms = self.converter.all_to_rooms(constraints_all)
        
        # 保存约束条件
        self.constraints_all = constraints_all
        self.constraints_rooms = constraints_rooms
        
        # 记录约束条件状态
        self.session_manager.update_constraints(
            {"all": constraints_all, "rooms": constraints_rooms}
        )
        
        return constraints_all
    
def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='建筑布局设计AI系统')
    parser.add_argument('--resume', type=str, help='恢复会话的路径')
    parser.add_argument('--input', type=str, default='input.json', help='初始输入文件路径')
    parser.add_argument('--if_rooms_constraints', type=bool, default=False, help='是否使用rooms格式约束条件')
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    
    # 初始化系统，如果提供了会话路径则从会话恢复
    system = ArchitectureAISystem(resume_session_path=args.resume, input_file=args.input, if_rooms_constraints=args.if_rooms_constraints)
    system.start_interaction()