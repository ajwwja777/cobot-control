from cobot_control.can_health import CanTxMonitor


def test_backlogged_queue_needs_sustained_no_progress_not_historical_drops():
    now = [0]
    state = dict(ifindex=3, tx_packets=20, queued=10, drops=50000)
    monitor = CanTxMonitor(lambda buses: {"can_left": dict(state)}, lambda: now[0])
    def sample(): return monitor.sample(["can_left"])["can_left"]
    assert sample()["phase"] == "checking"
    now[0] = .9
    assert sample()["phase"] == "checking"
    now[0] = 1.1
    assert sample()["phase"] == "error"
    state["tx_packets"] += 1
    assert sample()["phase"] == "checking"
    state["queued"] = 0
    now[0] = 4
    assert sample()["phase"] == "ready"
    state["queued"] = 10
    assert sample()["phase"] == "checking"


def test_disconnect_reenumeration_or_missing_tc_does_not_reuse_old_stall():
    now = [0]
    state = dict(ifindex=3, tx_packets=20, queued=10, drops=1)
    monitor = CanTxMonitor(lambda buses: {"can_left": dict(state)}, lambda: now[0])
    monitor.sample(["can_left"])
    now[0] = 2
    assert monitor.sample(["can_left"])["can_left"]["phase"] == "error"
    state["ifindex"] = 4
    assert monitor.sample(["can_left"])["can_left"]["phase"] == "checking"
    monitor.reader = lambda buses: {}
    assert monitor.sample(["can_left"])["can_left"]["phase"] == "unknown"
    def fail(buses): raise FileNotFoundError("tc")
    monitor.reader = fail
    assert monitor.sample(["can_left"])["can_left"]["phase"] == "unknown"
    assert not monitor.previous


def test_probe_only_uses_passive_tc_and_sysfs(tmp_path, monkeypatch):
    from cobot_control import can_health as module
    root = tmp_path / "can_left"
    (root / "statistics").mkdir(parents=True)
    (root / "statistics/tx_packets").write_text("55")
    (root / "ifindex").write_text("3")
    monkeypatch.setattr(module, "Path", lambda path: tmp_path)
    calls = []
    def read(args, **kwargs):
        calls.append(args)
        return '[{"dev":"can_left","root":true,"qlen":10,"drops":77}]'
    monkeypatch.setattr(module.subprocess, "check_output", read)
    assert module.read_queues(["can_left"])["can_left"] == dict(ifindex=3, tx_packets=55, queued=10, drops=77)
    assert calls == [["tc", "-s", "-j", "qdisc", "show"]]
