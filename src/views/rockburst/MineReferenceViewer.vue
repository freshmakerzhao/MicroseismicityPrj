<template>
  <div class="reference-viewer">
    <div ref="canvasHost" class="reference-canvas"></div>
    <div class="reference-heading">
      <strong>井下地图 1.0 · 巷道云图展示</strong>
      <span>hangdao.glb · 当前冲击危险云图</span>
      <small>云图沿巷道坡度铺设，位置为展示配准</small>
    </div>
    <div class="reference-controls">
      <button :disabled="loading" @click="resetView">参考视角</button>
      <button :disabled="!cloudReady" @click="toggleCloud">{{ cloudVisible ? '隐藏云图' : '显示云图' }}</button>
      <button :disabled="!cloudReady" @click="rotateCloud">旋转云图</button>
      <label>导入贴图 <input type="file" accept="image/png,image/jpeg" @change="importTexture" /></label>
      <label><input v-model="cropMargins" type="checkbox" @change="reloadCloud" />裁去默认云图边框</label>
      <label>透明度 <input v-model.number="opacity" type="range" min="0.25" max="1" step="0.05" @input="updateOpacity" /></label>
      <span>拖动旋转 · 滚轮缩放</span>
    </div>
    <div v-if="loading" class="reference-message">正在加载巷道模型与云图…</div>
    <div v-if="errorMessage" class="reference-error">{{ errorMessage }}</div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

const props = defineProps({ cloudImageUrl: { type: String, default: '/defaults/hongyang-rockburst-warning-map.png' } })
const canvasHost = ref(null)
const loading = ref(true)
const cloudVisible = ref(true)
const cloudReady = ref(false)
const opacity = ref(0.92)
const errorMessage = ref('')
const cropMargins = ref(true)
let localTextureUrl = ''
let rotation = 0
let renderer, scene, camera, controls, resizeObserver, animationFrame
let model, cloudMesh, cloudMaterial, cloudTexture, modelBounds
let disposed = false
let textureRequest = 0

function disposeModel(root) {
  root?.traverse(object => {
    object.geometry?.dispose()
    const materials = Array.isArray(object.material) ? object.material : [object.material]
    materials.forEach(material => {
      if (!material) return
      Object.values(material).forEach(value => { if (value?.isTexture) value.dispose() })
      material.dispose()
    })
  })
}

function createCloudSurface() {
  const rail = model.getObjectByName('巷道011')
  if (!rail?.isMesh) throw new Error('hangdao.glb 中缺少工作面边界巷道')
  rail.material.side = THREE.DoubleSide
  const bounds = new THREE.Box3().setFromObject(rail)
  const minX = bounds.min.x + 0.06, maxX = bounds.max.x - 0.06
  const minZ = -9.48, maxZ = 3.65
  const columns = 96, rows = 128
  const raycaster = new THREE.Raycaster()
  const heights = []
  for (let column = 0; column <= columns; column += 1) {
    const east = minX + column / columns * (maxX - minX)
    raycaster.set(new THREE.Vector3(east, modelBounds.max.y + 5, (bounds.min.z + bounds.max.z) / 2), new THREE.Vector3(0, -1, 0))
    const hit = raycaster.intersectObject(rail)[0]
    if (!hit) throw new Error(`工作面坡度采样失败：${column}`)
    heights.push(hit.point.y - 0.012)
  }
  const positions = [], uvs = [], indices = []
  for (let row = 0; row <= rows; row += 1) {
    for (let column = 0; column <= columns; column += 1) {
      positions.push(minX + column / columns * (maxX - minX), heights[column], minZ + row / rows * (maxZ - minZ))
      uvs.push(column / columns, row / rows)
    }
  }
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const first = row * (columns + 1) + column, second = first + columns + 1
      indices.push(first, second, first + 1, first + 1, second, second + 1)
    }
  }
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2))
  geometry.setIndex(indices)
  geometry.computeVertexNormals()
  cloudMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: opacity.value,
    side: THREE.DoubleSide, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 })
  cloudMesh = new THREE.Mesh(geometry, cloudMaterial)
  cloudMesh.name = 'hangdao-draped-project-cloud'
  cloudMesh.visible = false
  scene.add(cloudMesh)
}

async function loadCloud(url) {
  const request = ++textureRequest
  if (!url) { errorMessage.value = '当前没有云图，请先在冲击危险云图页面生成。'; return }
  try {
    const source = await new THREE.TextureLoader().loadAsync(url)
    if (disposed || request !== textureRequest) { source.dispose(); return }
    const image = source.image
    const canvas = document.createElement('canvas')
    const crop = cropMargins.value
      ? { x: image.width * (42 / 777), y: image.height * (31 / 451), width: image.width * (628 / 777), height: image.height * (380 / 451) }
      : { x: 0, y: 0, width: image.width, height: image.height }
    canvas.width = Math.round(crop.height)
    canvas.height = Math.round(crop.width)
    const context = canvas.getContext('2d')
    context.translate(canvas.width, 0)
    context.rotate(Math.PI / 2)
    context.drawImage(image, crop.x, crop.y, crop.width, crop.height, 0, 0, crop.width, crop.height)
    source.dispose()
    const next = new THREE.CanvasTexture(canvas)
    next.colorSpace = THREE.SRGBColorSpace
    next.anisotropy = renderer.capabilities.getMaxAnisotropy()
    next.center.set(0.5, 0.5)
    next.rotation = rotation
    cloudTexture?.dispose()
    cloudTexture = next
    cloudMaterial.map = next
    cloudMaterial.needsUpdate = true
    cloudMesh.visible = cloudVisible.value
    cloudReady.value = true
    errorMessage.value = ''
  } catch (error) {
    if (!disposed && request === textureRequest) errorMessage.value = `云图加载失败：${error.message}`
  }
}

function resize() {
  if (!renderer || !canvasHost.value) return
  const width = canvasHost.value.clientWidth, height = canvasHost.value.clientHeight
  if (!width || !height) return
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

function resetView() {
  if (!modelBounds) return
  const center = modelBounds.getCenter(new THREE.Vector3())
  const size = modelBounds.getSize(new THREE.Vector3())
  const span = Math.max(size.x, size.y, size.z)
  camera.position.set(center.x + span * 0.95, center.y + span * 0.85, center.z + span * 1.15)
  controls.target.copy(center)
  controls.update()
}

function toggleCloud() {
  cloudVisible.value = !cloudVisible.value
  if (cloudMesh) cloudMesh.visible = cloudVisible.value && cloudReady.value
}
function rotateCloud() { rotation += Math.PI / 2; if (cloudTexture) cloudTexture.rotation = rotation }
function reloadCloud() { if (cloudMaterial) loadCloud(localTextureUrl || props.cloudImageUrl) }
function importTexture(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (!['image/png', 'image/jpeg'].includes(file.type) || file.size > 20 * 1024 * 1024) {
    errorMessage.value = '请选择不超过 20 MB 的 PNG/JPG 贴图'; return
  }
  if (localTextureUrl) URL.revokeObjectURL(localTextureUrl)
  localTextureUrl = URL.createObjectURL(file)
  cropMargins.value = false
  reloadCloud()
}
function updateOpacity() { if (cloudMaterial) cloudMaterial.opacity = opacity.value }

watch(() => props.cloudImageUrl, url => {
  if (localTextureUrl) URL.revokeObjectURL(localTextureUrl)
  localTextureUrl = ''
  if (cloudMaterial) loadCloud(url)
})

onMounted(async () => {
  try {
    scene = new THREE.Scene()
    scene.background = new THREE.Color(0x07101c)
    renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    canvasHost.value.appendChild(renderer.domElement)
    camera = new THREE.PerspectiveCamera(42, 1, 0.01, 1000)
    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    scene.add(new THREE.HemisphereLight(0xd0efff, 0x283344, 2.2))
    const light = new THREE.DirectionalLight(0xffffff, 2)
    light.position.set(8, 20, 12)
    scene.add(light)
    resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(canvasHost.value)
    resize()
    const animate = () => {
      animationFrame = requestAnimationFrame(animate)
      controls.update()
      renderer.render(scene, camera)
    }
    animate()
    const gltf = await new GLTFLoader().loadAsync('/models/hangdao.glb')
    if (disposed) { disposeModel(gltf.scene); return }
    model = gltf.scene
    model.name = 'user-hangdao-model'
    model.traverse(object => {
      if (!object.isMesh) return
      const materials = Array.isArray(object.material) ? object.material : [object.material]
      materials.forEach(material => {
        material.color.set(0xc0d3db)
        material.roughness = 0.7
        material.metalness = 0.1
      })
    })
    scene.add(model)
    model.updateMatrixWorld(true)
    modelBounds = new THREE.Box3().setFromObject(model)
    createCloudSurface()
    resetView()
    await loadCloud(props.cloudImageUrl)
  } catch (error) {
    if (!disposed) errorMessage.value = `巷道模型加载失败：${error.message}`
  } finally {
    if (!disposed) loading.value = false
  }
})

onBeforeUnmount(() => {
  disposed = true
  if (localTextureUrl) URL.revokeObjectURL(localTextureUrl)
  textureRequest += 1
  cancelAnimationFrame(animationFrame)
  resizeObserver?.disconnect()
  controls?.dispose()
  disposeModel(scene)
  renderer?.dispose()
  renderer?.domElement.remove()
})
</script>

<style scoped>
.reference-viewer, .reference-canvas { position: relative; width: 100%; height: 100%; overflow: hidden; }
.reference-heading { position: absolute; top: 38px; left: 12%; display: flex; flex-direction: column; gap: 8px; pointer-events: none; }
.reference-heading strong { color: #dce9ee; font-size: 17px; letter-spacing: 2px; }
.reference-heading span { color: #a4b9c6; font-size: 12px; }
.reference-heading small { color: #7792a1; font-size: 11px; }
.reference-controls { position: absolute; bottom: 26px; left: 0; right: 0; display: flex; align-items: center; justify-content: center; gap: 12px; }
.reference-controls button { border: 1px solid #31768b; color: #bbebf9; background: #0a2639; padding: 8px 14px; cursor: pointer; }
.reference-controls button:hover { background: #15435b; }
.reference-controls button:disabled { opacity: 0.4; cursor: default; }
.reference-controls span, .reference-controls label { color: #7d9ca9; font-size: 12px; }
.reference-controls label { display: flex; gap: 8px; align-items: center; }
.reference-controls input { width: 90px; }
.reference-controls { flex-wrap: wrap; padding: 0 12px; }
.reference-controls input[type="checkbox"] { width: auto; }
.reference-controls input[type="file"] { width: 150px; }
.reference-error, .reference-message { position: absolute; top: 50%; left: 20%; color: #ffa0a0; }
.reference-message { color: #b9e6f0; }
</style>
