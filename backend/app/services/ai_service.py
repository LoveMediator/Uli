"""AI 服务层占位。

当前为 mock 实现，后续替换为真实 LLM 调用。
所有需要 LLM 的场景（judge / followup / elf）统一通过本模块入口。
"""


def call_llm(*, prompt: str, model_name: str = "mock-v1") -> dict:
    """调用 LLM（当前 mock）。后续替换为真实 API 调用。"""
    return {
        "model_name": model_name,
        "input_tokens": 0,
        "output_tokens": 0,
        "content": f"[MOCK] AI response for prompt length={len(prompt)}",
    }
