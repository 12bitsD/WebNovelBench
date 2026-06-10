"""
WebNovelBench 配置
"""
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LLMConfig:
    """LLM 提供商配置

    优先级：环境变量 > 代码默认值
    支持任何 OpenAI 兼容的 API（OpenAI、Xiaomi MiMo、Kimi、本地模型等）
    """
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "mimo-v2.5"
    max_tokens: int = 4096
    temperature: float = 0.1  # 低温度确保稳定输出

    def __post_init__(self):
        # 依次尝试多个环境变量
        if not self.api_key:
            self.api_key = (
                os.environ.get("OPENAI_API_KEY", "")
                or os.environ.get("XIAOMI_API_KEY", "")
                or os.environ.get("KIMI_API_KEY", "")
            )
        if base := os.environ.get("OPENAI_BASE_URL") or os.environ.get("XIAOMI_BASE_URL"):
            self.base_url = base
        if model := os.environ.get("MODEL_NAME"):
            self.model = model


@dataclass
class SamplerConfig:
    """文本采样配置"""
    default_chunk_size: int = 3000  # 每个片段的字符数
    default_num_chunks: int = 10    # 默认采样片段数
    chapter_pattern: str = r"第[一二三四五六七八九十百千\d]+[章回节卷]"  # 章节标题正则


@dataclass
class Config:
    """全局配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    sampler: SamplerConfig = field(default_factory=SamplerConfig)
    rubrics_dir: Path = Path(__file__).parent / "judges" / "rubrics"
    output_dir: Path = Path(__file__).parent.parent / "data" / "results"

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)


# 全局配置实例
config = Config()
