<template>
  <div
    class="mine-glb-viewer"
    :class="{ 'is-dragging': isDragging }"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <div class="viewer-toolbar">
      <div class="model-info">
        <span class="title">井下地图</span>
        <span class="file-name">{{ currentName }}</span>
      </div>
      <div class="viewer-actions">
        <button class="viewer-btn" type="button" :disabled="loading || !observations.length" @click="toggleObservationLayer">
          {{ showObservations ? "隐藏震源" : "显示震源" }}
        </button>
        <button class="viewer-btn" type="button" :disabled="loading || !observations.length" @click="recalculateObservationColors">
          重算颜色
        </button>
        <button class="viewer-btn" type="button" :disabled="loading || !modelRootReady" @click="regenerateSyntheticSources">
          重新生成
        </button>
        <button class="viewer-btn" type="button" :disabled="loading || !modelStats" @click="showModelInfo = !showModelInfo">
          {{ showModelInfo ? "隐藏信息" : "模型信息" }}
        </button>
        <button class="viewer-btn" type="button" :disabled="loading" @click="resetCamera">重置视角</button>
        <button class="viewer-btn primary" type="button" :disabled="loading" @click="fileInputRef && fileInputRef.click()">打开 GLB</button>
        <input
          ref="fileInputRef"
          class="file-input"
          type="file"
          accept=".glb,.gltf,model/gltf-binary,model/gltf+json"
          @change="onFileChange"
        />
      </div>
    </div>

    <div ref="viewerRef" class="viewer-canvas"></div>

    <div v-if="loading" class="state-panel">
      <span class="spinner"></span>
      <span>正在加载模型...</span>
    </div>

    <div v-if="errorMessage" class="error-panel">{{ errorMessage }}</div>

    <div v-if="showModelInfo && modelStats" class="model-stats-panel">
      <div class="panel-title">GLB 模型信息</div>
      <div class="stats-grid">
        <span>节点</span><strong>{{ modelStats.nodeCount }}</strong>
        <span>网格</span><strong>{{ modelStats.meshCount }}</strong>
        <span>顶点</span><strong>{{ formatNumber(modelStats.vertexCount) }}</strong>
        <span>三角面</span><strong>{{ formatNumber(modelStats.triangleCount) }}</strong>
        <span>材质</span><strong>{{ modelStats.materialCount }}</strong>
        <span>动画</span><strong>{{ modelStats.animationCount }}</strong>
      </div>
      <div class="stats-line">尺寸 X/Y/Z：{{ modelStats.sizeText }}</div>
      <div class="stats-line">中心点：{{ modelStats.centerText }}</div>
      <div class="stats-line">假设震源：{{ observations.length }} 个</div>
    </div>

    <div v-if="selectedObservation" class="observation-panel">
      <div class="panel-title">{{ selectedObservation.name }}</div>
      <div>ID：{{ selectedObservation.id }}</div>
      <div>风险值：{{ selectedObservation.riskValue.toFixed(3) }}</div>
      <div>震级：{{ selectedObservation.magnitude.toFixed(1) }}</div>
      <div>埋深：{{ selectedObservation.depth.toFixed(1) }} m</div>
      <div>应力指数：{{ selectedObservation.stressIndex.toFixed(2) }}</div>
      <div>能量指数：{{ selectedObservation.energyIndex.toFixed(2) }}</div>
      <div>坐标：{{ selectedObservation.x.toFixed(2) }}, {{ selectedObservation.y.toFixed(2) }}, {{ selectedObservation.z.toFixed(2) }}</div>
    </div>

    <div class="drop-hint">拖拽 .glb / .gltf 到此处加载；点击彩色震源点查看信息</div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue"
import gsap from "gsap"
import * as THREE from "three"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js"
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js"

const DEFAULT_MODEL = "/models/hangdao.glb"
const SYNTHETIC_POINT_COUNT = 28
const EXCLUDED_SOURCE_IDS = new Set(["MS-008", "MS-013"])

const viewerRef = ref(null)
const fileInputRef = ref(null)
const loading = ref(false)
const isDragging = ref(false)
const currentName = ref("hangdao.glb")
const errorMessage = ref("")
const observations = ref([])
const selectedObservation = ref(null)
const showObservations = ref(true)
const showModelInfo = ref(true)
const modelStats = ref(null)
const modelRootReady = ref(false)

let renderer = null
let scene = null
let camera = null
let controls = null
let loader = null
let raycaster = null
let mouse = null
let modelRoot = null
let pointLayer = null
let animationId = 0
let resizeObserver = null
let objectUrl = ""
let dragDepth = 0
let cameraHome = null
let sceneTimeline = null
let formulaVersion = 0
let currentModelSeed = 1
let currentPointRadius = 0.38

onMounted(async () => {
  initScene()
  loadModel(DEFAULT_MODEL, currentName.value)
  await nextTick()
})

onBeforeUnmount(() => {
  if (sceneTimeline) sceneTimeline.kill()
  disposeObjectUrl()
  disposeModel()
  clearObservationLayer()
  if (resizeObserver) resizeObserver.disconnect()
  window.removeEventListener("resize", resize)
  if (animationId) cancelAnimationFrame(animationId)
  if (controls) controls.dispose()
  if (renderer) {
    renderer.domElement.removeEventListener("click", onCanvasClick)
    renderer.dispose()
    renderer.domElement && renderer.domElement.remove()
  }
})

function initScene() {
  const width = viewerRef.value.clientWidth || 800
  const height = viewerRef.value.clientHeight || 520

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x07101c)

  camera = new THREE.PerspectiveCamera(45, width / height, 0.01, 100000)
  camera.position.set(0, 4, 10)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setSize(width, height)
  if ("outputColorSpace" in renderer) {
    renderer.outputColorSpace = THREE.SRGBColorSpace
  }
  viewerRef.value.appendChild(renderer.domElement)
  renderer.domElement.addEventListener("click", onCanvasClick)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.screenSpacePanning = true

  loader = new GLTFLoader()
  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()
  pointLayer = new THREE.Group()
  pointLayer.name = "synthetic-seismic-source-layer"

  addLights()
  addHelpers()
  scene.add(pointLayer)
  observeResize()
  animate()
}

function addLights() {
  scene.add(new THREE.AmbientLight(0xffffff, 0.65))

  const key = new THREE.DirectionalLight(0xffffff, 1.2)
  key.position.set(6, 10, 8)
  scene.add(key)

  const fill = new THREE.DirectionalLight(0x78c7ff, 0.5)
  fill.position.set(-8, 4, -6)
  scene.add(fill)
}

function addHelpers() {
  const grid = new THREE.GridHelper(20, 20, 0x31506b, 0x203647)
  grid.name = "viewer-grid"
  scene.add(grid)

  const axes = new THREE.AxesHelper(2)
  axes.name = "viewer-axes"
  scene.add(axes)
}

function observeResize() {
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(viewerRef.value)
  window.addEventListener("resize", resize)
}

function resize() {
  if (!renderer || !camera || !viewerRef.value) return
  const width = viewerRef.value.clientWidth
  const height = viewerRef.value.clientHeight
  if (!width || !height) return
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

function animate() {
  animationId = requestAnimationFrame(animate)
  controls && controls.update()
  pointLayer && pointLayer.children.forEach((child, index) => {
    const pulse = 1 + Math.sin(Date.now() * 0.003 + index * 0.7) * 0.08
    const base = child.userData.baseScale || 1
    child.scale.setScalar(base * pulse)
  })
  renderer && scene && camera && renderer.render(scene, camera)
}

function loadModel(url, name) {
  loading.value = true
  errorMessage.value = ""
  currentName.value = name || "model.glb"
  modelRootReady.value = false
  modelStats.value = null
  selectedObservation.value = null
  observations.value = []
  clearObservationLayer()

  loader.load(
    url,
    (gltf) => {
      disposeModel()
      modelRoot = gltf.scene || gltf.scenes[0]
      normalizeMaterials(modelRoot)
      scene.add(modelRoot)
      modelRoot.updateMatrixWorld(true)

      modelStats.value = collectModelStats(modelRoot, gltf)
      currentModelSeed = hashString(`${currentName.value}-${modelStats.value.vertexCount}-${modelStats.value.triangleCount}`)
      currentPointRadius = calculatePointRadius(modelStats.value)
      observations.value = generateSyntheticSources(modelRoot, SYNTHETIC_POINT_COUNT, currentModelSeed)
      renderObservationLayer()

      fitCameraToModel(true)
      modelRootReady.value = true
      loading.value = false
    },
    undefined,
    (error) => {
      loading.value = false
      errorMessage.value = "模型加载失败，请检查文件格式或模型路径。"
      console.error(error)
    }
  )
}

function normalizeMaterials(root) {
  root.traverse((child) => {
    if (!child.isMesh) return
    child.castShadow = false
    child.receiveShadow = true
    const materials = Array.isArray(child.material) ? child.material : [child.material]
    materials.filter(Boolean).forEach((material) => {
      if (material.map && "colorSpace" in material.map) {
        material.map.colorSpace = THREE.SRGBColorSpace
      }
      material.needsUpdate = true
    })
  })
}

function collectModelStats(root, gltf) {
  const materialNames = new Set()
  let nodeCount = 0
  let meshCount = 0
  let vertexCount = 0
  let triangleCount = 0

  root.traverse((child) => {
    nodeCount += 1
    if (!child.isMesh || !child.geometry) return
    meshCount += 1

    const position = child.geometry.attributes && child.geometry.attributes.position
    const index = child.geometry.index
    if (position) vertexCount += position.count
    if (index) {
      triangleCount += Math.floor(index.count / 3)
    } else if (position) {
      triangleCount += Math.floor(position.count / 3)
    }

    const materials = Array.isArray(child.material) ? child.material : [child.material]
    materials.filter(Boolean).forEach((material) => materialNames.add(material.uuid || material.name))
  })

  const box = new THREE.Box3().setFromObject(root)
  const size = box.getSize(new THREE.Vector3())
  const center = box.getCenter(new THREE.Vector3())

  return {
    nodeCount,
    meshCount,
    vertexCount,
    triangleCount,
    materialCount: materialNames.size,
    animationCount: gltf.animations ? gltf.animations.length : 0,
    box,
    size,
    center,
    sizeText: `${formatVectorValue(size.x)} / ${formatVectorValue(size.y)} / ${formatVectorValue(size.z)}`,
    centerText: `${formatVectorValue(center.x)}, ${formatVectorValue(center.y)}, ${formatVectorValue(center.z)}`,
  }
}

function collectSampledWorldVertices(root, maxSamples = 5000) {
  const vertices = []
  root.updateMatrixWorld(true)

  root.traverse((child) => {
    if (vertices.length >= maxSamples) return
    if (!child.isMesh || !child.geometry || !child.geometry.attributes.position) return
    const position = child.geometry.attributes.position
    const localPoint = new THREE.Vector3()
    const stride = Math.max(1, Math.ceil(position.count / Math.max(80, maxSamples / 4)))

    for (let i = 0; i < position.count && vertices.length < maxSamples; i += stride) {
      localPoint.fromBufferAttribute(position, i)
      vertices.push(localPoint.clone().applyMatrix4(child.matrixWorld))
    }
  })

  return vertices
}

function generateSyntheticSources(root, count, seed) {
  const rand = createRandom(seed + formulaVersion * 1009)
  const box = new THREE.Box3().setFromObject(root)
  const size = box.getSize(new THREE.Vector3())
  const center = box.getCenter(new THREE.Vector3())
  const maxSize = Math.max(size.x, size.y, size.z) || 1
  const vertices = collectSampledWorldVertices(root)
  const points = []

  for (let i = 0; i < count; i += 1) {
    let position
    if (vertices.length) {
      const source = vertices[Math.floor(rand() * vertices.length)].clone()
      const inward = 0.04 + rand() * 0.14
      position = source.lerp(center, inward)
      position.x += (rand() - 0.5) * maxSize * 0.012
      position.y += (rand() - 0.5) * maxSize * 0.012
      position.z += (rand() - 0.5) * maxSize * 0.012
    } else {
      position = new THREE.Vector3(
        box.min.x + rand() * size.x,
        box.min.y + rand() * size.y,
        box.min.z + rand() * size.z
      )
    }

    const stressIndex = 0.18 + rand() * 0.82
    const energyIndex = 0.12 + rand() * 0.88
    const faultInfluence = rand()
    const baseValue = 0.16 + rand() * 0.74
    const magnitude = 0.6 + energyIndex * 2.7 + rand() * 0.35
    const depth = Math.abs(position.y - box.max.y)
    const point = {
      id: `MS-${String(i + 1).padStart(3, "0")}`,
      name: `假设震源 ${String(i + 1).padStart(2, "0")}`,
      x: position.x,
      y: position.y,
      z: position.z,
      baseValue,
      stressIndex,
      energyIndex,
      faultInfluence,
      magnitude,
      depth,
    }
    point.riskValue = calculateRiskValue(point)
    points.push(point)
  }

  return points.filter((point) => !EXCLUDED_SOURCE_IDS.has(point.id))
}

function calculatePointRadius(stats) {
  if (!stats) return 0.38
  const maxSize = Math.max(stats.size.x, stats.size.y, stats.size.z) || 1
  return THREE.MathUtils.clamp(maxSize * 0.012, 0.08, 2.2)
}

function fitCameraToModel(animateIntro = false) {
  if (!modelRoot) return
  const box = new THREE.Box3().setFromObject(modelRoot)
  const size = box.getSize(new THREE.Vector3())
  const center = box.getCenter(new THREE.Vector3())
  const maxSize = Math.max(size.x, size.y, size.z) || 1
  const distance = maxSize / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)))

  controls.target.copy(center)
  camera.near = Math.max(distance / 1000, 0.01)
  camera.far = distance * 1000
  camera.position.set(center.x + distance * 0.8, center.y + distance * 0.55, center.z + distance * 1.15)
  camera.updateProjectionMatrix()
  controls.update()
  cameraHome = {
    pos: camera.position.clone(),
    target: controls.target.clone(),
  }

  if (animateIntro) playModelIntro()
}

function playModelIntro() {
  if (!modelRoot || !cameraHome) return
  if (sceneTimeline) sceneTimeline.kill()

  const finalPos = cameraHome.pos.clone()
  const finalTarget = cameraHome.target.clone()
  const startPos = finalPos.clone().multiplyScalar(1.22)
  startPos.y += Math.max(1, finalPos.length() * 0.08)

  modelRoot.scale.setScalar(0.92)
  camera.position.copy(startPos)
  controls.target.set(finalTarget.x, finalTarget.y - Math.max(0.5, finalPos.length() * 0.03), finalTarget.z)
  controls.update()

  sceneTimeline = gsap.timeline({ defaults: { ease: "power3.out" } })
  sceneTimeline
    .to(camera.position, {
      x: finalPos.x,
      y: finalPos.y,
      z: finalPos.z,
      duration: 1.15,
      onUpdate: () => controls && controls.update(),
    }, 0)
    .to(controls.target, {
      x: finalTarget.x,
      y: finalTarget.y,
      z: finalTarget.z,
      duration: 1.15,
      onUpdate: () => controls && controls.update(),
    }, 0)
    .to(modelRoot.scale, { x: 1, y: 1, z: 1, duration: 0.95 }, 0.08)
}

function resetCamera() {
  if (sceneTimeline) sceneTimeline.kill()
  fitCameraToModel(false)
}

function calculateRiskValue(point) {
  const wave = Math.sin(formulaVersion * 0.85 + point.x * 0.31 + point.z * 0.17) * 0.08
  const value =
    point.baseValue * 0.38 +
    point.stressIndex * 0.32 +
    point.energyIndex * 0.2 +
    point.faultInfluence * 0.1 +
    wave
  return Math.max(0, Math.min(1, value))
}

function riskColor(value) {
  if (value >= 0.75) return 0xff4d4f
  if (value >= 0.5) return 0xfaad14
  if (value >= 0.25) return 0xfadb14
  return 0x36cfc9
}

function renderObservationLayer() {
  clearObservationLayer()
  if (!pointLayer) return

  observations.value.forEach((point) => {
    const color = riskColor(point.riskValue)
    const material = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: 0.45,
      roughness: 0.35,
      metalness: 0.05,
    })
    const geometry = new THREE.SphereGeometry(currentPointRadius, 24, 16)
    const mesh = new THREE.Mesh(geometry, material)
    const scale = 0.85 + point.riskValue * 0.7
    mesh.name = point.id
    mesh.position.set(point.x, point.y, point.z)
    mesh.userData = { type: "synthetic-seismic-source", point, baseScale: scale }
    mesh.scale.setScalar(scale)
    pointLayer.add(mesh)
  })
  pointLayer.visible = showObservations.value
}

function clearObservationLayer() {
  if (!pointLayer) return
  while (pointLayer.children.length) {
    const child = pointLayer.children.pop()
    child.geometry && child.geometry.dispose()
    child.material && child.material.dispose()
  }
}

function toggleObservationLayer() {
  showObservations.value = !showObservations.value
  if (pointLayer) pointLayer.visible = showObservations.value
  if (!showObservations.value) selectedObservation.value = null
}

function regenerateSyntheticSources() {
  if (!modelRoot) return
  formulaVersion += 1
  observations.value = generateSyntheticSources(modelRoot, SYNTHETIC_POINT_COUNT, currentModelSeed + formulaVersion * 7919)
  selectedObservation.value = null
  renderObservationLayer()
}

function recalculateObservationColors() {
  formulaVersion += 1
  observations.value = observations.value.map((point) => ({
    ...point,
    riskValue: calculateRiskValue(point),
  }))

  pointLayer.children.forEach((mesh) => {
    const point = observations.value.find((item) => item.id === mesh.userData.point.id)
    if (!point) return
    const color = riskColor(point.riskValue)
    const scale = 0.85 + point.riskValue * 0.7
    mesh.userData.point = point
    mesh.userData.baseScale = scale
    mesh.material.color.set(color)
    mesh.material.emissive.set(color)
  })
}

function onCanvasClick(event) {
  if (!showObservations.value || !pointLayer || !camera || !renderer) return
  const rect = renderer.domElement.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  raycaster.setFromCamera(mouse, camera)

  const hits = raycaster.intersectObjects(pointLayer.children, true)
  selectedObservation.value = hits.length ? hits[0].object.userData.point : null
}

function onFileChange(event) {
  const file = event.target.files && event.target.files[0]
  if (file) loadLocalFile(file)
  event.target.value = ""
}

function onDragEnter() {
  dragDepth += 1
  isDragging.value = true
}

function onDragOver() {
  isDragging.value = true
}

function onDragLeave() {
  dragDepth = Math.max(0, dragDepth - 1)
  isDragging.value = dragDepth > 0
}

function onDrop(event) {
  dragDepth = 0
  isDragging.value = false
  const file = event.dataTransfer.files && event.dataTransfer.files[0]
  if (file) loadLocalFile(file)
}

function loadLocalFile(file) {
  const lowerName = file.name.toLowerCase()
  if (!lowerName.endsWith(".glb") && !lowerName.endsWith(".gltf")) {
    errorMessage.value = "仅支持 .glb 和 .gltf 文件。"
    return
  }
  disposeObjectUrl()
  objectUrl = URL.createObjectURL(file)
  loadModel(objectUrl, file.name)
}

function disposeObjectUrl() {
  if (!objectUrl) return
  URL.revokeObjectURL(objectUrl)
  objectUrl = ""
}

function disposeModel() {
  if (sceneTimeline) sceneTimeline.kill()
  if (!modelRoot) return
  scene.remove(modelRoot)
  modelRoot.traverse((child) => {
    if (child.geometry) child.geometry.dispose()
    if (child.material) {
      const materials = Array.isArray(child.material) ? child.material : [child.material]
      materials.forEach((material) => {
        Object.keys(material).forEach((key) => {
          const value = material[key]
          if (value && value.isTexture) value.dispose()
        })
        material.dispose()
      })
    }
  })
  modelRoot = null
  modelRootReady.value = false
}

function createRandom(seed) {
  let value = seed >>> 0
  return () => {
    value += 0x6d2b79f5
    let next = value
    next = Math.imul(next ^ (next >>> 15), next | 1)
    next ^= next + Math.imul(next ^ (next >>> 7), next | 61)
    return ((next ^ (next >>> 14)) >>> 0) / 4294967296
  }
}

function hashString(value) {
  let hash = 2166136261
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(value || 0)
}

function formatVectorValue(value) {
  return Number.isFinite(value) ? value.toFixed(2) : "0.00"
}
</script>

<style scoped>
.mine-glb-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 42%, rgba(48, 220, 255, 0.12), transparent 34%),
    #07101c;
}

.viewer-canvas {
  position: absolute;
  inset: 0;
}

.viewer-toolbar {
  position: absolute;
  top: 18px;
  left: 22px;
  right: 22px;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  pointer-events: none;
}

.model-info {
  position: relative;
  min-width: 0;
  padding: 10px 14px;
  overflow: hidden;
  border: 1px solid rgba(48, 220, 255, 0.24);
  background: linear-gradient(90deg, rgba(8, 39, 74, 0.76), rgba(8, 39, 74, 0.12));
  color: #d8f3ff;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.45);
}

.model-info::after {
  content: "";
  position: absolute;
  left: -80px;
  top: 0;
  width: 70px;
  height: 100%;
  background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transform: skewX(-18deg);
  animation: glbInfoSweep 5.5s linear infinite;
  pointer-events: none;
}

.title {
  display: block;
  font-size: 18px;
  font-weight: 600;
}

.file-name {
  display: block;
  max-width: 38vw;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #93bdd1;
  font-size: 12px;
}

.viewer-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  pointer-events: auto;
}

.viewer-btn {
  height: 28px;
  padding: 0 12px;
  border: 1px solid rgba(48, 220, 255, 0.55);
  color: #c4f3fe;
  background: linear-gradient(180deg, rgba(21, 91, 127, 0.85), rgba(7, 30, 64, 0.85));
  box-shadow: inset 0 0 12px rgba(48, 220, 255, 0.12);
  cursor: pointer;
}

.viewer-btn.primary {
  border-color: rgba(117, 232, 255, 0.85);
  background: linear-gradient(180deg, rgba(40, 184, 231, 0.7), rgba(16, 95, 144, 0.6));
}

.viewer-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.file-input {
  display: none;
}

.state-panel,
.error-panel {
  position: absolute;
  left: 50%;
  top: 50%;
  z-index: 12;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-width: 220px;
  padding: 18px 22px;
  border: 1px solid rgba(120, 199, 255, 0.4);
  background: rgba(9, 24, 38, 0.92);
  color: #d8f3ff;
}

.error-panel {
  top: auto;
  bottom: 34px;
  color: #ffd9d9;
  border-color: rgba(255, 100, 100, 0.5);
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(117, 232, 255, 0.22);
  border-top-color: #75e8ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.model-stats-panel,
.observation-panel {
  position: absolute;
  z-index: 11;
  min-width: 230px;
  padding: 12px 14px;
  border: 1px solid rgba(120, 199, 255, 0.45);
  background: rgba(9, 24, 38, 0.86);
  color: #d8f3ff;
  font-size: 12px;
  line-height: 1.8;
  pointer-events: none;
}

.model-stats-panel {
  right: 24px;
  top: 66px;
}

.observation-panel {
  left: 22px;
  bottom: 22px;
}

.panel-title {
  margin-bottom: 4px;
  color: #78c7ff;
  font-size: 14px;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: auto minmax(56px, 1fr);
  gap: 2px 14px;
}

.stats-grid strong {
  color: #75e8ff;
  text-align: right;
}

.stats-line {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drop-hint {
  position: absolute;
  right: 24px;
  bottom: 22px;
  z-index: 8;
  color: rgba(216, 243, 255, 0.68);
  font-size: 12px;
  pointer-events: none;
}

.mine-glb-viewer.is-dragging::after {
  content: "释放 GLB / GLTF 文件以加载";
  position: absolute;
  inset: 18px;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed #78c7ff;
  background: rgba(10, 34, 54, 0.72);
  color: #d8f3ff;
  font-size: 22px;
  font-weight: 600;
  pointer-events: none;
}

@keyframes glbInfoSweep {
  0% {
    transform: translateX(0) skewX(-18deg);
    opacity: 0;
  }
  14% {
    opacity: 0.85;
  }
  42% {
    transform: translateX(560px) skewX(-18deg);
    opacity: 0;
  }
  100% {
    transform: translateX(560px) skewX(-18deg);
    opacity: 0;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
