"""
LLM API 客户端
支持 OpenAI API 格式（兼容 OpenAI、Anthropic proxy、本地模型等）
"""
import json
import logging
import time
from typing import Optional

import httpx

from src.config import config

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM API 客户端"""

    def __init__(self):
        self.cfg = config.llm

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> str:
        """
        调用 LLM API，返回文本响应。
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词（包含文本样本和评估要求）
            max_retries: 最大重试次数
        
        Returns:
            LLM 的文本响应
        """
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.cfg.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.cfg.max_tokens,
            "temperature": self.cfg.temperature,
        }

        url = f"{self.cfg.base_url.rstrip('/')}/chat/completions"

        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return content
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait = 2 ** attempt * 5
                    logger.warning(f"Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt * 2
                    logger.warning(f"API error: {e}, retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                raise

        raise RuntimeError(f"Failed after {max_retries} retries")

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> dict:
        """
        调用 LLM API，解析 JSON 输出。
        如果 LLM 输出不是有效 JSON，尝试提取 JSON 块。
        """
        raw = self.chat(system_prompt, user_prompt, max_retries)
        return self._parse_json(raw)

    @staticmethod
    def _parse_json(text: str) -> dict:
        """从 LLM 输出中提取 JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 块
        import re
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取 { ... } 块
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse JSON from LLM output:\n{text[:500]}")


# 全局客户端实例
llm_client = LLMClient()
