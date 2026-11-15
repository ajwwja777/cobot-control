from pathlib import Path
import xml.etree.ElementTree as ET


def test_native_camera_profile_applies_to_all_three_streams():
    root=ET.parse(Path(__file__).parents[1]/"integrations/legacy_control/launch/multi_camera_shuai.launch").getroot()
    args={node.attrib['name']:node.attrib.get('default') for node in root.findall('arg')}
    assert (int(args['color_width']),int(args['color_height']))==(1632,1224)
    includes=root.findall('include');assert len(includes)==3
    for node in includes:
        values={arg.attrib['name']:arg.attrib['value'] for arg in node.findall('arg')}
        assert values['color_width']=='$(arg color_width)' and values['color_height']=='$(arg color_height)' and values['color_fps']=='$(arg color_fps)'
