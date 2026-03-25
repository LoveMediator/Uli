"""Judge service 单元测试。"""

from types import SimpleNamespace

from app.services import judge_service


def test_generate_judge_result_single_snapshot(monkeypatch):
    snapshot_a = SimpleNamespace(summary="A的描述是关于沟通问题")
    result_obj = SimpleNamespace(
        public_id="jr_1", objective_summary="mock",
        triggers=["t1"], model_name="mock-judge-v1",
    )
    monkeypatch.setattr(
        judge_service.judge_repo, "create_judge_result",
        lambda *_a, **_kw: result_obj,
    )

    class _DB:
        def add(self, _obj):
            pass
        def flush(self):
            pass

    result = judge_service.generate_judge_result(
        _DB(), event_id=1, snapshot_a=snapshot_a,
    )
    assert result.public_id == "jr_1"


def test_generate_judge_result_with_both_snapshots(monkeypatch):
    snapshot_a = SimpleNamespace(summary="A的描述")
    snapshot_b = SimpleNamespace(summary="B的描述")
    result_obj = SimpleNamespace(public_id="jr_2", objective_summary="dual mock")

    monkeypatch.setattr(
        judge_service.judge_repo, "create_judge_result",
        lambda *_a, **_kw: result_obj,
    )

    class _DB:
        def add(self, _obj):
            pass
        def flush(self):
            pass

    result = judge_service.generate_judge_result(
        _DB(), event_id=1, snapshot_a=snapshot_a, snapshot_b=snapshot_b,
    )
    assert result.public_id == "jr_2"
