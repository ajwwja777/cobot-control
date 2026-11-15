import importlib.util
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

ROBOT=Path(__file__).parents[2]
sys.path.insert(0,str(ROBOT))
import teleop_core as c
import teleop as t

P=[0,0,0,0,0,0,.02]


def sample(at,active=True,position=None):
    return {"type":"sample","t":at,"front":{s:{"position":list(position or P)} for s in c.SIDES},
            "teach":{"left":False,"right":active}}


def write_trace(path,frames,complete=True,**header_changes):
    header={"type":"header","schema":c.SCHEMA,"source":"front_measured","units":c.UNITS,"joint_names":c.JOINT_NAMES}
    header.update(header_changes)
    footer={"type":"footer","complete":complete,"valid_for_replay":True,"frames":len(frames)}
    path.write_text("\n".join(json.dumps(row) for row in [header,*frames,footer])+"\n")
    return path


def test_load_keeps_full_enter_to_enter_interval(tmp_path):
    frames=[sample(i*.02,active=10<=i<=40 and i!=25) for i in range(100)]
    got=c.load_trace(write_trace(tmp_path/"record.jsonl",frames))
    assert len(got)==100
    assert got[0]["t"]==0
    assert got[-1]["t"]==pytest.approx(1.98)
    assert any(f["t"]==.5 and not any(f["teach"].values()) for f in got)


@pytest.mark.parametrize("change",[{"units":{"joints":"deg"}}, {"joint_names":list(reversed(c.JOINT_NAMES))},
                                    {"source":"rear_measured"},{"schema":"other"}])
def test_wrong_units_or_source_rejected(tmp_path,change):
    with pytest.raises(ValueError):c.load_trace(write_trace(tmp_path/"bad.jsonl",[sample(0),sample(.02)],**change))


@pytest.mark.parametrize("frames",[[sample(0),sample(0)], [sample(.02),sample(0)]])
def test_invalid_time_order_rejected(tmp_path,frames):
    with pytest.raises(ValueError):c.load_trace(write_trace(tmp_path/"bad.jsonl",frames))


def test_incomplete_and_frame_count_mismatch_rejected(tmp_path):
    path=write_trace(tmp_path/"bad.jsonl",[sample(0),sample(.02)],complete=False)
    with pytest.raises(ValueError):c.load_trace(path)
    write_trace(path,[sample(0),sample(.02)])
    text=path.read_text().replace('"frames": 2','"frames": 3');path.write_text(text)
    with pytest.raises(ValueError):c.load_trace(path)


@pytest.mark.parametrize("value",[float("nan"),float("inf"),True,"1"])
def test_invalid_state_numbers_rejected(value):
    p=list(P);p[0]=value
    with pytest.raises(ValueError):c.position(p)


def test_gripper_and_joint_values_are_preserved_without_range_checks():
    for opening in [-.0002,.08,.085,.1]:
        p=list(P);p[6]=opening;p[2]=.04
        assert c.position(p)==p


def test_front_only_record_with_no_teach_fields_loads_in_full(tmp_path):
    frames=[sample(0,False),sample(.5,False)]
    for f in frames:del f["teach"]
    assert len(c.load_trace(write_trace(tmp_path/"front.jsonl",frames)))==2


def test_legacy_schema_is_readable_without_teach_filtering(tmp_path):
    frames=[sample(0,False),sample(.02,False)]
    assert len(c.load_trace(write_trace(tmp_path/"old.jsonl",frames,schema=c.LEGACY_SCHEMA)))==2


def test_interpolated_replay_never_exceeds_per_tick_speed_limits():
    end=list(P);end[0]=.3;end[6]=.07
    times,poses=c.retime([sample(0),sample(.02,position=end)])
    assert times[-1]>=1
    previous=c.interpolate(times,poses,0)
    for tick in range(1,math.ceil(times[-1]*c.RATE)+1):
        pair=c.interpolate(times,poses,tick/c.RATE)
        for side in c.SIDES:
            for i,(a,b) in enumerate(zip(previous[side],pair[side])):
                speed=c.GRIPPER_SPEED if i==6 else c.JOINT_SPEED
                assert abs(b-a)<=speed/c.RATE+1e-9
        previous=pair
    assert previous==poses[-1]


def test_return_to_start_is_gradual_and_arrives_exactly():
    start={s:list(P) for s in c.SIDES};end={s:list(P) for s in c.SIDES};end["right"][0]=.6
    previous=start
    path=list(c.start_path(start,end))
    assert len(path)>100
    for pair in path:
        assert abs(pair["right"][0]-previous["right"][0])<=c.JOINT_SPEED/c.RATE+1e-9
        previous=pair
    assert path[-1]==end


def ready_state(monkeypatch):
    monkeypatch.setattr(t.time,"monotonic",lambda:10)
    state=t.State.__new__(t.State)
    import threading
    state.lock=threading.RLock();state.ros=SimpleNamespace(is_shutdown=lambda:False);state.cache={}
    stamp=SimpleNamespace(to_sec=lambda:0)
    for side in c.SIDES:
        msg=SimpleNamespace(name=c.JOINT_NAMES,position=P,velocity=[],effort=[],header=SimpleNamespace(stamp=stamp))
        for key in ["front_"+side,"rear_"+side]:state.cache[key]=(10,msg)
        state.cache["teach_"+side]=(10,SimpleNamespace(data=False))
        state.cache["status_"+side]=(10,SimpleNamespace(ctrl_mode=1,arm_status=0,teach_status=0,err_code=0))
        state.cache["fault_"+side]=(10,SimpleNamespace(data=""))
    state.cache["fault"]=(10,SimpleNamespace(data=""))
    return state


def test_manual_takeover_is_recorded_but_aborts_replay(monkeypatch):
    state=ready_state(monkeypatch);state.cache["teach_right"]=(10,SimpleNamespace(data=True))
    assert set(state.sample())=={"front"}
    with pytest.raises(RuntimeError,match="接管"):state.sample(replay=True)


@pytest.mark.parametrize("kind",["stale","hardware","coordinator","shutdown"])
def test_runtime_faults_stop_playback(monkeypatch,kind):
    state=ready_state(monkeypatch)
    if kind=="stale":state.cache["front_left"]=(9,state.cache["front_left"][1])
    elif kind=="hardware":state.cache["status_right"][1].err_code=1
    elif kind=="coordinator":state.cache["fault"][1].data="fault"
    elif kind=="shutdown":state.ros.is_shutdown=lambda:True
    with pytest.raises(RuntimeError):state.sample(replay=True)


def test_ownership_guard_rejects_rlt_and_second_writer(monkeypatch):
    fake_ros=SimpleNamespace(get_name=lambda:"/replay")
    home="/task2/teach_handover/home_front";owner="/coordinator"
    pubs=[["/master/joint_"+s,[owner]] for s in c.SIDES]
    subs=[["/task2/policy/joint_"+s,[owner]] for s in c.SIDES]
    services=[[home,[owner]]]
    graph=Mock();graph.getSystemState.return_value=[pubs,subs,services]
    monkeypatch.setitem(sys.modules,"rospy",fake_ros)
    monkeypatch.setitem(sys.modules,"rosgraph",SimpleNamespace(Master=lambda name:graph))
    t.graph_check()
    services.append(["/task2/policy/arm",["/rlt"]])
    with pytest.raises(RuntimeError):t.graph_check()
    services.pop();pubs.append(["/task2/policy/joint_right",["/other"]])
    with pytest.raises(RuntimeError):t.graph_check()


def test_latest_pointer_cannot_escape_data_dir(tmp_path,monkeypatch):
    monkeypatch.setattr(t,"DATA",tmp_path)
    (tmp_path/"latest.txt").write_text("../outside.jsonl")
    with pytest.raises(RuntimeError):t.latest_file()


def test_info_is_read_only_and_never_imports_ros(tmp_path,monkeypatch):
    p=write_trace(tmp_path/"record.jsonl",[sample(0),sample(.02)])
    monkeypatch.setitem(sys.modules,"rospy",None)
    assert t.main(["info",str(p)])==0


class FakeClock:
    def __init__(self):self.now=0
    def monotonic(self):return self.now
    def sleep(self,seconds):self.now+=max(0,seconds)


def fake_replay(monkeypatch,fail_after=None):
    clock=FakeClock();monkeypatch.setattr(t.time,"monotonic",clock.monotonic);monkeypatch.setattr(t.time,"sleep",clock.sleep)
    current={s:list(P) for s in c.SIDES};current["right"][0]=.05
    emitted=[];pubs=[]
    class Message:
        def __init__(self):self.header=SimpleNamespace(stamp=None)
    class Pub:
        def __init__(self,topic,*a,**kw):self.topic=topic;self.closed=False;pubs.append(self)
        def get_num_connections(self):return 1
        def publish(self,msg):
            side=self.topic.rsplit("_",1)[1];current[side]=list(msg.position)
            emitted.append((self.topic,list(msg.position)))
        def unregister(self):self.closed=True
    def sample_state(*a,**kw):
        if fail_after is not None and len(emitted)>=fail_after:raise RuntimeError("teach takeover")
        return {"front":{s:{"position":list(current[s])} for s in c.SIDES}}
    state=SimpleNamespace(sample=sample_state,wait_ready=sample_state)
    monkeypatch.setattr(t.sys.stdin,"isatty",lambda:True)
    monkeypatch.setattr("builtins.input",lambda prompt="":"")
    monkeypatch.setitem(sys.modules,"rospy",SimpleNamespace(Publisher=Pub,Time=SimpleNamespace(now=lambda:clock.now)))
    monkeypatch.setitem(sys.modules,"sensor_msgs",SimpleNamespace())
    monkeypatch.setitem(sys.modules,"sensor_msgs.msg",SimpleNamespace(JointState=Message))
    monkeypatch.setitem(sys.modules,"front_mode",SimpleNamespace(operator_guard=Mock(),feedback=Mock(),check_ready=Mock()))
    from contextlib import nullcontext
    monkeypatch.setattr(t,"Health",lambda:nullcontext(SimpleNamespace(check=lambda:None)))
    monkeypatch.setattr(t,"graph_check",lambda:None)
    return state,current,emitted,pubs


def test_actual_replay_routes_only_through_coordinator_with_gradual_start(monkeypatch):
    state,current,emitted,pubs=fake_replay(monkeypatch)
    last={s:list(current[s]) for s in c.SIDES}
    end=list(P);end[0]=.02
    frames=[sample(0),sample(.02,position=end)]
    assert t.replay(state,Path("fake.jsonl"),frames)==0
    for topic,pos in emitted:
        assert topic in ["/task2/policy/joint_left","/task2/policy/joint_right"]
        side=topic.rsplit("_",1)[1]
        for i,(a,b) in enumerate(zip(last[side],pos)):
            speed=c.GRIPPER_SPEED if i==6 else c.JOINT_SPEED
            assert abs(b-a)<=speed/c.RATE+1e-8
        last[side]=pos
    assert current=={s:end for s in c.SIDES}
    assert all(pub.closed for pub in pubs)


def test_actual_replay_unregisters_and_does_not_continue_after_takeover(monkeypatch):
    state,current,emitted,pubs=fake_replay(monkeypatch,fail_after=8)
    with pytest.raises(RuntimeError,match="takeover"):t.replay(state,Path("fake.jsonl"),[sample(0),sample(.02)])
    assert len(emitted)==8
    assert all(pub.closed for pub in pubs)


@pytest.mark.parametrize("fault",[False,True])
def test_actual_record_writes_complete_jsonl_and_never_replaces_latest_on_fault(tmp_path,monkeypatch,fault):
    clock=FakeClock();monkeypatch.setattr(t.time,"monotonic",clock.monotonic)
    monkeypatch.setattr(t,"DATA",tmp_path);monkeypatch.setattr(t.sys.stdin,"isatty",lambda:True)
    monkeypatch.setattr("builtins.input",lambda prompt="":"")
    class Event:
        def __init__(self):self.done=False;self.waits=0
        def is_set(self):return self.done
        def set(self):self.done=True
        def wait(self,seconds):
            clock.sleep(seconds);self.waits+=1
            if self.waits==4:self.done=True
    monkeypatch.setattr(t.threading,"Event",Event)
    monkeypatch.setattr(t.threading,"Thread",lambda **kw:SimpleNamespace(start=lambda:None))
    calls=0
    def sample_state():
        nonlocal calls
        calls+=1
        if fault and calls>=4:raise RuntimeError("stale feedback")
        return {"front":{s:{"position":[0,0,.04,0,0,0,.085]} for s in c.SIDES},"rear":{s:{"position":list(P)} for s in c.SIDES},
                "teach":{"left":False,"right":True}}
    state=SimpleNamespace(wait_ready=lambda:None,sample=sample_state)
    pointer=tmp_path/"latest.txt";pointer.write_text("previous.jsonl\n")
    if fault:
        with pytest.raises(RuntimeError,match="stale"):t.record(state)
        assert pointer.read_text()=="previous.jsonl\n"
    else:
        assert t.record(state)==0
        frames=c.load_trace(t.latest_file());assert len(frames)==4
        assert frames[0]["front"]["right"]["position"][6]==.085
        assert all(set(f)=={"type","t","front"} for f in frames)
    files=list(tmp_path.glob("teleop-*.jsonl"));assert len(files)==1
    rows=[json.loads(line) for line in files[0].read_text().splitlines()]
    assert rows[0]["schema"]==c.SCHEMA and rows[-1]["complete"] is (not fault)
    assert not list(tmp_path.glob("*.incomplete"))


def test_record_state_needs_no_rear_topics_flags_status_or_fault(monkeypatch):
    state=ready_state(monkeypatch)
    state.cache={key:value for key,value in state.cache.items() if key.startswith("front_")}
    state.cache["front_left"]=(9,state.cache["front_left"][1])
    state.cache["front_right"][1].position=[0,0,.04,0,0,0,.085]
    got=state.sample()
    assert set(got)=={"front"}
    assert got["front"]["right"]["position"][6]==.085
    assert got["front"]["left"]["feedback_age_sec"]==1


def test_record_mode_subscribes_only_two_front_topics(monkeypatch):
    topics=[]
    fake_ros=SimpleNamespace(Subscriber=lambda topic,*a,**kw:topics.append(topic) or Mock())
    monkeypatch.setitem(sys.modules,"rospy",fake_ros)
    monkeypatch.setitem(sys.modules,"sensor_msgs",SimpleNamespace())
    monkeypatch.setitem(sys.modules,"sensor_msgs.msg",SimpleNamespace(JointState=object))
    monkeypatch.setitem(sys.modules,"std_msgs.msg",None)
    monkeypatch.setitem(sys.modules,"piper_msgs.msg",None)
    state=t.State()
    assert topics==["/puppet/joint_left","/puppet/joint_right"]
    state.close()


def test_web_record_uses_explicit_stop_and_preserves_name(tmp_path,monkeypatch):
    import time as real_time
    monkeypatch.setattr(t,"DATA",tmp_path)
    class Input:
        def isatty(self):return False
        def readline(self):real_time.sleep(.08);return "stop\n"
    monkeypatch.setattr(t.sys,"stdin",Input())
    monkeypatch.setattr("builtins.input",lambda *args:(_ for _ in ()).throw(AssertionError("terminal prompt")))
    state=SimpleNamespace(wait_ready=lambda:None,sample=lambda:{"front":{s:{"position":list(P)} for s in c.SIDES}})
    assert t.record(state,confirmed=True,name="轨迹名称")==0
    path=t.latest_file();header=json.loads(path.read_text().splitlines()[0])
    assert header["name"]=="轨迹名称" and len(c.load_trace(path))>=2


def test_web_record_control_eof_keeps_incomplete_result_and_latest(tmp_path,monkeypatch):
    import io
    monkeypatch.setattr(t,"DATA",tmp_path);monkeypatch.setattr(t.sys,"stdin",io.StringIO(""))
    pointer=tmp_path/"latest.txt";pointer.write_text("old.jsonl\n")
    state=SimpleNamespace(wait_ready=lambda:None,sample=lambda:{"front":{s:{"position":list(P)} for s in c.SIDES}})
    with pytest.raises(RuntimeError,match="控制连接中断"):t.record(state,confirmed=True,name="test")
    assert pointer.read_text()=="old.jsonl\n"
    rows=[json.loads(line) for line in next(tmp_path.glob("teleop-*.jsonl")).read_text().splitlines()]
    assert not rows[-1]["complete"] and not rows[-1]["valid_for_replay"]


def test_web_replay_still_aborts_on_teaching_takeover(monkeypatch):
    state,current,emitted,pubs=fake_replay(monkeypatch,fail_after=8)
    monkeypatch.setattr(t.sys.stdin,"isatty",lambda:False)
    monkeypatch.setattr("builtins.input",lambda *args:(_ for _ in ()).throw(AssertionError("terminal prompt")))
    with pytest.raises(RuntimeError,match="takeover"):t.replay(state,Path("fake.jsonl"),[sample(0),sample(.02)],confirmed=True)
    assert len(emitted)==8 and all(pub.closed for pub in pubs)


def test_sequence_keeps_publishers_and_smoothly_bridges_all_joints(monkeypatch,capsys):
    state,current,emitted,pubs=fake_replay(monkeypatch)
    initial={s:list(current[s]) for s in c.SIDES}
    first_end=[.08,.02,0,0,0,0,.03]
    second_start=[-.08,-.02,0,0,0,0,.01]
    second_end=[-.04,-.01,0,0,0,0,.02]
    plans=[(Path("one.jsonl"),[sample(0),sample(.02,position=first_end)]),
           (Path("two.jsonl"),[sample(0,position=second_start),sample(.02,position=second_end)])]
    assert t.replay_sequence(state,plans,confirmed=True)==0
    assert len(pubs)==2 and all(pub.closed for pub in pubs)
    previous=initial;left=[initial["left"]]
    for topic,pos in emitted:
        side=topic.rsplit("_",1)[1]
        for index,(a,b) in enumerate(zip(previous[side],pos)):
            speed=c.GRIPPER_SPEED if index==6 else c.JOINT_SPEED
            assert abs(b-a)<=speed/c.RATE+1e-8
        previous[side]=pos
        if side=="left":left.append(pos)
    end_index=next(i for i,pair in enumerate(left) if pair==first_end)
    start_index=next(i for i,pair in enumerate(left) if i>end_index and pair==second_start)
    assert start_index-end_index>20
    assert any(second_start[0]<pair[0]<first_end[0] for pair in left[end_index+1:start_index])
    assert current=={s:second_end for s in c.SIDES}
    assert "轨迹 2/2" in capsys.readouterr().out


@pytest.mark.parametrize("exception",[RuntimeError("teach takeover"),KeyboardInterrupt()])
def test_sequence_aborts_during_bridge_and_never_starts_next(monkeypatch,capsys,exception):
    state,current,emitted,pubs=fake_replay(monkeypatch)
    original=c.start_path;calls=[]
    def path(start,target):
        calls.append(target)
        for index,pair in enumerate(original(start,target)):
            if len(calls)==2 and index==4:raise exception
            yield pair
    monkeypatch.setattr(c,"start_path",path)
    second=[-.1,0,0,0,0,0,.01]
    with pytest.raises(type(exception)):
        t.replay_sequence(state,[(Path("one"),[sample(0),sample(.02)]),
                                 (Path("two"),[sample(0,position=second),sample(.02,position=second)])],confirmed=True)
    assert len(calls)==2 and all(pub.closed for pub in pubs)
    assert "轨迹 2/2：开始回放" not in capsys.readouterr().out
    assert current["left"]!=second


def test_sequence_validates_later_trace_before_importing_ros_or_moving(tmp_path,monkeypatch):
    first=write_trace(tmp_path/"one.jsonl",[sample(0),sample(.02)])
    second=write_trace(tmp_path/"two.jsonl",[sample(0),sample(.02)],complete=False)
    monkeypatch.setitem(sys.modules,"rospy",None)
    with pytest.raises(ValueError,match="完整"):
        t.main(["replay",str(first),"--next",str(second),"--web-confirmed"])
    with pytest.raises(SystemExit):t.main(["record","--next",str(first)])


def test_sequence_cli_preserves_explicit_order_and_one_state(tmp_path,monkeypatch):
    from contextlib import nullcontext
    paths=[write_trace(tmp_path/(str(i)+".jsonl"),[sample(0),sample(.02)]) for i in range(2)]
    monkeypatch.setitem(sys.modules,"rospy",SimpleNamespace(init_node=Mock()))
    state=SimpleNamespace(close=Mock());monkeypatch.setattr(t,"State",lambda **kw:state)
    monkeypatch.setattr(t,"operation_lock",lambda:nullcontext())
    run=Mock(return_value=0);monkeypatch.setattr(t,"replay_sequence",run)
    assert t.main(["replay",str(paths[1]),"--next",str(paths[0]),"--next",str(paths[1]),"--web-confirmed"])==0
    assert [path for path,frames in run.call_args.args[1]]==[paths[1],paths[0],paths[1]]
    assert run.call_args.kwargs["confirmed"] and state.close.call_count==1


def test_web_discard_removes_only_current_pending_and_keeps_latest(tmp_path,monkeypatch):
    import io
    monkeypatch.setattr(t,"DATA",tmp_path);monkeypatch.setattr(t.sys,"stdin",io.StringIO("discard\n"))
    original=write_trace(tmp_path/"old.jsonl",[sample(0),sample(.02)])
    before=original.read_bytes();pointer=tmp_path/"latest.txt";pointer.write_text("old.jsonl\n")
    state=SimpleNamespace(wait_ready=lambda:None,sample=lambda:{"front":{s:{"position":list(P)} for s in c.SIDES}})
    assert t.record(state,confirmed=True,name="discard")==10
    assert original.read_bytes()==before and pointer.read_text()=="old.jsonl\n"
    assert sorted(path.name for path in tmp_path.iterdir())==["latest.txt","old.jsonl"]


@pytest.mark.parametrize("strict",[False,True])
def test_tracking_lag_is_warning_by_default_and_strict_mode_exits(monkeypatch,capsys,strict):
    state,current,emitted,pubs=fake_replay(monkeypatch)
    original=sys.modules['rospy'].Publisher
    def publisher(topic,*args,**kw):
        pub=original(topic,*args,**kw);publish=pub.publish
        def stationary_left(msg):
            before=list(current['left']);publish(msg)
            if topic.endswith('_left'):current['left']=before
        pub.publish=stationary_left;return pub
    monkeypatch.setattr(sys.modules['rospy'],'Publisher',publisher)
    end=[.3,0,0,0,0,0,.02];frames=[sample(0),sample(1,position=end)]
    if strict:
        with pytest.raises(RuntimeError,match="跟踪偏差"):t.replay(state,Path('lag'),frames,confirmed=True,strict_monitoring=True)
    else:assert t.replay(state,Path('lag'),frames,confirmed=True)==0
    assert all(pub.closed for pub in pubs)
    text=capsys.readouterr().out
    assert ('replay_tracking_error' if strict else 'replay_tracking_warning') in text
    assert '"joint": 1' in text and '"measured_rad"' in text


@pytest.mark.parametrize("strict",[False,True])
def test_scheduler_delay_is_paced_without_bursts_unless_strict(monkeypatch,strict):
    state,current,emitted,pubs=fake_replay(monkeypatch)
    clock=t.time.monotonic.__self__;calls=[];stamps=[]
    original=sys.modules['rospy'].Publisher
    def publisher(topic,*args,**kw):
        pub=original(topic,*args,**kw);publish=pub.publish
        def receive(msg):
            if topic.endswith('_left'):stamps.append(clock.now)
            publish(msg)
        pub.publish=receive;return pub
    monkeypatch.setattr(sys.modules['rospy'],'Publisher',publisher)
    def graph():
        calls.append(True)
        if len(calls)==3:clock.now+=.08
    monkeypatch.setattr(t,'graph_check',graph)
    if strict:
        with pytest.raises(RuntimeError,match="调度延迟"):t.replay(state,Path('delay'),[sample(0),sample(.1)],confirmed=True,strict_monitoring=True)
    else:
        assert t.replay(state,Path('delay'),[sample(0),sample(.1)],confirmed=True)==0
        assert all(after-before>=1/c.RATE-1e-8 for before,after in zip(stamps,stamps[1:]))
    assert all(pub.closed for pub in pubs)
