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
      <div class="viewer-actions">
        <button class="viewer-btn" type="button" :disabled="loading || !observations.length" @click="toggleObservationLayer">
          {{ showObservations ? "隐藏震源" : "显示震源" }}
        </button>
        <button v-if="georeferenced" class="viewer-btn" type="button" :disabled="loading" @click="toggleCoordinateMode">
          {{ coordinateMode === "surface" ? "查看原始震源" : "查看贴面投影" }}
        </button>
        <button v-else class="viewer-btn" type="button" :disabled="loading || !observations.length" @click="recalculateObservationColors">
          重算颜色
        </button>
        <button class="viewer-btn" type="button" :disabled="loading || !modelRootReady" @click="reprojectObservations">
          重新投影
        </button>
        <button class="viewer-btn" type="button" :disabled="loading || !riskOverlayReady" @click="toggleRiskOverlay">
          {{ showRiskOverlay ? "隐藏云图" : "显示云图" }}
        </button>
        <label class="opacity-control" title="调整工作面云图透明度">
          <span>云图</span>
          <input
            v-model.number="riskOverlayOpacity"
            type="range"
            min="0.25"
            max="1"
            step="0.05"
            :disabled="!riskOverlayReady"
            @input="updateRiskOverlayOpacity"
          />
        </label>
        <button class="viewer-btn" type="button" :disabled="loading || !riskOverlayReady" @click="focusRiskWorkface">
          聚焦工作面
        </button>
        <button class="viewer-btn" type="button" :disabled="loading" @click="resetCamera">重置视角</button>
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
    <div v-if="georeferenced" class="layer-controls">
      <button class="viewer-btn" @click="toggleTopView">{{ topView ? "返回双层三维" : "俯视核对点位" }}</button>
      <button class="viewer-btn" :disabled="topView" @click="toggleUpperLayer">{{ upperVisible ? "隐藏 7 煤层" : "显示 7 煤层" }}</button>
      <button class="viewer-btn" :disabled="topView" @click="toggleLayerSeparation">{{ layersSeparated ? "恢复层间位置" : "层间展开" }}</button>
      <button class="viewer-btn" :disabled="topView" @click="toggleHeightScale">{{ heightScale === 1 ? "垂向放大 ×3" : "恢复真实比例" }}</button>
    </div>

    <div v-if="loading" class="state-panel">
      <span class="spinner"></span>
      <span>正在加载模型...</span>
    </div>

    <div v-if="errorMessage" class="error-panel">{{ errorMessage }}</div>

    <div v-if="projectionSummary" class="projection-status">{{ projectionSummary }}</div>
    <div v-if="georeferenced" class="coordinate-legend">
      <strong>{{ topView ? "12 煤层 · 正交俯视核对" : "7 煤 / 12 煤 · 双层矿山" }}</strong>
      <span>{{ coordinateMode === "surface" ? "点位投影至插值煤层面" : "点位使用原始 X / Y / Z" }}</span>
      <span>米制假设 · 标高插值 · 测量基准待核验</span>
      <div class="risk-scale"></div>
      <span>统一 W 色标：0　　　0.5　　　≥1</span>
      <span>金色：7 煤层　青色：12 煤层</span>
      <span>垂向 {{ heightScale }}×{{ layersSeparated ? " · 上层展开 +80m（示意）" : " · 原始层间位置" }}</span>
      <span>层边厚度为示意；点击点位对照 W</span>
    </div>

    <div v-if="selectedObservation" class="observation-panel">
      <div class="panel-title">{{ selectedObservation.name }}</div>
      <div>ID：{{ selectedObservation.id }}</div>
      <div>风险值：{{ selectedObservation.riskValue.toFixed(3) }}</div>
      <div v-if="!georeferenced">震级：{{ selectedObservation.magnitude.toFixed(1) }}</div>
      <div>原始高程：{{ selectedObservation.sourceZ.toFixed(2) }} m</div>
      <div>事件能量：{{ selectedObservation.energyJ.toFixed(0) }} J</div>
      <div v-if="!georeferenced">应力指数：{{ selectedObservation.stressIndex.toFixed(2) }}</div>
      <div v-if="!georeferenced">能量指数：{{ selectedObservation.energyIndex.toFixed(2) }}</div>
      <div v-if="georeferenced && selectedObservation.seamElevation != null">插值煤层标高：{{ selectedObservation.seamElevation.toFixed(2) }} m</div>
      <div v-if="georeferenced && selectedObservation.cloudValue != null">同坐标云图 W：{{ selectedObservation.cloudValue.toFixed(3) }}（网格插值）</div>
      <div v-if="georeferenced">点位 W 为原始记录，云图 W 为插值结果</div>
      <div>平面坐标：{{ selectedObservation.sourceX.toFixed(2) }}, {{ selectedObservation.sourceY.toFixed(2) }}</div>
      <div>模型坐标：{{ selectedObservation.x.toFixed(3) }}, {{ selectedObservation.y.toFixed(3) }}, {{ selectedObservation.z.toFixed(3) }}</div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue"
import gsap from "gsap"
import * as THREE from "three"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js"
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js"
import { createWorkfaceBounds, planarPointToUv, uvToWorkface } from "../../lib/workfaceProjection.js"
import { georeferencedObservations, riskRgb } from "../../lib/mineCoordinates.js"

const DEFAULT_MODEL = "/models/hongyang-coal12-georef.glb"
const GEOREFERENCE_DATA = "/defaults/hongyang-coal12-georef.json"
const DEFAULT_RISK_MAP = "/defaults/hongyang-rockburst-warning-map.png"
const DEFAULT_EVENT_DATA = "/defaults/hongyang-microseismic-events.json"
const SURFACE_SEGMENTS_X = 18
const SURFACE_SEGMENTS_Z = 48

const viewerRef = ref(null)
const fileInputRef = ref(null)
const loading = ref(false)
const isDragging = ref(false)
const currentName = ref("12 煤层坐标验证模型")
const errorMessage = ref("")
const observations = ref([])
const selectedObservation = ref(null)
const showObservations = ref(true)
const showRiskOverlay = ref(true)
const riskOverlayOpacity = ref(0.82)
const riskOverlayReady = ref(false)
const modelStats = ref(null)
const modelRootReady = ref(false)
const projectionSummary = ref("")
const georeferenced = ref(false)
const coordinateMode = ref("surface")
const topView = ref(false)
const upperVisible = ref(true)
const heightScale = ref(3)
const layersSeparated = ref(false)
let georeferenceData = null

let renderer = null
let scene = null
let camera = null
let controls = null
let loader = null
let raycaster = null
let mouse = null
let modelRoot = null
let pointLayer = null
let pointMesh = null
let riskOverlayGroup = null
let riskOverlayMaterial = null
let riskOverlayTexture = null
let riskProjectionGrid = null
let riskSurfaceSamples = []
let activeWorkfaceBounds = null
let planarObservationSource = null
let gridHelper = null
let axesHelper = null
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
  disposeRiskOverlay()
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
  gridHelper = new THREE.GridHelper(1, 20, 0x31506b, 0x203647)
  gridHelper.name = "viewer-grid"
  scene.add(gridHelper)

  axesHelper = new THREE.AxesHelper(0.12)
  axesHelper.name = "viewer-axes"
  scene.add(axesHelper)
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
  if (camera.isOrthographicCamera) {
    const vertical = camera.top
    camera.left = -vertical * width / height
    camera.right = vertical * width / height
  } else camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

function animate() {
  animationId = requestAnimationFrame(animate)
  controls && controls.update()
  renderer && scene && camera && renderer.render(scene, camera)
}

function loadModel(url, name) {
  if (camera.isOrthographicCamera) restorePerspectiveCamera()
  pointLayer.scale.set(1, 1, 1)
  loading.value = true
  errorMessage.value = ""
  currentName.value = name || "model.glb"
  modelRootReady.value = false
  modelStats.value = null
  selectedObservation.value = null
  observations.value = []
  projectionSummary.value = ""
  planarObservationSource = null
  georeferenced.value = false
  georeferenceData = null
  clearObservationLayer()

  loader.load(
    url,
    async (gltf) => {
      try {
        disposeModel()
        modelRoot = gltf.scene || gltf.scenes[0]
        let hasCoordinateMetadata = false
        modelRoot.traverse((child) => {
          if (child.userData.georef_id === "hongyang-coal12-local-v1") hasCoordinateMetadata = true
        })
        if (url === DEFAULT_MODEL || hasCoordinateMetadata) {
          const response = await fetch(GEOREFERENCE_DATA)
          if (!response.ok) throw new Error("真实坐标数据加载失败")
          georeferenceData = await response.json()
          if (!hasCoordinateMetadata) throw new Error("模型缺少匹配的坐标标识")
          georeferenced.value = true
        }
        normalizeMaterials(modelRoot)
        scene.add(modelRoot)
        modelRoot.updateMatrixWorld(true)

        modelStats.value = collectModelStats(modelRoot, gltf)
        currentModelSeed = hashString(`${currentName.value}-${modelStats.value.vertexCount}-${modelStats.value.triangleCount}`)
        currentPointRadius = georeferenced.value ? 1.8 : calculatePointRadius(modelStats.value)
        updateSceneHelpers(modelStats.value)
        createRiskOverlay()
        await loadProjectedObservations()
        renderObservationLayer()
        if (georeferenced.value) applyLayerDisplay()
        fitCameraToModel(true)
        if (georeferenced.value) focusRiskWorkface()
        modelRootReady.value = true
      } catch (error) {
        errorMessage.value = `表面投影失败：${error.message || error}`
        console.error(error)
      } finally {
        loading.value = false
      }
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
      if (!georeferenced.value && !material.map && material.color) {
        material.color.set(0x6d8390)
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

function sampleTopSurfaceGrid(bounds) {
  const rowSize = SURFACE_SEGMENTS_X + 1
  const points = new Array(rowSize * (SURFACE_SEGMENTS_Z + 1)).fill(null)
  const width = Math.max(bounds.xMax - bounds.xMin, Number.EPSILON)
  const depth = Math.max(bounds.zMax - bounds.zMin, Number.EPSILON)
  const halfCellX = width / SURFACE_SEGMENTS_X / 2
  const halfCellZ = depth / SURFACE_SEGMENTS_Z / 2
  const worldPoint = new THREE.Vector3()

  modelRoot.updateMatrixWorld(true)
  modelRoot.traverse((child) => {
    const position = child.isMesh && child.geometry && child.geometry.attributes.position
    if (!position) return
    for (let index = 0; index < position.count; index += 1) {
      worldPoint.fromBufferAttribute(position, index).applyMatrix4(child.matrixWorld)
      if (
        worldPoint.x < bounds.xMin - halfCellX || worldPoint.x > bounds.xMax + halfCellX ||
        worldPoint.z < bounds.zMin - halfCellZ || worldPoint.z > bounds.zMax + halfCellZ
      ) continue
      const ix = THREE.MathUtils.clamp(Math.round(((worldPoint.x - bounds.xMin) / width) * SURFACE_SEGMENTS_X), 0, SURFACE_SEGMENTS_X)
      const iz = THREE.MathUtils.clamp(Math.round(((worldPoint.z - bounds.zMin) / depth) * SURFACE_SEGMENTS_Z), 0, SURFACE_SEGMENTS_Z)
      const gridIndex = iz * rowSize + ix
      if (!points[gridIndex] || worldPoint.y > points[gridIndex].y) points[gridIndex] = worldPoint.clone()
    }
  })

  const populated = points
    .map((point, index) => point ? { point, ix: index % rowSize, iz: Math.floor(index / rowSize) } : null)
    .filter(Boolean)
  if (!populated.length) throw new Error("指定工作面范围内没有模型顶面顶点")
  const sortedHeights = populated.map((sample) => sample.point.y).sort((a, b) => a - b)
  const upperReference = sortedHeights[Math.floor((sortedHeights.length - 1) * 0.7)]
  const upperFloor = upperReference - modelStats.value.size.y * 0.1
  const upperSamples = populated.filter((sample) => sample.point.y >= upperFloor)
  const surfaceSamples = upperSamples.length >= 4 ? upperSamples : populated

  points.forEach((point, index) => {
    const ix = index % rowSize
    const iz = Math.floor(index / rowSize)
    const x = bounds.xMin + (ix / SURFACE_SEGMENTS_X) * width
    const z = bounds.zMin + (iz / SURFACE_SEGMENTS_Z) * depth
    if (point && point.y >= upperFloor) {
      point.x = x
      point.z = z
      return
    }
    let nearest = surfaceSamples[0]
    let nearestDistance = Infinity
    surfaceSamples.forEach((sample) => {
      const distance = (sample.ix - ix) ** 2 + (sample.iz - iz) ** 2
      if (distance < nearestDistance) {
        nearest = sample
        nearestDistance = distance
      }
    })
    points[index] = new THREE.Vector3(x, nearest.point.y, z)
  })
  return points
}

function createDrapedRiskGeometry(bounds) {
  const positions = []
  const uvs = []
  const indices = []
  const points = sampleTopSurfaceGrid(bounds)
  const maxSize = Math.max(modelStats.value.size.x, modelStats.value.size.y, modelStats.value.size.z) || 1
  const surfaceOffset = maxSize * 0.0012

  riskSurfaceSamples = []
  for (let iz = 0; iz <= SURFACE_SEGMENTS_Z; iz += 1) {
    const v = iz / SURFACE_SEGMENTS_Z
    for (let ix = 0; ix <= SURFACE_SEGMENTS_X; ix += 1) {
      const u = ix / SURFACE_SEGMENTS_X
      const point = points[iz * (SURFACE_SEGMENTS_X + 1) + ix]
      point.y += surfaceOffset
      positions.push(point.x, point.y, point.z)
      uvs.push(u, v)
      riskSurfaceSamples.push({ point: point.clone(), u, v })
    }
  }

  const rowSize = SURFACE_SEGMENTS_X + 1
  const maxStep = Math.max(modelStats.value.size.y * 0.35, surfaceOffset * 8)
  for (let iz = 0; iz < SURFACE_SEGMENTS_Z; iz += 1) {
    for (let ix = 0; ix < SURFACE_SEGMENTS_X; ix += 1) {
      const a = iz * rowSize + ix
      const b = a + 1
      const c = a + rowSize
      const d = c + 1
      const cell = [points[a], points[b], points[c], points[d]]
      if (cell.some((point) => !point)) continue
      const heights = cell.map((point) => point.y)
      if (Math.max(...heights) - Math.min(...heights) > maxStep) continue
      indices.push(a, c, b, b, c, d)
    }
  }

  if (!indices.length) throw new Error("指定工作面范围内没有可投射的模型表面")

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3))
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2))
  geometry.setIndex(indices)
  geometry.computeVertexNormals()
  riskProjectionGrid = {
    points,
    segmentsX: SURFACE_SEGMENTS_X,
    segmentsZ: SURFACE_SEGMENTS_Z,
  }
  return geometry
}

function interpolateProjectedSurface(uv) {
  if (!riskProjectionGrid) return null
  const { points, segmentsX, segmentsZ } = riskProjectionGrid
  const gx = THREE.MathUtils.clamp(uv.u, 0, 1) * segmentsX
  const gz = THREE.MathUtils.clamp(uv.v, 0, 1) * segmentsZ
  const ix = Math.min(Math.floor(gx), segmentsX - 1)
  const iz = Math.min(Math.floor(gz), segmentsZ - 1)
  const tx = gx - ix
  const tz = gz - iz
  const rowSize = segmentsX + 1
  const a = points[iz * rowSize + ix]
  const b = points[iz * rowSize + ix + 1]
  const c = points[(iz + 1) * rowSize + ix]
  const d = points[(iz + 1) * rowSize + ix + 1]

  if (a && b && c && d) {
    const lower = a.clone().lerp(b, tx)
    const upper = c.clone().lerp(d, tx)
    return lower.lerp(upper, tz)
  }

  let nearest = null
  let nearestDistance = Infinity
  riskSurfaceSamples.forEach((sample) => {
    const distance = (sample.u - uv.u) ** 2 + (sample.v - uv.v) ** 2
    if (distance < nearestDistance) {
      nearest = sample.point
      nearestDistance = distance
    }
  })
  return nearest ? nearest.clone() : null
}

async function loadProjectedObservations() {
  if (georeferenced.value) {
    observations.value = georeferencedObservations(georeferenceData, coordinateMode.value)
    updateCoordinateSummary()
    return
  }
  let payload
  try {
    const response = await fetch(DEFAULT_EVENT_DATA)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    payload = await response.json()
  } catch (error) {
    console.warn("真实微震事件加载失败，改用演示点位", error)
    payload = createFallbackObservationPayload(currentModelSeed)
  }

  planarObservationSource = payload
  observations.value = projectObservationPayload(payload)
  projectionSummary.value = `表面投影 ${observations.value.length}/${payload.events.length} 个微震点 · ${riskSurfaceSamples.length} 个贴面采样`
}

function projectObservationPayload(payload) {
  const events = Array.isArray(payload.events) ? payload.events : []
  const bounds = payload.meta && payload.meta.bounds
  if (!bounds || !activeWorkfaceBounds) return []
  const energyLogs = events.map((event) => Math.log10(Math.max(Number(event.energy_j) || 1, 1)))
  const minEnergy = Math.min(...energyLogs)
  const maxEnergy = Math.max(...energyLogs)
  const energySpan = Math.max(maxEnergy - minEnergy, Number.EPSILON)

  return events.flatMap((event, index) => {
    const uv = planarPointToUv(event, bounds)
    const footprintPoint = uvToWorkface(uv, activeWorkfaceBounds)
    const surfacePoint = interpolateProjectedSurface(uv)
    if (!surfacePoint) return []
    const energyJ = Math.max(Number(event.energy_j) || 1, 1)
    const energyIndex = (Math.log10(energyJ) - minEnergy) / energySpan
    const riskValue = THREE.MathUtils.clamp(Number(event.risk_value) || 0, 0, 1)
    const sourceZ = Number(event.z) || 0
    const point = {
      id: event.id || `MS-${String(index + 1).padStart(3, "0")}`,
      name: `微震事件 ${String(index + 1).padStart(3, "0")}`,
      x: surfacePoint.x,
      y: surfacePoint.y + currentPointRadius * 0.35,
      z: surfacePoint.z,
      sourceX: Number(event.x) || 0,
      sourceY: Number(event.y) || 0,
      sourceZ,
      energyJ,
      baseValue: riskValue,
      stressIndex: THREE.MathUtils.clamp(riskValue * 0.72 + energyIndex * 0.28, 0, 1),
      energyIndex,
      faultInfluence: createRandom(hashString(`${event.id}-${event.x}-${event.y}`))(),
      magnitude: THREE.MathUtils.clamp(Math.log10(energyJ) - 2, 0.5, 4.2),
      footprintX: footprintPoint.x,
      footprintZ: footprintPoint.z,
      riskValue,
    }
    return [point]
  })
}

function createFallbackObservationPayload(seed) {
  const rand = createRandom(seed)
  const events = Array.from({ length: 48 }, (_, index) => ({
    id: `DEMO-${String(index + 1).padStart(3, "0")}`,
    x: rand(),
    y: rand(),
    z: -1000 - rand() * 100,
    energy_j: 10000 + rand() * 350000,
    risk_value: rand() > 0.9 ? 0.5 + rand() * 0.5 : rand() * 0.22,
  }))
  return {
    meta: { bounds: { xMin: 0, xMax: 1, yMin: 0, yMax: 1 } },
    events,
  }
}

function calculatePointRadius(stats) {
  if (!stats) return 0.38
  const maxSize = Math.max(stats.size.x, stats.size.y, stats.size.z) || 1
  return THREE.MathUtils.clamp(maxSize * 0.0032, 0.0015, 0.7)
}

function updateSceneHelpers(stats) {
  if (!stats) return
  const maxSize = Math.max(stats.size.x, stats.size.y, stats.size.z) || 1
  if (gridHelper) {
    gridHelper.scale.setScalar(maxSize * 1.45)
    gridHelper.position.set(stats.center.x, stats.box.min.y - maxSize * 0.012, stats.center.z)
  }
  if (axesHelper) {
    axesHelper.scale.setScalar(maxSize)
    axesHelper.position.copy(stats.box.min)
  }
}

function createRiskOverlay() {
  disposeRiskOverlay()
  if (!modelRoot || !modelStats.value) return
  if (georeferenced.value) {
    createGeoreferencedRiskOverlay()
    return
  }

  riskOverlayGroup = new THREE.Group()
  riskOverlayGroup.name = "draped-workface-risk-overlay"
  activeWorkfaceBounds = createWorkfaceBounds(modelStats.value.box)
  const geometry = createDrapedRiskGeometry(activeWorkfaceBounds)

  riskOverlayMaterial = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: riskOverlayOpacity.value,
    side: THREE.DoubleSide,
    depthWrite: false,
    polygonOffset: true,
    polygonOffsetFactor: -3,
    polygonOffsetUnits: -3,
  })

  const surface = new THREE.Mesh(geometry, riskOverlayMaterial)
  surface.name = "upper-workface-risk-map"
  surface.renderOrder = 5
  riskOverlayGroup.add(surface)

  const border = new THREE.LineSegments(
    new THREE.EdgesGeometry(geometry, 50),
    new THREE.LineBasicMaterial({ color: 0x63e8ff, transparent: true, opacity: 0.8 })
  )
  border.renderOrder = 6
  riskOverlayGroup.add(border)
  riskOverlayGroup.visible = showRiskOverlay.value
  scene.add(riskOverlayGroup)
  const overlayGroup = riskOverlayGroup
  const overlayMaterial = riskOverlayMaterial

  new THREE.TextureLoader().load(
    DEFAULT_RISK_MAP,
    (sourceTexture) => {
      if (riskOverlayMaterial !== overlayMaterial || riskOverlayGroup !== overlayGroup) {
        sourceTexture.dispose()
        return
      }
      const image = sourceTexture.image
      const crop = {
        x: Math.round(image.width * 0.0534),
        y: Math.round(image.height * 0.0687),
        width: Math.round(image.width * 0.799),
        height: Math.round(image.height * 0.843),
      }
      const canvas = document.createElement("canvas")
      canvas.width = crop.height
      canvas.height = crop.width
      const context = canvas.getContext("2d")
      context.translate(canvas.width, 0)
      context.rotate(Math.PI / 2)
      context.drawImage(
        image,
        crop.x,
        crop.y,
        crop.width,
        crop.height,
        0,
        0,
        crop.width,
        crop.height
      )
      sourceTexture.dispose()

      const texture = new THREE.CanvasTexture(canvas)
      texture.colorSpace = THREE.SRGBColorSpace
      texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy())
      riskOverlayTexture = texture
      overlayMaterial.map = texture
      overlayMaterial.needsUpdate = true
      riskOverlayReady.value = true
    },
    undefined,
    () => {
      if (riskOverlayMaterial !== overlayMaterial || riskOverlayGroup !== overlayGroup) return
      riskOverlayReady.value = false
      errorMessage.value = "工作面云图纹理加载失败"
    }
  )
}

function toggleRiskOverlay() {
  showRiskOverlay.value = !showRiskOverlay.value
  if (riskOverlayGroup) riskOverlayGroup.visible = showRiskOverlay.value
}

function updateRiskOverlayOpacity() {
  if (riskOverlayMaterial) {
    riskOverlayMaterial.opacity = riskOverlayOpacity.value
  }
}

function focusRiskWorkface() {
  if (!camera || !controls || !riskOverlayReady.value || !activeWorkfaceBounds) return
  if (camera.isOrthographicCamera) restorePerspectiveCamera()
  if (sceneTimeline) sceneTimeline.kill()

  const { xMin, xMax, zMin, zMax } = activeWorkfaceBounds
  const averageY = riskSurfaceSamples.length
    ? riskSurfaceSamples.reduce((sum, sample) => sum + sample.point.y, 0) / riskSurfaceSamples.length
    : modelStats.value.center.y
  const center = new THREE.Vector3((xMin + xMax) / 2, averageY * (georeferenced.value ? heightScale.value : 1), (zMin + zMax) / 2)
  const span = Math.max(xMax - xMin, zMax - zMin) * (georeferenced.value ? 1.22 : 1)
  const destination = new THREE.Vector3(
    center.x + span * 0.82,
    center.y + span * (georeferenced.value ? 0.62 : 1.08),
    center.z + span * 1.12
  )

  sceneTimeline = gsap.timeline({ defaults: { duration: 0.85, ease: "power3.inOut" } })
  sceneTimeline
    .to(camera.position, {
      x: destination.x,
      y: destination.y,
      z: destination.z,
      onUpdate: () => controls.update(),
    }, 0)
    .to(controls.target, {
      x: center.x,
      y: center.y,
      z: center.z,
      onUpdate: () => controls.update(),
    }, 0)
}

function disposeRiskOverlay() {
  riskOverlayReady.value = false
  if (riskOverlayGroup) {
    riskOverlayGroup.parent && riskOverlayGroup.parent.remove(riskOverlayGroup)
    riskOverlayGroup.traverse((child) => {
      child.geometry && child.geometry.dispose()
      if (child.material) {
        const materials = Array.isArray(child.material) ? child.material : [child.material]
        materials.forEach((material) => material.dispose())
      }
    })
  }
  if (riskOverlayTexture) riskOverlayTexture.dispose()
  riskOverlayGroup = null
  riskOverlayMaterial = null
  riskOverlayTexture = null
  riskProjectionGrid = null
  riskSurfaceSamples = []
  activeWorkfaceBounds = null
}

function fitCameraToModel(animateIntro = false) {
  if (!modelRoot) return
  if (sceneTimeline) sceneTimeline.kill()
  if (camera.isOrthographicCamera) restorePerspectiveCamera()
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
  if (!pointLayer || !observations.value.length) return

  const geometry = new THREE.SphereGeometry(currentPointRadius, 14, 10)
  const material = new THREE.MeshBasicMaterial({
    color: 0xffffff,
  })
  pointMesh = new THREE.InstancedMesh(geometry, material, observations.value.length)
  pointMesh.name = "projected-microseismic-events"
  pointMesh.userData = { type: "projected-microseismic-events", points: observations.value }
  pointMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage)
  const matrix = new THREE.Matrix4()
  const color = new THREE.Color()

  observations.value.forEach((point, index) => {
    const scale = 0.8 + point.riskValue * 1.6
    matrix.compose(
      new THREE.Vector3(point.x, point.y, point.z),
      new THREE.Quaternion(),
      new THREE.Vector3(scale, georeferenced.value ? scale / heightScale.value : scale, scale)
    )
    pointMesh.setMatrixAt(index, matrix)
    if (georeferenced.value) color.setRGB(...riskRgb(point.riskValue), THREE.SRGBColorSpace)
    else color.setHex(riskColor(point.riskValue))
    pointMesh.setColorAt(index, color)
  })
  pointMesh.instanceMatrix.needsUpdate = true
  if (pointMesh.instanceColor) pointMesh.instanceColor.needsUpdate = true
  pointLayer.add(pointMesh)
  pointLayer.visible = showObservations.value
}

function clearObservationLayer() {
  if (!pointLayer) return
  while (pointLayer.children.length) {
    const child = pointLayer.children[pointLayer.children.length - 1]
    pointLayer.remove(child)
    child.geometry && child.geometry.dispose()
    child.material && child.material.dispose()
  }
  pointMesh = null
}

function toggleObservationLayer() {
  showObservations.value = !showObservations.value
  if (pointLayer) pointLayer.visible = showObservations.value
  if (!showObservations.value) selectedObservation.value = null
}

function reprojectObservations() {
  if (georeferenced.value) {
    observations.value = georeferencedObservations(georeferenceData, coordinateMode.value)
    selectedObservation.value = null
    renderObservationLayer()
    updateCoordinateSummary()
    return
  }
  if (!modelRoot || !planarObservationSource) return
  observations.value = projectObservationPayload(planarObservationSource)
  selectedObservation.value = null
  renderObservationLayer()
  projectionSummary.value = `表面投影 ${observations.value.length}/${planarObservationSource.events.length} 个微震点 · ${riskSurfaceSamples.length} 个贴面采样`
}

function recalculateObservationColors() {
  formulaVersion += 1
  observations.value = observations.value.map((point) => ({
    ...point,
    riskValue: calculateRiskValue(point),
  }))

  if (!pointMesh) return
  const matrix = new THREE.Matrix4()
  const color = new THREE.Color()
  observations.value.forEach((point, index) => {
    const scale = 0.8 + point.riskValue * 1.6
    matrix.compose(
      new THREE.Vector3(point.x, point.y, point.z),
      new THREE.Quaternion(),
      new THREE.Vector3(scale, scale, scale)
    )
    pointMesh.setMatrixAt(index, matrix)
    pointMesh.setColorAt(index, color.setHex(riskColor(point.riskValue)))
  })
  pointMesh.userData.points = observations.value
  pointMesh.instanceMatrix.needsUpdate = true
  if (pointMesh.instanceColor) pointMesh.instanceColor.needsUpdate = true
  if (selectedObservation.value) {
    selectedObservation.value = observations.value.find((point) => point.id === selectedObservation.value.id) || null
  }
}

function onCanvasClick(event) {
  if (!showObservations.value || !pointLayer || !camera || !renderer) return
  const rect = renderer.domElement.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  raycaster.setFromCamera(mouse, camera)

  const hits = raycaster.intersectObjects(pointLayer.children, true)
  const hit = hits[0]
  selectedObservation.value = hit && Number.isInteger(hit.instanceId)
    ? hit.object.userData.points[hit.instanceId] || null
    : null
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
  disposeRiskOverlay()
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

function formatVectorValue(value) {
  return Number.isFinite(value) ? value.toFixed(2) : "0.00"
}

function updateCoordinateSummary() {
  projectionSummary.value = `${coordinateMode.value === "surface" ? "贴面投影" : "原始三维震源"} · ${observations.value.length} 个事件 · 坐标基准待核验`
}

function toggleCoordinateMode() {
  if (topView.value) toggleTopView()
  coordinateMode.value = coordinateMode.value === "surface" ? "native" : "surface"
  reprojectObservations()
}

function applyLayerDisplay() {
  if (!georeferenced.value || !modelRoot) return
  modelRoot.scale.y = heightScale.value
  pointLayer.scale.y = heightScale.value
  if (riskOverlayGroup) riskOverlayGroup.scale.y = heightScale.value
  const upper = modelRoot.getObjectByName("Coal7_Layer")
  if (upper) {
    upper.visible = upperVisible.value && !topView.value
    upper.position.y = layersSeparated.value ? 80 : 0
  }
  modelRoot.updateMatrixWorld(true)
  const displayedBounds = new THREE.Box3().setFromObject(modelRoot)
  const displayedSize = displayedBounds.getSize(new THREE.Vector3())
  if (gridHelper) gridHelper.position.y = displayedBounds.min.y - Math.max(displayedSize.x, displayedSize.z) * 0.025
  if (axesHelper) axesHelper.visible = false
}

function toggleUpperLayer() {
  upperVisible.value = !upperVisible.value
  applyLayerDisplay()
}

function toggleLayerSeparation() {
  layersSeparated.value = !layersSeparated.value
  upperVisible.value = true
  applyLayerDisplay()
  fitCameraToModel(false)
}

function toggleHeightScale() {
  heightScale.value = heightScale.value === 1 ? 3 : 1
  applyLayerDisplay()
  renderObservationLayer()
  focusRiskWorkface()
}

function restorePerspectiveCamera() {
  topView.value = false
  camera = new THREE.PerspectiveCamera(45, viewerRef.value.clientWidth / viewerRef.value.clientHeight, 0.1, 100000)
  controls.object = camera
  controls.enableRotate = true
  applyLayerDisplay()
}

function toggleTopView() {
  if (sceneTimeline) sceneTimeline.kill()
  if (topView.value) {
    restorePerspectiveCamera()
    focusRiskWorkface()
    return
  }
  topView.value = true
  coordinateMode.value = "surface"
  reprojectObservations()
  const bounds = activeWorkfaceBounds
  const span = Math.max(bounds.xMax - bounds.xMin, bounds.zMax - bounds.zMin) * 0.66
  const aspect = viewerRef.value.clientWidth / viewerRef.value.clientHeight
  camera = new THREE.OrthographicCamera(-span * aspect, span * aspect, span, -span, 0.1, 100000)
  const center = new THREE.Vector3((bounds.xMin + bounds.xMax) / 2, 0, (bounds.zMin + bounds.zMax) / 2)
  camera.position.set(center.x, 10000, center.z)
  camera.up.set(0, 0, -1)
  controls.object = camera
  controls.target.copy(center)
  controls.enableRotate = false
  controls.update()
  applyLayerDisplay()
}

function createGeoreferencedRiskOverlay() {
  const { risk, meta } = georeferenceData
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(risk.vertices.flat(), 3))
  const colors = risk.colors.flatMap((value) => new THREE.Color().setRGB(...value, THREE.SRGBColorSpace).toArray())
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3))
  geometry.setIndex(risk.indices)
  geometry.computeVertexNormals()
  riskOverlayMaterial = new THREE.MeshBasicMaterial({
    vertexColors: true, transparent: true, opacity: riskOverlayOpacity.value,
    side: THREE.DoubleSide, depthWrite: false, polygonOffset: true,
    polygonOffsetFactor: -2, polygonOffsetUnits: -2,
  })
  riskOverlayGroup = new THREE.Group()
  riskOverlayGroup.name = "georeferenced-surfer-grid"
  const overlay = new THREE.Mesh(geometry, riskOverlayMaterial)
  overlay.renderOrder = 5
  riskOverlayGroup.add(overlay)
  riskOverlayGroup.visible = showRiskOverlay.value
  scene.add(riskOverlayGroup)
  activeWorkfaceBounds = {
    xMin: meta.bounds.xMin - meta.origin[0], xMax: meta.bounds.xMax - meta.origin[0],
    zMin: -(meta.bounds.yMax - meta.origin[1]), zMax: -(meta.bounds.yMin - meta.origin[1]),
  }
  riskSurfaceSamples = risk.vertices.map((point) => ({ point: new THREE.Vector3(...point) }))
  riskOverlayReady.value = true
}
</script>

<style scoped>
.layer-controls {
  position: absolute;
  top: 44px;
  left: 13.5%;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  max-width: 75%;
}
.coordinate-legend {
  position: absolute;
  left: 13.5%;
  top: 130px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 14px;
  color: #b5dbe8;
  font-size: 11px;
  background: rgba(6, 22, 35, 0.88);
  border: 1px solid #245063;
  pointer-events: none;
}
.risk-scale {
  height: 8px;
  background: linear-gradient(90deg, #0d8c9e, #33d6a1, #ffdb2e, #ff5c1f, #e61236);
}
.mine-glb-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 48%, rgba(48, 220, 255, 0.14), transparent 36%),
    radial-gradient(ellipse at 50% 70%, rgba(15, 74, 116, 0.26), transparent 62%),
    transparent;
}

.viewer-canvas {
  position: absolute;
  inset: 0;
}

.viewer-toolbar {
  position: absolute;
  left: 50%;
  bottom: 28px;
  z-index: 10;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.viewer-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px 14px;
  border: 1px solid rgba(48, 220, 255, 0.28);
  background: linear-gradient(180deg, rgba(9, 45, 76, 0.62), rgba(3, 16, 34, 0.68));
  box-shadow:
    inset 0 0 22px rgba(48, 220, 255, 0.12),
    0 0 22px rgba(48, 220, 255, 0.12);
  pointer-events: auto;
  backdrop-filter: blur(6px);
}

.viewer-btn {
  height: 32px;
  min-width: 88px;
  padding: 0 14px;
  border: 1px solid rgba(48, 220, 255, 0.55);
  color: #c4f3fe;
  background: linear-gradient(180deg, rgba(21, 91, 127, 0.85), rgba(7, 30, 64, 0.85));
  box-shadow:
    inset 0 0 12px rgba(48, 220, 255, 0.12),
    0 0 10px rgba(48, 220, 255, 0.1);
  cursor: pointer;
}

.viewer-btn:hover:not(:disabled) {
  color: #ffffff;
  border-color: rgba(117, 232, 255, 0.88);
  box-shadow:
    inset 0 0 16px rgba(48, 220, 255, 0.22),
    0 0 16px rgba(48, 220, 255, 0.24);
}

.viewer-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.opacity-control {
  display: flex;
  width: 156px;
  height: 32px;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border: 1px solid rgba(48, 220, 255, 0.38);
  color: #c4f3fe;
  background: rgba(7, 30, 64, 0.78);
  font-size: 12px;
}

.opacity-control span {
  flex: 0 0 auto;
  white-space: nowrap;
}

.opacity-control input {
  width: 98px;
  accent-color: #32d9ff;
  cursor: pointer;
}

.opacity-control input:disabled {
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

.projection-status {
  position: absolute;
  left: 170px;
  top: 92px;
  z-index: 9;
  padding: 7px 11px;
  border: 1px solid rgba(54, 207, 201, 0.34);
  background: rgba(7, 28, 43, 0.76);
  color: rgba(176, 248, 244, 0.9);
  font-size: 12px;
  pointer-events: none;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(117, 232, 255, 0.22);
  border-top-color: #75e8ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

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

.observation-panel {
  top: 92px;
  right: 170px;
}

.panel-title {
  margin-bottom: 4px;
  color: #78c7ff;
  font-size: 14px;
  font-weight: 600;
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

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
