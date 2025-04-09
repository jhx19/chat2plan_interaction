"""
工作流程管理器，负责跟踪系统当前所处的阶段并指导流程转换
"""

class WorkflowManager:
    """
    工作流程管理器类，管理系统的不同阶段和状态转换
    """
    
    # 定义系统的不同阶段
    STAGE_REQUIREMENT_GATHERING = "需求收集阶段"
    STAGE_CONSTRAINT_GENERATION = "约束条件生成阶段"
    STAGE_CONSTRAINT_VISUALIZATION = "约束条件可视化阶段"
    STAGE_CONSTRAINT_REFINEMENT = "约束条件优化阶段"
    STAGE_SOLUTION_GENERATION = "布局方案生成阶段"
    STAGE_SOLUTION_REFINEMENT = "布局方案优化阶段"
    
    def __init__(self, session_manager=None):
        """初始化工作流程管理器
        
        Args:
            session_manager: 会话记录管理器，用于记录状态变化
        """
        # 初始阶段是需求收集
        self.current_stage = self.STAGE_REQUIREMENT_GATHERING
        self.session_manager = session_manager
        
        # 记录已解决的关键问题数量，用于判断是否可以进入下一阶段
        self.resolved_key_questions = 0
        self.total_key_questions = 0
        
        # 当前迭代次数
        self.current_iteration = 1
    
    def get_current_stage(self):
        """获取当前阶段
        
        Returns:
            str: 当前阶段的名称
        """
        return self.current_stage
    
    def advance_to_next_stage(self):
        """进入下一个阶段
        
        Returns:
            str: 新的当前阶段
        """
        if self.current_stage == self.STAGE_REQUIREMENT_GATHERING:
            self.current_stage = self.STAGE_CONSTRAINT_GENERATION
        elif self.current_stage == self.STAGE_CONSTRAINT_GENERATION:
            self.current_stage = self.STAGE_CONSTRAINT_VISUALIZATION
        elif self.current_stage == self.STAGE_CONSTRAINT_VISUALIZATION:
            self.current_stage = self.STAGE_CONSTRAINT_REFINEMENT
            self.current_iteration = 1
        elif self.current_stage == self.STAGE_CONSTRAINT_REFINEMENT:
            self.current_stage = self.STAGE_SOLUTION_GENERATION
        elif self.current_stage == self.STAGE_SOLUTION_GENERATION:
            self.current_stage = self.STAGE_SOLUTION_REFINEMENT
            self.current_iteration = 1
        elif self.current_stage == self.STAGE_SOLUTION_REFINEMENT:
            self.current_stage = self.STAGE_SOLUTION_GENERATION
            self.current_iteration += 1
        
        # 记录阶段变化
        if self.session_manager:
            self.session_manager.add_intermediate_state(
                "workflow_stage_change", 
                {"new_stage": self.current_stage,
                 "iteration": self.current_iteration}
            )
        
        return self.current_stage
    
    def set_key_questions_status(self, resolved, total):
        """设置关键问题的解决状态
        
        Args:
            resolved (int): 已解决的关键问题数量
            total (int): 总关键问题数量
        """
        self.resolved_key_questions = resolved
        self.total_key_questions = total
    
    def can_advance_to_constraint_generation(self):
        """判断是否可以进入约束条件生成阶段
        
        Returns:
            bool: 是否可以进入约束条件生成阶段
        """
        return self.resolved_key_questions == self.total_key_questions
    
    def get_stage_description(self):
        """获取当前阶段的描述，用于向用户展示
        
        Returns:
            str: 当前阶段的描述
        """
        if self.current_stage == self.STAGE_REQUIREMENT_GATHERING:
            return f"[需求收集阶段] 已解决 {self.resolved_key_questions}/{self.total_key_questions} 个关键问题"
        
        elif self.current_stage == self.STAGE_CONSTRAINT_GENERATION:
            return "[约束条件生成阶段] 正在根据您的需求生成约束条件"
        
        elif self.current_stage == self.STAGE_CONSTRAINT_VISUALIZATION:
            return "[约束条件可视化阶段] 正在可视化展示约束条件"
        
        elif self.current_stage == self.STAGE_CONSTRAINT_REFINEMENT:
            return f"[约束条件优化阶段] 第{self.current_iteration}轮优化，请提供约束条件的修改意见（输入'skip'跳过此阶段）"
        
        elif self.current_stage == self.STAGE_SOLUTION_GENERATION:
            return f"[布局方案生成阶段] 第{self.current_iteration}轮，正在根据约束条件生成布局方案"
        
        elif self.current_stage == self.STAGE_SOLUTION_REFINEMENT:
            return f"[布局方案优化阶段] 第{self.current_iteration}轮优化，请提供布局方案的修改意见（输入'skip'跳过此阶段）"
        
        return "未知阶段"