import os
import signal
import subprocess
import sys
from pathlib import Path
import pytest
from cobot_control.device_control import DeviceController, DeviceControlError, _matches_process_marker
from cobot_control.processes import process_identity

def test_identical_basename_in_another_workspace_is_not_owned():
    marker = "/project/control/integrations/legacy_control/launch/multi_camera_shuai.launch"
    assert _matches_process_marker("roslaunch " + marker, marker)
    assert not _matches_process_marker("roslaunch /other/multi_camera_shuai.launch", marker)

def test_terminal_adopts_and_stops_http_created_group_without_http(tmp_path):
    script = tmp_path / "sleeper.py"
    script.write_text("import time\ntime.sleep(60)\n")
    web = DeviceController(tmp_path / "jobs", system_probe=lambda: {"arms": {"phase": "ready"}})
    web.stop_markers = dict(web.stop_markers, arms=str(script))
    web._command = lambda spec: [sys.executable, str(script)]
    spec = {"component": "arms", "action": "start"}
    job = web.start(spec, web.confirm(spec)["confirmation_token"])
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True)
    try:
        terminal = DeviceController(tmp_path / "jobs", system_probe=lambda: {"arms": {"phase": "ready"}})
        terminal.stop_markers = web.stop_markers
        terminal._command = web._command
        adopted = terminal.start(spec, terminal.confirm(spec)["confirmation_token"])
        assert adopted["adopted"] and adopted["pid"] == job["pid"]
        assert adopted["start_ticks"] == process_identity(job["pid"])
        with pytest.raises(DeviceControlError):
            terminal.stop_job("arms", adopted["job_id"], job["pid"], adopted["start_ticks"] + 1)
        terminal.stop_job("arms", adopted["job_id"], job["pid"], adopted["start_ticks"])
        web._processes["arms"].wait(timeout=3)
        assert unrelated.poll() is None
    finally:
        for proc in [web._processes["arms"], unrelated]:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=3)

def test_read_only_status_does_not_launch(tmp_path):
    ctl = DeviceController(tmp_path, launcher=lambda *args: pytest.fail("launched"), system_probe=lambda: {})
    assert ctl.status()["jobs"] == {}
