# Current Progress

## 已完成

### 基础项目

- Vue 2 前端结构存在，使用 `home.vue` 作为主布局。
- 右上角功能导航通过 `featureTabs` 配置。
- 后端 FastAPI 项目存在，入口为 `server/main.py`。
- 前后端默认 API 约定为 `http://localhost:5000/api`。

### Surfer 等值图功能

- `/page5` 已实现上传 `.xls` 并调用后端生成 Surfer 图片。
- 支持图片显示、缩放、拖拽、重置和关闭。
- 支持全局配置弹窗，包括输出目录、上传目录、Surfer 安装路径、Surfer exe 路径、色阶文件路径等。

### 微震预警二维展示

- `/page6` 已实现中心线加载和微震 Excel 上传。
- 后端可返回中心线、事件点和元信息。
- 前端使用 ECharts 展示中心线和风险散点。
- 散点颜色按 W 值分级。

### Three.js / GLB 查看器

- 已在 `package.json` 增加：

```json
"three": "0.140.2"
```

- 已新增 `src/views/page7.vue`。
- 已在 `src/router/index.js` 注册 `/page7`。
- 已在 `src/views/home.vue` 顶部导航增加 `3D Viewer`。
- 已复制默认模型：

```text
public/models/ferriere_mines_lower_tunnels_1k.glb
```

- `/page7` 支持：
  - 默认加载 GLB。
  - 拖拽本地 GLB/GLTF。
  - 文件选择加载 GLB/GLTF。
  - OrbitControls 交互。
  - 自动适配相机。
  - Reset 重置相机。

## 验证记录

最近一次已验证：

```bash
npm run build
```

结果：

- 构建成功。
- 只有资源体积警告。
- `public/models/ferriere_mines_lower_tunnels_1k.glb` 约 31.8 MiB，触发 webpack 资源大小警告。

开发服务曾启动成功：

```text
http://localhost:8081
http://localhost:8081/#/page7
```

`Invoke-WebRequest http://localhost:8081/#/page7` 曾返回 200。

## 当前风险和问题

### 1. npm install 异常

现象：

```text
TypeError: Cannot read properties of null (reading 'matches')
at Link.matches ...
```

判断：

- 不是 Three.js 版本问题。
- 更可能是当前 `node_modules/.store` 链接式依赖结构与 npm 9 arborist 不兼容。

处理现状：

- 已绕过 `npm install`。
- 使用 `npm pack three@0.140.2` 下载包。
- 手动解压到 `node_modules/three`。
- 已确认 Three.js revision 为 140。

建议：

- 短期继续开发，不必马上重装 Node。
- 长期建议在关闭 VS Code、终端、杀毒占用后，备份或重建 `node_modules`。
- 如果后续环境仍不稳，建议切换到 Node.js 16.20.2 + npm 8.x。

### 2. Git safe.directory

执行 `git status` 曾出现：

```text
fatal: detected dubious ownership in repository at 'E:/Workspace_school/vue-echarts-master'
```

不要擅自运行全局配置命令。若用户同意，可执行：

```bash
git config --global --add safe.directory E:/Workspace_school/vue-echarts-master
```

### 3. README 中文乱码

根目录 `README.md` 当前有明显中文乱码。不要以 README 作为唯一事实来源。本目录文档是新的正常中文交接材料。

### 4. 3D 默认模型体积较大

默认模型约 33 MB。用于测试可接受，但生产环境建议：

- 压缩 GLB。
- 考虑 Draco / meshopt。
- 或把大模型放到后端静态资源、对象存储、局域网文件服务。

### 5. 3D 点位叠加尚未实现

用户明确提出后续希望：

- 模型中显示业务点位。
- 根据计算结果修改点位颜色。
- 或叠加一层图层实现不同颜色显示。

当前只完成了 GLB 查看器，没有实现点位图层。

## 当前建议不要动的内容

- 不要删除 `资料/`，里面有 DXF、业务数据源等。
- 不要删除 `server/output/` 和 `server/uploads/`，可能包含用户生成和上传数据。
- 不要随意替换 `page1.vue`，用户有 `page1 copy.vue` 打开的历史上下文。
- 不要重构已有 ECharts 大屏页面，除非任务明确要求。
