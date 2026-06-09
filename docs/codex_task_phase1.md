# Codex Task: Phase 1 Implementation

## Context

WebNovelBench is a benchmark for evaluating Chinese web novel quality.
The core design is in `docs/vision.md` and `docs/judge_prompt_template.md`.
Read those first.

## Design Constraints (MUST FOLLOW)

1. **NO statistical methods** - no word counting, sentence length, n-gram analysis.
   All evaluation is done by LLM-as-Judge reading the text and applying rubrics.

2. **All evaluation dimensions are defined in YAML rubric files** - not hardcoded in Python.
   Each dimension has its own YAML file under `src/judges/rubrics/`.

3. **Structured JSON output** - every judge call returns a JSON object with:
   - score (1-10)
   - evidence (list of text excerpts with analysis)
   - reasoning (how evidence maps to score)
   - borderline_notes (if score is between two levels)

4. **Configurable LLM provider** - support OpenAI API format (works with OpenAI, Anthropic via proxy, local models, etc.)
   Config via environment variables or config file.

5. **Text sampling must be flexible** - different dimensions need different sampling strategies.
   Sampling strategies are defined in config, not hardcoded.

## What to Build

### Phase 1: Core Pipeline

Build a minimal working pipeline that can:
1. Read a text file (Chinese web novel in .txt format)
2. Sample the text according to a strategy
3. Call an LLM with a judge prompt for one dimension
4. Parse the JSON output from the LLM
5. Print the structured result

### File Structure

```
src/
├── config.py              # Configuration (LLM provider, paths, etc.)
├── judges/
│   ├── __init__.py
│   ├── base.py            # Base judge class
│   ├── rubrics/           # YAML rubric files (one per dimension)
│   │   ├── D1_information_flow.yaml
│   │   ├── D2_character_arc.yaml
│   │   ├── D3_world_building.yaml
│   │   ├── D4_theme.yaml
│   │   ├── D5_structure_tension.yaml
│   │   ├── D6_reversal.yaml
│   │   ├── D7_show_dont_tell.yaml
│   │   ├── D8_conflict.yaml
│   │   ├── D9_cultural_texture.yaml
│   │   └── D10_satisfaction.yaml
│   └── dimension_judge.py # Loads rubric YAML, builds prompt, calls LLM
├── evaluators/
│   ├── __init__.py
│   ├── sampler.py         # Text sampling strategies
│   └── pipeline.py        # Orchestrates: sample → judge → aggregate
└── utils/
    ├── __init__.py
    └── llm_client.py      # LLM API client (configurable provider)
```

### Rubric YAML Format

Each rubric file should follow this structure:

```yaml
dimension:
  id: "D1"
  name: "信息流管理"
  name_en: "Information Flow Management"
  definition: |
    核心概念描述...
  
sampling:
  strategy: "dispersed"  # dispersed | key_nodes | continuous
  chunk_size: 3000       # characters per chunk
  num_chunks: 10         # number of chunks to sample

scoring:
  "1-2":
    label: "信息线性释放"
    characteristics:
      - "信息按时间顺序平铺，无悬念管理"
      - "读者从头到尾知道的和角色一样多"
      - "无伏笔，无信息缺口"
    counter_examples:
      - "有简单悬念但管理粗糙 → 应评3-4分"
  "3-4":
    label: "有基础悬念但管理粗糙"
    characteristics:
      - ...
    counter_examples:
      - ...
  # ... (all score ranges)

borderline_rules:
  - question: "伏笔回收了但方式平淡，算不算？"
    answer: "回收本身算+1，但平淡的回收不加分。回收方式单独评估。"
  - question: "信息级联和叙事重构怎么区分？"
    answer: "级联=新问题替代旧问题；重构=整个理解框架被推翻。"

positive_examples:
  - work: "进击的巨人"
    score: 8
    reason: "马莱篇的视角反转，信息级联精密"
  - work: "诡秘之主"
    score: 8
    reason: "22途径体系的信息管理非常精密"

negative_examples:
  - work: "典型系统文"
    score: 2
    reason: "信息线性释放，无悬念管理"
```

### LLM Client

```python
# Should support:
# - OpenAI API format (works with most providers)
# - Configurable via env vars or config file
# - Retry logic for API failures
# - Token counting (to stay within context limits)

# Config options:
# OPENAI_API_KEY or ANTHROPIC_API_KEY
# OPENAI_BASE_URL (for proxies)
# MODEL_NAME (default: gpt-4 or claude-3.5-sonnet)
```

### Text Sampler

```python
# Strategy: dispersed
# - Split text into N equal chunks
# - Sample from the beginning, middle, and end
# - Each chunk is chunk_size characters
# - Return list of (position, text) tuples

# Strategy: key_nodes
# - Requires chapter detection (look for "第X章" patterns)
# - Sample: first 5 chapters, last 5 chapters, and chapters at 25%, 50%, 75%
# - Return list of (chapter_num, text) tuples

# Strategy: continuous
# - Select N consecutive chapters from specified position
# - Return list of (chapter_num, text) tuples
```

### Judge Output Format

```python
{
    "dimension": "D1_信息流管理",
    "score": 7,
    "score_range": "7-8分: 信息级联精密",
    "evidence": [
        {
            "location": "样本片段3，第2段",
            "text_excerpt": "原文引用...",
            "analysis": "这段展示了..."
        }
    ],
    "reasoning": "推理过程...",
    "borderline_notes": "边界案例说明...",
    "improvement_suggestions": "改进建议..."
}
```

## Testing

Create a simple test that:
1. Reads a sample text file
2. Samples it
3. Calls the judge for D1 (information flow)
4. Prints the result

Use a short test text (5000 characters) for quick iteration.

## Important Notes

- This is a Chinese language project - all rubrics, prompts, and output should be in Chinese
- The judge prompt should be in Chinese (the LLM evaluates Chinese text)
- Use `httpx` or `openai` SDK for API calls
- Handle JSON parsing errors gracefully (LLM output may not be valid JSON)
- Add retry logic for API failures

## DO NOT

- Do NOT add statistical analysis (word counting, sentence length, etc.)
- Do NOT hardcode rubrics in Python code (use YAML files)
- Do NOT assume a specific LLM provider (make it configurable)
- Do NOT skip the evidence requirement (every score must have text evidence)
