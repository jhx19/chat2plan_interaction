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

# 加载环境变量（包括OpenAI API密钥）
load_dotenv()

class ArchitectureAISystem:
    """建筑布局设计AI系统的主类，控制整个交互流程"""
    
    def __init__(self):
        """初始化系统各组件"""
        # 初始化OpenAI客户端
        self.openai_client = OpenAIClient()
        
        # 初始化各功能模块
        self.spatial_understanding = SpatialUnderstanding(self.openai_client)
        self.requirement_analysis = RequirementAnalysis(self.openai_client)
        self.question_generation = QuestionGeneration(self.openai_client)
        self.constraint_quantification = ConstraintQuantification(self.openai_client)
        
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
                "questions": [
                    {"question": "您需要哪些类型的房间？", "status": "未知"}
                ]
            },
            {
                "category": "住户信息",
                "questions": [
                    {"question": "这个住宅将容纳多少人？家庭成员构成如何？", "status": "未知"},
                    {"question": "您对未来的家庭规划有什么考虑？", "status": "未知"}
                ]
            },
            {
                "category": "生活方式",
                "questions": [
                    {"question": "您更偏好社交空间还是私人空间？", "status": "未知"},
                    {"question": "您在家中会做饭吗？频率如何？", "status": "未知"},
                    {"question": "您是否需要在家工作的空间？", "status": "未知"}
                ]
            },
            {
                "category": "空间使用偏好",
                "questions": [
                    {"question": "您喜欢明亮开放的空间还是独立封闭的空间？", "status": "未知"},
                    {"question": "您对采光有什么特别的要求？", "status": "未知"}
                ]
            },
            {
                "category": "功能需求",
                "questions": [
                    {"question": "您需要专门的储物空间吗？", "status": "未知"},
                    {"question": "您有特殊的爱好需要专门空间吗？", "status": "未知"}
                ]
            },
            {
                "category": "环境应对",
                "questions": [
                    {"question": "您对噪音敏感吗？需要特别的隔音设计吗？", "status": "未知"},
                    {"question": "您希望拥有室外空间（如阳台）吗？", "status": "未知"}
                ]
            },
            {
                "category": "其他特殊需求",
                "questions": [
                    {"question": "您还有其他特殊的设计需求吗？", "status": "未知"}
                ]
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
    
    def start_interaction(self):
        """开始交互流程"""
        print("欢迎使用建筑布局设计AI系统！")
        print("请描述您的建筑边界和环境信息，我将帮助您设计布局。")
        
        # 主交互循环
        while True:
            # 获取用户输入
            user_input = input("用户: ")
            
            # 记录用户输入到对话历史
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # 检查是否退出
            if user_input.lower() in ["退出", "结束", "quit", "exit"]:
                print("感谢使用！再见！")
                break
            
            # 处理用户输入并获取回应
            response = self.process_user_input(user_input)
            
            # 输出系统回应
            print(f"系统: {response}")
            
            # 记录系统回应到对话历史
            self.conversation_history.append({"role": "system", "content": response})
            
            # 检查是否所有关键问题已解决，可以进入约束条件量化阶段
            if self.all_key_questions_resolved():
                # 进入约束条件量化阶段
                constraints_json = self.finalize_constraints()
                print("\n根据我们的对话，我已经为您生成了设计约束条件:")
                print(json.dumps(constraints_json, ensure_ascii=False, indent=2))
                
                # 调用求解器（只保留接口）
                print("\n正在调用求解器生成布局方案...")
                # solver_result = self.call_solver(constraints_json)
                
                # 打印结果（示例）
                # print("布局方案已生成!")
                
                break
    
    def process_user_input(self, user_input):
        """处理用户输入，调用相应模块，返回系统回应"""
        # 1. 空间理解：解析用户输入的建筑边界和环境信息
        updated_spatial_understanding = self.spatial_understanding.process(
            user_input, self.spatial_understanding_record
        )
        if updated_spatial_understanding != self.spatial_understanding_record:
            self.spatial_understanding_record = updated_spatial_understanding
        
        # 2. 需求分析：根据用户输入和已有信息，推测用户需求
        updated_user_requirement = self.requirement_analysis.process(
            user_input, self.user_requirement_guess, self.spatial_understanding_record
        )
        if updated_user_requirement != self.user_requirement_guess:
            self.user_requirement_guess = updated_user_requirement
        
        # 3. 更新关键问题状态
        self.update_question_status()
        
        # 4. 提问：生成下一个问题
        next_question = self.question_generation.generate_question(
            self.user_requirement_guess, self.key_questions
        )
        
        return next_question
    
    def update_question_status(self):
        """根据当前的用户需求猜测，更新关键问题列表的状态"""
        # 使用需求分析模块来检查哪些问题已经有了答案
        for category in self.key_questions:
            for question in category["questions"]:
                is_answered = self.requirement_analysis.check_question_answered(
                    question["question"], self.user_requirement_guess
                )
                if is_answered:
                    question["status"] = "已知"
    
    def all_key_questions_resolved(self):
        """检查是否所有关键问题都已解决"""
        for category in self.key_questions:
            for question in category["questions"]:
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
        
        return constraints_all
    
    def call_solver(self, constraints):
        """调用布局求解器（仅保留接口）"""
        # 这里仅保留接口，实际实现会调用外部求解器
        print("假设求解器已被调用，并返回了布局方案。")
        return {"status": "success", "message": "布局方案生成成功"}

if __name__ == "__main__":
    system = ArchitectureAISystem()
    system.start_interaction() 