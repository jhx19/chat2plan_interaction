# 建筑布局设计AI系统

本项目是一个基于AI的建筑布局设计辅助系统，通过自然语言交互帮助用户（设计师）生成和优化建筑布局方案。系统通过多轮对话，逐步逼近用户真实需求，并生成量化的软约束条件，供后续求解器生成设计方案。

## 系统架构

系统由以下四个核心模块组成：

1. **空间理解模块**：解析用户输入的建筑边界和环境信息，提取空间信息。
2. **需求分析模块**：根据用户输入和已有信息，推测用户需求，更新用户需求猜测。
3. **提问模块**：根据用户需求猜测和关键问题列表，生成下一个问题，引导用户提供更多信息。
4. **约束条件量化模块**：将用户需求猜测转化为软约束条件，进行冲突检测和用户确认。

## 多模型支持

系统支持使用不同公司的大语言模型，通过统一的API接口进行调用。目前支持以下模型：

1. **OpenAI模型**：如GPT-4、GPT-3.5
2. **Anthropic模型**：如Claude Opus、Claude Instant
3. **百度文心一言**：如ERNIE Bot 4
4. **智谱GLM**：如GLM-4

您可以在`config.py`文件中为每个模块单独指定使用的模型，例如：
- 空间理解模块可以使用较轻量的GPT-3.5
- 需求分析模块可以使用更强大的GPT-4
- 提问生成模块可以使用Claude
- 约束量化模块可以使用文心一言

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 在`.env`文件中设置您需要使用的模型的API密钥：

```
# OpenAI API密钥
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic (Claude) API密钥
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 百度文心一言API密钥
BAIDU_API_KEY=your_baidu_api_key_here
BAIDU_SECRET_KEY=your_baidu_secret_key_here

# 智谱AI (GLM) API密钥
ZHIPU_API_KEY=your_zhipu_api_key_here
```

2. 在`config.py`中配置各模块使用的模型（可选，已有默认配置）：

```python
# 为每个模块指定默认模型
SPATIAL_UNDERSTANDING_MODEL = "gpt-3.5-turbo"  # 空间理解模块使用的模型
REQUIREMENT_ANALYSIS_MODEL = "gpt-4"  # 需求分析模块使用的模型
QUESTION_GENERATION_MODEL = "claude-instant"  # 提问生成模块使用的模型 
CONSTRAINT_QUANTIFICATION_MODEL = "gpt-4"  # 约束量化模块使用的模型
```

3. 运行主程序：

```bash
python main.py
```

4. 按照系统提示，描述您的建筑项目和需求，与系统进行交互。

## 文件结构

- `main.py`：主程序，控制整个系统的流程。
- `config.py`：配置文件，包含API设置、模型配置和提示词模板。
- `models/`：功能模块目录
  - `spatial_understanding.py`：空间理解模块
  - `requirement_analysis.py`：需求分析模块
  - `question_generation.py`：提问生成模块
  - `constraint_quantification.py`：约束条件量化模块
- `utils/`：工具类目录
  - `openai_client.py`：LLM API客户端，封装各种模型的调用
  - `json_handler.py`：JSON处理工具
  - `converter.py`：约束条件格式转换工具
- `template_constraints_all.txt`：all格式约束条件模板
- `template_constraints_rooms.txt`：rooms格式约束条件模板

## 示例对话

**系统**：欢迎使用建筑布局设计AI系统！请描述您的建筑边界和环境信息，我将帮助您设计布局。

**用户**：我想设计一套三口之家的小户型住宅，占地面积大约100平方米，南侧临街，北侧为小区内部。入口在南侧。

**系统**：感谢您提供的信息。您是一个三口之家，需要设计一套小户型住宅，占地面积大约100平方米，南侧临街并设有入口，北侧为小区内部。您能告诉我，您对住宅中各个空间的功能需求和偏好吗？比如您希望有哪些房间，以及它们的使用方式？

...（后续对话）

## 注意事项

- 本系统需要API密钥才能运行，请在使用前设置相应的环境变量。
- 系统假设存在可用的布局求解器，本项目仅实现交互部分。
- 生成的约束条件保存为JSON格式，可供后续布局求解器使用。
- 每个模型都有各自的特点和优势，您可以根据实际需求配置最适合的模型组合。 