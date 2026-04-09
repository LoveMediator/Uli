from types import SimpleNamespace

from app.core.config import settings
from app.services import judge_service


class _DB:
    def add(self, _obj):
        pass

    def flush(self):
        pass


def test_generate_judge_result_single_snapshot(monkeypatch):
    snapshot_a = SimpleNamespace(summary="A描述", points_a=["a1"], points_b=[])
    captured: dict[str, object] = {}
    result_obj = SimpleNamespace(
        public_id="jr_1",
        objective_summary="这是客观总结",
        triggers=["触发点1"],
        misunderstandings=["误解点1"],
        advice_for_a=["建议A"],
        advice_for_b=["建议B"],
        model_name=settings.kimi_text_model,
        input_tokens=10,
        output_tokens=20,
    )

    def _mock_call_llm_json(**kwargs):
        captured.update(kwargs)
        return {
            "data": judge_service.JudgeAiPayload(
                objective_summary="这是客观总结",
                triggers=["触发点1"],
                misunderstandings=["误解点1"],
                adviceForA=["建议A"],
                adviceForB=["建议B"],
            ),
            "model_name": settings.kimi_text_model,
            "input_tokens": 10,
            "output_tokens": 20,
        }

    monkeypatch.setattr(judge_service.ai_service, "call_llm_json", _mock_call_llm_json)
    monkeypatch.setattr(
        judge_service.judge_repo,
        "create_judge_result",
        lambda *_a, **_kw: result_obj,
    )

    result = judge_service.generate_judge_result(
        _DB(),
        event_id=1,
        snapshot_a=snapshot_a,
    )

    assert result.public_id == "jr_1"
    assert captured["model_name"] == settings.kimi_text_model
    assert "所有自然语言字段必须使用简体中文" in str(captured["prompt"])
    assert "你只能输出合法 JSON" in str(captured["system_prompt"])


def test_generate_judge_result_with_both_snapshots(monkeypatch):
    snapshot_a = SimpleNamespace(summary="A描述", points_a=["a1"], points_b=[])
    snapshot_b = SimpleNamespace(summary="B描述", points_a=[], points_b=["b1"])
    captured: dict[str, object] = {}
    result_obj = SimpleNamespace(
        public_id="jr_2",
        objective_summary="双边客观总结",
        triggers=["触发点1"],
        misunderstandings=["误解点1"],
        advice_for_a=["建议A"],
        advice_for_b=["建议B"],
        model_name=settings.kimi_text_model,
        input_tokens=10,
        output_tokens=20,
    )

    def _mock_call_llm_json(**kwargs):
        captured.update(kwargs)
        return {
            "data": judge_service.JudgeAiPayload(
                objective_summary="双边客观总结",
                triggers=["触发点1"],
                misunderstandings=["误解点1"],
                adviceForA=["建议A"],
                adviceForB=["建议B"],
            ),
            "model_name": settings.kimi_text_model,
            "input_tokens": 10,
            "output_tokens": 20,
        }

    monkeypatch.setattr(judge_service.ai_service, "call_llm_json", _mock_call_llm_json)
    monkeypatch.setattr(
        judge_service.judge_repo,
        "create_judge_result",
        lambda *_a, **_kw: result_obj,
    )

    result = judge_service.generate_judge_result(
        _DB(),
        event_id=1,
        snapshot_a=snapshot_a,
        snapshot_b=snapshot_b,
    )

    assert result.public_id == "jr_2"
    assert "B方摘要" in str(captured["prompt"])
