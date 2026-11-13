from pathlib import Path
import os
import pytest
from cobot_control.camera_guard import usb_camera_conflicts
from cobot_control import device_control as dc


def process(root,pid,parent,group,argv,usb=None):
    directory=root/str(pid);directory.mkdir();(directory/"fd").mkdir()
    fields=['S',str(parent),str(group)]+['0']*20
    (directory/"stat").write_text(str(pid)+' (camera) '+' '.join(fields))
    (directory/"cmdline").write_bytes('\0'.join(argv).encode())
    if usb:(directory/"fd/3").symlink_to(usb)
    return directory


def test_old_camera_usb_owners_block_but_managed_group_and_unrelated_usb_do_not(tmp_path,monkeypatch):
    monkeypatch.setattr(os,'getpgid',lambda pid:100)
    process(tmp_path,100,1,100,['roslaunch','managed.launch'])
    process(tmp_path,101,100,100,['/drivers/astra_camera_node','/camera_l/color:=/color'],'/dev/bus/usb/001/013')
    process(tmp_path,200,1,200,['roslaunch','old.launch'])
    process(tmp_path,201,200,200,['/drivers/astra_camera_node','/camera_f/color:=/color'],'/dev/bus/usb/001/059')
    process(tmp_path,300,1,300,['/other/app'],'/dev/bus/usb/001/024')
    conflicts=usb_camera_conflicts([100],proc=tmp_path)
    assert [v['pid'] for v in conflicts]==[201]
    assert conflicts[0]['devices']==['/dev/bus/usb/001/059']


def test_guard_prevents_launch_and_never_stops_foreign_owner(tmp_path,monkeypatch):
    from cobot_control import camera_guard
    monkeypatch.setattr(camera_guard,'usb_camera_conflicts',lambda managed:[{'pid':55,'devices':['/dev/bus/usb/001/059']}])
    controller=dc.DeviceController(tmp_path,launcher=lambda *args:pytest.fail('duplicate launch'),stopper=lambda *args:pytest.fail('stopped foreign owner'),process_finder=lambda marker:[],system_probe=lambda:{})
    spec={'component':'cameras','action':'start'}
    with pytest.raises(dc.DeviceControlError,match='PID 55'):controller.start(spec,controller.confirm(spec)['confirmation_token'])


def test_registered_nodes_without_image_publishers_are_not_ready(tmp_path,monkeypatch):
    monkeypatch.setattr(dc,'_ros_nodes',lambda:(True,{'/camera_f/camera','/camera_l/camera','/camera_r/camera'},'ok'))
    monkeypatch.setattr(dc,'_camera_image_publishers',lambda:{'camera_high':False,'camera_left':False,'camera_right':False})
    monkeypatch.setattr(dc,'_passive_arm_feedback',lambda bus:{'phase':'offline','fresh':False})
    monkeypatch.setattr(dc,'_control_routes',lambda:{})
    result=dc._default_system_probe()['cameras']
    assert result['phase']=='error' and '0/3 image publishers' in result['detail']
