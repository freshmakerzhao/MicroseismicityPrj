import hashlib
import json
import math
import re
import struct
from collections import defaultdict
from pathlib import Path

import ezdxf
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import Delaunay
from ezdxf import path as dxf_path
from build_mine3d import clip_polygon_to_bbox


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'public' / 'defaults' / 'hongyang-coal12-georef.json'
SMALL = ROOT / '资料' / '平面' / 'out' / 'hoangyangDraw.dxf'
BIG = ROOT / '资料' / '数据源' / 'out' / '红阳三矿采掘工程图10.28.dxf'
GRID = ROOT / '资料' / '红阳矿区微震预警判据.grd'
EVENTS = ROOT / 'public' / 'defaults' / 'hongyang-microseismic-events.json'


def read_surfer_grid(filename):
    data = filename.read_bytes()
    if data[:4] != b'DSRB':
        raise ValueError('Expected Surfer 7 binary grid')
    cursor = 12
    metadata = None
    values = None
    while cursor + 8 <= len(data):
        tag, length = struct.unpack_from('<4sI', data, cursor)
        cursor += 8
        if tag == b'GRID':
            metadata = struct.unpack_from('<ii8d', data, cursor)
        elif tag == b'DATA':
            values = np.frombuffer(data[cursor:cursor + length], dtype='<f8').copy()
        cursor += length
    if metadata is None or values is None:
        raise ValueError('Missing GRID or DATA section')
    rows, columns, east, north, east_step, north_step, low, high, rotation, blank = metadata
    if rotation != 0 or len(values) != rows * columns:
        raise ValueError('Unsupported grid rotation or invalid grid size')
    return {
        'rows': rows, 'columns': columns,
        'mineXMin': north, 'mineYMin': east,
        'mineXStep': north_step, 'mineYStep': east_step,
        'rawRange': [low, high], 'blank': blank,
        'axisMapping': 'Surfer column axis = mine Y; row axis = mine X',
    }, values.reshape(rows, columns)


def transform(point, origin):
    return [point[0] - origin[0], point[2] - origin[2], -(point[1] - origin[1])]


def risk_color(value):
    stops = [(0, [0.05, 0.55, 0.62]), (0.25, [0.20, 0.84, 0.63]),
             (0.5, [1, 0.86, 0.18]), (0.75, [1, 0.36, 0.12]), (1, [0.90, 0.07, 0.21])]
    value = min(1, max(0, value))
    for index in range(1, len(stops)):
        upper, right = stops[index]
        lower, left = stops[index - 1]
        if value <= upper:
            weight = (value - lower) / (upper - lower)
            return [left[channel] * (1 - weight) + right[channel] * weight for channel in range(3)]


def clipped_seam(coordinates, triangulation, origin, bounds):
    clip_bounds = [bounds['xMin'] - 100, bounds['yMin'] - 100, bounds['xMax'] + 100, bounds['yMax'] + 100]
    vertices, indices = [], []
    for triangle in triangulation.simplices:
        polygon = clip_polygon_to_bbox(coordinates[triangle, :2].tolist(), clip_bounds)
        if len(polygon) < 4:
            continue
        polygon = polygon[:-1]
        offset = len(vertices)
        coefficients = np.linalg.solve(np.column_stack((coordinates[triangle, :2], np.ones(3))), coordinates[triangle, 2])
        vertices.extend(transform([point[0], point[1], float(np.dot([*point, 1], coefficients))], origin) for point in polygon)
        for index in range(1, len(polygon) - 1):
            indices.extend([offset, offset + index, offset + index + 1])
    return {'vertices': vertices, 'indices': indices}


def main():
    payload = json.loads(EVENTS.read_text(encoding='utf-8-sig'))
    bounds = payload['meta']['bounds']
    origin = [4500.0, 7800.0, -1040.0]
    small = ezdxf.readfile(SMALL)
    big = ezdxf.readfile(BIG)
    clustered = defaultdict(list)
    rejected = []
    for entity in big.modelspace():
        if entity.dxf.layer != '12煤标高' or entity.dxftype() not in ('TEXT', 'MTEXT'):
            continue
        position = entity.dxf.insert
        if not (bounds['xMin'] - 300 <= position.x <= bounds['xMax'] + 300 and
                bounds['yMin'] - 300 <= position.y <= bounds['yMax'] + 300):
            continue
        raw = entity.dxf.text if entity.dxftype() == 'TEXT' else entity.plain_text()
        raw = raw.strip()
        if not re.fullmatch(r'-?\d+(\.\d+)?', raw):
            rejected.append({'handle': entity.dxf.handle, 'text': raw, 'reason': 'non-numeric'})
            continue
        height = float(raw)
        if not -1400 <= height <= -700:
            rejected.append({'handle': entity.dxf.handle, 'text': raw, 'reason': 'outside coal12 review window'})
            continue
        clustered[(round(position.x, 4), round(position.y, 4))].append((height, entity.dxf.handle))
    samples = []
    for position, entries in sorted(clustered.items()):
        samples.append({'mine': [*position, float(np.median([entry[0] for entry in entries]))],
                        'handles': [entry[1] for entry in entries]})
    coordinates = np.array([sample['mine'] for sample in samples])
    triangulation = Delaunay(coordinates[:, :2])
    interpolator = LinearNDInterpolator(triangulation, coordinates[:, 2])

    def elevation(east, north):
        height = float(interpolator(east, north))
        return height if math.isfinite(height) else None

    grid_meta, grid_values = read_surfer_grid(GRID)
    expected = [bounds['xMin'], bounds['yMin'], bounds['xMax'], bounds['yMax']]
    actual = [grid_meta['mineXMin'], grid_meta['mineYMin'],
              grid_meta['mineXMin'] + (grid_meta['rows'] - 1) * grid_meta['mineXStep'],
              grid_meta['mineYMin'] + (grid_meta['columns'] - 1) * grid_meta['mineYStep']]
    if not np.allclose(expected, actual, atol=0.001, rtol=0):
        raise ValueError(f'Grid and event extents disagree: {expected} vs {actual}')
    vertices, colors, indices, valid, raw_values = [], [], [], [], []
    for row in range(grid_meta['rows']):
        for column in range(grid_meta['columns']):
            east = grid_meta['mineXMin'] + row * grid_meta['mineXStep']
            north = grid_meta['mineYMin'] + column * grid_meta['mineYStep']
            height = elevation(east, north)
            value = float(grid_values[row, column])
            usable = height is not None and math.isfinite(value) and value < grid_meta['blank']
            valid.append(usable)
            vertices.append(transform([east, north, (height if height is not None else origin[2]) + 0.25], origin))
            colors.append(risk_color(value) if usable else [0, 0, 0])
            raw_values.append(value if math.isfinite(value) and value < grid_meta['blank'] else None)
    for row in range(grid_meta['rows'] - 1):
        for column in range(grid_meta['columns'] - 1):
            first = row * grid_meta['columns'] + column
            second = first + grid_meta['columns']
            for triangle in ([first, second, first + 1], [first + 1, second, second + 1]):
                if all(valid[index] for index in triangle):
                    indices.extend(triangle)
    roadways = []
    for entity in small.modelspace():
        if entity.dxf.layer not in ('12煤巷道', '12煤巷') or entity.dxftype() not in ('LINE', 'LWPOLYLINE', 'POLYLINE'):
            continue
        flattened = list(dxf_path.make_path(entity).flattening(0.25))
        run = []
        for start, end in zip(flattened, flattened[1:]):
            length = (end - start).magnitude
            steps = max(1, math.ceil(length / 8))
            for step in range(steps):
                point = start.lerp(end, step / steps)
                height = elevation(point.x, point.y)
                if height is None or not (bounds['xMin'] - 100 <= point.x <= bounds['xMax'] + 100 and bounds['yMin'] - 100 <= point.y <= bounds['yMax'] + 100):
                    if len(run) > 1:
                        roadways.append({'handle': entity.dxf.handle, 'points': run})
                    run = []
                else:
                    run.append([point.x, point.y, height])
        if flattened:
            point = flattened[-1]
            height = elevation(point.x, point.y)
            if height is not None and bounds['xMin'] - 100 <= point.x <= bounds['xMax'] + 100 and bounds['yMin'] - 100 <= point.y <= bounds['yMax'] + 100:
                run.append([point.x, point.y, height])
        if len(run) > 1:
            roadways.append({'handle': entity.dxf.handle, 'points': run})
    controls = []
    for entity in small.modelspace().query('CIRCLE'):
        if entity.dxf.layer == '12煤测点':
            point = entity.dxf.center
            height = elevation(point.x, point.y)
            if height is not None:
                controls.append({'id': entity.dxf.handle, 'mine': [point.x, point.y, height],
                                 'scene': transform([point.x, point.y, height], origin)})
    events = []
    for event in payload['events']:
        height = elevation(event['x'], event['y'])
        events.append({**event, 'scene': transform([event['x'], event['y'], event['z']], origin),
                       'surface': transform([event['x'], event['y'], height + 0.6], origin) if height is not None else None,
                       'seamElevation': height})
    validation = {
        'gridExtentError': float(np.max(np.abs(np.array(expected) - actual))),
        'events': len(events), 'surfaceEvents': sum(event['surface'] is not None for event in events),
        'gridNodes': len(vertices), 'supportedGridNodes': sum(valid),
        'annotationSamples': len(samples), 'rejectedAnnotations': rejected,
        'controlPoints': len(controls),
        'note': 'DXF round-trip checks are pipeline checks, not independent survey validation.',
    }
    upper = build_upper_layer(big, small, bounds, origin)
    data = {
        'meta': {'id': 'hongyang-coal12-local-v1', 'origin': origin, 'units': 'assumed meters',
                 'dxfInsunits': small.header.get('$INSUNITS'), 'bounds': bounds,
                 'transform': '[X-X0, Z-Z0, -(Y-Y0)]',
                 'limitations': ['DXF INSUNITS=4 (mm) conflicts with numeric mine coordinates; meters assumed pending survey confirmation.',
                                'Heights interpolated from TEXT insertion positions, not verified survey anchors.',
                                'Roadway lines are CAD traces; displayed tube widths are schematic, not measured cross-sections.',
                                'Rectangular risk extent is not an identified working-face boundary.',
                                'Mine datum, axis naming and source dates require external confirmation.'],
                 'sources': [{'path': str(filename.relative_to(ROOT)).replace('\\', '/'),
                              'sha256': hashlib.sha256(filename.read_bytes()).hexdigest()}
                             for filename in (SMALL, BIG, GRID, EVENTS)]},
        'elevationSamples': samples,
        'seam': clipped_seam(coordinates, triangulation, origin, bounds),
        'roadways': roadways, 'controls': controls, 'events': events,
        'risk': {'vertices': vertices, 'colors': colors, 'indices': indices,
                 'values': raw_values, 'grid': grid_meta},
        'validation': validation,
        'upperLayer': upper,
    }
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False), encoding='utf-8')
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    print('Coal7:', len(upper['samples']), 'height anchors;', len(upper['roadways']), 'CAD traces')


def build_upper_layer(big, small, bounds, origin):
    grouped = defaultdict(list)
    for entity in big.modelspace():
        if entity.dxf.layer != '7煤标高' or entity.dxftype() not in ('TEXT', 'MTEXT'):
            continue
        position = entity.dxf.insert
        raw = (entity.dxf.text if entity.dxftype() == 'TEXT' else entity.plain_text()).strip()
        if not re.fullmatch(r'-?\d+(\.\d+)?', raw):
            continue
        height = float(raw)
        if (bounds['xMin'] - 300 <= position.x <= bounds['xMax'] + 300 and
                bounds['yMin'] - 300 <= position.y <= bounds['yMax'] + 300 and -1400 <= height <= -700):
            grouped[(round(position.x, 4), round(position.y, 4))].append((height, entity.dxf.handle))
    samples = [{'mine': [*position, float(np.median([value[0] for value in heights]))],
                'handles': [value[1] for value in heights]} for position, heights in sorted(grouped.items())]
    coordinates = np.array([sample['mine'] for sample in samples])
    triangulation = Delaunay(coordinates[:, :2])
    interpolator = LinearNDInterpolator(triangulation, coordinates[:, 2])
    roadways = []
    for entity in small.modelspace():
        if entity.dxf.layer not in ('7煤巷道', '7煤巷') or entity.dxftype() not in ('LINE', 'LWPOLYLINE', 'POLYLINE'):
            continue
        path = list(dxf_path.make_path(entity).flattening(0.25))
        points = []
        for start, end in zip(path, path[1:]):
            steps = max(1, math.ceil((end - start).magnitude / 8))
            points.extend(start.lerp(end, step / steps) for step in range(steps))
        if path:
            points.append(path[-1])
        run = []
        for point in points:
            height = float(interpolator(point.x, point.y))
            if math.isfinite(height) and bounds['xMin'] - 100 <= point.x <= bounds['xMax'] + 100 and bounds['yMin'] - 100 <= point.y <= bounds['yMax'] + 100:
                run.append([point.x, point.y, height])
            else:
                if len(run) > 1:
                    roadways.append({'handle': entity.dxf.handle, 'points': run})
                run = []
        if len(run) > 1:
            roadways.append({'handle': entity.dxf.handle, 'points': run})
    return {'name': '7煤', 'samples': samples, 'roadways': roadways,
            'seam': clipped_seam(coordinates, triangulation, origin, bounds)}


if __name__ == '__main__':
    main()
