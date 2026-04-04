# vue-echarts

基于 Vue 2 和 FastAPI 的本地数据可视化项目，支持上传数据文件并调用 Surfer 自动生成等值线图。

## 项目简介

本项目包含前端展示层与后端处理层。

- 前端技术栈：Vue 2、Vue Router、iView、ECharts、Axios
- 后端技术栈：FastAPI、Uvicorn、python-multipart、pywin32
- 核心能力：上传本地数据文件，调用 Surfer COM 自动绘图，返回并展示生成图片
- 配置能力：支持页面内修改全局配置并持久化到本地配置文件

## 目录结构

- src：前端源码
- server：后端源码
- server/config/app_config.json：后端全局配置文件
- server/uploads：上传临时目录（可配置）
- server/output：图片输出目录（可配置）

## 环境要求

### 前端

- Node.js 14 及以上（建议 16）
- npm 6 及以上

### 后端

- Python 3.10 及以上（建议与现有环境一致）
- Windows 系统（当前路径选择器与 Surfer COM 自动化默认按 Windows 设计）
- 本机安装 Golden Software Surfer（并确保 COM 可用）

## 快速启动

### 1. 启动前端

在项目根目录执行：

```bash
npm install
npm run serve
```

默认访问地址：

- http://localhost:8080

### 2. 启动后端

在 server 目录执行：

```bash
pip install -r requirements.txt
python main.py
```

默认后端地址：

- http://localhost:5000

### 3. 运行检查

启动后可访问以下地址进行自检：

- http://localhost:5000/api/health
- http://localhost:5000/docs

## 功能说明

### 1. 图片生成与交互

- 页面中央默认空白
- 上传成功后居中显示生成图片
- 支持滚轮缩放、拖拽平移、重置视图、关闭图片
- 上传处理中显示遮罩与提示，处理中禁用再次上传

### 2. 全局配置面板

点击右上角设置图标可打开全局配置面板，支持：

- 输出目录
- 上传目录
- 上传大小限制
- Surfer 安装目录
- Surfer EXE 路径
- 色阶文件路径

支持通过按钮弹出本机路径选择窗口（目录或文件），保存后自动写入配置文件并立即生效。

## 后端接口说明

### 健康检查

- 方法：GET
- 路径：/api/health
- 说明：服务可用性检查

### 生成图片

- 方法：POST
- 路径：/api/generate-surfer
- 请求：multipart/form-data，字段名为 file
- 返回：code、imageUrl、msg

### 获取当前配置

- 方法：GET
- 路径：/api/config
- 说明：返回当前生效配置和原始配置

### 更新配置

- 方法：PUT
- 路径：/api/config
- 说明：更新并持久化配置

### 选择目录

- 方法：POST
- 路径：/api/config/pick-directory
- 说明：在后端所在机器弹出目录选择框

### 选择文件

- 方法：POST
- 路径：/api/config/pick-file
- 说明：在后端所在机器弹出文件选择框

### 静态图片访问

- 方法：GET
- 路径：/output/{filename}
- 说明：访问生成后的图片资源

## 配置文件说明

配置文件路径：

- server/config/app_config.json

示例：

```json
{
	"upload_folder": "uploads",
	"output_folder": "D:/surfer_output",
	"max_upload_mb": 30,
	"allowed_extensions": [".xls", ".xlsx", ".csv", ".txt"],
	"cors_origins": [
		"http://localhost:8080",
		"http://localhost:3000",
		"http://127.0.0.1:8080"
	],
	"surfer": {
		"prog_id": "Surfer.Application",
		"install_dir": "E:/Application_surfer11",
		"exe_path": "",
		"clr_path": "",
		"default_colormap": "Terrain.clr",
		"visible": false,
		"screen_updating": false
	}
}
```

字段说明：

- upload_folder：上传临时目录
- output_folder：输出图片目录
- max_upload_mb：上传大小限制（MB）
- allowed_extensions：允许上传的文件后缀
- cors_origins：跨域白名单
- surfer.prog_id：Surfer COM 标识
- surfer.install_dir：Surfer 安装目录
- surfer.exe_path：Surfer 可执行文件路径
- surfer.clr_path：色阶文件路径
- surfer.default_colormap：默认色阶文件名
- surfer.visible：是否显示 Surfer 窗口
- surfer.screen_updating：是否开启界面刷新

路径规则：

- 相对路径按 server 目录解析
- 绝对路径按系统路径直接使用

色阶自动推断规则：

- 若 surfer.clr_path 为空，系统按以下顺序查找色阶文件：
1. surfer.install_dir/ColorScales/default_colormap
2. surfer.exe_path 所在目录/ColorScales/default_colormap
3. E:/Application_surfer11/ColorScales/default_colormap

## 前后端联动配置

前端请求基地址位于：

- src/lib/surfer.js
- src/lib/globalConfig.js

默认请求地址：

- http://localhost:5000/api

可通过环境变量覆盖：

- VUE_APP_API_BASE_URL

## 常见问题

### 1. 后端启动失败，python main.py 退出码为 1

建议按顺序检查：

1. 当前目录是否在 server
2. 依赖是否已安装：pip install -r requirements.txt
3. Python 环境是否与 pywin32 安装环境一致
4. 5000 端口是否被占用
5. 配置文件是否为合法 JSON

### 2. 前端启动失败，npm run serve 退出码为 1

建议按顺序检查：

1. 是否在项目根目录执行
2. 是否已安装依赖：npm install
3. Node 版本是否兼容（建议 14/16）
4. 是否有端口冲突

### 3. 上传后无图片或报 Surfer 错误

建议检查：

1. Surfer 是否正确安装
2. surfer.prog_id 是否可用
3. install_dir、exe_path、clr_path 是否正确
4. 上传文件列配置是否符合当前脚本逻辑（xCol=4, yCol=3, zCol=7）

### 5. 上传同名文件如何处理

系统会自动为上传文件和输出图片添加时间戳与随机前缀，命名格式如下：

- `yyyyMMdd_HHmmss_随机码_原始文件名`

示例：

- `20260404_213015_a1b2c3d4_红阳矿区微震预警判据.xls`

这样可以同时满足：

- 防止同名覆盖
- 便于按时间定位任务

### 4. 路径选择窗口没有弹出

说明：

- 路径选择窗口由后端弹出
- 后端必须运行在有桌面会话的本机环境
- 若后端部署在无图形界面服务器，则无法使用路径弹窗

## 维护建议

- 建议将输出目录配置到独立磁盘目录，便于管理历史图片
- 建议定期清理输出目录旧文件
- 生产场景建议将配置修改接口增加鉴权

## 许可证

当前仓库未显式提供许可证文件，请按团队规范补充 LICENSE 后再对外分发。
