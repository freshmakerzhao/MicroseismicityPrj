# Agent Handoff Index

这个目录用于多个 AI 对话或多个 Agent 之间共享项目上下文。新 Agent 接手时建议按下面顺序阅读。

## 阅读顺序

1. `project-overview.md`
   - 项目目标、技术栈、当前功能模块、运行方式。
2. `current-progress.md`
   - 已完成事项、当前未完成事项、环境问题和验证记录。
3. `next-agent-tasks.md`
   - 后续任务拆解、实现建议、注意事项。

## 项目一句话目标

基于 Vue 2 + FastAPI 构建一个本地矿山/微震数据可视化平台：支持 Surfer 自动生成等值图、微震预警二维展示、GLB 巷道模型三维查看，并逐步扩展为三维模型叠加业务点位和风险颜色图层。

## 当前最重要上下文

- 前端入口：`src/views/home.vue`
- 当前默认路由：`/page5`
- 新增 3D 查看器路由：`/page7`
- Three.js 版本：`three@0.140.2`
- 默认 GLB 模型：`public/models/ferriere_mines_lower_tunnels_1k.glb`
- 后端入口：`server/main.py`
- 后端 API 基础地址：`http://localhost:5000/api`

## 协作规则

- 不要轻易删除 `node_modules`、`dist`、`server/output`、`资料` 目录中的用户数据。
- 当前仓库 Git 可能触发 `dubious ownership`，不要擅自修改全局 Git 配置，除非用户明确同意。
- README 里存在历史中文乱码，本目录内文档使用正常中文作为新的交接依据。
- 做代码修改前优先阅读 `current-progress.md` 和 `next-agent-tasks.md`。
