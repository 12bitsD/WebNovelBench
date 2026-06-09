# WebNovelBench

中文网文/长篇故事质量评估 Benchmark

## 核心理念

- **Agent-as-Judge**: 不用统计方法，用 LLM 像人一样阅读和评判
- **Rubric 驱动**: 每个评分都有明确标准、文本证据和推理过程
- **10 维度评估**: 信息流、角色弧光、世界观、主题、张力、反转、展示、冲突、文化、爽点

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 LLM
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
export MODEL_NAME="gpt-4o"  # 可选

# 运行测试
python tests/test_judge.py --mode single  # 单维度测试
python tests/test_judge.py --mode full    # 双维度测试
```

## 项目结构

```
WebNovelBench/
├── docs/                  # 设计文档
│   ├── vision.md          # 核心设计文档（权威）
│   ├── judge_prompt_template.md
│   └── codex_task_phase1.md
├── src/
│   ├── config.py          # 配置
│   ├── judges/
│   │   ├── rubrics/       # 10个维度的 Rubric YAML
│   │   └── dimension_judge.py  # 维度评估器
│   ├── evaluators/
│   │   ├── sampler.py     # 文本采样器
│   │   └── pipeline.py    # 评估 Pipeline
│   └── utils/
│       └── llm_client.py  # LLM API 客户端
├── data/
│   ├── samples/           # 采样后的文本片段
│   ├── references/        # 人类共识评分
│   └── results/           # 评估结果
└── tests/
    └── test_judge.py      # 测试脚本
```

## 评估维度

| # | 维度 | 核心问题 |
|---|------|---------|
| D1 | 信息流管理 | 读者的好奇心是否被持续且精确地操控？ |
| D2 | 角色弧光 | 角色变化是否被故事逻辑驱动？ |
| D3 | 世界观构建 | 世界观是否自洽、有深度？ |
| D4 | 主题共振 | 主题是否通过结构自然呈现？ |
| D5 | 结构张力 | 张力是否有层次、有升级？ |
| D6 | 颠覆与反转 | 反转是否"意料之外，情理之中"？ |
| D7 | 展示艺术 | 是否通过行动而非旁白展示？ |
| D8 | 冲突设计 | 冲突是否有层次、有策略？ |
| D9 | 文化质感 | 文化元素是贴皮还是内化？ |
| D10 | 爽点工艺 | 爽点是否有创意、有层次？ |

## 设计文档

详见 `docs/vision.md` — 这是项目的唯一设计权威。
