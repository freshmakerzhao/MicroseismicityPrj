export function mineToScene(point, origin) {
  if (![point.x, point.y, point.z, ...origin].every(Number.isFinite)) {
    throw new Error("矿井坐标必须为有限数值")
  }
  return { x: point.x - origin[0], y: point.z - origin[2], z: -(point.y - origin[1]) }
}

export function sceneToMine(point, origin) {
  return { x: point.x + origin[0], y: origin[1] - point.z, z: point.y + origin[2] }
}

export function georeferencedObservations(dataset, mode) {
  return dataset.events.flatMap((event) => {
    const native = mineToScene(event, dataset.meta.origin)
    const cloud = sampleCloudAtMine(dataset, event)
    const surface = cloud ? [native.x, cloud.height + 0.6, native.z] : null
    if (mode === "surface" && !surface) return []
    const position = mode === "surface" ? { x: surface[0], y: surface[1], z: surface[2] } : native
    return [{
      ...position, id: event.id, name: "微震事件 " + event.id,
      sourceX: event.x, sourceY: event.y, sourceZ: event.z,
      energyJ: event.energy_j, riskValue: event.risk_value,
      seamElevation: event.seamElevation,
      cloudValue: cloud?.value ?? null,
    }]
  })
}

export function sampleCloudAtMine(dataset, point) {
  const { grid, vertices, values } = dataset.risk
  const rowPosition = (point.x - grid.mineXMin) / grid.mineXStep
  const columnPosition = (point.y - grid.mineYMin) / grid.mineYStep
  if (rowPosition < -1e-8 || columnPosition < -1e-8 || rowPosition > grid.rows - 1 + 1e-8 || columnPosition > grid.columns - 1 + 1e-8) return null
  const row = Math.min(Math.max(0, Math.floor(rowPosition)), grid.rows - 2)
  const column = Math.min(Math.max(0, Math.floor(columnPosition)), grid.columns - 2)
  const rowWeight = Math.min(1, Math.max(0, rowPosition - row))
  const columnWeight = Math.min(1, Math.max(0, columnPosition - column))
  const first = row * grid.columns + column
  const second = first + grid.columns
  const indices = rowWeight + columnWeight <= 1 ? [first, second, first + 1] : [second + 1, first + 1, second]
  const weights = rowWeight + columnWeight <= 1
    ? [1 - rowWeight - columnWeight, rowWeight, columnWeight]
    : [rowWeight + columnWeight - 1, 1 - rowWeight, 1 - columnWeight]
  if (indices.some(index => values[index] == null)) return null
  return {
    height: indices.reduce((sum, index, corner) => sum + vertices[index][1] * weights[corner], 0),
    value: indices.reduce((sum, index, corner) => sum + values[index] * weights[corner], 0),
  }
}

export function riskRgb(value) {
  const stops = [[0, [0.05, 0.55, 0.62]], [0.25, [0.20, 0.84, 0.63]],
    [0.5, [1, 0.86, 0.18]], [0.75, [1, 0.36, 0.12]], [1, [0.90, 0.07, 0.21]]]
  const clamped = Math.min(1, Math.max(0, value))
  for (let index = 1; index < stops.length; index += 1) {
    const [upper, right] = stops[index]
    const [lower, left] = stops[index - 1]
    if (clamped <= upper) {
      const weight = (clamped - lower) / (upper - lower)
      return left.map((channel, channelIndex) => channel * (1 - weight) + right[channelIndex] * weight)
    }
  }
}
