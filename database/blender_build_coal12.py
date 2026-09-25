import json
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'public/defaults/hongyang-coal12-georef.json').read_text(encoding='utf-8'))
origin = data['meta']['origin']
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1


def material(name, color, alpha=1):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, alpha)
    result.use_nodes = True
    shader = result.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = 0.72
    shader.inputs['Metallic'].default_value = 0.12
    shader.inputs['Alpha'].default_value = alpha
    return result


def to_blender(scene_point):
    return [scene_point[0], -scene_point[2], scene_point[1]]


def mine_to_blender(point):
    return [point[index] - origin[index] for index in range(3)]


seam_material = material('Coal12 / interpolated elevation surface', (0.035, 0.12, 0.19), 0.7)
road_material = material('CAD roadway traces / schematic width', (0.18, 0.83, 0.9))
control_material = material('DXF survey symbols', (1, 0.73, 0.16))
mesh = bpy.data.meshes.new('coal12-tin')
indices = data['seam']['indices']
mesh.from_pydata([to_blender(point) for point in data['seam']['vertices']], [],
                 [indices[index:index + 3] for index in range(0, len(indices), 3)])
mesh.update()
seam = bpy.data.objects.new('Coal12_Interpolated_Surface', mesh)
bpy.context.collection.objects.link(seam)
seam.data.materials.append(seam_material)
seam['georef_id'] = data['meta']['id']
seam['origin'] = origin
seam['height_source'] = 'DXF text anchors / linear TIN interpolation / unverified survey datum'
for index, trace in enumerate(data['roadways']):
    curve = bpy.data.curves.new(f'CAD_{trace["handle"]}_{index}', 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = 1.2
    curve.bevel_resolution = 2
    spline = curve.splines.new('POLY')
    spline.points.add(len(trace['points']) - 1)
    for vertex, point in zip(spline.points, trace['points']):
        vertex.co = (*mine_to_blender(point), 1)
    roadway = bpy.data.objects.new(curve.name, curve)
    bpy.context.collection.objects.link(roadway)
    roadway.data.materials.append(road_material)
    roadway['source_handle'] = trace['handle']
    roadway['geometry_status'] = 'CAD trace with schematic 2.4m display diameter'
for control in data['controls']:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=2.4,
                                       location=mine_to_blender(control['mine']))
    marker = bpy.context.object
    marker.name = 'Control_' + control['id']
    marker.data.materials.append(control_material)
    marker['mine_coordinates'] = control['mine']
    marker['source_handle'] = control['id']


def add_slab_edges(name, source, parent, color):
    unique = {}
    remap = []
    points = []
    for point in source['vertices']:
        key = tuple(round(value, 6) for value in point)
        if key not in unique:
            unique[key] = len(points)
            points.append(to_blender(point))
        remap.append(unique[key])
    count = len(points)
    faces = [[remap[vertex] for vertex in source['indices'][index:index + 3]] for index in range(0, len(source['indices']), 3)]
    edges = Counter(tuple(sorted((face[index], face[(index + 1) % 3]))) for face in faces for index in range(3))
    boundary = [edge for edge, occurrences in edges.items() if occurrences == 1]
    vertices = points + [[point[0], point[1], point[2] - 6] for point in points]
    walls = [(first, second, second + count, first + count) for first, second in boundary]
    wall_mesh = bpy.data.meshes.new(name + '_illustrative_thickness')
    wall_mesh.from_pydata(vertices, [], walls)
    wall_mesh.update()
    wall_object = bpy.data.objects.new(name + '_Edges', wall_mesh)
    bpy.context.collection.objects.link(wall_object)
    wall_object.parent = parent
    wall_object.data.materials.append(material(name + '_edge_material', color))
    wall_object['thickness_status'] = '6m illustrative display edge; not measured coal thickness'


lower_objects = list(bpy.context.scene.objects)
lower_group = bpy.data.objects.new('Coal12_Layer', None)
bpy.context.collection.objects.link(lower_group)
lower_group['seam'] = 'coal12'
for lower_object in lower_objects:
    lower_object.parent = lower_group
add_slab_edges('Coal12', data['seam'], lower_group, (0.06, 0.28, 0.36))
upper_group = bpy.data.objects.new('Coal7_Layer', None)
bpy.context.collection.objects.link(upper_group)
upper_group['seam'] = 'coal7'
upper_data = data['upperLayer']
upper_mesh = bpy.data.meshes.new('coal7-tin')
upper_indices = upper_data['seam']['indices']
upper_mesh.from_pydata([to_blender(point) for point in upper_data['seam']['vertices']], [],
                       [upper_indices[index:index + 3] for index in range(0, len(upper_indices), 3)])
upper_mesh.update()
upper_surface = bpy.data.objects.new('Coal7_Interpolated_Surface', upper_mesh)
bpy.context.collection.objects.link(upper_surface)
upper_surface.parent = upper_group
upper_surface.data.materials.append(material('Coal7 / translucent roof', (0.38, 0.25, 0.09), 0.13))
add_slab_edges('Coal7', upper_data['seam'], upper_group, (0.65, 0.37, 0.08))
upper_road_material = material('Coal7 CAD traces', (1, 0.64, 0.18))
for index, trace in enumerate(upper_data['roadways']):
    curve = bpy.data.curves.new(f'Coal7_CAD_{trace["handle"]}_{index}', 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = 1.2
    curve.bevel_resolution = 2
    spline = curve.splines.new('POLY')
    spline.points.add(len(trace['points']) - 1)
    for vertex, point in zip(spline.points, trace['points']):
        vertex.co = (*mine_to_blender(point), 1)
    roadway = bpy.data.objects.new(curve.name, curve)
    bpy.context.collection.objects.link(roadway)
    roadway.parent = upper_group
    roadway.data.materials.append(upper_road_material)
    roadway['source_handle'] = trace['handle']
bpy.context.scene['georef_id'] = data['meta']['id']
bpy.context.scene['mine_origin'] = origin
bpy.context.scene['limitations'] = '\n'.join(data['meta']['limitations'])
output = ROOT / 'public/models/hongyang-coal12-georef.glb'
bpy.ops.object.select_all(action='SELECT')
for selected in list(bpy.context.selected_objects):
    if selected.type == 'CURVE':
        bpy.context.view_layer.objects.active = selected
        bpy.ops.object.convert(target='MESH')
bpy.ops.export_scene.gltf(filepath=str(output), export_format='GLB', export_yup=True, export_extras=True)
risk_mesh = bpy.data.meshes.new('Surfer risk grid / mine coordinates')
risk_indices = data['risk']['indices']
risk_mesh.from_pydata([to_blender(point) for point in data['risk']['vertices']], [],
                     [risk_indices[index:index + 3] for index in range(0, len(risk_indices), 3)])
risk_mesh.update()
risk_attribute = risk_mesh.color_attributes.new(name='RiskColor', type='FLOAT_COLOR', domain='POINT')
for vertex_color, color in zip(risk_attribute.data, data['risk']['colors']):
    vertex_color.color_srgb = (*color, 1)
risk_object = bpy.data.objects.new('Surfer_W_Coordinate_Grid', risk_mesh)
bpy.context.collection.objects.link(risk_object)
risk_material = material('W / Surfer grid color', (1, 1, 1))
attribute = risk_material.node_tree.nodes.new('ShaderNodeVertexColor')
attribute.layer_name = 'RiskColor'
shader = risk_material.node_tree.nodes.get('Principled BSDF')
risk_material.node_tree.links.new(attribute.outputs['Color'], shader.inputs['Base Color'])
risk_material.node_tree.links.new(attribute.outputs['Color'], shader.inputs['Emission Color'])
shader.inputs['Emission Strength'].default_value = 0.3
risk_object.data.materials.append(risk_material)
events_collection = bpy.data.collections.new('Original XYZ events / toggle visibility to inspect depth')
bpy.context.scene.collection.children.link(events_collection)
event_material = material('Microseismic events', (0.8, 1, 0.95))
for event in data['events']:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.8,
                                        location=mine_to_blender([event['x'], event['y'], event['z']]))
    marker = bpy.context.object
    marker.name = event['id']
    marker['mine_coordinates'] = [event['x'], event['y'], event['z']]
    marker['energy_j'] = event['energy_j']
    marker['risk_value'] = event['risk_value']
    marker.data.materials.append(event_material)
    for collection in list(marker.users_collection):
        collection.objects.unlink(marker)
    events_collection.objects.link(marker)
bpy.ops.object.camera_add(location=(750, -850, 950))
camera = bpy.context.object
target = Vector((20, -45, 0))
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 1250
bpy.context.scene.camera = camera
bpy.ops.object.light_add(type='SUN', location=(0, 0, 900))
bpy.context.object.data.energy = 2
bpy.context.scene.world.color = (0.09, 0.09, 0.09)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_distance = 1300
            area.spaces.active.region_3d.view_location = target
            area.spaces.active.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
            area.spaces.active.shading.type = 'MATERIAL'
bpy.ops.object.select_all(action='DESELECT')
risk_object.select_set(True)
bpy.context.view_layer.objects.active = risk_object
bpy.context.preferences.filepaths.save_version = 0
blend_path = ROOT / 'database/hongyang-coal12-georef.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
print('Generated', output, 'and', blend_path)
