<template>
    <div
        class="glb-page"
        :class="{ 'is-dragging': isDragging }"
        @dragenter.prevent="onDragEnter"
        @dragover.prevent="onDragOver"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
    >
        <div class="viewer-toolbar">
            <div class="model-info">
                <span class="title">3D Model Viewer</span>
                <span class="file-name">{{ currentName }}</span>
            </div>
            <div class="actions">
                <Button size="small" :disabled="loading || !observations.length" @click="toggleObservationLayer">
                    {{ showObservations ? 'Hide Points' : 'Show Points' }}
                </Button>
                <Button size="small" :disabled="loading || !observations.length" @click="recalculateObservationColors">Recalculate Colors</Button>
                <Button size="small" :disabled="loading" @click="resetCamera">Reset</Button>
                <Button size="small" type="primary" :loading="loading" @click="$refs.fileInput.click()">Open GLB</Button>
                <input
                    ref="fileInput"
                    class="file-input"
                    type="file"
                    accept=".glb,.gltf,model/gltf-binary,model/gltf+json"
                    @change="onFileChange"
                >
            </div>
        </div>

        <div ref="viewer" class="viewer"></div>

        <div v-if="loading" class="state-panel">
            <Spin size="large"></Spin>
            <span>Loading model...</span>
        </div>

        <div v-if="errorMessage" class="error-panel">
            {{ errorMessage }}
        </div>

        <div v-if="selectedObservation" class="observation-panel">
            <div class="panel-title">{{ selectedObservation.name }}</div>
            <div>ID: {{ selectedObservation.id }}</div>
            <div>Risk: {{ selectedObservation.riskValue.toFixed(3) }}</div>
            <div>Stress: {{ selectedObservation.stressIndex.toFixed(2) }}</div>
            <div>Energy: {{ selectedObservation.energyIndex.toFixed(2) }}</div>
        </div>

        <div class="drop-hint">
            Drag a .glb or .gltf file here. Click colored points to inspect observations.
        </div>
    </div>
</template>

<script>
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

const DEFAULT_MODEL = '/models/hongyang-coal-mine.glb';
const OBSERVATION_POINTS = '/mock/hongyang-observation-points.json';

export default {
    name: 'page7',
    data() {
        return {
            renderer: null,
            scene: null,
            camera: null,
            controls: null,
            loader: null,
            raycaster: null,
            mouse: null,
            modelRoot: null,
            pointLayer: null,
            animationId: null,
            resizeObserver: null,
            objectUrl: '',
            currentName: 'hongyang-coal-mine.glb',
            observations: [],
            selectedObservation: null,
            showObservations: true,
            formulaVersion: 0,
            loading: false,
            isDragging: false,
            dragDepth: 0,
            errorMessage: ''
        };
    },
    mounted() {
        this.initScene();
        this.loadObservationPoints();
        this.loadModel(DEFAULT_MODEL, this.currentName);
    },
    beforeDestroy() {
        this.disposeObjectUrl();
        this.disposeModel();

        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        window.removeEventListener('resize', this.resize);
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.controls) {
            this.controls.dispose();
        }
        if (this.renderer) {
            this.renderer.domElement.removeEventListener('click', this.onCanvasClick);
            this.renderer.dispose();
            if (this.renderer.domElement && this.renderer.domElement.parentNode) {
                this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
            }
        }
    },
    methods: {
        initScene() {
            const width = this.$refs.viewer.clientWidth || 800;
            const height = this.$refs.viewer.clientHeight || 600;

            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0x101820);

            this.camera = new THREE.PerspectiveCamera(45, width / height, 0.01, 100000);
            this.camera.position.set(0, 4, 10);

            this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
            this.renderer.setSize(width, height);
            this.renderer.outputEncoding = THREE.sRGBEncoding;
            this.$refs.viewer.appendChild(this.renderer.domElement);
            this.renderer.domElement.addEventListener('click', this.onCanvasClick);

            this.controls = new OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.08;
            this.controls.screenSpacePanning = true;

            this.loader = new GLTFLoader();
            this.raycaster = new THREE.Raycaster();
            this.mouse = new THREE.Vector2();
            this.pointLayer = new THREE.Group();
            this.pointLayer.name = 'observation-point-layer';

            this.addLights();
            this.addHelpers();
            this.scene.add(this.pointLayer);
            this.observeResize();
            this.animate();
        },
        addLights() {
            const ambient = new THREE.AmbientLight(0xffffff, 0.65);
            this.scene.add(ambient);

            const key = new THREE.DirectionalLight(0xffffff, 1.2);
            key.position.set(6, 10, 8);
            this.scene.add(key);

            const fill = new THREE.DirectionalLight(0x78c7ff, 0.5);
            fill.position.set(-8, 4, -6);
            this.scene.add(fill);
        },
        addHelpers() {
            const grid = new THREE.GridHelper(20, 20, 0x31506b, 0x203647);
            grid.name = 'viewer-grid';
            this.scene.add(grid);

            const axes = new THREE.AxesHelper(2);
            axes.name = 'viewer-axes';
            this.scene.add(axes);
        },
        observeResize() {
            this.resizeObserver = new ResizeObserver(this.resize);
            this.resizeObserver.observe(this.$refs.viewer);
            window.addEventListener('resize', this.resize);
        },
        resize() {
            if (!this.renderer || !this.camera || !this.$refs.viewer) {
                return;
            }

            const width = this.$refs.viewer.clientWidth;
            const height = this.$refs.viewer.clientHeight;
            if (!width || !height) {
                return;
            }

            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        },
        animate() {
            this.animationId = requestAnimationFrame(this.animate);
            if (this.controls) {
                this.controls.update();
            }
            if (this.renderer && this.scene && this.camera) {
                this.renderer.render(this.scene, this.camera);
            }
        },
        loadModel(url, name) {
            this.loading = true;
            this.errorMessage = '';
            this.currentName = name || 'model.glb';

            this.loader.load(
                url,
                gltf => {
                    this.disposeModel();
                    this.modelRoot = gltf.scene || gltf.scenes[0];
                    this.normalizeMaterials(this.modelRoot);
                    this.scene.add(this.modelRoot);
                    this.fitCameraToModel();
                    this.loading = false;
                },
                undefined,
                error => {
                    this.loading = false;
                    this.errorMessage = 'Model loading failed. Please check the file format.';
                    // eslint-disable-next-line no-console
                    console.error(error);
                }
            );
        },
        normalizeMaterials(root) {
            root.traverse(child => {
                if (!child.isMesh) {
                    return;
                }
                child.castShadow = false;
                child.receiveShadow = true;

                if (child.material && child.material.map) {
                    child.material.map.encoding = THREE.sRGBEncoding;
                }
            });
        },
        fitCameraToModel() {
            if (!this.modelRoot) {
                return;
            }

            const box = new THREE.Box3().setFromObject(this.modelRoot);
            const size = box.getSize(new THREE.Vector3());
            const center = box.getCenter(new THREE.Vector3());
            const maxSize = Math.max(size.x, size.y, size.z) || 1;
            const distance = maxSize / (2 * Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2)));

            this.controls.target.copy(center);
            this.camera.near = Math.max(distance / 1000, 0.01);
            this.camera.far = distance * 1000;
            this.camera.position.set(
                center.x + distance * 0.8,
                center.y + distance * 0.55,
                center.z + distance * 1.15
            );
            this.camera.updateProjectionMatrix();
            this.controls.update();
        },
        resetCamera() {
            this.fitCameraToModel();
        },
        async loadObservationPoints() {
            try {
                const response = await fetch(OBSERVATION_POINTS);
                const points = await response.json();
                this.observations = points.map(point => ({
                    ...point,
                    riskValue: this.calculateRiskValue(point)
                }));
                this.renderObservationLayer();
            } catch (error) {
                this.errorMessage = 'Observation points loading failed.';
                // eslint-disable-next-line no-console
                console.error(error);
            }
        },
        calculateRiskValue(point) {
            const wave = Math.sin(this.formulaVersion * 0.85 + point.x * 0.31 + point.z * 0.17) * 0.08;
            const value =
                point.baseValue * 0.45 +
                point.stressIndex * 0.30 +
                point.energyIndex * 0.18 +
                point.faultInfluence * 0.07 +
                wave;

            return Math.max(0, Math.min(1, value));
        },
        riskColor(value) {
            if (value >= 0.75) return 0xff4d4f;
            if (value >= 0.5) return 0xfaad14;
            if (value >= 0.25) return 0xfadb14;
            return 0x36cfc9;
        },
        renderObservationLayer() {
            this.clearObservationLayer();

            this.observations.forEach(point => {
                const material = new THREE.MeshStandardMaterial({
                    color: this.riskColor(point.riskValue),
                    emissive: this.riskColor(point.riskValue),
                    emissiveIntensity: 0.35,
                    roughness: 0.45,
                    metalness: 0.1
                });
                const mesh = new THREE.Mesh(
                    new THREE.SphereGeometry(0.38, 24, 16),
                    material
                );

                mesh.name = point.id;
                mesh.position.set(point.x, point.y, point.z);
                mesh.userData = { type: 'observation', point };
                this.pointLayer.add(mesh);
            });

            this.pointLayer.visible = this.showObservations;
        },
        clearObservationLayer() {
            if (!this.pointLayer) {
                return;
            }

            while (this.pointLayer.children.length) {
                const child = this.pointLayer.children.pop();
                if (child.geometry) {
                    child.geometry.dispose();
                }
                if (child.material) {
                    child.material.dispose();
                }
            }
        },
        toggleObservationLayer() {
            this.showObservations = !this.showObservations;
            if (this.pointLayer) {
                this.pointLayer.visible = this.showObservations;
            }
            if (!this.showObservations) {
                this.selectedObservation = null;
            }
        },
        recalculateObservationColors() {
            this.formulaVersion += 1;
            this.observations = this.observations.map(point => ({
                ...point,
                riskValue: this.calculateRiskValue(point)
            }));

            this.pointLayer.children.forEach(mesh => {
                const point = this.observations.find(item => item.id === mesh.userData.point.id);
                if (!point) {
                    return;
                }
                mesh.userData.point = point;
                mesh.material.color.set(this.riskColor(point.riskValue));
                mesh.material.emissive.set(this.riskColor(point.riskValue));
            });

            if (this.selectedObservation) {
                this.selectedObservation = this.observations.find(point => point.id === this.selectedObservation.id) || null;
            }
        },
        onCanvasClick(event) {
            if (!this.showObservations || !this.pointLayer || !this.camera || !this.renderer) {
                return;
            }

            const rect = this.renderer.domElement.getBoundingClientRect();
            this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            this.raycaster.setFromCamera(this.mouse, this.camera);

            const hits = this.raycaster.intersectObjects(this.pointLayer.children, true);
            if (hits.length) {
                this.selectedObservation = hits[0].object.userData.point;
            } else {
                this.selectedObservation = null;
            }
        },
        onFileChange(event) {
            const file = event.target.files && event.target.files[0];
            if (file) {
                this.loadLocalFile(file);
            }
            event.target.value = '';
        },
        onDragEnter() {
            this.dragDepth += 1;
            this.isDragging = true;
        },
        onDragOver() {
            this.isDragging = true;
        },
        onDragLeave() {
            this.dragDepth = Math.max(0, this.dragDepth - 1);
            this.isDragging = this.dragDepth > 0;
        },
        onDrop(event) {
            this.dragDepth = 0;
            this.isDragging = false;

            const file = event.dataTransfer.files && event.dataTransfer.files[0];
            if (file) {
                this.loadLocalFile(file);
            }
        },
        loadLocalFile(file) {
            const lowerName = file.name.toLowerCase();
            if (!lowerName.endsWith('.glb') && !lowerName.endsWith('.gltf')) {
                this.errorMessage = 'Only .glb and .gltf files are supported.';
                return;
            }

            this.disposeObjectUrl();
            this.objectUrl = URL.createObjectURL(file);
            this.loadModel(this.objectUrl, file.name);
        },
        disposeObjectUrl() {
            if (this.objectUrl) {
                URL.revokeObjectURL(this.objectUrl);
                this.objectUrl = '';
            }
        },
        disposeModel() {
            if (!this.modelRoot) {
                return;
            }

            this.scene.remove(this.modelRoot);
            this.modelRoot.traverse(child => {
                if (child.geometry) {
                    child.geometry.dispose();
                }
                if (child.material) {
                    const materials = Array.isArray(child.material) ? child.material : [child.material];
                    materials.forEach(material => {
                        Object.keys(material).forEach(key => {
                            const value = material[key];
                            if (value && value.isTexture) {
                                value.dispose();
                            }
                        });
                        material.dispose();
                    });
                }
            });
            this.modelRoot = null;
        }
    }
};
</script>

<style lang="less" scoped>
.glb-page {
    position: relative;
    width: 100%;
    height: 100%;
    background: #101820;
    overflow: hidden;
}

.viewer {
    width: 100%;
    height: 100%;
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
    min-width: 0;
    color: #d8f3ff;
    text-shadow: 0 1px 8px rgba(0, 0, 0, 0.45);

    .title {
        display: block;
        font-size: 18px;
        font-weight: 600;
    }

    .file-name {
        display: block;
        max-width: 52vw;
        margin-top: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: #93bdd1;
        font-size: 12px;
    }
}

.actions {
    display: flex;
    align-items: center;
    gap: 10px;
    pointer-events: auto;
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
    gap: 12px;
    min-width: 220px;
    padding: 18px 22px;
    border: 1px solid rgba(120, 199, 255, 0.4);
    border-radius: 6px;
    background: rgba(9, 24, 38, 0.92);
    color: #d8f3ff;
    justify-content: center;
}

.error-panel {
    top: auto;
    bottom: 34px;
    color: #ffd9d9;
    border-color: rgba(255, 100, 100, 0.5);
}

.observation-panel {
    position: absolute;
    left: 22px;
    bottom: 22px;
    z-index: 11;
    min-width: 210px;
    padding: 12px 14px;
    border: 1px solid rgba(120, 199, 255, 0.45);
    border-radius: 6px;
    background: rgba(9, 24, 38, 0.86);
    color: #d8f3ff;
    font-size: 12px;
    line-height: 1.8;
    pointer-events: none;

    .panel-title {
        margin-bottom: 4px;
        color: #78c7ff;
        font-size: 14px;
        font-weight: 600;
    }
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

.glb-page.is-dragging::after {
    content: 'Drop GLB / GLTF file to load';
    position: absolute;
    inset: 18px;
    z-index: 20;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #78c7ff;
    border-radius: 8px;
    background: rgba(10, 34, 54, 0.72);
    color: #d8f3ff;
    font-size: 22px;
    font-weight: 600;
    pointer-events: none;
}
</style>
