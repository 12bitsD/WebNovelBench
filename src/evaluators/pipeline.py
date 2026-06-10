"""
评估 Pipeline
协调采样、评估、聚合的完整流程
"""
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.config import config
from src.evaluators.sampler import sampler
from src.judges.dimension_judge import DimensionJudge, DimensionResult

logger = logging.getLogger(__name__)


@dataclass
class EvaluationReport:
    """评估报告"""
    title: str
    timestamp: str
    dimensions: Dict[str, DimensionResult]
    overall_score: float
    summary: str


class Pipeline:
    """评估 Pipeline"""

    # 所有维度的 rubric 文件映射
    DIMENSION_RUBRICS = {
        "D1": "D1_information_flow.yaml",
        "D2": "D2_character_arc.yaml",
        "D3": "D3_world_building.yaml",
        "D4": "D4_theme.yaml",
        "D5": "D5_structure_tension.yaml",
        "D6": "D6_reversal.yaml",
        "D7": "D7_show_dont_tell.yaml",
        "D8": "D8_conflict.yaml",
        "D9": "D9_cultural_texture.yaml",
        "D10": "D10_satisfaction.yaml",
    }

    # 维度权重（总计1.0）
    # 基于 vision.md 的设计：结构30% + 角色25% + 技艺25% + 灵魂20%
    DIMENSION_WEIGHTS = {
        "D1": 0.10,   # 信息流管理（结构）
        "D2": 0.12,   # 角色弧光（角色）
        "D3": 0.10,   # 世界观构建（结构）
        "D4": 0.10,   # 主题共振（灵魂）
        "D5": 0.08,   # 结构张力（结构）
        "D6": 0.08,   # 颠覆与反转（技艺）
        "D7": 0.07,   # 展示艺术（技艺）
        "D8": 0.08,   # 冲突设计（技艺）
        "D9": 0.07,   # 文化质感（灵魂）
        "D10": 0.10,  # 爽点工艺（角色）
    }

    # 面层分类
    LAYER_NAMES = {
        "A": "结构工程",
        "B": "角色生态",
        "C": "叙事技艺",
        "D": "灵魂深度",
    }
    DIMENSION_LAYERS = {
        "D1": "A", "D3": "A", "D5": "A",
        "D2": "B", "D10": "B",
        "D6": "C", "D7": "C", "D8": "C",
        "D4": "D", "D9": "D",
    }

    def evaluate(
        self,
        text: str,
        title: str = "未命名作品",
        dimensions: Optional[List[str]] = None,
    ) -> EvaluationReport:
        """
        评估一部作品。
        
        Args:
            text: 作品全文
            title: 作品标题
            dimensions: 要评估的维度列表（默认全部）
        
        Returns:
            EvaluationReport
        """
        if dimensions is None:
            dimensions = list(self.DIMENSION_RUBRICS.keys())

        results = {}
        for dim_id in dimensions:
            rubric_file = self.DIMENSION_RUBRICS.get(dim_id)
            if not rubric_file:
                logger.warning(f"Unknown dimension: {dim_id}")
                continue

            rubric_path = config.rubrics_dir / rubric_file
            if not rubric_path.exists():
                logger.warning(f"Rubric file not found: {rubric_path}")
                continue

            logger.info(f"=== Evaluating {dim_id} ===")
            judge = DimensionJudge(rubric_path)

            # 根据 rubric 配置采样
            rubric = judge.rubric
            sampling_cfg = rubric.sampling_config
            strategy = sampling_cfg.get("strategy", "dispersed")

            samples = sampler.sample(
                text,
                strategy=strategy,
                chunk_size=sampling_cfg.get("chunk_size", config.sampler.default_chunk_size),
                num_chunks=sampling_cfg.get("num_chunks", config.sampler.default_num_chunks),
            )

            logger.info(f"Sampled {len(samples)} chunks for {dim_id}")

            # 评估
            result = judge.evaluate(samples)
            results[dim_id] = result
            logger.info(f"{dim_id}: {result.score}/10 - {result.score_range}")

        # 计算加权总分
        weighted_sum = 0.0
        weight_sum = 0.0
        for dim_id, result in results.items():
            w = self.DIMENSION_WEIGHTS.get(dim_id, 0.1)
            weighted_sum += result.score * w
            weight_sum += w
        overall = weighted_sum / weight_sum if weight_sum > 0 else 0.0

        # 计算面层分数
        layer_scores = {}
        for dim_id, result in results.items():
            layer = self.DIMENSION_LAYERS.get(dim_id, "A")
            if layer not in layer_scores:
                layer_scores[layer] = []
            layer_scores[layer].append(result.score)
        layer_averages = {
            layer: sum(scores) / len(scores)
            for layer, scores in layer_scores.items()
        }

        # 生成摘要
        summary = self._generate_summary(results, overall, layer_averages)

        report = EvaluationReport(
            title=title,
            timestamp=datetime.now().isoformat(),
            dimensions=results,
            overall_score=round(overall, 2),
            summary=summary,
        )

        return report

    def evaluate_single(
        self, text: str, dimension: str, title: str = "未命名作品"
    ) -> DimensionResult:
        """
        评估单个维度（用于测试和调试）。
        """
        rubric_file = self.DIMENSION_RUBRICS.get(dimension)
        if not rubric_file:
            raise ValueError(f"Unknown dimension: {dimension}")

        rubric_path = config.rubrics_dir / rubric_file
        judge = DimensionJudge(rubric_path)
        rubric = judge.rubric
        sampling_cfg = rubric.sampling_config

        samples = sampler.sample(
            text,
            strategy=sampling_cfg.get("strategy", "dispersed"),
            chunk_size=sampling_cfg.get("chunk_size", config.sampler.default_chunk_size),
            num_chunks=sampling_cfg.get("num_chunks", config.sampler.default_num_chunks),
        )

        return judge.evaluate(samples)

    def _generate_summary(
        self, results: Dict[str, DimensionResult], overall: float,
        layer_averages: Optional[Dict[str, float]] = None,
    ) -> str:
        """生成评估摘要"""
        lines = [f"综合评分: {overall:.1f}/10\n"]

        if layer_averages:
            lines.append("面层评分:")
            for layer, avg in sorted(layer_averages.items()):
                layer_name = self.LAYER_NAMES.get(layer, layer)
                bar = "█" * int(round(avg)) + "░" * (10 - int(round(avg)))
                lines.append(f"  {layer_name}({layer}): {bar} {avg:.1f}/10")
            lines.append("")

        lines.append("各维度评分:")
        for dim_id, result in sorted(results.items()):
            lines.append(f"  {result.dimension}: {result.score}/10")
        return "\n".join(lines)

    @staticmethod
    def save_report(report: EvaluationReport, output_path: Optional[Path] = None):
        """保存评估报告"""
        if output_path is None:
            output_path = (
                config.output_dir
                / f"{report.title}_{report.timestamp.replace(':', '-')}.json"
            )

        report_data = {
            "title": report.title,
            "timestamp": report.timestamp,
            "overall_score": report.overall_score,
            "summary": report.summary,
            "layer_scores": {},
            "dimensions": {},
        }

        # 计算面层分数
        layer_scores = {}
        for dim_id, result in report.dimensions.items():
            layer = Pipeline.DIMENSION_LAYERS.get(dim_id, "A")
            if layer not in layer_scores:
                layer_scores[layer] = []
            layer_scores[layer].append(result.score)
        report_data["layer_scores"] = {
            Pipeline.LAYER_NAMES.get(layer, layer): round(sum(scores) / len(scores), 2)
            for layer, scores in layer_scores.items()
        }

        for dim_id, result in report.dimensions.items():
            report_data["dimensions"][dim_id] = {
                "dimension": result.dimension,
                "score": result.score,
                "score_range": result.score_range,
                "evidence": [
                    {
                        "location": ev.location,
                        "text_excerpt": ev.text_excerpt,
                        "analysis": ev.analysis,
                    }
                    for ev in result.evidence
                ],
                "reasoning": result.reasoning,
                "borderline_notes": result.borderline_notes,
                "improvement_suggestions": result.improvement_suggestions,
            }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Report saved to {output_path}")
        return output_path
