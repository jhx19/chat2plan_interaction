import os
import json
from dotenv import load_dotenv
from models.spatial_understanding import SpatialUnderstanding
from models.requirement_analysis import RequirementAnalysis
from models.question_generation import QuestionGeneration
from models.constraint_quantification import ConstraintQuantification
from utils.openai_client import OpenAIClient
from utils.json_handler import JsonHandler
from utils.converter import ConstraintConverter
from utils.session_manager import SessionManager
from models.unified_processor import UnifiedProcessor

# 加载环境变量（包括OpenAI API密钥）
load_dotenv()

class ArchitectureAISystem:
    """建筑布局设计AI系统的主类，控制整个交互流程"""
    
    def __init__(self):
        """初始化系统各组件"""
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
        
        # 初始化系统状态
        self.initialize_system_state()
        
    def initialize_system_state(self):
        """初始化系统状态，包括关键问题列表、用户需求猜测和空间理解"""
        # 初始化空间理解（空）
        self.spatial_understanding_record = ""
        
        # 初始化用户需求猜测（空）
        self.user_requirement_guess = ""
        
        # 加载预设的关键问题列表
        self.load_key_questions()
        
        # 初始化对话历史
        self.conversation_history = []
        
        # 初始化约束条件（空）
        self.constraints_all = self.load_template("template_constraints_all.txt")
        self.constraints_rooms = self.load_template("template_constraints_rooms.txt")
    
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
    
    def load_template(self, template_name):
        """加载约束条件模板"""
        try:
            with open(template_name, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果文件不存在，返回一个空的模板
            if template_name == "template_constraints_all.txt":
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
    
    def load_input_json(self, file_path="input.json"):
        """从JSON文件加载初始输入数据
        
        Args:
            file_path (str): JSON文件路径
            
        Returns:
            dict: 包含spatial_info和user_requirement的字典，如果加载失败则返回None
        """
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
        
        # 获取下一个问题
        next_question = result.get("next_question", "能否再详细描述一下您对这个建筑设计的期望和需求？")
        
        return next_question
    
    def start_interaction(self):
        """开始交互流程"""
        print("欢迎使用建筑布局设计AI系统！")
        
        # 尝试从input.json加载初始输入
        input_data = self.load_input_json()
        
        # 如果成功加载了初始输入
        if input_data and "spatial_info" in input_data and "user_requirement" in input_data:
            print("已从input.json加载初始输入数据。")
            
            # 合并空间信息和用户需求作为首次输入
            user_input = f"空间信息：{input_data['spatial_info']}\n\n用户需求：{input_data['user_requirement']}"
            
            # 记录用户输入
            self.session_manager.add_user_input(user_input)
            
            # 获取当前对话历史
            conversation_history = self.session_manager.get_conversation_history()
        
        # 主交互循环
        while True:
            
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
                print("您已选择跳过提问阶段，直接进入约束条件量化阶段。")
                constraints_json = self.finalize_constraints()
                print("\n根据我们的对话，我已经为您生成了设计约束条件:")
                print(json.dumps(constraints_json, ensure_ascii=False, indent=2))
                
                # 保存最终结果
                self.session_manager.set_final_result({
                    "constraints": constraints_json,
                    "solver_status": "not_implemented"
                })
                
                # 调用求解器（只保留接口）
                print("\n正在调用求解器生成布局方案...")
                # solver_result = self.call_solver(constraints_json)
                
                break
            
            # 处理用户输入并获取回应
            response = self.process_user_input(user_input)
            user_input = ""
            # 如果response是字典（包含question和explanation），则提取问题
            if isinstance(response, dict) and "question" in response:
                question_text = response["question"]
                # 输出系统回应
                print(f"Chat2Plan: {question_text}")
            else:
                # 向后兼容，处理response是字符串的情况
                print(f"Chat2Plan: {response}")
            
            # 记录系统回应
            self.session_manager.add_system_response(response)
            
            # 检查是否所有关键问题已解决，可以进入约束条件量化阶段
            if self.all_key_questions_resolved():
                # 进入约束条件量化阶段
                constraints_json = self.finalize_constraints()
                print("\n根据我们的对话，我已经为您生成了设计约束条件:")
                print(json.dumps(constraints_json, ensure_ascii=False, indent=2))
                
                # 保存最终结果
                self.session_manager.set_final_result({
                    "constraints": constraints_json,
                    "solver_status": "not_implemented"
                })
                
                # 调用求解器（只保留接口）
                print("\n正在调用求解器生成布局方案...")
                # solver_result = self.call_solver(constraints_json)
                
                break
    
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
    
    def update_question_status(self):
        """根据当前的用户需求猜测，更新关键问题列表的状态
        
        注意：此方法已弃用，关键问题状态更新已集成到question_generation.generate_question方法中
        """
        # 此方法已弃用，保留方法签名以保持兼容性
        pass
    
    def all_key_questions_resolved(self):
        """检查是否所有关键问题都已解决""" 
        # self.key_questions 是一个列表st，每个元素是一个dict，包含category, status, details
        for question in self.key_questions:
            if question["status"] == "未知":
                return False
        return True
    
    def finalize_constraints(self):
        """生成最终的约束条件"""
        # 使用约束条件量化模块将用户需求猜测转化为约束条件
        constraints_all = self.constraint_quantification.generate_constraints(
            self.user_requirement_guess, self.spatial_understanding_record
        )
        
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
    
    def call_solver(self, constraints):
        """调用布局求解器（仅保留接口）"""
        # 这里仅保留接口，实际实现会调用外部求解器
        print("假设求解器已被调用，并返回了布局方案。")
        return {"status": "success", "message": "布局方案生成成功"}

if __name__ == "__main__":
    system = ArchitectureAISystem()
    system.start_interaction()