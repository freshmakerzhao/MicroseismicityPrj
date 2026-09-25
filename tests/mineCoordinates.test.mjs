import test from "node:test"
import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import * as THREE from "three"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js"
import { mineToScene, sceneToMine, georeferencedObservations, riskRgb } from "../src/lib/mineCoordinates.js"

const data = JSON.parse(readFileSync(new URL('../public/defaults/hongyang-coal12-georef.json', import.meta.url)))

test("projected events sit on the displayed cloud mesh, not a different interpolated surface", () => {
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(data.risk.vertices.flat(), 3))
  geometry.setIndex(data.risk.indices)
  geometry.computeBoundingBox()
  const cloud = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }))
  cloud.updateMatrixWorld(true)
  const raycaster = new THREE.Raycaster()
  const projected = georeferencedObservations(data, 'surface')
  const errors = projected.map(point => {
    const east = THREE.MathUtils.clamp(point.x, geometry.boundingBox.min.x + 0.0001, geometry.boundingBox.max.x - 0.0001)
    const north = THREE.MathUtils.clamp(point.z, geometry.boundingBox.min.z + 0.0001, geometry.boundingBox.max.z - 0.0001)
    raycaster.set(new THREE.Vector3(east, 1000, north), new THREE.Vector3(0, -1, 0))
    const hit = raycaster.intersectObject(cloud)[0]
    assert.ok(hit, point.id)
    return Math.abs(point.y - hit.point.y - 0.6)
  })
  assert.ok(Math.max(...errors) < 0.001, `Maximum cloud / point height mismatch: ${Math.max(...errors).toFixed(3)} m`)
})

test("original event positions survive a mine / renderer coordinate round-trip", () => {
  for (const event of data.events) {
    const restored = sceneToMine(mineToScene(event, data.meta.origin), data.meta.origin)
    for (const axis of ["x", "y", "z"]) assert.ok(Math.abs(restored[axis] - event[axis]) < 1e-9)
  }
  const first = data.events[0]
  assert.deepEqual(mineToScene(first, data.meta.origin), { x: first.x - 4500, y: first.z + 1040, z: 7800 - first.y })
})

test("surface projection changes height only and preserves original elevation", () => {
  const native = georeferencedObservations(data, "native")
  const projected = georeferencedObservations(data, "surface")
  assert.equal(native.length, 301)
  assert.equal(projected.length, 301)
  for (let index = 0; index < native.length; index += 1) {
    assert.equal(native[index].x, projected[index].x)
    assert.equal(native[index].z, projected[index].z)
    assert.equal(native[index].sourceZ, projected[index].sourceZ)
  }
  assert.ok(native.some((point, index) => Math.abs(point.y - projected[index].y) > 1))
})

test("Surfer axis swap preserves all four physical grid bounds", () => {
  const first = sceneToMine(new THREE.Vector3(...data.risk.vertices[0]), data.meta.origin)
  const last = sceneToMine(new THREE.Vector3(...data.risk.vertices.at(-1)), data.meta.origin)
  assert.equal(first.x, data.meta.bounds.xMin)
  assert.equal(first.y, data.meta.bounds.yMin)
  assert.equal(last.x, data.meta.bounds.xMax)
  assert.equal(last.y, data.meta.bounds.yMax)
  assert.equal(data.risk.vertices.length, 5800)
})

test("point colors and the cloud use the same W scale, including values above one", () => {
  for (let index = 0; index < data.risk.values.length; index += 1) {
    const expected = riskRgb(data.risk.values[index])
    for (let channel = 0; channel < 3; channel += 1) {
      assert.ok(Math.abs(expected[channel] - data.risk.colors[index][channel]) < 1e-9)
    }
  }
  assert.deepEqual(riskRgb(1.1), riskRgb(1))
})

test("Blender GLB retains nine CAD control coordinates within 1 mm", async () => {
  const buffer = readFileSync(new URL('../public/models/hongyang-coal12-georef.glb', import.meta.url))
  const gltf = await new GLTFLoader().parseAsync(buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength), "")
  gltf.scene.updateMatrixWorld(true)
  assert.equal(data.controls.length, 9)
  for (const control of data.controls) {
    const object = gltf.scene.getObjectByName('Control_' + control.id)
    assert.ok(object, control.id)
    const actual = object.getWorldPosition(new THREE.Vector3())
    assert.ok(actual.distanceTo(new THREE.Vector3(...control.scene)) < 0.001, control.id)
  }
  const surface = gltf.scene.getObjectByName('Coal12_Interpolated_Surface')
  const upper = gltf.scene.getObjectByName('Coal7_Interpolated_Surface')
  assert.ok(gltf.scene.getObjectByName('Coal7_Layer'))
  assert.ok(gltf.scene.getObjectByName('Coal12_Layer'))
  assert.ok(upper)
  upper.material.side = THREE.DoubleSide
  const raycaster = new THREE.Raycaster()
  for (const event of data.events) {
    raycaster.set(new THREE.Vector3(event.scene[0], 1000, event.scene[2]), new THREE.Vector3(0, -1, 0))
    surface.material.side = THREE.DoubleSide
    const hits = raycaster.intersectObject(surface)
    assert.ok(hits.length, event.id)
    assert.ok(Math.abs(hits[0].point.y - (event.seamElevation - data.meta.origin[2])) < 0.001, event.id)
    const upperHits = raycaster.intersectObject(upper)
    assert.ok(upperHits.length, event.id)
    assert.ok(upperHits[0].point.y > hits[0].point.y, `${event.id}: coal7 must be above coal12`)
  }
})
