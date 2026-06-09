"""
维度评估器
加载 Rubric YAML，构建 Judge Prompt，调用 LLM 评估
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

from src.config import config
from src.evaluators.sampler import TextSample
from src.utils.llm_client import llm_client

logger = logging.getLogger(__name__)


@dataclass
class Evidence:
    """评分证据"""
    location: str
    text_excerpt: str
    analysis: str


@dataclass
class DimensionResult:
    """单维度评估结果"""
    dimension: str
    score: int
    score_range: str
    evidence: List[Evidence]
    reasoning: str
    borderline_notes: str = ""
    improvement_suggestions: str = ""


class Rubric:
    """Rubric YAML 加载器"""

    def __init__(self, yaml_path: Path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)

        self.dim_id = self.data["dimension"]["id"]
        self.dim_name = self.data["dimension"]["name"]
        self.dim_name_en = self.data["dimension"]["name_en"]
        self.definition = self.data["dimension"]["definition"]
        self.sampling_config = self.data.get("sampling", {})
        self.scoring = self.data.get("scoring", {})
        self.borderline_rules = self.data.get("borderline_rules", [])
        self.positive_examples = self.data.get("positive_examples", [])
        self.negative_examples = self.data.get("negative_examples", [])
        self.judge_prompt_addition = self.data.get("judge_prompt_addition", "")

    def build_system_prompt(self) -> str:
        """构建系统提示词"""
        return f"""你是一位资深的叙事分析专家，拥有以下专业背景：
- 深度理解叙事结构理论（三幕式、英雄旅程、起承转合）
- 熟悉中文网文的创作规律和类型特征
- 能够从文本中识别叙事技法并评估其效果
- 评估风格：严谨、客观、有理有据

你的评估原则：
1. 每个判断必须有文本证据支持
2. 不凭感觉打分，只根据明确的评分标准
3. 如果两个分数都可能，选择更接近边界案例规则的那个
4. 不因为一个维度好就默认另一个维度也好
5. 评分基于提供的文本，不假设未提供的内容

{self.judge_prompt_addition}"""

    def build_user_prompt(self, samples: List[TextSample]) -> str:
        """构建用户提示词（包含文本样本和评估要求）"""
        # 构建评分标准
        scoring_text = ""
        for score_range, details in self.scoring.items():
            scoring_text += f"\n{score_range}分: {details.get('label', '')}\n"
            for char in details.get("characteristics", []):
                scoring_text += f"  - {char}\n"
            for ce in details.get("counter_examples", []):
                scoring_text += f"  反例: {ce}\n"

        # 构建边界案例规则
        borderline_text = ""
        for rule in self.borderline_rules:
            borderline_text += f"\nQ: {rule['question']}\nA: {rule['answer']}\n"

        # 构建正面/反面例子
        examples_text = ""
        if self.positive_examples:
            examples_text += "\n正面例子（高分参考）：\n"
            for ex in self.positive_examples:
                examples_text += f"  - {ex['work']} ({ex['score']}分): {ex['reason']}\n"
        if self.negative_examples:
            examples_text += "\n反面例子（低分参考）：\n"
            for ex in self.negative_examples:
                examples_text += f"  - {ex['work']} ({ex['score']}分): {ex['reason']}\n"

        # 构建文本样本
        samples_text = ""
        for i, sample in enumerate(samples):
            samples_text += f"\n--- 样本 {i+1} ({sample.position}) ---\n{sample.text}\n"

        return f"""## 评估维度：{self.dim_name} ({self.dim_name_en})

### 维度定义
{self.definition}

### 评分标准
{scoring_text}

### 边界案例规则
{borderline_text}

{examples_text}

---

## 文本样本
{samples_text}

---

## 评估要求

请按以下步骤进行评估：

1. **通读文本**：完整阅读提供的文本片段。
2. **寻找证据**：在文本中寻找与该维度相关的具体证据。每个证据必须引用原文（50-100字）。
3. **对照标准**：将观察到的证据与评分标准逐条对照。
4. **确定分数**：基于证据和标准，确定最终分数。
5. **输出评分**：按以下 JSON 格式输出。

```json
{{
    "dimension": "{self.dim_id}_{self.dim_name}",
    "score": <1-10的整数>,
    "score_range": "<分数段描述>",
    "evidence": [
        {{
            "location": "<文本位置描述>",
            "text_excerpt": "<引用原文50-100字>",
            "analysis": "<这段文本如何支持你的判断>"
        }}
    ],
    "reasoning": "<从证据到分数的完整推理过程>",
    "borderline_notes": "<如果在两个分数之间，说明选择的理由>",
    "improvement_suggestions": "<如果分数较低，指出具体的改进方向>"
}}
```"""


class DimensionJudge:
    """维度评估器"""

    def __init__(self, rubric_path: Path):
        self.rubric = Rubric(rubric_path)

    def evaluate(self, samples: List[TextSample]) -> DimensionResult:
        """
        评估一个维度。
        
        Args:
            samples: 文本样本列表
        
        Returns:
            DimensionResult
        """
        system_prompt = self.rubric.build_system_prompt()
        user_prompt = self.rubric.build_user_prompt(samples)

        logger.info(
            f"Evaluating {self.rubric.dim_name} with {len(samples)} samples..."
        )

        result_json = llm_client.chat_json(system_prompt, user_prompt)

        # 解析证据
        evidence_list = []
        for ev in result_json.get("evidence", []):
            evidence_list.append(Evidence(
                location=ev.get("location", ""),
                text_excerpt=ev.get("text_excerpt", ""),
                analysis=ev.get("analysis", ""),
            ))

        return DimensionResult(
            dimension=result_json.get(
                "dimension",
                f"{self.rubric.dim_id}_{self.rubric.dim_name}",
            ),
            score=result_json.get("score", 0),
            score_range=result_json.get("score_range", ""),
            evidence=evidence_list,
            reasoning=result_json.get("reasoning", ""),
            borderline_notes=result_json.get("borderline_notes", ""),
            improvement_suggestions=result_json.get("improvement_suggestions", ""),
        )
