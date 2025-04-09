# 建筑布局设计AI系统

本项目是一个基于AI的建筑布局设计辅助系统，通过自然语言交互帮助用户（设计师）生成和优化建筑布局方案。系统通过多轮对话，逐步逼近用户真实需求，并生成量化的软约束条件，供后续求解器生成设计方案。

## 系统架构

系统由以下四个核心模块组成：

1. **空间理解模块**：解析用户输入的建筑边界和环境信息，提取空间信息。
2. **需求分析模块**：根据用户输入和已有信息，推测用户需求，更新用户需求猜测。
3. **提问模块**：根据用户需求猜测和关键问题列表，生成下一个问题，引导用户提供更多信息。
4. **约束条件量化模块**：将用户需求猜测转化为软约束条件，进行冲突检测和用户确认。

## 工作流程

系统采用循序渐进的交互工作流程：

1. **需求收集阶段**：用户描述项目需求，系统提问并收集信息
2. **约束条件生成阶段**：系统根据收集到的需求生成约束条件
3. **约束条件可视化阶段**：系统将约束条件转化为图形和表格展示
4. **约束条件优化阶段**：用户通过自然语言反馈优化约束条件
5. **布局方案生成阶段**：系统根据约束条件生成布局方案
6. **布局方案优化阶段**：用户对布局方案进行评价，系统调整约束条件并重新生成方案

## 主要功能亮点

### 空间流线与连接关系

- 自动添加**流线空间(path)**和**入口(entrance)**形成完整空间结构
- 支持两种空间关系：**直接连接(connection)**和**空间邻接(adjacency)**
- 智能可达性检测，确保所有房间都能从entrance通过path到达
- 空间连接关系自动优化，符合建筑设计原则

### 约束条件可视化

- 生成直观的房间连接关系图，使用艺术审美色卡为各房间配色
- 实线表示直接连接关系，虚线表示空间邻接关系
- 节点大小反映房间面积，形状反映房间长宽比
- 完整的约束条件表格展示房间的面积、朝向、窗户需求等
- 可视化文件自动保存，便于查看和分享

### 约束条件对比分析

- 约束条件优化后自动生成变化对比表格
- 只展示发生变化的部分，便于用户理解调整内容
- 支持对房间添加/删除、约束值修改等多种变化的分析
- 对比分析结果保存为图片，方便后续参考

### 多轮交互优化

- 支持对约束条件进行多轮自然语言优化
- 支持对布局方案进行反馈，系统能据此调整约束条件
- 循环生成-评价-优化流程，不断提升方案质量

### 会话恢复功能

- 通过`--resume`参数恢复之前的会话状态
- 自动判断应进入哪个工作阶段
- 保存完整的交互历史和中间结果

## 多模型支持

系统支持使用不同公司的大语言模型，通过统一的API接口进行调用。目前支持以下模型：

1. **OpenAI模型**：如GPT-4o、GPT-4-turbo
2. **Anthropic模型**：如Claude Opus
3. **腾讯云deepseek模型**：如deepseek-v3、deepseek-r1

您可以在`config.py`文件中为每个模块单独指定使用的模型。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 在`.env`文件中设置您需要使用的模型的API密钥：

```
# OpenAI API密钥
OPENAI_API_KEY=your_openai_api_key_here

# 腾讯云 API密钥
TENCENT_DEEPSEEK_API_KEY=your_tencent_deepseek_api_key_here

# Anthropic (Claude) API密钥
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

2. 在`config.py`中配置各模块使用的模型（可选，已有默认配置）：

```python
# 为每个模块指定默认模型
SPATIAL_UNDERSTANDING_MODEL = "deepseek-v3"  # 空间理解模块使用的模型
REQUIREMENT_ANALYSIS_MODEL = "deepseek-v3"  # 需求分析模块使用的模型
QUESTION_GENERATION_MODEL = "deepseek-v3"  # 提问生成模块使用的模型
CONSTRAINT_QUANTIFICATION_MODEL = "deepseek-v3"  # 约束量化模块使用的模型
```

3. 启动新会话：

```bash
python main.py
```

4. 恢复已有会话：

```bash
python main.py --resume sessions/20240410_123456
```

5. 按照系统提示，描述您的建筑项目和需求，与系统进行交互。

## 约束条件结构

系统生成的约束条件分为两种格式：

### all格式

```json
{
  "hard_constraints": {
    "room_list": ["living_room", "bedroom", "kitchen"]
  },
  "soft_constraints": {
    "connection": { "weight": 0.8, "constraints": [...] },
    "adjacency": { "weight": 0.6, "constraints": [...] },
    "area": { "weight": 0.7, "constraints": [...] },
    "orientation": { "weight": 0.5, "constraints": [...] },
    "window_access": { "weight": 0.6, "constraints": [...] },
    "aspect_ratio": { "weight": 0.4, "constraints": [...] },
    "repulsion": { "weight": 0.5, "constraints": [...] }
  },
  "special_spaces": {
    "path": true,
    "entrance": true
  }
}
```

### rooms格式

```json
{
  "rooms": {
    "living_room": {
      "connection": ["kitchen", "entrance"],
      "adjacency": ["bedroom"],
      "area": {"min": 20, "max": 30},
      "orientation": "south",
      "window_access": true,
      "aspect_ratio": {"min": 0.7, "max": 1.5},
      "repulsion": []
    },
    // 其他房间...
  },
  "special_spaces": {
    "path": true,
    "entrance": true
  }
}
```

## 文件结构

- `main.py`：主程序，控制整个系统的流程。
- `config.py`：配置文件，包含API设置、模型配置和提示词模板。
- `models/`：功能模块目录
  - `spatial_understanding.py`：空间理解模块
  - `requirement_analysis.py`：需求分析模块
  - `question_generation.py`：提问生成模块
  - `constraint_quantification.py`：约束条件量化模块
  - `constraint_visualization.py`：约束条件可视化模块
  - `constraint_refinement.py`：约束条件优化模块
  - `solution_refinement.py`：布局方案优化模块
  - `unified_processor.py`：统一处理模块
- `utils/`：工具类目录
  - `openai_client.py`：LLM API客户端，封装各种模型的调用
  - `json_handler.py`：JSON处理工具
  - `converter.py`：约束条件格式转换工具
  - `session_manager.py`：会话记录管理器
  - `workflow_manager.py`：工作流程管理器
  - `constraint_validator.py`：约束条件验证工具
- `templates/`：模板文件目录
  - `template_constraints_all.txt`：all格式约束条件模板
  - `template_constraints_rooms.txt`：rooms格式约束条件模板
  - `prompt_template_constraints_all.txt`：all格式约束条件提示词模板
  - `prompt_template_constraints_rooms.txt`：rooms格式约束条件提示词模板
  - `constraint_base_prompt.txt`：约束条件基础提示词

## 注意事项

- 本系统需要API密钥才能运行，请在使用前设置相应的环境变量。
- 系统假设存在可用的布局求解器，本项目仅实现交互部分。
- 生成的约束条件保存为JSON格式，可供后续布局求解器使用。
- 可视化约束条件需要matplotlib、networkx和numpy库支持。
- 每个模型都有各自的特点和优势，您可以根据实际需求配置最适合的模型组合。