#!/usr/bin/env python3
"""
WebNovelBench CLI
中文网文质量评估工具

用法：
  python -m src.cli evaluate <text_file> [--title TITLE] [--dims D1,D2,...]
  python -m src.cli evaluate <text_file> --dims D1 --title "测试作品"
  python -m src.cli list-dimensions
"""
import argparse
import json
import logging
import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.evaluators.pipeline import Pipeline


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_evaluate(args):
    """执行评估"""
    text_path = Path(args.text_file)
    if not text_path.exists():
        print(f"错误: 文件不存在: {text_path}")
        sys.exit(1)

    text = text_path.read_text(encoding="utf-8")
    title = args.title or text_path.stem

    dimensions = None
    if args.dims:
        dimensions = [d.strip() for d in args.dims.split(",")]

    pipeline = Pipeline()

    if dimensions and len(dimensions) == 1:
        # 单维度评估
        result = pipeline.evaluate_single(text, dimensions[0], title)
        _print_single_result(result)
        # 保存结果
        output_path = config.output_dir / f"{title}_{dimensions[0]}.json"
        _save_single_result(result, output_path)
    else:
        # 多维度/全维度评估
        report = pipeline.evaluate(text, title, dimensions)
        _print_report(report)
        # 保存报告
        output_path = pipeline.save_report(report)
        print(f"\n报告已保存: {output_path}")


def cmd_list_dimensions(args):
    """列出所有评估维度"""
    rubrics_dir = config.rubrics_dir
    print("WebNovelBench 评估维度:\n")
    print(f"{'ID':<5} {'名称':<12} {'英文名':<25} {'采样策略':<12}")
    print("-" * 60)

    import yaml
    for yaml_file in sorted(rubrics_dir.glob("D*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        dim = data["dimension"]
        sampling = data.get("sampling", {})
        print(
            f"{dim['id']:<5} {dim['name']:<12} {dim['name_en']:<25} "
            f"{sampling.get('strategy', 'N/A'):<12}"
        )

    print(f"\n共 {len(list(rubrics_dir.glob('D*.yaml')))} 个维度")


def _print_single_result(result):
    """打印单维度评估结果"""
    print(f"\n{'='*60}")
    print(f"维度: {result.dimension}")
    print(f"分数: {result.score}/10")
    print(f"分数段: {result.score_range}")
    print(f"{'='*60}")

    if result.evidence:
        print(f"\n证据 ({len(result.evidence)} 条):")
        for i, ev in enumerate(result.evidence):
            print(f"\n  [{i+1}] {ev.location}")
            print(f"      文本: {ev.text_excerpt[:100]}...")
            print(f"      分析: {ev.analysis}")

    print(f"\n推理: {result.reasoning}")

    if result.borderline_notes:
        print(f"\n边界案例: {result.borderline_notes}")
    if result.improvement_suggestions:
        print(f"\n改进建议: {result.improvement_suggestions}")


def _print_report(report):
    """打印完整评估报告"""
    print(f"\n{'='*60}")
    print(f"作品: {report.title}")
    print(f"时间: {report.timestamp}")
    print(f"综合评分: {report.overall_score}/10")
    print(f"{'='*60}")

    # 面层评分
    layer_scores = {}
    for dim_id, result in report.dimensions.items():
        layer = Pipeline.DIMENSION_LAYERS.get(dim_id, "A")
        if layer not in layer_scores:
            layer_scores[layer] = []
        layer_scores[layer].append(result.score)

    print(f"\n面层评分:")
    for layer in sorted(layer_scores.keys()):
        scores = layer_scores[layer]
        avg = sum(scores) / len(scores)
        layer_name = Pipeline.LAYER_NAMES.get(layer, layer)
        bar = "█" * int(round(avg)) + "░" * (10 - int(round(avg)))
        print(f"  {layer_name}({layer}): {bar} {avg:.1f}/10")

    print(f"\n各维度评分:")
    for dim_id, result in sorted(report.dimensions.items()):
        bar = "█" * result.score + "░" * (10 - result.score)
        print(f"  {result.dimension:<20} {bar} {result.score}/10")

    print(f"\n{report.summary}")


def _save_single_result(result, output_path):
    """保存单维度评估结果"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
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
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="WebNovelBench - 中文网文质量评估",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.cli evaluate novel.txt --title "诡秘之主"
  python -m src.cli evaluate novel.txt --dims D1,D2,D3
  python -m src.cli list-dimensions
        """,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # evaluate 子命令
    eval_parser = subparsers.add_parser("evaluate", help="评估一部作品")
    eval_parser.add_argument("text_file", help="文本文件路径")
    eval_parser.add_argument("--title", help="作品标题")
    eval_parser.add_argument(
        "--dims",
        help="要评估的维度（逗号分隔，如 D1,D2,D3）。默认全部。",
    )

    # list-dimensions 子命令
    subparsers.add_parser("list-dimensions", help="列出所有评估维度")

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "list-dimensions":
        cmd_list_dimensions(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
