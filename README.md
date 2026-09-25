# 矿井微震云图与三维展示

## 环境

- Windows 10/11，Chrome 或 Edge（启用硬件加速）。
- Node.js 18.16 或以上、npm；Python 3.10/3.11（64 位）。
- 生成云图需要安装并激活 Golden Software Surfer（已使用 Surfer 11），先手动打开一次完成授权。展示内置云图和导入图片无需 Surfer。
- 无需 Blender、数据库服务器或 C++ 编译器。

## 安装与启动

项目根目录打开 PowerShell：

```powershell
npm ci
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r server\requirements.txt
Copy-Item server\config\app_config.example.json server\config\app_config.json
```

编辑 `server/config/app_config.json`：`surfer.install_dir` 填实际安装目录；COM 无法自动启动时，`exe_path` 填实际 `Surfer.exe` 完整路径。`clr_path` 可指定色标；留空则尝试安装目录下的 `ColorScales/Terrain.clr`，找不到时使用 Surfer 默认色标。路径使用 `/` 或双反斜杠。

分别在两个 PowerShell 窗口的项目根目录运行：

```powershell
# 窗口一
$credential = Get-Credential -UserName admin -Message '设置首次管理员密码（至少 12 位）'
$env:ROCKBURST_ADMIN_PASSWORD = $credential.GetNetworkCredential().Password
.\.venv\Scripts\python.exe server\main.py
```

```powershell
# 窗口二
npm run dev
```

打开 http://127.0.0.1:8084 。管理员为 `admin`，密码使用上一步自行设置的值；不再提供固定默认密码或自动创建演示账户。SQLite 数据库自动创建。环境变量仅用于首次建号，不会重置已有账户，之后启动可省略前两行。仅用于可信本地环境，请勿直接暴露到公网。

后端端口 `5000`、前端 `8084`；占用时先停止旧服务。接口说明：http://127.0.0.1:5000/docs 。默认无需环境变量；自定义后端可在 `.env.local` 设置 `VITE_API_BASE_URL`（含 `/api`），并配置后端跨域及图片访问。

## 生成与贴图

演示数据、云图及两版模型已随仓库提供，无需另找资料：

- `public/samples/hongyang-warning-demo.xls`：生成云图的上传示例，也可在页面点击“下载演示数据”。
- `public/models/hangdao.glb`：井下地图 1.0 巷道模型。
- `public/models/hongyang-coal12-georef.glb`：井下地图 2.0 双层模型。
- `public/defaults/`：默认云图、事件和坐标配准数据；页面自动加载。

1. 在“冲击危险云图”上传 `.xls`（非空、最多 30 MB）。首个工作表第一行为标题，A～G 列依次为日期、时间、X、Y、Z、能量（J）、原 W；W 会重新计算。不能直接将 `.xlsx` 改后缀。
2. 生成后切换“井下地图1.0”，云图自动铺在 `hangdao.glb` 的工作面载体上，可旋转、调整透明度。失败保留上一张云图。
3. 也可直接导入 PNG/JPG（最多 20 MB），无需 Surfer。默认云图可勾选“裁去默认云图边框”，自制无边框贴图取消勾选。导入图片仅在当前页面有效，切换页面后需重新导入。
4. 1.0 是外观展示配准，不代表测量坐标精确对应；2.0 为内置双层坐标数据展示，不随新云图更新。展示不能代替实际安全判定。

## 检查与交付

```powershell
npm test
npm run build
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
.\.venv\Scripts\python.exe scripts\package_release.py
```

分享 `release/rockburst-platform.zip`，接收者解压后按上述步骤安装。`database/centerline_points.csv` 和 `public` 下数据、模型为运行必需。更换矿区需重新校准中线、坐标和模型。

笔记、论文、截图、其余原始资料、本地配置、账户、依赖及生成结果不进入交付包。本地资料保留并忽略，结果在 `server/output`。旧测试模型 `zhengti-demo.glb` 已移除，可从 Git 历史恢复。忽略规则不会清除 Git 历史，分享时优先使用 ZIP。

安全提示：旧 Git 历史含账户密码哈希、盐值、本地路径和内部文档，历史默认密码视为公开。已有安装需修改管理员及其他旧账户密码、禁用不用的演示账户；本次更新不会替你修改本地账户。矿区坐标、能量与模型属于业务数据，分享前确认授权。可运行 `python scripts/audit_secrets.py`（当前提交）或加 `--history`（本地全部引用）作常见凭据模式检查；模式扫描不等于完整安全审计。
