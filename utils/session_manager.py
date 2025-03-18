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