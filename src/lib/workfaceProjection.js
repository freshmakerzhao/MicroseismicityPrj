const clamp01 = (value) => Math.max(0, Math.min(1, value))

export const DEFAULT_WORKFACE_REGION = Object.freeze({
  xMin: 0.508,
  xMax: 0.727,
  zMin: 0.242,
  zMax: 0.861,
})

export function createWorkfaceBounds(modelBox, region = DEFAULT_WORKFACE_REGION) {
  const sizeX = modelBox.max.x - modelBox.min.x
  const sizeZ = modelBox.max.z - modelBox.min.z
  return {
    xMin: modelBox.min.x + sizeX * region.xMin,
    xMax: modelBox.min.x + sizeX * region.xMax,
    zMin: modelBox.min.z + sizeZ * region.zMin,
    zMax: modelBox.min.z + sizeZ * region.zMax,
  }
}

export function planarPointToUv(point, bounds) {
  const xSpan = Math.max(bounds.xMax - bounds.xMin, Number.EPSILON)
  const ySpan = Math.max(bounds.yMax - bounds.yMin, Number.EPSILON)
  return {
    u: clamp01((point.x - bounds.xMin) / xSpan),
    v: clamp01(1 - (point.y - bounds.yMin) / ySpan),
  }
}

export function uvToWorkface(uv, workfaceBounds) {
  return {
    x: workfaceBounds.xMin + (workfaceBounds.xMax - workfaceBounds.xMin) * clamp01(uv.u),
    z: workfaceBounds.zMin + (workfaceBounds.zMax - workfaceBounds.zMin) * clamp01(uv.v),
  }
}
