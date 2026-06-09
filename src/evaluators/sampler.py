"""
文本采样器
从长篇小说中提取有代表性的片段
"""
import re
from dataclasses import dataclass
from typing import List, Tuple

from src.config import config


@dataclass
class TextSample:
    """一个文本样本"""
    position: str       # 位置描述（如"开头第3段"、"50%处"）
    text: str           # 文本内容
    char_offset: int    # 在原文中的字符偏移量


class TextSampler:
    """文本采样器"""

    def __init__(self):
        self.cfg = config.sampler

    def sample(self, text: str, strategy: str, **kwargs) -> List[TextSample]:
        """
        根据策略采样文本。
        
        Args:
            text: 完整文本
            strategy: 采样策略 ("dispersed" | "key_nodes" | "continuous")
            **kwargs: 策略特定参数
        
        Returns:
            TextSample 列表
        """
        if strategy == "dispersed":
            return self._dispersed_sample(
                text,
                chunk_size=kwargs.get("chunk_size", self.cfg.default_chunk_size),
                num_chunks=kwargs.get("num_chunks", self.cfg.default_num_chunks),
            )
        elif strategy == "key_nodes":
            return self._key_nodes_sample(
                text,
                chunk_size=kwargs.get("chunk_size", self.cfg.default_chunk_size),
            )
        elif strategy == "continuous":
            return self._continuous_sample(
                text,
                start_pct=kwargs.get("start_pct", 0.5),
                num_chapters=kwargs.get("num_chapters", 3),
                chunk_size=kwargs.get("chunk_size", self.cfg.default_chunk_size),
            )
        else:
            raise ValueError(f"Unknown sampling strategy: {strategy}")

    def _dispersed_sample(
        self, text: str, chunk_size: int, num_chunks: int
    ) -> List[TextSample]:
        """
        分散采样：均匀分布在文本中的片段。
        适用于：世界观构建、文化质感、信息流管理
        """
        if len(text) <= chunk_size:
            return [TextSample(position="全文", text=text, char_offset=0)]

        # 计算每个片段的起始位置
        total_len = len(text)
        step = total_len // (num_chunks + 1)
        
        samples = []
        for i in range(num_chunks):
            start = step * (i + 1)
            end = min(start + chunk_size, total_len)
            pct = int(start / total_len * 100)
            samples.append(TextSample(
                position=f"{pct}%处",
                text=text[start:end],
                char_offset=start,
            ))
        
        return samples

    def _key_nodes_sample(
        self, text: str, chunk_size: int
    ) -> List[TextSample]:
        """
        关键节点采样：提取开头、结尾和重大转折点。
        适用于：角色弧光、主题共振、反转评估
        """
        chapters = self._split_chapters(text)
        
        if len(chapters) <= 10:
            # 章节太少，直接取开头和结尾
            return [
                TextSample(position="开头", text=text[:chunk_size], char_offset=0),
                TextSample(
                    position="结尾",
                    text=text[-chunk_size:],
                    char_offset=max(0, len(text) - chunk_size),
                ),
            ]

        total_chapters = len(chapters)
        # 取：前5章 + 25%处 + 50%处 + 75%处 + 后5章
        key_indices = (
            list(range(5))
            + [total_chapters // 4, total_chapters // 2, 3 * total_chapters // 4]
            + list(range(total_chapters - 5, total_chapters))
        )
        # 去重并排序
        key_indices = sorted(set(i for i in key_indices if 0 <= i < total_chapters))

        samples = []
        offset = 0
        for i, (ch_title, ch_text) in enumerate(chapters):
            if i in key_indices:
                # 取每章的前 chunk_size 字符
                excerpt = ch_text[:chunk_size]
                pct = int(i / total_chapters * 100)
                samples.append(TextSample(
                    position=f"第{i+1}章({pct}%)",
                    text=excerpt,
                    char_offset=offset,
                ))
            offset += len(ch_title) + len(ch_text)
        
        return samples

    def _continuous_sample(
        self, text: str, start_pct: float, num_chapters: int, chunk_size: int
    ) -> List[TextSample]:
        """
        连续章节采样：从指定位置取连续N章。
        适用于：节奏分析、展示艺术、冲突设计
        """
        chapters = self._split_chapters(text)
        
        if not chapters:
            # 无法分章节，取连续片段
            start = int(len(text) * start_pct)
            end = min(start + chunk_size * num_chapters, len(text))
            return [TextSample(
                position=f"{int(start_pct*100)}%处连续片段",
                text=text[start:end],
                char_offset=start,
            )]

        total_chapters = len(chapters)
        start_idx = int(total_chapters * start_pct)
        end_idx = min(start_idx + num_chapters, total_chapters)

        samples = []
        offset = 0
        for i, (ch_title, ch_text) in enumerate(chapters):
            if start_idx <= i < end_idx:
                excerpt = ch_text[:chunk_size]
                samples.append(TextSample(
                    position=f"第{i+1}章(连续)",
                    text=excerpt,
                    char_offset=offset,
                ))
            offset += len(ch_title) + len(ch_text)

        return samples

    @staticmethod
    def _split_chapters(text: str) -> List[Tuple[str, str]]:
        """
        按章节标题分割文本。
        返回 [(标题行, 章节内容), ...]
        """
        pattern = config.sampler.chapter_pattern
        # 找到所有章节标题的位置
        matches = list(re.finditer(pattern, text))
        
        if not matches:
            return []

        chapters = []
        for i, match in enumerate(matches):
            title = match.group(0)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end]
            chapters.append((title, content))

        return chapters


# 全局采样器实例
sampler = TextSampler()
