import test from "node:test"
import assert from "node:assert/strict"

import {
  createWorkfaceBounds,
  planarPointToUv,
  uvToWorkface,
} from "../src/lib/workfaceProjection.js"

test("creates a model-relative workface footprint", () => {
  const bounds = createWorkfaceBounds(
    { min: { x: -10, z: -20 }, max: { x: 10, z: 20 } },
    { xMin: 0.25, xMax: 0.75, zMin: 0.1, zMax: 0.9 }
  )

  assert.deepEqual(bounds, { xMin: -5, xMax: 5, zMin: -16, zMax: 16 })
})

test("rotates planar mine coordinates into the risk texture UV orientation", () => {
  const sourceBounds = { xMin: 4400, xMax: 4700, yMin: 7500, yMax: 8100 }

  assert.deepEqual(planarPointToUv({ x: 4400, y: 7500 }, sourceBounds), { u: 0, v: 1 })
  assert.deepEqual(planarPointToUv({ x: 4700, y: 8100 }, sourceBounds), { u: 1, v: 0 })
})

test("maps UV coordinates onto the 3D workface footprint", () => {
  const point = uvToWorkface(
    { u: 0.25, v: 0.75 },
    { xMin: 2, xMax: 10, zMin: -6, zMax: 2 }
  )

  assert.deepEqual(point, { x: 4, z: 0 })
})
