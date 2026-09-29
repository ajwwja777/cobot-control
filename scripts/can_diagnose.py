#!/usr/bin/env python3
"""Observe CAN queues without ROS, motor commands, root privileges or link resets."""
import argparse,json,sys,time,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from cobot_control.can_health import CanTxMonitor,record_event
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--seconds",type=float,default=2);p.add_argument("--output",type=Path);a=p.parse_args()
 if not 1.2<=a.seconds<=60:p.error("--seconds must be 1.2..60")
 buses=("can_left","can_right","can_mid","can_rear_left","can_rear_right")
 monitor=CanTxMonitor(event_sink=record_event);samples=[];end=time.monotonic()+a.seconds
 while time.monotonic()<end:
  samples.append({"timestamp":time.time(),"interfaces":monitor.sample(buses)});time.sleep(.25)
 q=subprocess.run(["ip","-details","-statistics","-json","link","show","type","can"],capture_output=True,text=True,timeout=2)
 try:links=json.loads(q.stdout)
 except ValueError:links=[]
 report={"passive_only":True,"samples":samples,"link_details":links,
  "automatic_recovery":"Existing restart-ms handles BUS-OFF only. Queue draining is observed, not forced. No motor Recover or interface reset was performed.",
  "next_step":"If a sustained stall remains: pause policy/teach, retain this evidence, check power/CAN/USB. Use the registered targeted link reset only after stopping command producers; do not blindly enlarge txqueuelen."}
 if a.output:
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(report,indent=2))
if __name__=="__main__":main()
