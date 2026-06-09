"""
测试脚本：验证评估 Pipeline 的核心功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluators.pipeline import Pipeline


# 测试用短文本（模拟一个简单的故事片段）
TEST_TEXT = """
第一章 墙内的世界

艾伦从来没有见过墙外的世界。

"妈妈，墙外面是什么？"年幼的艾伦拉着母亲的衣角问道。

母亲蹲下身，轻轻抚摸他的头发："墙外面...是大海，艾伦。无边无际的大海。"

"我想去看大海！"艾伦的眼睛闪闪发光。

母亲的笑容突然凝固了。她望向窗外那堵高耸入墙，眼中闪过一丝恐惧。

"艾伦，答应妈妈，永远不要去墙外面。"

"为什么？"

"因为..."母亲的声音低了下去，"因为墙外面有巨人。"

那是107年前的事了。准确地说，是人类被巨人驱赶，退缩到三道高墙之内的第107年。

玛利亚、罗塞、希娜——三道同心圆的墙壁保护着人类最后的栖息地。墙内的人们过着平静的生活，仿佛外面的世界从未存在过。

但艾伦从未忘记母亲的话。

不是"不要去墙外面"——而是"墙外面有巨人"。

这两句话之间的区别，改变了他的一生。

第二章 破碎的和平

845年，那一天，天空仿佛被撕裂了。

一只巨大的手掌——比城墙还要高的手掌——缓缓地搭在了玛利亚之墙上。

城墙在颤抖。

人们抬起头，看到了一张脸。一张没有表情的、巨大的人脸，从墙的另一边探了进来。

"巨...巨人？"

恐慌像瘟疫一样蔓延。人们开始奔跑，尖叫，互相踩踏。

艾伦站在原地，仰望着那个巨大的身影。

他的母亲——

"不！！！"

他看到一只巨手伸向了他们的家。母亲正在房子里，还有断了腿无法逃跑的祖母。

"妈妈！！！"

巨手掀开了屋顶。母亲抱着祖母，试图逃跑。但一切都太晚了。

艾伦的眼睛里映着火光和血色。他的瞳孔收缩，呼吸停止。

从那一刻起，他的心中只剩下一个念头：

"我要杀光所有巨人。"

第三章 调查兵团

五年后。

"你确定？"教官基斯·夏迪斯盯着眼前的少年。

"确定。"艾伦的回答没有一丝犹豫。

"加入训练兵团，意味着你要面对死亡。你可能被巨人吃掉，就像你母亲一样。"

"我知道。"

"你不怕？"

"怕。"艾伦说，"但我更怕的是——一辈子躲在墙里，像牲畜一样活着。"

基斯教官看着这个少年的眼睛，看到了某种让他不安的东西。不是勇气，不是鲁莽——而是一种近乎偏执的决心。

"好吧。"他说，"欢迎加入第104期训练兵团。"

在训练兵团里，艾伦遇到了改变他一生的两个人。

第一个是三笠·阿克曼。他的青梅竹马，总是沉默寡言，却拥有惊人的战斗天赋。

第二个是阿尔敏·亚鲁雷特。他最好的朋友，体能平平，却有着非凡的智慧和对墙外世界的向往。

"阿尔敏，你为什么想加入训练兵团？"艾伦问。

阿尔敏望着远处的墙壁，眼中闪烁着光芒："因为...我想看看外面的世界。书上说过的——火焰之水、冰之大地、沙之雪原...我想亲眼看到那些。"

"那如果有一天，我们真的能去墙外呢？"

"那我会...我会觉得自己终于自由了。"

艾伦笑了："阿尔敏，你的眼睛，和那天看到天空时一模一样。"

"什么？"

"就是...充满好奇心的眼睛。"艾伦说，"我妈妈说过，能对世界充满好奇的人，是最了不起的。"

这一刻，三个少年不会知道，命运为他们准备了怎样的未来。
"""


def test_single_dimension():
    """测试单维度评估"""
    print("=" * 60)
    print("测试: 单维度评估 (D1 信息流管理)")
    print("=" * 60)

    pipeline = Pipeline()
    result = pipeline.evaluate_single(TEST_TEXT, "D1", title="测试作品")

    print(f"\n维度: {result.dimension}")
    print(f"分数: {result.score}/10")
    print(f"分数段: {result.score_range}")
    print(f"\n推理: {result.reasoning}")
    print(f"\n证据 ({len(result.evidence)} 条):")
    for i, ev in enumerate(result.evidence):
        print(f"  [{i+1}] {ev.location}")
        print(f"      文本: {ev.text_excerpt[:80]}...")
        print(f"      分析: {ev.analysis}")
    if result.borderline_notes:
        print(f"\n边界案例: {result.borderline_notes}")
    if result.improvement_suggestions:
        print(f"\n改进建议: {result.improvement_suggestions}")


def test_full_evaluation():
    """测试完整评估（仅 D1 和 D2，避免太慢）"""
    print("\n" + "=" * 60)
    print("测试: 双维度评估 (D1 + D2)")
    print("=" * 60)

    pipeline = Pipeline()
    report = pipeline.evaluate(
        TEST_TEXT,
        title="测试作品",
        dimensions=["D1", "D2"],
    )

    print(f"\n{report.summary}")
    print(f"\n报告已保存。")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WebNovelBench 测试")
    parser.add_argument(
        "--mode",
        choices=["single", "full"],
        default="single",
        help="测试模式: single=单维度, full=双维度",
    )
    args = parser.parse_args()

    if args.mode == "single":
        test_single_dimension()
    else:
        test_full_evaluation()
