"""Subscribe and read CAN only. No publishers, services or motor commands."""
import threading
import time
from .device_control import _default_system_probe, _CAN_TX_MONITOR, _CAN_BUSES
from .device_health import DeviceHealth
from .ros_topics import REQUIRED_TOPICS, CAMERA_KEYS, freshness_window_seconds

class Snapshot:
    def __init__(self, values, now):
        self.values, self.now = values, now
    def get(self, key):
        return self.values.get(key, (None, 0))[0]
    def has_value(self, key):
        return key in self.values
    def is_fresh(self, key):
        return key in self.values and 0 <= self.now - self.values[key][1] <= freshness_window_seconds(key)

def observe(seconds=1.5):
    if not .5 <= seconds <= 10:
        raise ValueError("seconds must be between 0.5 and 10")
    import rospy
    from sensor_msgs.msg import JointState
    from std_msgs.msg import Bool, String
    rospy.init_node("cobot_control_passive_health", anonymous=True, disable_signals=True)
    values, subscriptions, lock = {}, [], threading.Lock()
    def callback(key):
        def accept(message):
            value = {"position": list(message.position)} if hasattr(message, "position") else message.data
            with lock:
                values[key] = (value, time.monotonic())
        return accept
    try:
        for key, topic in REQUIRED_TOPICS.items():
            if key in CAMERA_KEYS:
                continue
            kind = Bool if key.startswith("teach_") else String if key.startswith("handover_") else JointState
            subscriptions.append(rospy.Subscriber(topic, kind, callback(key), queue_size=1))
        _CAN_TX_MONITOR.sample(tuple(_CAN_BUSES.values()))
        time.sleep(max(seconds, 1.05))
        systems = _default_system_probe()
        with lock:
            snapshot = Snapshot(dict(values), time.monotonic())
        return {"systems": systems, "health": DeviceHealth().evaluate(systems, snapshot)}
    finally:
        for subscriber in subscriptions:
            subscriber.unregister()
        rospy.signal_shutdown("Passive observation complete")
