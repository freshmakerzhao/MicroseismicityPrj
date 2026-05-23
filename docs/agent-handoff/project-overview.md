# Project Overview

## 总体目标

本项目是一个本地数据可视化平台，面向矿山、微震、巷道模型等业务场景。目标是把 Excel/空间数据/三维模型整合到一个 Web 界面中，完成：

- 上传微震或计算数据文件。
- 调用后端和 Surfer 生成等值图。
- 在前端查看、缩放、拖拽生成结果图。
- 使用 ECharts 展示微震中心线和预警点位。
- 使用 Three.js 加载 GLB/GLTF 巷道模型。
- 后续在 3D 模型上叠加业务点位、颜色风险等级、事件分布等图层。

## 技术栈

### 前端

- Vue 2.6
- Vue Router 3
- Vue CLI 4 / webpack 4
- iView 3
- ECharts 5
- Axios
- Three.js 0.140.2

### 后端

- Python / FastAPI / Uvicorn
- Surfer COM 自动化
- pywin32
- python-multipart

## 目录结构

- `src/`: 前端源码。
- `src/views/home.vue`: 顶层页面布局和右上角功能导航。
- `src/router/index.js`: 路由注册。
- `src/lib/surfer.js`: 前端调用 Surfer 和微震 API 的 Axios 封装。
- `src/lib/globalConfig.js`: 前端调用全局配置 API 的 Axios 封装。
- `server/`: 后端源码。
- `server/main.py`: 后端启动入口，运行 `uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)`。
- `server/app/api/routes/`: FastAPI 路由。
- `server/app/services/`: 业务服务。
- `server/config/app_config.json`: 后端全局配置。
- `server/output/`: Surfer 生成图输出目录。
- `server/uploads/`: 上传文件和中间文件目录。
- `public/models/`: 前端静态 3D 模型目录。
- `test/`: 测试模型、脚本、实验文件。
- `docs/agent-handoff/`: 当前 Agent 交接文档目录。

## 当前页面模块

### `/page5` 微震 W 等值图

文件：`src/views/page5.vue`

能力：

- 上传 `.xls` 文件。
- 调用 `generateSurferMap(file)`。
- 后端调用 Surfer 生成图片。
- 前端居中展示图片。
- 支持滚轮缩放、鼠标拖拽平移、重置视图、关闭图片。
- 右上角可打开全局配置面板。

相关前端 API：

- `src/lib/surfer.js` 中的 `generateSurferMap`

相关后端：

- `server/app/api/routes/surfer.py`
- `server/app/services/surfer_service.py`
- `server/surfer_worker.py`

### `/page6` 微震预警

文件：`src/views/page6.vue`

能力：

- 加载巷道中心线。
- 上传微震 Excel。
- 调用后端计算预警数据。
- 使用 ECharts 绘制中心线和微震事件散点。
- 根据 W 值对散点做颜色分级。
- 支持显示/隐藏微震点、刷新、重置视图。

相关前端 API：

- `getMicroseismicCenterline`
- `calculateMicroseismicWarning`

相关后端：

- `server/app/api/routes/microseismic.py`
- `server/app/services/centerline_service.py`
- `server/app/services/microseismic_service.py`

### `/page7` 3D Viewer

文件：`src/views/page7.vue`

能力：

- 使用 Three.js 加载 GLB/GLTF。
- 默认加载 `public/models/ferriere_mines_lower_tunnels_1k.glb`。
- 支持 OrbitControls 鼠标旋转、缩放、平移。
- 支持 `Open GLB` 按钮选择本地 `.glb/.gltf`。
- 支持拖拽本地 `.glb/.gltf` 到页面加载。
- 加载后自动计算模型包围盒并调整相机。
- 带基础灯光、GridHelper 和 AxesHelper。

当前用途：

- 验证 Web 端三维巷道模型加载流程。
- 为后续“模型叠加点位颜色图层”打基础。

## 启动方式

### 前端

```bash
npm run serve
```

当前曾验证开发服务可运行在：

```text
http://localhost:8081/#/page7
```

端口可能因 8080 被占用而自动变化。

### 后端

```bash
cd server
python main.py
```

默认地址：

```text
http://localhost:5000
http://localhost:5000/api/health
http://localhost:5000/docs
```

## 重要环境说明

- 项目适合 Node.js 16.x + npm 8.x，但当前环境可见 Node.js 18.16.0 + npm 9.5.1。
- 当前 `node_modules` 存在 `.store` 和符号链接结构，`npm install three@0.140.2 --save` 曾触发 npm arborist 错误。
- Three.js 已通过 `npm pack three@0.140.2` 后手动解压到 `node_modules/three`，并写入 `package.json`。
- `three-0.140.2.tgz` 当前留在项目根目录，属于安装过程产物，后续可在确认依赖稳定后清理。
