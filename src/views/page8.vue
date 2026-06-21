<template>
    <div class="mine3d-page">
        <div class="viewer-toolbar">
            <div class="model-info">
                <span class="title">3D 矿井地图 · 红阳矿区</span>
                <span class="sub" v-if="stats.events !== null">
                    {{ stats.roadways }} 条巷道 · {{ stats.faces }} 个工作面 ·
                    {{ stats.events }} 个微震事件 · {{ stats.elevations }} 个高程点
                </span>
            </div>
            <div class="actions">
                <Button size="small" @click="toggleEvents">{{ showEvents ? '隐藏微震' : '显示微震' }}</Button>
                <Button size="small" @click="toggleFaces">{{ showFaces ? '隐藏工作面' : '显示工作面' }}</Button>
                <Button size="small" type="primary" @click="resetCamera">重置视角</Button>
            </div>
        </div>

        <div ref="viewer" class="viewer"></div>

        <div v-if="loading" class="state-panel">
            <Spin size="large"></Spin>
            <span>正在加载矿井几何数据...</span>
        </div>

        <div v-if="errorMessage" class="error-panel">{{ errorMessage }}</div>

        <div class="legend" v-if="!loading && !errorMessage">
            <div class="legend-row"><span class="dot" style="background:#ff8a3d"></span>7煤巷道</div>
            <div class="legend-row"><span class="dot" style="background:#ffd24d"></span>12煤巷道</div>
            <div class="legend-row"><span class="dot" style="background:#9aa0a6"></span>岩巷</div>
            <div class="legend-row"><span class="dot" style="background:#cfd8dc"></span>工作面 / 采空区</div>
            <div class="legend-row"><span class="dot glow" style="background:#ff3b3b"></span>微震事件（大=高能）</div>
        </div>
    </div>
</template>

<script>
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

const SEAM_FALLBACK_Z = -1000;
const FACE_HEIGHT = 6;          // visual extrusion height (m), exaggerated
const ROADWAY_RADIUS = 2.2;     // tube radius (m), exaggerated
const SCENE_Z_GAIN = 6;         // exaggerate vertical variation to make depth visible

// Seam-specific colors for the semi-transparent reference planes
const SEAM_PLANE_STYLE = {
    coal7:  { color: 0x3a2a18, opacity: 0.35 },
    coal12: { color: 0x18253a, opacity: 0.35 },
    rock:   { color: 0x222831, opacity: 0.20 }
};

export default {
    name: 'page8',
    data() {
        return {
            renderer: null,
            scene: null,
            camera: null,
            controls: null,
            animationId: null,
            resizeObserver: null,
            data: null,
            loading: true,
            errorMessage: '',
            showEvents: true,
            showFaces: true,
            stats: { roadways: 0, faces: 0, events: null, elevations: 0 },
            // group references for toggling visibility
            groups: {
                roadways: null,
                faces: null,
                events: null,
                floor: null,
                axes: null
            },
            cameraHome: null
        };
    },
    mounted() {
        this.initScene();
        this.fetchData();
    },
    beforeDestroy() {
        if (this.resizeObserver) this.resizeObserver.disconnect();
        window.removeEventListener('resize', this.resize);
        if (this.animationId) cancelAnimationFrame(this.animationId);
        if (this.controls) this.controls.dispose();
        if (this.renderer) {
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
            this.scene.background = new THREE.Color(0x05122a);
            this.scene.fog = new THREE.Fog(0x05122a, 1200, 4500);

            this.camera = new THREE.PerspectiveCamera(45, width / height, 1, 20000);
            this.camera.position.set(800, 800, 800);

            this.renderer = new THREE.WebGLRenderer({ antialias: true });
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
            this.renderer.setSize(width, height);
            this.renderer.outputEncoding = THREE.sRGBEncoding;
            this.$refs.viewer.appendChild(this.renderer.domElement);

            this.controls = new OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.08;

            this.addLights();
            this.observeResize();
            this.animate();
        },
        addLights() {
            this.scene.add(new THREE.AmbientLight(0xffffff, 0.55));
            const key = new THREE.DirectionalLight(0xffffff, 0.9);
            key.position.set(800, 1500, 600);
            this.scene.add(key);
            const fill = new THREE.DirectionalLight(0x78c7ff, 0.45);
            fill.position.set(-800, 600, -600);
            this.scene.add(fill);
            const rim = new THREE.DirectionalLight(0xffb070, 0.3);
            rim.position.set(0, 400, -1200);
            this.scene.add(rim);
        },
        observeResize() {
            this.resizeObserver = new ResizeObserver(this.resize);
            this.resizeObserver.observe(this.$refs.viewer);
            window.addEventListener('resize', this.resize);
        },
        resize() {
            if (!this.renderer || !this.camera || !this.$refs.viewer) return;
            const w = this.$refs.viewer.clientWidth;
            const h = this.$refs.viewer.clientHeight;
            if (!w || !h) return;
            this.camera.aspect = w / h;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(w, h);
        },
        animate() {
            this.animationId = requestAnimationFrame(this.animate);
            if (this.controls) this.controls.update();
            if (this.renderer && this.scene && this.camera) {
                this.renderer.render(this.scene, this.camera);
            }
        },
        async fetchData() {
            try {
                const resp = await fetch('/mine3d.json');
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                this.data = await resp.json();
                this.buildScene();
                this.loading = false;
            } catch (err) {
                this.loading = false;
                this.errorMessage = '加载 mine3d.json 失败: ' + err.message;
                // eslint-disable-next-line no-console
                console.error(err);
            }
        },
        // Transform mine-local (x, y, z_elevation) → three.js (x, y_up, -z).
        // We center on bbox and exaggerate vertical variation.
        // `seamZBySeam` maps seam tag → mine elevation; the renderer picks the
        // correct Z per polyline/polygon so different coal layers don't overlap.
        makeTransform() {
            const meta = this.data.meta;
            const cx = meta.center[0];
            const cy = meta.center[1];
            const seamMap = meta.seamZBySeam || {};
            const fallback = meta.seamZ != null ? meta.seamZ : SEAM_FALLBACK_Z;
            // Use the overall median as the visual "y=0" reference so the
            // stack sits centered around the camera target.
            const refZ = fallback;
            const seamY = seam => {
                const z = seamMap[seam];
                if (z == null) return 0;
                return (z - refZ) * SCENE_Z_GAIN;
            };
            return {
                cx,
                cy,
                refZ,
                seamMap,
                seamY,
                v3: (x, y, zMineElev) => {
                    const dz = (zMineElev - refZ) * SCENE_Z_GAIN;
                    return new THREE.Vector3(x - cx, dz, -(y - cy));
                }
            };
        },
        buildScene() {
            const tf = this.makeTransform();
            this.buildFloor(tf);
            this.buildFaces(tf);
            this.buildRoadways(tf);
            this.buildEvents(tf);
            this.fitCamera();
        },
        buildFloor(tf) {
            const meta = this.data.meta;
            const [minx, miny, maxx, maxy] = meta.bbox;
            const w = maxx - minx;
            const h = maxy - miny;
            const group = new THREE.Group();
            group.name = 'floor';

            // Reference plane below the lowest seam, acting as the "ground"
            const seamYs = Object.keys(meta.seamZBySeam || {}).map(s =>
                (meta.seamZBySeam[s] - tf.refZ) * SCENE_Z_GAIN
            );
            const lowestY = seamYs.length ? Math.min(...seamYs) - FACE_HEIGHT * 1.5 : -50;

            const planeGeom = new THREE.PlaneGeometry(w * 1.05, h * 1.05);
            const planeMat = new THREE.MeshStandardMaterial({
                color: 0x0a1a30,
                metalness: 0.1,
                roughness: 0.95,
                transparent: true,
                opacity: 0.55,
                side: THREE.DoubleSide
            });
            const plane = new THREE.Mesh(planeGeom, planeMat);
            plane.rotation.x = -Math.PI / 2;
            plane.position.y = lowestY;
            group.add(plane);

            // Grid at the ground reference
            const gridSize = Math.max(w, h) * 1.05;
            const grid = new THREE.GridHelper(gridSize, 24, 0x2a5680, 0x14304a);
            grid.position.y = lowestY + 0.2;
            group.add(grid);

            // Per-seam reference planes so the layered structure reads as 3D
            const seamMap = meta.seamZBySeam || {};
            Object.keys(seamMap).forEach(seam => {
                const style = SEAM_PLANE_STYLE[seam] || { color: 0x223040, opacity: 0.2 };
                const sGeom = new THREE.PlaneGeometry(w, h);
                const sMat = new THREE.MeshBasicMaterial({
                    color: style.color,
                    transparent: true,
                    opacity: style.opacity,
                    side: THREE.DoubleSide,
                    depthWrite: false
                });
                const sMesh = new THREE.Mesh(sGeom, sMat);
                sMesh.rotation.x = -Math.PI / 2;
                sMesh.position.y = tf.seamY(seam) - 0.2;
                sMesh.name = `seam-plane-${seam}`;
                group.add(sMesh);
            });

            this.scene.add(group);
            this.groups.floor = group;
        },
        buildFaces(tf) {
            const group = new THREE.Group();
            group.name = 'faces';
            const faces = this.data.faces || [];
            this.stats.faces = faces.length;

            // Per-seam material so 7煤 / 12煤 / 岩巷 blocks read differently
            const seamMatCache = {};
            const matForSeam = seam => {
                if (seamMatCache[seam]) return seamMatCache[seam];
                const color = ({
                    coal7:  0xe6d2a8,
                    coal12: 0xc0d4e0,
                    rock:   0x9aa0a6
                })[seam] || 0xcfd8dc;
                seamMatCache[seam] = new THREE.MeshStandardMaterial({
                    color,
                    metalness: 0.15,
                    roughness: 0.6,
                    transparent: true,
                    opacity: 0.92
                });
                return seamMatCache[seam];
            };
            const edgeMat = new THREE.LineBasicMaterial({ color: 0x9ab4cc, transparent: true, opacity: 0.55 });

            faces.forEach(face => {
                const pts = face.points;
                if (!pts || pts.length < 3) return;
                const shape = new THREE.Shape();
                shape.moveTo(pts[0][0] - tf.cx, -(pts[0][1] - tf.cy));
                for (let i = 1; i < pts.length; i++) {
                    shape.lineTo(pts[i][0] - tf.cx, -(pts[i][1] - tf.cy));
                }
                const geom = new THREE.ExtrudeGeometry(shape, {
                    depth: FACE_HEIGHT,
                    bevelEnabled: false,
                    steps: 1
                });
                geom.rotateX(-Math.PI / 2);
                // Lift each face to its seam Z
                const yOffset = tf.seamY(face.seam);
                geom.translate(0, yOffset, 0);

                const mesh = new THREE.Mesh(geom, matForSeam(face.seam));
                group.add(mesh);

                const edges = new THREE.EdgesGeometry(geom, 1);
                group.add(new THREE.LineSegments(edges, edgeMat));
            });

            this.scene.add(group);
            this.groups.faces = group;
        },
        buildRoadways(tf) {
            const group = new THREE.Group();
            group.name = 'roadways';
            const roadways = this.data.roadways || [];
            this.stats.roadways = roadways.length;

            const materialCache = new Map();
            roadways.forEach(rw => {
                const pts = rw.points;
                if (!pts || pts.length < 2) return;
                const seamY = tf.seamY(rw.seam) + FACE_HEIGHT * 0.55;
                const v3 = pts.map(p => new THREE.Vector3(p[0] - tf.cx, seamY, -(p[1] - tf.cy)));
                if (v3.length < 2) return;

                let mat = materialCache.get(rw.color);
                if (!mat) {
                    const color = new THREE.Color(rw.color || '#cccccc');
                    mat = new THREE.MeshStandardMaterial({
                        color,
                        emissive: color.clone().multiplyScalar(0.35),
                        metalness: 0.4,
                        roughness: 0.35
                    });
                    materialCache.set(rw.color, mat);
                }

                try {
                    const curve = new THREE.CatmullRomCurve3(v3, false, 'catmullrom', 0.0);
                    const tubularSegments = Math.max(2, (v3.length - 1) * 2);
                    const tube = new THREE.TubeGeometry(curve, tubularSegments, ROADWAY_RADIUS, 6, false);
                    group.add(new THREE.Mesh(tube, mat));
                } catch (err) {
                    // Fall back to a simple line if tube fails for degenerate inputs
                    const geom = new THREE.BufferGeometry().setFromPoints(v3);
                    const lineMat = new THREE.LineBasicMaterial({ color: rw.color || '#cccccc' });
                    group.add(new THREE.Line(geom, lineMat));
                }
            });

            this.scene.add(group);
            this.groups.roadways = group;
        },
        buildEvents(tf) {
            const group = new THREE.Group();
            group.name = 'events';
            const events = this.data.events || [];
            this.stats.events = events.length;
            this.stats.elevations = (this.data.elevations || []).length;
            if (events.length === 0) {
                this.scene.add(group);
                this.groups.events = group;
                return;
            }

            // Normalize energy on a log scale (huge dynamic range: 0.06 .. 1.45M J)
            const energies = events.map(e => e[3]).filter(e => e > 0);
            const logMin = Math.log10(Math.min(...energies));
            const logMax = Math.log10(Math.max(...energies));
            const span = Math.max(1e-3, logMax - logMin);
            // Event z values live in their own datum (mean ~+700), well above the
            // mine seam (~-1000). Center events around seam_z so they read as
            // depth-varying near the geometry.
            const eventZs = events.map(e => e[2]);
            const meanEventZ = eventZs.reduce((a, b) => a + b, 0) / eventZs.length;

            const sphereGeom = new THREE.SphereGeometry(1, 12, 10);

            events.forEach(ev => {
                const [x, y, z, energy] = ev;
                if (energy <= 0) return;
                const t = (Math.log10(energy) - logMin) / span; // 0..1
                const radius = 3 + t * 10;
                // color: cool blue (low) → yellow → red (high)
                const color = new THREE.Color();
                if (t < 0.5) {
                    color.lerpColors(new THREE.Color('#4fc3f7'), new THREE.Color('#ffeb3b'), t * 2);
                } else {
                    color.lerpColors(new THREE.Color('#ffeb3b'), new THREE.Color('#ff3b3b'), (t - 0.5) * 2);
                }
                const mat = new THREE.MeshStandardMaterial({
                    color,
                    emissive: color.clone().multiplyScalar(0.9),
                    emissiveIntensity: 1.0,
                    metalness: 0.1,
                    roughness: 0.4,
                    transparent: true,
                    opacity: 0.95
                });
                const mesh = new THREE.Mesh(sphereGeom, mat);
                mesh.scale.setScalar(radius);

                // Place near the seam, with relative depth variation around it
                const relativeZ = z - meanEventZ; // 0-centered
                const sceneY = relativeZ * SCENE_Z_GAIN * 0.3 + FACE_HEIGHT * 1.5;
                mesh.position.set(x - tf.cx, sceneY, -(y - tf.cy));

                group.add(mesh);
            });

            this.scene.add(group);
            this.groups.events = group;
        },
        fitCamera() {
            const meta = this.data.meta;
            const [minx, miny, maxx, maxy] = meta.bbox;
            const w = maxx - minx;
            const h = maxy - miny;
            const radius = Math.max(w, h);
            this.controls.target.set(0, FACE_HEIGHT / 2, 0);
            this.camera.position.set(radius * 0.45, radius * 0.55, radius * 0.95);
            this.camera.updateProjectionMatrix();
            this.controls.update();
            this.cameraHome = {
                pos: this.camera.position.clone(),
                target: this.controls.target.clone()
            };
        },
        resetCamera() {
            if (!this.cameraHome) return;
            this.camera.position.copy(this.cameraHome.pos);
            this.controls.target.copy(this.cameraHome.target);
            this.controls.update();
        },
        toggleEvents() {
            this.showEvents = !this.showEvents;
            if (this.groups.events) this.groups.events.visible = this.showEvents;
        },
        toggleFaces() {
            this.showFaces = !this.showFaces;
            if (this.groups.faces) this.groups.faces.visible = this.showFaces;
        }
    }
};
</script>

<style lang="less" scoped>
.mine3d-page {
    position: relative;
    width: 100%;
    height: 100%;
    background:
        radial-gradient(circle at 50% 40%, rgba(48, 220, 255, 0.1), transparent 34%),
        rgba(2, 8, 20, 0.2);
    overflow: hidden;
}

.viewer {
    width: 100%;
    height: 100%;
}

.viewer-toolbar {
    position: absolute;
    top: 18px;
    left: 28px;
    right: 28px;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    pointer-events: none;
}

.model-info {
    padding: 10px 14px;
    border: 1px solid rgba(48, 220, 255, 0.24);
    background: linear-gradient(90deg, rgba(8, 39, 74, 0.76), rgba(8, 39, 74, 0.12));
    color: #d8f3ff;
    text-shadow: 0 1px 8px rgba(0, 0, 0, 0.55);

    .title {
        display: block;
        font-size: 17px;
        font-weight: 600;
        letter-spacing: 1px;
        background: linear-gradient(180deg, #dffbff 0%, #73ecff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .sub {
        display: block;
        margin-top: 4px;
        color: #93bdd1;
        font-size: 12px;
    }
}

.actions {
    display: flex;
    align-items: center;
    gap: 10px;
    pointer-events: auto;

    /deep/ .ivu-btn {
        color: #c4f3fe;
        border-color: rgba(48, 220, 255, 0.55);
        background: linear-gradient(180deg, rgba(21, 91, 127, 0.85), rgba(7, 30, 64, 0.85));
        box-shadow: inset 0 0 12px rgba(48, 220, 255, 0.12);
    }
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
    padding: 18px 22px;
    border: 1px solid rgba(120, 199, 255, 0.4);
    border-radius: 4px;
    background: rgba(5, 18, 42, 0.9);
    color: #d8f3ff;
}

.error-panel {
    top: auto;
    bottom: 34px;
    color: #ffd9d9;
    border-color: rgba(255, 100, 100, 0.5);
}

.legend {
    position: absolute;
    left: 22px;
    bottom: 22px;
    z-index: 8;
    padding: 12px 14px;
    border: 1px solid rgba(48, 220, 255, 0.28);
    border-radius: 4px;
    background: linear-gradient(180deg, rgba(13, 55, 80, 0.72), rgba(6, 20, 45, 0.76));
    box-shadow: inset 0 0 18px rgba(48, 220, 255, 0.08);
    color: #d8f3ff;
    font-size: 12px;
    line-height: 1.9;
    pointer-events: none;

    .legend-row {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;

        &.glow {
            box-shadow: 0 0 8px currentColor;
        }
    }
}
</style>
