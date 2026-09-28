"""Read-only display health, independent of the motion safety state machine."""
import math
import time

ARMS = ("front-left", "front-right", "mid", "rear-left", "rear-right")
def result(code, phase="warning", raw=""):
    return dict(code=code, phase=phase, detail=raw)

class DeviceHealth:
    def __init__(self):
        self.rear_modes = {}
        self.rear_exited = {}

    def evaluate(self, systems, snapshot, *, home_started=0, now=None):
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
                values[front]=result("pair",raw=values[rear]["detail"])
        mode = snapshot.get("handover_mode") or ""
        for side in ("left", "right"):
            front, rear = "front-" + side, "rear-" + side
            hardware_teach = feedback.get(rear, {}).get("rear_mode") == "teaching"
            teach = snapshot.get("teach_" + side) is True
            if not hardware_teach and not teach:
                continue
            routed = mode.startswith("manual:") and side in mode.split(":", 1)[1].split("+")
            keys = ("rear_" + side, "front_" + side, "coordinator_" + side, "teach_" + side)
            fresh = all(snapshot.is_fresh(key) for key in keys)
            tracking = False
            if fresh:
                actual = snapshot.get("front_" + side)["position"]
                command = snapshot.get("coordinator_" + side)["position"]
                tracking = len(actual) >= 6 and len(command) >= 6 and all(math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a)-float(b)) < .15
                               for a, b in zip(actual[:6], command[:6]))
            synchronized = hardware_teach and teach and routed and fresh and tracking and all(values[n]["phase"] == "ready" for n in (front,rear))
            for name in (front, rear):
                if values[name]["phase"] == "ready":
                    values[name] = result("teaching" if synchronized else "sync", "teaching" if synchronized else "warning",
                                          feedback.get(name, {}).get("detail", ""))
        for side in ("left", "right"):
            gripper = feedback.get("front-" + side, {}).get("gripper", {})
            values["gripper-" + side] = (result("gripper", raw=gripper.get("detail", "")) if gripper.get("error_bits")
                                        else dict(values["front-" + side]))
        return values
