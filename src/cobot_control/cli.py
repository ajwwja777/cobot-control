"""Hardware lifecycle without a running web service."""
import argparse
import getpass
import json
import time
from .device_control import DeviceController, DeviceControlError, _default_system_probe, _CAN_TX_MONITOR, _CAN_BUSES
from .paths import RUNTIME_ROOT
from . import site_hardware

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Read jobs, CAN and ROS; never moves hardware")
    diagnostic = commands.add_parser("diagnose", help="Subscribe to feedback only; source ROS first")
    diagnostic.add_argument("--seconds", type=float, default=1.5)
    for action in ("start", "stop"):
        sub = commands.add_parser(action)
        sub.add_argument("component", choices=("roscore", "arms", "cameras", "home", "recover") if action == "stop" else ("roscore", "arms", "cameras"))
    can = commands.add_parser("can")
    can.add_argument("action", choices=("configure", "reset"))
    for action in ("home", "recover"):
        sub = commands.add_parser(action)
        sub.add_argument("target")
        if action == "home":
            sub.add_argument("--pose", required=True)
            sub.add_argument("--arms", help="Comma separated arms when target=selection")
        sub.add_argument("--execute", action="store_true", help="Execute the displayed movement command")
    launch = commands.add_parser("configure-launch")
    launch.add_argument("component", choices=("arms", "cameras"))
    launch.add_argument("--path", default="")
    launch.add_argument("--setup", default="")
    launch.add_argument("--cwd", default="")
    launch.add_argument("args", nargs="*")
    args = parser.parse_args(argv)
    control = DeviceController(RUNTIME_ROOT / "devices")
    try:
        if args.command == "status":
            _CAN_TX_MONITOR.sample(tuple(_CAN_BUSES.values()))
            time.sleep(1.05)
            control.system_probe = lambda: _default_system_probe()
            result = control.status()
        elif args.command == "diagnose":
            from .diagnostics import observe
            result = observe(args.seconds)
        elif args.command == "configure-launch":
            with control.operation_lock():
                if any(control.process_finder(control._marker(k)) for k in ("arms", "cameras")):
                    raise DeviceControlError("Stop hardware tasks before changing launch identity")
                site_hardware.save_hardware(args.component, args.path, args.setup, args.cwd, args.args)
            result = site_hardware.hardware()
        else:
            if args.command in ("start", "stop"):
                spec = {"component": args.component, "action": args.command}
            elif args.command == "can":
                spec = {"component": "can", "action": args.action, "target": "task2"}
            else:
                spec = {"component": args.command, "action": "run", "target": args.target}
                if args.command == "home":
                    spec["pose"] = args.pose
                    if args.arms:
                        spec["arms"] = args.arms.split(",")
                if not args.execute:
                    print(json.dumps({"command": control._command(control._normalize(spec)), "executed": False}, indent=2))
                    return 0
            token = control.confirm(spec)["confirmation_token"]
            if args.command == "can":
                spec["sudo_password"] = getpass.getpass("sudo password: ")
            result = control.start(spec, token)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, ImportError) as error:
        parser.exit(1, str(error) + "\n")

if __name__ == "__main__":
    raise SystemExit(main())
