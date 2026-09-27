#!/usr/bin/env python3
"""一键把机械臂送回统一起点。

    task2_home_cli.py front            前双臂回起点（它们一直在 CAN 控制，不失能不掉落）
    task2_home_cli.py rear             后双臂回起点（从重力位使能 → 进 CAN → 静止 1.2s → 上去）
    task2_home_cli.py all              前双臂、左右后臂并行归位
    task2_home_cli.py capture          把当前实测位姿存成起点
    task2_home_cli.py show             打印当前配置和实测位姿的差值

    --pose <name>                      用别的命名位姿（默认 collect_start）
    --config <path>                    用别的配置文件

设计上的两点，改之前先读：

  · 位姿目标通过 ROS 参数传给节点，不是通过服务请求。std_srvs 里没有能装位姿
    的消息，自定义 srv 就得重新编译 piper 包。本脚本在调用服务之前把参数写好。

  · 真正动手臂的是两个节点，不是这个脚本。前臂归协调器管（它是 /master/joint_*
    的唯一发布者），后臂归后臂驱动管（它持有 CAN 句柄，并且在退出示教时会发
    DisableArm）。另起进程去抢这两样东西早晚出事。
"""

import argparse
import os
import sys
import threading
import time

import rospy
import yaml
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task2_homing_core as homing  # noqa: E402


DEFAULT_CONFIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs", "home_poses.yaml")
FRONT_FEEDBACK = {"left": "/puppet/joint_left", "right": "/puppet/joint_right"}
REAR_FEEDBACK = {
    "left": "/task2/teach/rear_left/joint_states",
    "right": "/task2/teach/rear_right/joint_states",
}
FRONT_HOME_SERVICE = "/task2/teach_handover/home_front"
REAR_HOME_SERVICES = {
    "left": "/task2/teach/rear_left/home",
    "right": "/task2/teach/rear_right/home",
}


def load_config(path):
    with open(path, "r") as handle:
        return yaml.safe_load(handle) or {}


def measured(topic, timeout=5.0):
    message = rospy.wait_for_message(topic, JointState, timeout=timeout)
    return homing.validate_pose(list(message.position)[:7], topic)


def push_params(resolved, config):
    joint_speed, gripper_speed, rate = homing.speed_settings(config)
    rospy.set_param(
        "/task2/homing/speed",
        {
            "joint_rad_per_sec": joint_speed,
            "gripper_m_per_sec": gripper_speed,
            "publish_rate_hz": rate,
        },
    )
    for key, values in resolved.items():
        rospy.set_param("/task2/homing/" + key, list(values))


def call(service, label=None):
    try:
        rospy.wait_for_service(service, timeout=5.0)
    except rospy.ROSException:
        print("服务不可用: {}".format(service))
        return False
    try:
        response = rospy.ServiceProxy(service, Trigger)()
    except rospy.ServiceException as exc:
        print("{} 调用失败: {}".format(service, exc))
        return False
    status = "OK  " if response.success else "失败"
    print("{} {}: {}".format(status, label or service, response.message))
    return bool(response.success)


def do_front(resolved, config):
    push_params(resolved, config)
    print("前臂归位中（一直在 CAN 控制，不会失能、不会掉落）...")
    if not call(FRONT_HOME_SERVICE):
        return False
    return verify_front_arrival(resolved)


def verify_front_arrival(resolved):
    # The legacy service reports published trajectory, not measured arrival.
    deadline = time.monotonic() + 3.0
    last_errors = {}
    while time.monotonic() < deadline:
        try:
            last_errors = {}
            for side in ("left", "right"):
                now = measured(FRONT_FEEDBACK[side], timeout=1.0)
                target = resolved["front_" + side]
                last_errors[side] = max(abs(a-b) for a,b in zip(now[:6], target[:6]))
            if all(value <= 0.03 for value in last_errors.values()):
                print("前双臂实测关节已到位（容差0.03 rad；夹爪未纳入此检查）。")
                return True
        except Exception as exc:
            print("归位实测反馈不可用: {}".format(exc))
        time.sleep(0.1)
    print("归位未到位: {}；服务成功仅代表指令已发布，不代表实际到位。".format(last_errors))
    return False


def do_rear(resolved, config):
    """两条后臂并行归位。

    它们是两个独立的驱动进程、两条独立的 CAN 总线，本来就能同时动。
    串行调用会让总时间翻倍，而且看起来像"左臂先、右臂后"——那是 CLI
    在一条一条地等，不是机械臂的限制。
    """
    push_params(resolved, config)
    print("后臂归位中（从重力位使能 → 进 CAN 控制 → 静止等故障过去 → 移动）...")
    results = {}
    threads = []
    for side in ("left", "right"):
        def run(side=side):
            results[side] = call(REAR_HOME_SERVICES[side])

        thread = threading.Thread(target=run, name="home-" + side)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    ok = all(results.get(side) for side in ("left", "right"))
    if ok:
        print("后臂已停在起点保持，可以按示教按钮了。")
    return ok



def do_all(resolved, config):
    """Preflight every endpoint, then request all three owners concurrently.

    This removes CLI sequencing. Legacy rear enable/settle preparation remains
    inside each driver; a CLI barrier is not a shared physical trajectory clock.
    """
    services = {"front": FRONT_HOME_SERVICE,
                "rear_left": REAR_HOME_SERVICES["left"],
                "rear_right": REAR_HOME_SERVICES["right"]}
    proxies = {}
    try:
        for name, service in services.items():
            rospy.wait_for_service(service, timeout=5.0)
            proxies[name] = rospy.ServiceProxy(service, Trigger)
    except (rospy.ROSException, rospy.ServiceException) as exc:
        print("归位服务预检失败，本次未发出归位请求: {}".format(exc))
        return False
    push_params(resolved, config)
    print("前双臂、左右后臂并行归位；后臂保留驱动内部使能/稳定准备。")
    start = threading.Barrier(len(services) + 1)
    results = {}
    def run(name):
        try:
            start.wait()
            response = proxies[name]()
            print("{} {}: {}".format("OK  " if response.success else "失败",
                                     services[name], response.message))
            ok = bool(response.success)
            if name == "front" and ok:
                ok = verify_front_arrival(resolved)
            results[name] = ok
        except threading.BrokenBarrierError:
            results[name] = False
        except Exception as exc:
            results[name] = False
            print("{} 归位失败: {}".format(services[name], exc))
    threads = []
    try:
        for name in services:
            thread = threading.Thread(target=run, args=(name,), name="home-" + name)
            thread.start()
            threads.append(thread)
    except Exception as exc:
        start.abort()
        for thread in threads:
            thread.join()
        print("归位线程准备失败，本次未发出归位请求: {}".format(exc))
        return False
    start.wait()
    for thread in threads:
        thread.join()
    ok = all(results.get(name, False) for name in services)
    print("四臂归位完成。" if ok else "并行归位未全部成功，请查看各臂结果。")
    return ok


def do_capture(args, config):
    """把当前实测位姿写回配置。

    存的是前臂的【实测】位姿，不是最后一条指令：指令是我们想让它去的地方，
    实测是它实际在的地方，而操作员是照着实际位置摆的。
    """
    poses = config.setdefault("poses", {})
    entry = poses.setdefault(args.pose, {})
    for side in ("left", "right"):
        entry["front_{}".format(side)] = [
            round(v, 6) for v in measured(FRONT_FEEDBACK[side])
        ]
    if args.include_rear:
        for side in ("left", "right"):
            entry["rear_{}".format(side)] = [
                round(v, 6) for v in measured(REAR_FEEDBACK[side])
            ]
    with open(args.config, "w") as handle:
        yaml.safe_dump(config, handle, default_flow_style=False, allow_unicode=True)
    print("已把当前位姿存为 {!r} → {}".format(args.pose, args.config))
    for key, value in sorted(entry.items()):
        print("  {:<12} {}".format(key, [round(v, 4) for v in value]))
    return True


def do_show(resolved):
    """当前位姿离起点还有多远。

    表头故意全用 ASCII：中文字符在终端里占两列，而 str.format 的宽度按一列算，
    混在一起表格必歪。
    """
    topics = [
        ("front_left", FRONT_FEEDBACK["left"]),
        ("front_right", FRONT_FEEDBACK["right"]),
        ("rear_left", REAR_FEEDBACK["left"]),
        ("rear_right", REAR_FEEDBACK["right"]),
    ]
    print("当前位姿与起点的偏差（关节 rad，夹爪 m）:")
    print("  {:<12}{:>10}  {}".format("arm", "max", "joint"))
    for name, topic in topics:
        try:
            now = measured(topic, timeout=2.0)
        except Exception as exc:  # noqa: BLE001
            print("  {:<12}{:>10}  读不到 ({})".format(name, "-", exc))
            continue
        deltas = [abs(a - b) for a, b in zip(now, resolved[name])]
        worst = max(range(homing.JOINT_COUNT), key=lambda index: deltas[index])
        print("  {:<12}{:>10.4f}  j{}".format(name, deltas[worst], worst + 1))
    print("  (后臂失能躺在重力位时偏差大是正常的)")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("front", "rear", "all", "capture", "show", "gripper"))
    parser.add_argument("--pose", default="collect_start")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument(
        "--include-rear",
        action="store_true",
        help="capture 时把后臂位姿也单独存下来（默认后臂跟随前臂）",
    )
    args = parser.parse_args()

    if args.action == "gripper":
        if args.pose != "reinit":
            parser.error("夹爪操作请使用 home.sh gripper --pose reinit")
        import gripper_cycle
        return gripper_cycle.cli()

    rospy.init_node("task2_home_cli", anonymous=True, disable_signals=True)
    config = load_config(args.config)

    if args.action == "capture":
        return 0 if do_capture(args, config) else 1

    try:
        resolved = homing.resolve_pose_set(config, args.pose)
    except homing.HomingError as exc:
        print("配置有问题: {}".format(exc))
        print("先用 `task2_home_cli.py capture` 把当前位姿存成起点。")
        return 2

    if args.action == "show":
        return 0 if do_show(resolved) else 1
    if args.action == "front":
        return 0 if do_front(resolved, config) else 1
    if args.action == "rear":
        return 0 if do_rear(resolved, config) else 1
    return 0 if do_all(resolved, config) else 1


if __name__ == "__main__":
    sys.exit(main())
