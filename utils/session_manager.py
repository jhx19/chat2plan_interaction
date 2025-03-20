"""\n会话记录管理器，负责创建和管理每次会话的记录\n"""
import os
import json
import time
from datetime import datetime

class SessionManager:
    """会话记录管理器类，处理每次会话的记录保存"""
    
    def __init__(self):
        """初始化会话记录管理器"""
        # 创建sessions目录（如果不存在）
        self.sessions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sessions')
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        # 创建新的会话目录
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_dir = os.path.join(self.sessions_dir, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        
        # 初始化会话记录
        self.session_record = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'conversation_history': [],
            'api_calls': [],
            'tokens_used': {
                'total': 0,
                'prompt': 0,
                'completion': 0
            },
            'intermediate_states': [],
            'final_result': None
        }
        
        # 初始化四个关键模块的记录
        self.spatial_understanding = {}
        self.user_requirements = {}
        self.key_questions = {}
        self.constraints = {}
        
        # 创建四个模块的历史记录和最终状态文件
        self._create_module_files()
    
    def add_user_input(self, user_input):
        """记录用户输入
        
        Args:
            user_input (str): 用户输入的内容
        """
        self.session_record['conversation_history'].append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        self._save_session_record()
    
    def add_system_response(self, response):
        """记录系统回应
        
        Args:
            response (str): 系统的回应内容
        """
        self.session_record['conversation_history'].append({
            'role': 'system',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        self._save_session_record()
    
    def add_api_call(self, model_name, prompt, response, tokens_used):
        """记录API调用信息
        
        Args:
            model_name (str): 使用的模型名称
            prompt (str): 发送的提示词
            response (str): 收到的回应
            tokens_used (dict): 使用的token数量
        """
        self.session_record['api_calls'].append({
            'timestamp': datetime.now().isoformat(),
            'model': model_name,
            'prompt': prompt,
            'response': response,
            'tokens': tokens_used
        })
        
        # 更新总token使用量
        self.session_record['tokens_used']['prompt'] += tokens_used.get('prompt', 0)
        self.session_record['tokens_used']['completion'] += tokens_used.get('completion', 0)
        self.session_record['tokens_used']['total'] = (
            self.session_record['tokens_used']['prompt'] +
            self.session_record['tokens_used']['completion']
        )
        
        self._save_session_record()
    
    def add_intermediate_state(self, state_name, state_data):
        """记录中间状态
        
        Args:
            state_name (str): 状态名称
            state_data (dict): 状态数据
        """
        self.session_record['intermediate_states'].append({
            'timestamp': datetime.now().isoformat(),
            'name': state_name,
            'data': state_data
        })
        self._save_session_record()
    
    def set_final_result(self, result):
        """设置最终结果
        
        Args:
            result (dict): 最终的约束条件和布局方案
        """
        self.session_record['final_result'] = {
            'timestamp': datetime.now().isoformat(),
            'data': result
        }
        self._save_session_record()
    
    def _save_session_record(self):
        """保存会话记录到文件"""
        # 更新结束时间
        self.session_record['end_time'] = datetime.now().isoformat()
        
        # 保存完整的会话记录
        record_path = os.path.join(self.session_dir, 'session_record.json')
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(self.session_record, f, ensure_ascii=False, indent=2)
    
    def get_session_dir(self):
        """获取当前会话目录路径
        
        Returns:
            str: 会话目录的绝对路径
        """
        return self.session_dir
    
    def _create_module_files(self):
        """创建四个模块的历史记录和最终状态文件"""
        # 创建最终状态文件
        self.final_state_path = os.path.join(self.session_dir, 'final_state.json')
        final_state = {
            'spatial_understanding': {},
            'user_requirements': {},
            'key_questions': {},
            'constraints': {}
        }
        with open(self.final_state_path, 'w', encoding='utf-8') as f:
            json.dump(final_state, f, ensure_ascii=False, indent=2)
        
        # 创建四个模块的历史记录文件
        self.history_files = {
            'spatial_understanding': os.path.join(self.session_dir, 'spatial_understanding_history.json'),
            'user_requirements': os.path.join(self.session_dir, 'user_requirements_history.json'),
            'key_questions': os.path.join(self.session_dir, 'key_questions_history.json'),
            'constraints': os.path.join(self.session_dir, 'constraints_history.json')
        }
        
        # 初始化历史记录文件
        for file_path in self.history_files.values():
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def update_spatial_understanding(self, content, user_input=None):
        """更新空间理解内容
        
        Args:
            content (dict): 空间理解的内容
            user_input (str, optional): 触发更新的用户输入
        """
        # 更新内存中的空间理解
        self.spatial_understanding = content
        
        # 更新最终状态文件
        self._update_final_state('spatial_understanding', content)
        
        # 添加到历史记录
        self._add_to_history('spatial_understanding', content, user_input)
    
    def update_user_requirements(self, content, user_input=None):
        """更新用户需求猜测内容
        
        Args:
            content (dict): 用户需求猜测的内容
            user_input (str, optional): 触发更新的用户输入
        """
        # 更新内存中的用户需求猜测
        self.user_requirements = content
        
        # 更新最终状态文件
        self._update_final_state('user_requirements', content)
        
        # 添加到历史记录
        self._add_to_history('user_requirements', content, user_input)
    
    def update_key_questions(self, content, user_input=None):
        """更新关键问题列表内容
        
        Args:
            content (dict): 关键问题列表的内容
            user_input (str, optional): 触发更新的用户输入
        """
        # 更新内存中的关键问题列表
        self.key_questions = content
        
        # 更新最终状态文件
        self._update_final_state('key_questions', content)
        
        # 添加到历史记录
        self._add_to_history('key_questions', content, user_input)
    
    def update_constraints(self, content, user_input=None):
        """更新约束条件内容
        
        Args:
            content (dict): 约束条件的内容
            user_input (str, optional): 触发更新的用户输入
        """
        # 更新内存中的约束条件
        self.constraints = content
        
        # 更新最终状态文件
        self._update_final_state('constraints', content)
        
        # 添加到历史记录
        self._add_to_history('constraints', content, user_input)
    
    def _update_final_state(self, module_name, content):
        """更新最终状态文件中的指定模块
        
        Args:
            module_name (str): 模块名称
            content (dict): 模块内容
        """
        # 读取当前最终状态
        with open(self.final_state_path, 'r', encoding='utf-8') as f:
            final_state = json.load(f)
        
        # 更新指定模块
        final_state[module_name] = content
        
        # 保存更新后的最终状态
        with open(self.final_state_path, 'w', encoding='utf-8') as f:
            json.dump(final_state, f, ensure_ascii=False, indent=2)
    
    def _add_to_history(self, module_name, content, user_input=None):
        """添加模块更新记录到历史文件
        
        Args:
            module_name (str): 模块名称
            content (dict): 模块内容
            user_input (str, optional): 触发更新的用户输入
        """
        # 读取当前历史记录
        history_path = self.history_files[module_name]
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        # 创建新的历史记录
        record = {
            'timestamp': datetime.now().isoformat(),
            'content': content
        }
        
        # 如果有触发更新的用户输入，则添加到记录中
        if user_input:
            record['user_input'] = user_input
        
        # 添加到历史记录
        history.append(record)
        
        # 保存更新后的历史记录
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def get_module_final_state(self, module_name):
        """获取指定模块的最终状态
        
        Args:
            module_name (str): 模块名称，可选值为'spatial_understanding', 'user_requirements', 'key_questions', 'constraints'
            
        Returns:
            dict: 模块的最终状态
        """
        with open(self.final_state_path, 'r', encoding='utf-8') as f:
            final_state = json.load(f)
        return final_state.get(module_name, {})
    
    def get_module_history(self, module_name):
        """获取指定模块的历史记录
        
        Args:
            module_name (str): 模块名称，可选值为'spatial_understanding', 'user_requirements', 'key_questions', 'constraints'
            
        Returns:
            list: 模块的历史记录列表
        """
        history_path = self.history_files.get(module_name)
        if not history_path:
            return []
        
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
        return history