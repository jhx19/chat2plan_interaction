"""
配置文件，保存系统设置和常量
"""

# 可用的LLM模型配置
AVAILABLE_MODELS = {
    # 腾讯云deepseek-v3
    "deepseek-v3": {
        "type": "openai",
        "model": "deepseek-v3",
        "base_url": "https://api.lkeap.cloud.tencent.com/v1",
        "api_key_env": "TENCENT_DEEPSEEK_API_KEY",
        "max_tokens": 2000
        },
    # 腾讯云deepseek-r1
    "deepseek-r1": {
        "type": "openai",
        "model": "deepseek-r1",
        "base_url": "https://api.lkeap.cloud.tencent.com/v1",
        "api_key_env": "TENCENT_DEEPSEEK_API_KEY",
        "max_tokens": 2000,
        "temperature": 0.7
    },
    
    # OpenAI模型
    "gpt-4o": {
        "type": "openai",
        "model": "gpt-4o",
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "max_tokens": 2000,
        "temperature": 0.7
    },
    "gpt-4-turbo": {
        "type": "openai",
        "model": "gpt-4-turbo",
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "max_tokens": 2000,
        "temperature": 0.7
    },
    # 其他公司的兼容OpenAI API的模型，例如Claude
    "claude-3-opus": {
        "type": "anthropic",
        "model": "claude-3-opus-20240229",
        "base_url": "https://api.anthropic.com/v1/messages",
        "api_key_env": "ANTHROPIC_API_KEY",
        "max_tokens": 2000,
        "temperature": 0.7,
        "api_version": "2023-06-01"
    }
}

# 为每个模块指定默认模型（可根据需要修改）
# 默认模型
DEFAULT_MODEL = "deepseek-v3"
SPATIAL_UNDERSTANDING_MODEL = DEFAULT_MODEL  # 空间理解模块使用的模型
REQUIREMENT_ANALYSIS_MODEL = DEFAULT_MODEL  # 需求分析模块使用的模型
QUESTION_GENERATION_MODEL = DEFAULT_MODEL  # 提问生成模块使用的模型
CONSTRAINT_QUANTIFICATION_MODEL = DEFAULT_MODEL  # 约束量化模块使用的模型

# 每个模块的个性化设置
SPATIAL_UNDERSTANDING_TEMPERATURE = 0.7
REQUIREMENT_ANALYSIS_TEMPERATURE = 0.7
QUESTION_GENERATION_TEMPERATURE = 0.7
CONSTRAINT_QUANTIFICATION_TEMPERATURE = 0.5  # 约束量化需要更精确，所以温度稍低

# 路径设置
TEMPLATE_CONSTRAINTS_ALL_PATH = "template_constraints_all.txt"
TEMPLATE_CONSTRAINTS_ROOMS_PATH = "template_constraints_rooms.txt"

# 提示词设置 - 空间理解模块
SPATIAL_UNDERSTANDING_PROMPT = """
你是一个专业的建筑设计师助手，负责理解用户描述的建筑边界和环境信息。
请仔细分析以下用户输入，提取关于建筑边界的形状、面积、周围环境、入口位置等空间信息。
将提取的信息转换为简洁清晰的自然语言描述，作为"空间理解"记录。

用户当前输入: {user_input}

当前空间理解记录: {current_spatial_understanding}

请更新空间理解记录，包含所有相关的空间信息。如果用户输入中没有新的空间信息，请保持原记录不变。
"""

# 提示词设置 - 需求分析模块
REQUIREMENT_ANALYSIS_PROMPT = """
你是一个专业的建筑设计师助手，负责分析用户的建筑设计需求。
请根据用户的回答、当前的需求猜测以及空间理解记录，推测用户的设计需求，特别关注用户的个性化需求。

用户当前输入: {user_input}
当前用户需求猜测: {current_requirement_guess}
当前空间理解记录: {spatial_understanding}

请更新用户需求猜测，保持自然语言形式。在推测时：
1. 基于用户回答中的显性信息（如"朝南"）和隐性信息（如"喜欢阳光"暗示开窗需求）。
2. 考虑建筑设计常识和最佳实践，但以用户的个性化需求为优先。
3. 避免过度假设，应基于用户回答中的明确线索。
4. 若用户未提及某方面，可保持该部分不变或根据建筑设计常识补充。

提供一个全面更新的用户需求猜测，以便后续生成约束条件。
"""

# 提示词设置 - 提问生成模块
QUESTION_GENERATION_PROMPT = """
你是一个专业的建筑设计师助手，负责通过提问帮助用户明确设计需求。
请根据当前的用户需求猜测和关键问题列表，生成下一个问题。

当前用户需求猜测：
{current_requirement_guess}

关键问题列表（按类别）：
{key_questions_formatted}

请生成一个自然语言形式的问题，帮助进一步了解用户需求。要求：
1. 不要生硬照搬关键问题列表中的问题，而是基于它们创建流畅的对话。
2. 优先询问状态为"未知"且对布局影响最大的问题。
3. 问题应引导用户畅想他们期待的设计，而不是询问具体数值。
4. 基于当前的用户需求猜测，避免重复已知信息。
5. 使用友好、专业的语气，避免过于技术性的术语。

生成一个开放式问题，鼓励用户分享他们的生活方式、偏好和期望，从而帮助提取更多设计需求细节。
"""

# 提示词设置 - 约束条件量化模块
CONSTRAINT_QUANTIFICATION_PROMPT = """
你是一个专业的建筑设计师助手，负责将用户需求转化为量化的约束条件。
请根据用户需求猜测和空间理解记录，生成符合JSON模板的约束条件。

用户需求猜测：
{user_requirement_guess}

空间理解记录：
{spatial_understanding}

约束条件模板：
{constraint_template}

请完成以下任务：
1. 分析用户需求猜测，提取所有可量化的需求。
2. 将需求转化为JSON格式的约束条件，严格遵循提供的模板结构。
3. 为未明确提及但设计中必要的部分，根据建筑设计常识补充合理的默认值。
4. 为每类约束条件分配合理的权重（0.0-1.0），反映其在用户需求中的重要性。
5. 检测约束条件之间的潜在冲突，确保约束条件的一致性和合理性。

生成的约束条件应完整、精确，并适合直接输入到布局求解器中。
"""

# 检查问题是否已回答的提示词
CHECK_QUESTION_ANSWERED_PROMPT = """
你是一个专业的建筑设计师助手，负责判断一个问题是否已经在用户需求猜测中得到了回答。

问题：{question}

用户需求猜测：
{requirement_guess}

请判断这个问题是否已经在用户需求猜测中得到了明确或隐含的回答。
只返回"是"或"否"。
"""

# 约束条件转换提示词
CONSTRAINT_CONVERTER_PROMPT = """
你是一个专业的建筑设计师助手，负责在不同格式的约束条件之间进行转换。

请将以下all格式的约束条件转换为rooms格式：

all格式约束条件：
{constraints_all}

转换后的rooms格式应遵循以下模板：
{template_rooms}

请确保转换过程中不丢失任何信息，并保持约束条件的完整性和一致性。
"""