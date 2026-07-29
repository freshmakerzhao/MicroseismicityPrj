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
        <button class="viewer-btn" type="button" :disabled="loading || !observations.length" @click="recalculateObservationColors">
          重算颜色
        </button>
        <button class="viewer-btn" type="button" :disabled="loading || !modelRootReady" @click="regenerateSyntheticSources">
          重新生成
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

    <div v-if="loading" class="state-panel">
      <span class="spinner"></span>
      <span>正在加载模型...</span>
    </div>

    <div v-if="errorMessage" class="error-panel">{{ errorMessage }}</div>

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
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue"
import gsap from "gsap"
import * as THREE from "three"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js"
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js"

const DEFAULT_MODEL = "/models/zhengti-demo.glb"
const DEFAULT_RISK_MAP = "/defaults/hongyang-rockburst-warning-map.png"
const SYNTHETIC_POINT_COUNT = 28
const EXCLUDED_SOURCE_IDS = new Set(["MS-008", "MS-013"])
const DEMO_WORKFACE = {
  xMin: 0.0245,
  xMax: 0.2229,
  y: 0.365,
  zMin: -0.2069,
  zMax: 0.289,
}

const viewerRef = ref(null)
const fileInputRef = ref(null)
const loading = ref(false)
const isDragging = ref(false)
const currentName = ref("整体巷道模型")
const errorMessage = ref("")
const observations = ref([])
const selectedObservation = ref(null)
const showObservations = ref(true)
const showRiskOverlay = ref(true)
const riskOverlayOpacity = ref(0.82)
const riskOverlayReady = ref(false)
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
let riskOverlayGroup = null
let riskOverlayMaterial = null
let riskOverlayTexture = null
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
      updateSceneHelpers(modelStats.value)

      if (url === DEFAULT_MODEL) {
        createRiskOverlay()
      }

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
      if (!material.map && material.color) {
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
      name: `震源${String(i + 1).padStart(2, "0")}`,
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
  return THREE.MathUtils.clamp(maxSize * 0.012, 0.006, 2.2)
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
  if (!modelRoot) return

  riskOverlayGroup = new THREE.Group()
  riskOverlayGroup.name = "demo-workface-risk-overlay"

  const geometry = new THREE.BufferGeometry()
  const { xMin, xMax, y, zMin, zMax } = DEMO_WORKFACE
  geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(
      [
        xMin, y, zMin,
        xMax, y, zMin,
        xMax, y, zMax,
        xMin, y, zMax,
      ],
      3
    )
  )
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute([0, 0, 1, 0, 1, 1, 0, 1], 2))
  geometry.setIndex([0, 2, 1, 0, 3, 2])
  geometry.computeVertexNormals()

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
    new THREE.EdgesGeometry(geometry),
    new THREE.LineBasicMaterial({ color: 0x63e8ff, transparent: true, opacity: 0.8 })
  )
  border.renderOrder = 6
  riskOverlayGroup.add(border)
  riskOverlayGroup.visible = showRiskOverlay.value
  modelRoot.add(riskOverlayGroup)

  new THREE.TextureLoader().load(
    DEFAULT_RISK_MAP,
    (sourceTexture) => {
      if (!riskOverlayMaterial || !riskOverlayGroup) {
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

      riskOverlayTexture = new THREE.CanvasTexture(canvas)
      riskOverlayTexture.colorSpace = THREE.SRGBColorSpace
      riskOverlayTexture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy())
      riskOverlayMaterial.map = riskOverlayTexture
      riskOverlayMaterial.needsUpdate = true
      riskOverlayReady.value = true
    },
    undefined,
    () => {
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
  if (!camera || !controls || !riskOverlayReady.value) return
  if (sceneTimeline) sceneTimeline.kill()

  const { xMin, xMax, y, zMin, zMax } = DEMO_WORKFACE
  const center = new THREE.Vector3((xMin + xMax) / 2, y, (zMin + zMax) / 2)
  const span = Math.max(xMax - xMin, zMax - zMin)
  const destination = new THREE.Vector3(
    center.x + span * 0.82,
    center.y + span * 1.08,
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
</script>

<style scoped>
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
