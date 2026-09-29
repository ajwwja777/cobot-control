"""Read-only display health, independent of the motion safety state machine."""
import math
import time
import threading

ARMS = ("front-left", "front-right", "mid", "rear-left", "rear-right")
# Display confirmation only; these do not alter command routing or safety.
TEACH_ENTRY_SECONDS = 1.0
TRACKING_WARN_RAD = .15
TRACKING_CLEAR_RAD = .10
TRACKING_SEVERE_RAD = .50
TRACKING_CONFIRM_SECONDS = .8
SIGNAL_CONFIRM_SECONDS = .4
SYNC_RECOVERY_SECONDS = .5


class TeachDisplay:
    """Hysteresis for soft synchronization observations, never hardware faults."""
    def __init__(self, now):
        self.entered = now
        self.bad_since = None
        self.good_since = None
        self.warning = False
        self.confirmed = False

    def update(self, problem, now, live_feedback, urgent=False):
        if not problem:
            self.bad_since = None
            if self.good_since is None:
                self.good_since = now
            if self.warning and now-self.good_since < SYNC_RECOVERY_SECONDS:
                return "sync_recovering", "warning"
            self.warning = False
            self.confirmed = True
            return "teaching", "teaching"
        self.good_since = None
        if self.bad_since is None:
            self.bad_since = now
        # Incomplete/nonfinite joint values are not ordinary tracking lag.
        if urgent or problem in ("joints", "paired_health"):
            self.warning = True
        if self.warning:
            return "sync", "warning"
        if live_feedback and not self.confirmed and now-self.entered < TEACH_ENTRY_SECONDS:
            return "teach_transition", "teaching"
        delay = TRACKING_CONFIRM_SECONDS if problem == "tracking" else SIGNAL_CONFIRM_SECONDS
        if self.confirmed and now-self.bad_since < delay:
            return "teaching", "teaching"
        self.warning = True
        return "sync", "warning"

def result(code, phase="warning", raw=""):
    return dict(code=code, phase=phase, detail=raw)

class DeviceHealth:
    def __init__(self):
        self.rear_modes = {}
        self.rear_exited = {}
        self.teach_display = {}
        self._lock = threading.Lock()

    def evaluate(self, systems, snapshot, *, home_started=0, now=None):
        with self._lock:
            return self._evaluate(systems, snapshot, home_started=home_started, now=now)

    def _evaluate(self, systems, snapshot, *, home_started=0, now=None):
        display_now = time.monotonic() if now is None else now
        now = time.time() if now is None else now
        feedback = systems.get("arms_feedback", {})
        nodes = systems.get("arm_nodes", {})
        can = systems.get("can_interfaces", {})
        routes = systems.get("control_routes", {})
        values = {}
        for name in ARMS:
            arm = feedback.get(name, {})
            mode = arm.get("rear_mode")
            if name.startswith("rear-"):
                if self.rear_modes.get(name) == "teaching" and mode != "teaching":
                    self.rear_exited[name] = now
                if mode in ("teaching", "idle_disabled") or home_started > self.rear_exited.get(name, float("inf")):
                    self.rear_exited.pop(name, None)
                self.rear_modes[name] = mode
            raw = arm.get("detail", "")
            if not can.get(name, systems.get("can", {}).get("phase") == "ready"):
                value = result("can", raw=raw)
            elif not arm.get("fresh"):
                value = result("feedback", "offline", raw)
            elif systems.get("roscore", {}).get("phase") != "ready":
                value = result("ros", raw=raw)
            elif not nodes.get(name):
                value = result("node", raw=raw)
            elif arm.get("error_code") or arm.get("protected_joints") or arm.get("arm_status"):
                value = result("hardware", raw=raw)
            elif systems.get("can_tx", {}).get(name, {}).get("phase") == "error":
                value = result("can_tx", raw=raw+"; "+systems["can_tx"][name]["detail"])
            elif name.startswith("front-") or name == "mid":
                if arm.get("teach_status") or arm.get("ctrl_mode") == 2:
                    value = result("front_teach", raw=raw)
                elif arm.get("ctrl_mode") not in (0, 1):
                    value = result("mode", raw=raw)
                elif arm.get("enabled_joints") != 6:
                    value = result("disabled", raw=raw)
                elif name != "mid" and not routes.get(name.split("-")[1], {}).get("ready"):
                    value = result("route", raw=raw)
                elif name != "mid" and (not snapshot.has_value("handover_fault") or snapshot.get("handover_fault")):
                    value = result("handover", raw=raw + " " + str(snapshot.get("handover_fault") or ""))
                else:
                    value = result("ready", "ready", raw)
            elif mode in ("teaching", "can_holding") and arm.get("enabled_joints") != 6:
                value = result("disabled", raw=raw)
            elif name in self.rear_exited and now - self.rear_exited[name] > 1:
                value = result("rear_release", raw=raw)
            elif mode == "idle_disabled":
                value = result("idle", "ready", raw)
            elif mode in ("teaching", "can_holding"):
                value = result("ready", "ready", raw)
            else:
                value = result("rear_mode", raw=raw)
            values[name] = value
        for side in ("left","right"):
            front, rear = "front-"+side, "rear-"+side
            if values[front]["phase"]=="ready" and values[rear]["phase"] not in ("ready","teaching"):
                values[front]=dict(result("pair",raw=values[front]["detail"]),
                                   paired_arm=rear, paired_code=values[rear]["code"])
        mode = snapshot.get("handover_mode") or ""
        for side in ("left", "right"):
            front, rear = "front-" + side, "rear-" + side
            hardware_teach = feedback.get(rear, {}).get("rear_mode") == "teaching"
            teach = snapshot.get("teach_" + side) is True
            if not hardware_teach and not teach:
                self.teach_display.pop(side, None)
                continue
            display = self.teach_display.setdefault(side, TeachDisplay(display_now))
            routed = mode.startswith("manual:") and side in mode.split(":", 1)[1].split("+")
            # Mode/fault are latched, published only on state changes. Fresh
            # joint/command/button streams establish live teaching; do not age
            # out unchanged coordinator state as if it were a heartbeat.
            keys = ("rear_" + side, "front_" + side, "coordinator_" + side, "teach_" + side)
            stale = [key for key in keys if not snapshot.is_fresh(key)]
            problem, joint_error = "", None
            if not hardware_teach:
                problem = "teach_feedback"
            elif not teach:
                problem = "teach_button"
            elif stale:
                problem = "stale"
            elif not routed:
                problem = "routing"
            else:
                actual = snapshot.get("front_" + side)["position"]
                command = snapshot.get("coordinator_" + side)["position"]
                if len(actual) < 6 or len(command) < 6:
                    problem = "joints"
                else:
                    pairs = [(float(a), float(b)) for a,b in zip(actual[:6], command[:6])]
                    if not all(math.isfinite(a) and math.isfinite(b) for a,b in pairs):
                        problem = "joints"
                    else:
                        joint_error = max(abs(a-b) for a,b in pairs)
                        threshold = TRACKING_CLEAR_RAD if display.warning else TRACKING_WARN_RAD
                        if joint_error >= threshold:
                            problem = "tracking"
            pair_issue = next((name for name in (front,rear) if values[name]["phase"] != "ready"), None)
            if not problem and pair_issue:
                problem = "paired_health"
            # CAN/ROS loss, protection, disabled motors, wrong local teach
            # mode, ownership and TX stalls bypass display smoothing.
            if pair_issue:
                self.teach_display.pop(side, None)
                display_code, display_phase = "sync", "warning"
            else:
                live_feedback = all(snapshot.is_fresh(k) for k in
                                    ("rear_"+side, "front_"+side, "teach_"+side))
                urgent = joint_error is not None and joint_error >= TRACKING_SEVERE_RAD
                display_code, display_phase = display.update(problem, display_now, live_feedback, urgent)
            for name in (front, rear):
                if values[name]["phase"] == "ready":
                    values[name] = dict(
                        result(display_code, display_phase,
                               feedback.get(name, {}).get("detail", "")),
                        sync_issue=problem, sync_confirmed=not problem,
                        stale_topics=stale, handover_mode=mode,
                        max_joint_error=joint_error, paired_arm=pair_issue,
                        paired_code=values[pair_issue]["code"] if pair_issue else None)
        for side in ("left", "right"):
            gripper = feedback.get("front-" + side, {}).get("gripper", {})
            values["gripper-" + side] = (result("gripper", raw=gripper.get("detail", "")) if gripper.get("error_bits")
                                        else dict(values["front-" + side]))
        return values
