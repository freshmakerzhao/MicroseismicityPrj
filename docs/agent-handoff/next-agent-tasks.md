# Next Agent Tasks

## 推荐下一阶段目标

把 `/page7` 从“模型查看器”升级为“3D 巷道业务可视化底座”。

建议路线：

1. 保持 GLB 模型作为空间底图。
2. 新增独立点位图层，不直接修改 GLB 原始模型。
3. 点位数据先用本地 JSON mock，后续再接后端计算结果。
4. 根据点位 value / risk / status 映射颜色。
5. 增加点位开关、颜色图例、tooltip、点击选中。

## 点位图层建议设计

### 数据格式

先使用静态 JSON：

```json
[
  { "id": "P001", "name": "监测点001", "x": 1.2, "y": 0.4, "z": -2.5, "value": 0.82 },
  { "id": "P002", "name": "监测点002", "x": 2.8, "y": 0.9, "z": -1.1, "value": 0.35 }
]
```

推荐路径：

```text
public/mock/model-points.json
```

### 颜色规则

建议先用固定阈值：

```js
function getRiskColor(value) {
    if (value >= 0.8) return 0xff4d4f;
    if (value >= 0.5) return 0xfaad14;
    if (value >= 0.25) return 0xfadb14;
    return 0x36cfc9;
}
```

### 渲染方式

优先方案：

- 点数少于几千：使用 `THREE.Mesh` 小球，方便点击、tooltip、逐点改色。
- 点数很多：使用 `THREE.Points` + `BufferGeometry` + `vertexColors`，性能更好。

当前业务更像监测点和微震事件，建议先用小球 Mesh，后续再优化。

### 与模型坐标关系

需要确认点位坐标和 GLB 模型坐标是否同一坐标系。

如果不是，需要加一层坐标转换：

```js
function mapBusinessPointToModel(point) {
    return {
        x: point.x * scale + offsetX,
        y: point.z * scale + offsetY,
        z: -point.y * scale + offsetZ
    };
}
```

具体映射必须结合真实模型方向、业务数据坐标定义确认。

## 可拆分任务

### Task 1: 为 `/page7` 增加 mock 点位图层

目标：

- 新建 `public/mock/model-points.json`。
- 在 `page7.vue` 加载 JSON。
- 添加 `pointLayer` group。
- 使用小球显示点位。
- 根据 value 设置颜色。
- 加一个按钮控制点位显示/隐藏。

涉及文件：

- `src/views/page7.vue`
- `public/mock/model-points.json`

### Task 2: 增加点位 tooltip 和点击选中

目标：

- 使用 `THREE.Raycaster`。
- 鼠标移动时显示悬浮信息。
- 点击点位后高亮选中。

建议：

- tooltip 用普通 HTML 绝对定位，不要做成 3D Text。
- 点位 Mesh 的 `userData` 存储 id/name/value。

### Task 3: 接入后端计算结果

目标：

- 后端提供点位/事件 JSON。
- 前端请求后更新点位颜色。
- 保持模型和点位数据解耦。

可选接口：

```text
GET /api/model-points
POST /api/model-points/calculate
```

### Task 4: 支持 DXF 到 GLB 的正式转换流程

背景：

- 用户有 DXF 图纸，曾讨论过前端直接读 DXF 与 GLB 的取舍。
- 标准建议是：DXF 作为 CAD 源数据，转换成 GLB/GLTF 给 Three.js 加载。

建议流程：

```text
DXF 原始图纸
  -> 后端或离线转换
  -> GLB/GLTF
  -> 前端 Three.js 加载
```

注意：

- 不建议前端直接解析大型 DXF 做正式功能。
- 如果需要保留 CAD 图层语义，转换时应输出图层信息到 JSON sidecar。

## 当前开发注意事项

### Three.js 版本

使用：

```text
three@0.140.2
```

导入写法：

```js
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
```

### Vue 版本

项目是 Vue 2，不要使用 Vue 3 Composition API 写法。

### UI 风格

当前整体是深色大屏风格。新增 UI 应保持：

- 深色背景。
- 青蓝色边框/文字。
- iView Button 等已有组件优先。
- 不要引入新的 UI 框架。

### 大文件

GLB 默认模型很大。构建会有体积警告，这是预期现象。不要为了消除警告删除模型，除非另有替代资源。

### 后端

Surfer 自动化依赖 Windows 和本机 Surfer 安装。非 Windows 或未安装 Surfer 时，`/page5` 相关功能无法完整验证。

## 给后续 Agent 的建议

- 如果任务是 UI 或 Three.js 功能，优先改 `src/views/page7.vue`，保持改动集中。
- 如果任务是微震二维预警，优先看 `src/views/page6.vue` 和 `server/app/services/microseismic_service.py`。
- 如果任务是 Surfer 图片生成，优先看 `src/views/page5.vue`、`server/app/services/surfer_service.py`、`server/surfer_worker.py`。
- 如果任务是配置弹窗，优先看 `src/views/home.vue`、`src/lib/globalConfig.js`、`server/app/api/routes/config.py`。
