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
        
        # 创建会话文件结构
        self._create_session_files()
    
    def add_user_input(self, user_input):
        """记录用户输入
        
        Args:
            user_input (str): 用户输入的内容
        """
        # 创建用户输入记录
        user_message = {
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加到会话记录
        self.session_record['conversation_history'].append(user_message)
        
        # 保存会话记录
        self._save_session_record()
        
        # 保存到对话历史文件
        self._append_to_conversation_file(user_message)
        
        # 记录到调试文件
        self._log_debug_info('用户输入', {'input': user_input})
    
    def add_system_response(self, response):
        """记录系统回应
        
        Args:
            response (str or dict): 系统的回应内容
        """
        # 处理不同类型的响应
        if isinstance(response, dict) and 'question' in response:
            content = response['question']
            explanation = response.get('explanation', '')
            system_message = {
                'role': 'system',
                'content': content,
                'explanation': explanation,
                'timestamp': datetime.now().isoformat()
            }
        else:
            content = response
            system_message = {
                'role': 'system',
                'content': content,
                'timestamp': datetime.now().isoformat()
            }
        
        # 添加到会话记录
        self.session_record['conversation_history'].append(system_message)
        
        # 保存会话记录
        self._save_session_record()
        
        # 保存到对话历史文件
        self._append_to_conversation_file(system_message)
        
        # 记录到调试文件
        self._log_debug_info('系统回应', {'response': response})
    
    def add_api_call(self, model_name, prompt, response, tokens_used):
        """记录API调用信息
        
        Args:
            model_name (str): 使用的模型名称
            prompt (str): 发送的提示词
            response (str): 收到的回应
            tokens_used (dict): 使用的token数量
        """
        # 创建API调用记录
        api_call_record = {
            'timestamp': datetime.now().isoformat(),
            'model': model_name,
            'prompt': prompt,
            'response': response,
            'tokens': tokens_used
        }
        
        # 添加到会话记录
        self.session_record['api_calls'].append(api_call_record)
        
        # 更新总token使用量
        self.session_record['tokens_used']['prompt'] += tokens_used.get('prompt', 0)
        self.session_record['tokens_used']['completion'] += tokens_used.get('completion', 0)
        self.session_record['tokens_used']['total'] = (
            self.session_record['tokens_used']['prompt'] +
            self.session_record['tokens_used']['completion']
        )
        
        # 保存API调用记录到单独的文件
        self._save_llm_output(api_call_record)
        
        # 保存会话记录
        self._save_session_record()
        
        # 记录到调试文件
        self._log_debug_info('LLM调用', {
            'model': model_name,
            'tokens_used': tokens_used,
            'prompt_summary': prompt[:100] + '...' if len(prompt) > 100 else prompt
        })
    
    def add_intermediate_state(self, state_name, state_data, update_type=None):
        """记录中间状态
        
        Args:
            state_name (str): 状态名称
            state_data (dict): 状态数据
            update_type (str, optional): 更新内容类型，如'spatial_understanding'、'user_requirements'等
        """
        state_record = {
            'timestamp': datetime.now().isoformat(),
            'name': state_name,
            'data': state_data
        }
        
        # 如果提供了更新类型，则添加到记录中
        if update_type:
            state_record['update_type'] = update_type
            
        self.session_record['intermediate_states'].append(state_record)
        self._save_session_record()
        
        # 记录到调试文件
        self._log_debug_info('中间状态更新', {
            'state_name': state_name,
            'update_type': update_type,
            'data_summary': str(state_data)[:200] + '...' if len(str(state_data)) > 200 else str(state_data)
        })
    
    def set_final_result(self, result):
        """设置最终结果
        
        Args:
            result (dict): 最终的约束条件和布局方案
        """
        final_result = {
            'timestamp': datetime.now().isoformat(),
            'data': result
        }
        
        # 更新会话记录
        self.session_record['final_result'] = final_result
        
        # 保存会话记录
        self._save_session_record()
        
        # 保存最终结果到单独文件
        final_result_path = os.path.join(self.session_dir, 'final_result.json')
        with open(final_result_path, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        # 记录到调试文件
        self._log_debug_info('最终结果', {'result_summary': '已生成最终结果'})
    
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
    
    def _create_session_files(self):
        """创建会话所需的所有文件和目录"""
        # 创建最终状态文件 - 记录最新版本的四个模块数据
        self.current_state_path = os.path.join(self.session_dir, 'current_state.json')
        current_state = {
            'spatial_understanding': {},
            'user_requirements': {},
            'key_questions': {},
            'constraints': {},
            'last_updated': datetime.now().isoformat()
        }
        with open(self.current_state_path, 'w', encoding='utf-8') as f:
            json.dump(current_state, f, ensure_ascii=False, indent=2)
        
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
        
        # 创建LLM输出记录目录
        self.llm_output_dir = os.path.join(self.session_dir, 'llm_outputs')
        os.makedirs(self.llm_output_dir, exist_ok=True)
        
        # 创建对话历史文件
        self.conversation_file_path = os.path.join(self.session_dir, 'conversation.json')
        with open(self.conversation_file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        
        # 创建调试日志文件
        self.debug_log_path = os.path.join(self.session_dir, 'debug_log.json')
        with open(self.debug_log_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    
    def update_spatial_understanding(self, content, user_input=None):
        """更新空间理解内容
        
        Args:
            content (dict): 空间理解的内容
            user_input (str, optional): 触发更新的用户输入
        """
        # 更新内存中的空间理解
        self.spatial_understanding = content
        
        # 更新最新状态文件
        self._update_current_state('spatial_understanding', content)
        
        # 添加到历史记录
        self._add_to_history('spatial_understanding', content, user_input)
        
        # 记录到调试文件
        self._log_debug_info('空间理解更新', {
            'triggered_by': user_input if user_input else '系统内部更新',
            'content_summary': str(content)[:200] + '...' if len(str(content)) > 200 else str(content)
        })
    
    def update_user_requirements(self, content, user_input=None):
        """更新用户需求猜测内容
        
        Args:
            content (dict): 用户需求猜测的内容
            user_input (str, optional): 触发更新的用户输入
        """
        # 更新内存中的用户需求猜测
        self.user_requirements = content
        
        # 更新最新状态文件
        self._update_current_state('user_requirements', content)
        
        # 添加到历史记录
        self._add_to_history('user_requirements', content, user_input)
        
        # 记录到调试文件
        self._log_debug_info('用户需求更新', {
            'triggered_by': user_input if user_input else '系统内部更新',
            'content_summary': str(content)[:200] + '...' if len(str(content)) > 200 else str(content)
        })
    
    def update_key_questions(self, content, user_input=None):
        """更新关键问题列表内容
        
        Args:
            content (dict): 关键问题列表的内容
            user_input (str, optional): 触发更新的用户输入
        """
        # 更新内存中的关键问题列表
        self.key_questions = content
        
        # 更新最新状态文件
        self._update_current_state('key_questions', content)
        
        # 添加到历史记录
        self._add_to_history('key_questions', content, user_input)
        
        # 记录到调试文件
        self._log_debug_info('关键问题更新', {
            'triggered_by': user_input if user_input else '系统内部更新',
            'content_summary': str(content)[:200] + '...' if len(str(content)) > 200 else str(content)
        })
    
    def update_constraints(self, content, user_input=None):
        """更新约束条件内容
        
        Args:
            content (dict): 约束条件的内容
            user_input (str, optional): 触发更新的用户输入
        """
        # 更新内存中的约束条件
        self.constraints = content
        
        # 更新最新状态文件
        self._update_current_state('constraints', content)
        
        # 添加到历史记录
        self._add_to_history('constraints', content, user_input)
        
        # 记录到调试文件
        self._log_debug_info('约束条件更新', {
            'triggered_by': user_input if user_input else '系统内部更新',
            'content_summary': str(content)[:200] + '...' if len(str(content)) > 200 else str(content)
        })
    
    def _update_current_state(self, module_name, content):
        """更新最新状态文件中的指定模块
        
        Args:
            module_name (str): 模块名称
            content (dict): 模块内容
        """
        # 读取当前最新状态
        with open(self.current_state_path, 'r', encoding='utf-8') as f:
            current_state = json.load(f)
        
        # 更新指定模块
        current_state[module_name] = content
        current_state['last_updated'] = datetime.now().isoformat()
        
        # 保存更新后的最新状态
        with open(self.current_state_path, 'w', encoding='utf-8') as f:
            json.dump(current_state, f, ensure_ascii=False, indent=2)
    
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
            'content': content,
            'update_type': module_name  # 添加更新内容类型
        }
        
        # 如果有触发更新的用户输入，则添加到记录中
        if user_input:
            record['user_input'] = user_input
        
        # 添加到历史记录
        history.append(record)
        
        # 保存更新后的历史记录
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
            
        # 同时添加到session_record的intermediate_states中
        self.add_intermediate_state(f"{module_name}_update", content, module_name)
    
    def get_module_current_state(self, module_name):
        """获取指定模块的最新状态
        
        Args:
            module_name (str): 模块名称，可选值为'spatial_understanding', 'user_requirements', 'key_questions', 'constraints'
            
        Returns:
            dict: 模块的最新状态
        """
        with open(self.current_state_path, 'r', encoding='utf-8') as f:
            current_state = json.load(f)
        return current_state.get(module_name, {})
    
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
    
    def _save_llm_output(self, api_call_record):
        """保存LLM输出到单个JSON文件
        
        Args:
            api_call_record (dict): API调用记录
        """
        # 定义llm_output.json文件路径
        file_path = os.path.join(self.llm_output_dir, 'llm_output.json')
        
        # 如果文件不存在，创建一个包含空列表的文件
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        
        # 读取现有的LLM输出记录
        with open(file_path, 'r', encoding='utf-8') as f:
            llm_outputs = json.load(f)
        
        # 添加新的API调用记录
        llm_outputs.append(api_call_record)
        
        # 保存更新后的记录
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(llm_outputs, f, ensure_ascii=False, indent=2)
    
    def _append_to_conversation_file(self, message):
        """将消息添加到对话历史文件
        
        Args:
            message (dict): 消息记录
        """
        # 读取当前对话历史
        with open(self.conversation_file_path, 'r', encoding='utf-8') as f:
            conversation = json.load(f)
        
        # 添加新消息
        conversation.append(message)
        
        # 保存更新后的对话历史
        with open(self.conversation_file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation, f, ensure_ascii=False, indent=2)
    
    def _log_debug_info(self, action_type, details):
        """记录调试信息
        
        Args:
            action_type (str): 操作类型
            details (dict): 详细信息
        """
        # 读取当前调试日志
        with open(self.debug_log_path, 'r', encoding='utf-8') as f:
            debug_log = json.load(f)
        
        # 创建新的调试记录
        debug_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'details': details
        }
        
        # 添加到调试日志
        debug_log.append(debug_entry)
        
        # 保存更新后的调试日志
        with open(self.debug_log_path, 'w', encoding='utf-8') as f:
            json.dump(debug_log, f, ensure_ascii=False, indent=2)
    
    def get_conversation_history(self):
        """获取对话历史
        
        Returns:
            list: 对话历史列表
        """
        return self.session_record['conversation_history']
    
    def get_debug_log(self):
        """获取调试日志
        
        Returns:
            list: 调试日志列表
        """
        with open(self.debug_log_path, 'r', encoding='utf-8') as f:
            debug_log = json.load(f)
        return debug_log
    
    def get_all_llm_outputs(self):
        """获取所有LLM输出记录
        
        Returns:
            list: LLM输出记录列表
        """
        llm_outputs = []
        for filename in os.listdir(self.llm_output_dir):
            if filename.startswith('llm_output_') and filename.endswith('.json'):
                file_path = os.path.join(self.llm_output_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    llm_output = json.load(f)
                    llm_outputs.append(llm_output)
        
        # 按时间戳排序
        llm_outputs.sort(key=lambda x: x.get('timestamp', ''))
        return llm_outputs