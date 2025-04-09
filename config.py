"""
配置文件，保存系统设置和常量
"""

# 强制LLM输出JSON格式
FORCE_JSON_OUTPUT = True
RESPONSE_FORMAT = "json"

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
TEMPLATE_CONSTRAINTS_ALL_PATH = r"templates\template_constraints_all.txt"
TEMPLATE_CONSTRAINTS_ROOMS_PATH = r"templates\template_constraints_rooms.txt"
PROMPT_TEMPLATE_CONSTRAINTS_ALL_PATH = r"templates\prompt_template_constraints_all.txt"
PROMPT_TEMPLATE_CONSTRAINTS_ROOMS_PATH = r"templates\prompt_template_constraints_rooms.txt"

# 强制LLM输出JSON格式的参数设置
FORCE_JSON_OUTPUT = True  # 是否强制LLM输出JSON格式
RESPONSE_FORMAT = "json"  # 响应格式，可选值：json, text

# 通用基础提示词，用于所有模块
BASE_PROMPT = """
你是一个专业的建筑设计师助手，正在协助用户进行建筑布局设计。
本系统的方法论是：
1. 理解用户描述的空间边界和环境信息
2. 分析用户的建筑设计需求和偏好
3. 通过有针对性的提问帮助用户明确需求
4. 将用户需求转化为量化的约束条件
5. 基于这些约束条件生成最优的建筑布局方案
请确保你的回答专业、准确，并且符合建筑设计的最佳实践。
"""

# 提示词设置 - 空间理解模块
SPATIAL_UNDERSTANDING_PROMPT = """
{base_prompt}\n\n你的当前任务是理解用户描述的建筑边界和环境信息。
请仔细分析以下用户输入，提取关于建筑边界的形状、面积、周围环境、入口位置等空间信息。
将提取的信息转换为简洁清晰的自然语言描述，作为"空间理解"记录。

用户当前输入: {user_input}

当前空间理解记录: {current_spatial_understanding}

请更新空间理解记录，包含所有相关的空间信息。如果用户输入中没有新的空间信息，请保持原记录不变。

请以JSON格式返回结果，格式如下：
{{
  "updated": true/false,  // 是否有更新，true表示有更新，false表示无更新
  "spatial_understanding": "更新后的空间理解记录"  // 如果没有更新，则为空字符串
}}
"""

# 提示词设置 - 需求分析模块
REQUIREMENT_ANALYSIS_PROMPT = """
{base_prompt}\n\n你的当前任务是分析用户的建筑设计需求和空间信息。
请根据用户的回答、当前的需求猜测以及空间理解记录，推测用户的设计需求，特别关注用户的个性化需求。同时，评估是否需要更新空间理解记录。


当前用户需求猜测: {current_requirement_guess}
当前空间理解记录: {spatial_understanding}
用户当前输入: {user_input}

请完成以下任务：
1. 分析用户输入中的设计需求信息，更新用户需求猜测。
2. 分析用户输入中的空间信息，判断是否需要更新空间理解记录。
3. 以JSON格式返回结果，包含更新后的用户需求猜测和空间理解记录，以及它们是否有更新的标识。

在分析用户需求时：
1. 基于用户回答中的显性信息（如"朝南"）和隐性信息（如"喜欢阳光"暗示开窗需求）。
2. 考虑建筑设计常识和最佳实践，但以用户的个性化需求为优先。
3. 避免过度假设，应基于用户回答中的明确线索。
4. 若用户未提及某方面，可保持该部分不变或根据建筑设计常识补充。
5. 整理信息的表达顺序，如有新的信息，应补充到原有相关信息的位置。
注意：从需要哪些功能空间（房间）开始分析，再到各个功能空间（房间）应该满足的细节约束和各个功能空间（房间）之间的关系以及与周围环境之间的关系。

请以JSON格式返回结果，格式如下：
{{
  "spatial_updated": true/false,  // 空间理解是否有更新  
  "spatial_understanding": "更新后的空间理解记录"  // 如果没有更新，则返回空字符串
  "requirement_updated": true/false,  // 需求猜测是否有更新
  "requirement_guess": "更新后的用户需求猜测",  // 如果没有更新，则返回空字符串
}}
"""

# 提示词设置 - 提问生成模块
QUESTION_GENERATION_PROMPT = """
{base_prompt}\n\n你的当前任务是通过提问帮助用户明确设计需求，并同时评估关键问题类别的状态。
请根据当前的用户需求猜测和关键问题列表，生成下一个问题，并更新关键问题列表。

当前用户需求猜测：
{current_requirement_guess}

关键问题列表（按类别）：
{key_questions_formatted}

请完成以下两个任务：

任务1：根据用户需求猜测，判断每个类别的问题是否已经得到回答，更新关键问题列表中各问题的状态。
对于每个问题类别，其状态是"已知"还是"未知"。"已知"表示该类别的问题已得到回答，"未知"表示尚未得到回答。

任务2：生成一个自然语言形式的问题，帮助进一步了解用户需求。要求：
1. 不要生硬照搬关键问题列表中的问题，而是基于它们创建流畅的对话。
2. 优先询问状态为"未知"且对布局影响最大的问题。
3. 问题应引导用户畅想他们期待的设计，而不是询问具体数值。
4. 基于当前的用户需求猜测，避免重复已知信息。
5. 使用友好、专业的语气，避免过于技术性的术语。

任务3：提供一个简短的解释，说明你为什么选择这个问题，以及你如何判断更新各个关键问题类别的状态。这个解释应该包括：
1. 你如何根据用户需求猜测判断各个类别的状态
2. 为什么选择这个问题而不是其他问题
3. 这个问题与用户当前需求的关联性

生成一个开放式问题，鼓励用户分享他们的生活方式、偏好和期望，从而帮助提取更多设计需求细节。

请以JSON格式返回结果，格式如下：
{{
  "categories": [
    {{
      "category": "类别名称",
      "status": "已知/未知"  // 已知表示该类别的问题已得到回答，未知表示尚未得到回答
    }},
    // 其他类别...
  ],
  "question": "生成的问题",
  "explanation": "选择这个问题和判断关键问题类别状态的思考过程"
}}
"""


# 提示词设置 - 优化rooms格式约束条件
CONSTRAINT_ROOMS_OPTIMIZATION_PROMPT = """
你的当前任务是优化和完善房间约束条件。
请根据用户需求猜测和空间理解记录，优化以下房间约束条件。

用户需求猜测：
{user_requirement_guess}

空间理解记录：
{spatial_understanding}

当前房间约束条件：
{constraints_rooms}

房间约束条件模板格式参考：
{template_rooms_with_comments}

请完成以下任务：
1. 分析用户需求猜测，检查当前房间约束条件是否完整反映了用户需求。
2. 优化和完善房间约束条件，确保每个房间的约束条件合理且符合用户需求。
3. 检查房间之间的连接关系是否合理，确保空间布局的流畅性。
4. 确保所有房间的面积、朝向、窗户需求等约束条件都符合用户需求和建筑设计常识。有些房间的某些约束条件可以是空的。
5. 返回优化后的完整房间约束条件JSON。

请以JSON格式返回结果，格式如下：
{{
  "constraints": {{
        "rooms":{{
        // 房间约束条件，完整JSON,严格按照约束条件模板格式
        }}
    }}
}}
"""

# 检查问题是否已回答的提示词
CHECK_QUESTION_ANSWERED_PROMPT = """
{base_prompt}\n\n你的当前任务是判断一个问题是否已经在用户需求猜测中得到了回答。

问题：{question}

用户需求猜测：
{requirement_guess}

请判断这个问题是否已经在用户需求猜测中得到了明确或隐含的回答。
只返回"是"或"否"。

请以JSON格式返回结果，格式如下：
{{
  "answered": true/false  // true表示已回答，false表示未回答
}}
"""

# 更新约束条件相关的提示词，集成constraint_base_prompt

# 更新约束条件量化提示词
CONSTRAINT_QUANTIFICATION_PROMPT = """

{base_prompt}

你的当前任务是将用户需求转化为量化的约束条件。
请根据用户需求猜测和空间理解记录，生成符合JSON模板的约束条件。

{constraint_base_prompt}

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
4. 为每类约束条件分配合理的权重（0.0-1.0），反映其在用户需求中的重要性，无特殊依据的部分可以设置常规权重。
5. 检测约束条件之间的潜在冲突，确保约束条件的一致性和合理性。
6. 添加path和entrance作为特殊空间，并确保所有房间可从entrance通过path到达。
7. 适当添加adjacency约束，表示空间相邻但不直接连通的房间对。

生成的约束条件应完整、精确，并适合直接输入到布局求解器中。

请以JSON格式返回结果，格式如下：
{{
  "constraints": {{
    "hard_constraints": {{
      // 房间列表等硬约束
    }},
    "soft_constraints": {{
      // 各类软约束
    }},
    "special_spaces": {{
      "path": true,
      "entrance": true
    }}
  }}
}}
"""

# 更新约束条件优化提示词
CONSTRAINT_REFINEMENT_PROMPT = """
{base_prompt}

你的当前任务是根据用户反馈，优化现有的约束条件。

{constraint_base_prompt}

当前约束条件：
{current_constraints}

空间理解记录：
{spatial_understanding}

用户反馈：
{user_feedback}

请完成以下任务：
1. 分析用户反馈，找出用户希望修改的约束条件部分。
2. 根据用户反馈调整相应的约束条件，包括但不限于：
   - 添加或删除房间
   - 修改房间面积、朝向、连接关系等
   - 调整约束条件权重
   - 调整connection和adjacency关系
3. 确保修改后的约束条件仍然符合JSON模板格式。
4. 检查修改后的约束条件是否存在矛盾或不合理之处。
5. 确保所有房间都能从entrance通过path到达。

在优化过程中：
1. 只修改用户明确提出需要调整的部分，保持其他部分不变。
2. 如果用户反馈含糊不清，可以根据建筑设计常识进行合理推测。
3. 确保优化后的约束条件仍然满足基本建筑设计原则。
4. 保持path和entrance作为特殊空间，不要将它们添加到房间列表中。

请以JSON格式返回优化后的约束条件，格式如下：
{{
  "refined_constraints": {{
    "hard_constraints": {{
      // 房间列表等硬约束
    }},
    "soft_constraints": {{
      // 各类软约束
    }},
    "special_spaces": {{
      "path": true,
      "entrance": true
    }}
  }}
}}
"""

# 更新布局方案优化提示词
SOLUTION_REFINEMENT_PROMPT = """
{base_prompt}

你的当前任务是根据用户对布局方案的反馈，优化约束条件以生成更满意的方案。
{constraint_base_prompt}
当前约束条件：
{current_constraints}

当前布局方案：
{current_solution}

空间理解记录：
{spatial_understanding}

用户反馈：
{user_feedback}

请完成以下任务：
1. 分析用户对布局方案的反馈，找出用户不满意的方面。
2. 根据用户反馈调整相应的约束条件，包括但不限于：
   - 修改房间面积、朝向、连接关系等
   - 调整约束条件权重
   - 添加新的connection、adjacency或repulsion关系
3. 确保修改后的约束条件仍然符合JSON模板格式。
4. 检查修改后的约束条件是否存在矛盾或不合理之处。
5. 确保所有房间都能从entrance通过path到达。

在优化过程中：
1. 只修改约束条件，不直接修改布局方案。
2. 根据用户对布局方案的反馈，推断出需要调整的约束条件。
3. 如果用户反馈含糊不清，可以根据建筑设计常识进行合理推测。
4. 确保优化后的约束条件仍然满足基本建筑设计原则。
5. 保持path和entrance作为特殊空间，不要将它们添加到房间列表中。

请以JSON格式返回优化后的约束条件，格式如下：
{{
  "refined_constraints": {{
    "hard_constraints": {{
      // 房间列表等硬约束
    }},
    "soft_constraints": {{
      // 各类软约束
    }},
    "special_spaces": {{
      "path": true,
      "entrance": true
    }}
  }}
}}
"""