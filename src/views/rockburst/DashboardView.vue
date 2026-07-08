<template>
  <div class="large-screen dashboard-screen">
    <div class="tech-background" aria-hidden="true">
      <div class="tech-grid-plane"></div>
      <div class="tech-core"></div>
      <div class="tech-orbit tech-orbit-1"></div>
      <div class="tech-orbit tech-orbit-2"></div>
      <div class="tech-beam tech-beam-1"></div>
      <div class="tech-beam tech-beam-2"></div>
      <div class="tech-node tech-node-1"></div>
      <div class="tech-node tech-node-2"></div>
      <div class="tech-node tech-node-3"></div>
      <div class="tech-node tech-node-4"></div>
    </div>

    <div class="large-screen-wrap" id="large-screen">
      <m-header :title="systemTitle" sub-text="MICROSEISMIC ROCKBURST RISK IDENTIFICATION PLATFORM">
        <template #left>
          <div class="header-left-status">
            <span>在线监测</span>
            <span>智能判识</span>
          </div>
        </template>
        <template #right>
          <div class="header-user">
            <span class="header-user-name">{{ currentUser.display_name || currentUser.name || currentUser.username }}</span>
            <span class="header-user-role">{{ roleLabel }}</span>
            <button class="ghost-btn" type="button" @click="handleLogout">退出登录</button>
          </div>
        </template>
      </m-header>

      <div class="top-menu">
        <mMenu :default-active="state.activeIndex" @select="handleMenuSelect">
          <mMenuItem index="overview">监测总览</mMenuItem>
          <mMenuItem index="cloud">冲击危险云图</mMenuItem>
          <mMenuItem index="mine">井下地图</mMenuItem>
          <div class="top-menu-mid-space"></div>
          <mMenuItem v-if="isAdminUser" index="users">人员管理</mMenuItem>
          <mMenuItem index="settings">系统状态</mMenuItem>
        </mMenu>
      </div>

      <div class="left-wrap">
        <div class="left-wrap-3d">
          <m-card class="left-card" title="实时监测概览" :height="207">
            <div class="kpi-grid">
              <div
                class="kpi-item interactive-panel-item"
                v-for="item in overviewStats"
                :key="item.label"
                @mouseenter="showPanelTip($event, item.label, `${item.value}，${item.detail}`)"
                @mousemove="movePanelTip"
                @mouseleave="hidePanelTip"
              >
                <div class="kpi-value" :class="item.level">{{ item.value }}</div>
                <div class="kpi-label">{{ item.label }}</div>
              </div>
            </div>
          </m-card>

          <m-card class="left-card" title="工作面应力监测" :height="207">
            <div class="bar-list">
              <div
                class="bar-row interactive-panel-item"
                v-for="item in stressBars"
                :key="item.name"
                @mouseenter="showPanelTip($event, item.name, `当前应力 ${item.text} MPa，阈值 ${item.threshold} MPa，状态：${item.status}`)"
                @mousemove="movePanelTip"
                @mouseleave="hidePanelTip"
              >
                <span class="bar-name">{{ item.name }}</span>
                <span class="bar-track"><i :style="{ width: item.value + '%', background: item.color }"></i></span>
                <span class="bar-value">{{ item.text }}</span>
              </div>
            </div>
          </m-card>

          <m-card class="left-card" title="实时微震事件" :height="207">
            <div class="event-table">
              <div class="event-head">
                <span>时间</span><span>位置</span><span>能量(J)</span><span>等级</span>
              </div>
              <div
                class="event-row interactive-panel-item"
                v-for="event in eventRows"
                :key="event.time + event.place"
                @mouseenter="showPanelTip($event, `${event.place} 微震事件`, `${event.time} 发生，能量 ${event.energy} J，震级 ${event.level}，判识为${event.status}`)"
                @mousemove="movePanelTip"
                @mouseleave="hidePanelTip"
              >
                <span>{{ event.time }}</span>
                <span>{{ event.place }}</span>
                <span>{{ event.energy }}</span>
                <span :class="event.levelClass">{{ event.level }}</span>
              </div>
            </div>
          </m-card>
        </div>
      </div>

      <div class="right-wrap">
        <div class="right-wrap-3d">
          <m-card class="right-card" title="风险等级分布" :height="207">
            <div class="risk-donut">
              <div
                class="risk-ring interactive-panel-item"
                @mouseenter="showPanelTip($event, '风险等级分布', '极高 1 处，高 2 处，中 5 处，低 12 处，共 20 个预警点位')"
                @mousemove="movePanelTip"
                @mouseleave="hidePanelTip"
              >
                <div class="risk-number">20</div>
                <div class="risk-caption">预警点位</div>
              </div>
              <div class="risk-legend">
                <span><i class="risk-high"></i>极高</span>
                <span><i class="risk-warning"></i>高</span>
                <span><i class="risk-mid"></i>中</span>
                <span><i class="risk-low"></i>低</span>
              </div>
            </div>
          </m-card>

          <m-card class="right-card" title="24 小时事件趋势" :height="207">
            <div
              class="trend-chart interactive-panel-item"
              @mouseenter="showPanelTip($event, '24 小时事件趋势', '14:00-16:00 为事件活跃时段，峰值 8 次/小时，当前趋势回落')"
              @mousemove="movePanelTip"
              @mouseleave="hidePanelTip"
            >
              <svg viewBox="0 0 320 120" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="trendFill" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0" stop-color="#37efff" stop-opacity="0.45" />
                    <stop offset="1" stop-color="#37efff" stop-opacity="0" />
                  </linearGradient>
                </defs>
                <path class="trend-area" d="M0,96 L26,84 L52,91 L78,58 L104,76 L130,45 L156,62 L182,34 L208,20 L234,50 L260,39 L286,82 L320,68 L320,120 L0,120 Z" />
                <polyline class="trend-line" points="0,96 26,84 52,91 78,58 104,76 130,45 156,62 182,34 208,20 234,50 260,39 286,82 320,68" />
              </svg>
              <div class="trend-axis">
                <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span>
              </div>
            </div>
          </m-card>

          <m-card class="right-card" title="冲击危险指标" :height="207">
            <div
              class="radar-lite interactive-panel-item"
              @mouseenter="showPanelTip($event, '冲击危险指标', '综合考虑应力、微震、瓦斯、温度四类指标，当前处于中高风险监测状态')"
              @mousemove="movePanelTip"
              @mouseleave="hidePanelTip"
            >
              <div class="radar-web"></div>
              <div class="radar-core"></div>
              <div class="radar-label label-top">应力</div>
              <div class="radar-label label-right">瓦斯</div>
              <div class="radar-label label-bottom">温度</div>
              <div class="radar-label label-left">微震</div>
              <div class="radar-state">
                <span><i class="risk-high"></i>当前值</span>
                <span><i class="risk-warning"></i>预警阈值</span>
              </div>
            </div>
          </m-card>
        </div>
      </div>

      <section class="workbench" :class="'mode-' + state.activeIndex">
        <div v-if="state.activeIndex === 'overview'" class="center-panel center-overview">
          <div class="panel-title">冲击地压综合态势</div>
          <div class="center-count-card">
            <mCountCard v-for="item in state.totalView" :info="item" :key="item.zh"></mCountCard>
          </div>
          <div class="panel-metrics">
            <div v-for="item in centerMetrics" :key="item.label">
              <span>{{ item.value }}</span>
              <small>{{ item.label }}</small>
            </div>
          </div>
          <div class="panel-note">三维态势底图、监测事件、危险等级和区划结果已接入统一可视化场景。</div>
        </div>

        <div v-if="state.activeIndex === 'cloud'" class="center-panel cloud-panel">
          <div class="panel-title">冲击危险云图生成</div>
          <div
            class="upload-zone"
            :class="{ 'is-dragover': state.dragOver }"
            @dragover.prevent="state.dragOver = true"
            @dragleave.prevent="state.dragOver = false"
            @drop.prevent="handleCloudDrop"
          >
            <input ref="cloudInputRef" type="file" accept=".xls,.xlsx,.csv,.txt,.dat" @change="handleCloudPick" />
            <button class="primary-btn" type="button" @click="cloudInputRef && cloudInputRef.click()">上传文件</button>
            <span>{{ state.cloudFileName || "拖拽监测数据文件到此处，自动调用后端生成危险云图" }}</span>
          </div>
          <div class="cloud-tools" v-if="state.cloudImageUrl">
            <button class="ghost-btn" type="button" @click="zoomCloud(1.18)">放大</button>
            <button class="ghost-btn" type="button" @click="zoomCloud(0.85)">缩小</button>
            <button class="ghost-btn" type="button" @click="resetCloudView">重置</button>
            <span>滚轮缩放，按住图片拖动，双击重置</span>
          </div>
          <div
            class="cloud-preview"
            :class="{ 'is-panning': state.cloudDragging, 'has-image': state.cloudImageUrl }"
            @wheel.prevent="handleCloudWheel"
            @pointerdown="startCloudPan"
            @pointermove="moveCloudPan"
            @pointerup="endCloudPan"
            @pointercancel="endCloudPan"
            @pointerleave="endCloudPan"
            @dblclick="resetCloudView"
          >
            <img
              v-if="state.cloudImageUrl"
              :src="state.cloudImageUrl"
              :style="cloudImageStyle"
              draggable="false"
              alt="冲击危险云图"
              @load="resetCloudView"
            />
            <div v-else class="empty-text">{{ state.cloudStatus }}</div>
          </div>
        </div>

        <div v-if="state.activeIndex === 'mine'" class="center-panel mine-panel">
          <div class="panel-title">井下地图</div>
          <MineGlbViewer class="mine-viewer" />
        </div>

        <div v-if="state.activeIndex === 'users'" class="center-panel user-panel">
          <div class="panel-title">人员与权限管理</div>
          <div class="user-toolbar">
            <span>{{ userMessage }}</span>
            <button class="ghost-btn" type="button" @click="loadUsers">刷新</button>
          </div>
          <div class="user-table">
            <div class="user-table-row user-table-head">
              <span>用户名</span><span>姓名</span><span>角色</span><span>状态</span><span>操作</span>
            </div>
            <div class="user-table-row" v-for="item in users" :key="item.id || item.username">
              <span>{{ item.username }}</span>
              <span>{{ item.display_name || item.name || "-" }}</span>
              <span>
                <button class="tag-btn" type="button" @click="toggleRole(item)">
                  {{ item.role === "admin" ? "管理员" : "用户" }}
                </button>
              </span>
              <span>
                <button class="tag-btn" type="button" @click="toggleEnabled(item)">
                  {{ item.enabled === false ? "停用" : "启用" }}
                </button>
              </span>
              <span>
                <button class="danger-btn" type="button" :disabled="item.username === currentUser.username" @click="removeUser(item)">删除</button>
              </span>
            </div>
          </div>
        </div>

        <div v-if="state.activeIndex === 'settings'" class="center-panel center-overview">
          <div class="panel-title">系统运行状态</div>
          <div class="panel-metrics">
            <div><span>正常</span><small>后端服务</small></div>
            <div><span>Vite</span><small>前端运行环境</small></div>
            <div><span>Three 0.161</span><small>三维渲染内核</small></div>
          </div>
          <div class="panel-note">本分支已切换为 Vue3 + Vite + ThreeMaps 视觉框架，后端接口保持独立适配。</div>
        </div>
      </section>

      <div class="bottom-tray">
        <mSvglineAnimation
          class="bottom-svg-line-left"
          :width="721"
          :height="57"
          color="#30DCFF"
          :strokeWidth="2"
          :dir="[0, 1]"
          :length="50"
          path="M1 56.6105C1 31.5123 185.586 10.0503 451.904 1.35519C458.942 1.12543 465.781 4.00883 470.505 9.22964L484.991 25.2383C487.971 28.4775 492.938 30.4201 498.254 30.4201H720.142"
        ></mSvglineAnimation>
        <mSvglineAnimation
          class="bottom-svg-line-left bottom-svg-line-right"
          :width="721"
          :height="57"
          color="#30DCFF"
          :strokeWidth="2"
          :dir="[0, 1]"
          :length="50"
          path="M1 56.6105C1 31.5123 185.586 10.0503 451.904 1.35519C458.942 1.12543 465.781 4.00883 470.505 9.22964L484.991 25.2383C487.971 28.4775 492.938 30.4201 498.254 30.4201H720.142"
        ></mSvglineAnimation>
        <div class="bottom-tray-arrow">
          <img src="@/assets/images/bottom-menu-arrow-big.svg" alt="" />
          <img src="@/assets/images/bottom-menu-arrow-small.svg" alt="" />
        </div>
        <div class="bottom-menu">
          <div
            v-for="item in bottomMenu"
            :key="item.index"
            class="bottom-menu-item"
            :class="{ 'is-active': item.index === state.activeIndex }"
            @click="handleMenuSelect(item.index)"
          >
            <span>{{ item.label }}</span>
          </div>
        </div>
        <div class="bottom-tray-arrow is-reverse">
          <img src="@/assets/images/bottom-menu-arrow-big.svg" alt="" />
          <img src="@/assets/images/bottom-menu-arrow-small.svg" alt="" />
        </div>
      </div>

      <div class="bottom-radar">
        <mRadar></mRadar>
      </div>
      <div
        v-if="panelTooltip.visible"
        class="panel-tooltip"
        :style="{ left: panelTooltip.x + 'px', top: panelTooltip.y + 'px' }"
      >
        <strong>{{ panelTooltip.title }}</strong>
        <span>{{ panelTooltip.content }}</span>
      </div>
      <div class="large-screen-left-zsline"></div>
      <div class="large-screen-right-zsline"></div>
    </div>

    <div class="loading">
      <div class="loading-text">
        <span v-for="(letter, index) in 'LOADING'.split('')" :key="letter + index" :style="{ '--index': index + 1 }">{{ letter }}</span>
      </div>
      <div class="loading-progress">
        <span class="value">{{ state.progress }}</span>
        <span class="unit">%</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue"
import { useRouter } from "vue-router"
import gsap from "gsap"
import autofit from "autofit.js"

import mHeader from "@/components/mHeader/index.vue"
import mCountCard from "@/components/mCountCard/index.vue"
import mMenu from "@/components/mMenu/index.vue"
import mMenuItem from "@/components/mMenuItem/index.vue"
import mSvglineAnimation from "@/components/mSvglineAnimation/index.vue"
import mRadar from "@/components/mRadar/index.vue"
import mCard from "@/components/mCard/index.vue"
import MineGlbViewer from "@/views/rockburst/MineGlbViewer.vue"
import {
  deleteUser,
  fetchUsers,
  generateSurferMap,
  getCurrentUser,
  isAdmin,
  logout,
  updateUser,
} from "@/lib/apiClient"

const systemTitle = "冲击地压矿井微震监测智能判识冲击危险等级及区划系统"
const router = useRouter()
const cloudInputRef = ref(null)
const currentUser = reactive(getCurrentUser() || {})
const users = ref([])
const userMessage = ref("管理员可在此维护用户状态并分配权限。")
const mineSummary = ref([
  { label: "模型文件", value: "hangdao.glb" },
  { label: "点位图层", value: "可扩展" },
  { label: "着色方式", value: "公式驱动" },
])
const DEFAULT_CLOUD_IMAGE =
  "data:image/svg+xml;charset=utf-8," +
  encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="920" height="560" viewBox="0 0 920 560">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="#e8f3c1"/>
      <stop offset="0.44" stop-color="#aee0bb"/>
      <stop offset="0.72" stop-color="#76c7bd"/>
      <stop offset="1" stop-color="#4ba8c7"/>
    </linearGradient>
    <radialGradient id="hot1" cx="64%" cy="28%" r="16%">
      <stop offset="0" stop-color="#ff1f2d"/>
      <stop offset="0.18" stop-color="#ff8a00"/>
      <stop offset="0.38" stop-color="#ffe34d"/>
      <stop offset="0.72" stop-color="#51c886" stop-opacity=".72"/>
      <stop offset="1" stop-color="#51c886" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="hot2" cx="72%" cy="36%" r="12%">
      <stop offset="0" stop-color="#e10028"/>
      <stop offset="0.24" stop-color="#ff9a00"/>
      <stop offset="0.58" stop-color="#ffef7a" stop-opacity=".75"/>
      <stop offset="1" stop-color="#ffef7a" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="920" height="560" fill="#f8fafb"/>
  <rect x="72" y="54" width="720" height="430" fill="url(#bg)" stroke="#456" stroke-width="2"/>
  <path d="M96 140 C190 110 250 154 340 120 S520 92 626 138 S730 116 782 162" fill="none" stroke="#6f7f62" stroke-width="2"/>
  <path d="M92 255 C210 214 284 298 410 252 S588 215 775 278" fill="none" stroke="#506d58" stroke-width="2"/>
  <path d="M118 360 C244 336 326 386 456 350 S640 322 770 372" fill="none" stroke="#537062" stroke-width="2"/>
  <rect x="72" y="54" width="720" height="430" fill="url(#hot1)" opacity=".9"/>
  <rect x="72" y="54" width="720" height="430" fill="url(#hot2)" opacity=".88"/>
  <g fill="#20dfea" stroke="#073b48" stroke-width="2">
    <circle cx="628" cy="183" r="9"/><circle cx="650" cy="198" r="7"/><circle cx="672" cy="210" r="8"/>
    <circle cx="600" cy="168" r="5"/><circle cx="540" cy="210" r="4"/><circle cx="506" cy="245" r="4"/>
    <circle cx="320" cy="310" r="4"/><circle cx="355" cy="325" r="4"/><circle cx="398" cy="292" r="5"/>
    <circle cx="458" cy="306" r="4"/><circle cx="492" cy="318" r="4"/><circle cx="710" cy="252" r="5"/>
    <circle cx="746" cy="280" r="4"/><circle cx="240" cy="340" r="5"/><circle cx="190" cy="298" r="4"/>
  </g>
  <g fill="none" stroke="#47505a" stroke-width="1.5" opacity=".8">
    <path d="M150 470 V54"/><path d="M260 470 V54"/><path d="M370 470 V54"/><path d="M480 470 V54"/><path d="M590 470 V54"/><path d="M700 470 V54"/>
    <path d="M72 120 H792"/><path d="M72 200 H792"/><path d="M72 280 H792"/><path d="M72 360 H792"/><path d="M72 440 H792"/>
  </g>
  <g font-family="Arial, sans-serif" fill="#303944" font-size="18">
    <text x="70" y="520">7400</text><text x="235" y="520">7600</text><text x="400" y="520">7800</text><text x="565" y="520">8000</text>
    <text x="20" y="444">4400</text><text x="20" y="364">4500</text><text x="20" y="284">4600</text><text x="20" y="204">4700</text>
  </g>
  <g transform="translate(820 74)" font-family="Arial, sans-serif" font-size="14">
    <rect width="34" height="360" fill="#f2f5f6" stroke="#63717d"/>
    <g>
      <rect y="0" width="34" height="40" fill="#ff1f2d"/><rect y="40" width="34" height="40" fill="#ff8a00"/>
      <rect y="80" width="34" height="40" fill="#ffd33d"/><rect y="120" width="34" height="40" fill="#cce17b"/>
      <rect y="160" width="34" height="40" fill="#86cf9b"/><rect y="200" width="34" height="40" fill="#51bea8"/>
      <rect y="240" width="34" height="40" fill="#35aeca"/><rect y="280" width="34" height="40" fill="#168fd5"/>
      <rect y="320" width="34" height="40" fill="#0073ff"/>
    </g>
    <text x="42" y="10" fill="#303944">3.8</text><text x="42" y="88" fill="#303944">2.8</text><text x="42" y="166" fill="#303944">1.8</text><text x="42" y="244" fill="#303944">0.8</text><text x="42" y="352" fill="#303944">-0.2</text>
  </g>
  <text x="372" y="34" fill="#253341" font-family="Arial, sans-serif" font-size="22" font-weight="700">冲击危险云图示例</text>
  <circle cx="628" cy="183" r="24" fill="none" stroke="#ff2a35" stroke-width="4" filter="url(#glow)"/>
</svg>`)
const panelTooltip = reactive({
  visible: false,
  title: "",
  content: "",
  x: 0,
  y: 0,
})

const state = reactive({
  progress: 0,
  activeIndex: "overview",
  dragOver: false,
  cloudFileName: "默认示例云图",
  cloudImageUrl: DEFAULT_CLOUD_IMAGE,
  cloudStatus: "已加载默认冲击危险云图示例",
  cloudScale: 1,
  cloudOffsetX: 0,
  cloudOffsetY: 0,
  cloudDragging: false,
  cloudDragStartX: 0,
  cloudDragStartY: 0,
  cloudStartOffsetX: 0,
  cloudStartOffsetY: 0,
  totalView: [
    {
      icon: "xiaoshoujine",
      zh: "今日微震事件",
      en: "Microseismic Events Today",
      value: 45,
      unit: "次",
      decimals: 0,
    },
    {
      icon: "zongxiaoliang",
      zh: "综合危险指数",
      en: "Rockburst Risk Index",
      value: 82,
      unit: "分",
      decimals: 0,
    },
  ],
})

const roleLabel = computed(() => (currentUser.role === "admin" ? "管理员" : "用户"))
const isAdminUser = computed(() => isAdmin())
const cloudImageStyle = computed(() => ({
  transform: `translate(${state.cloudOffsetX}px, ${state.cloudOffsetY}px) scale(${state.cloudScale})`,
}))

const overviewStats = [
  { label: "今日事件次数", value: "45", level: "", detail: "较昨日增加 6 次，集中于 5304 工作面" },
  { label: "最大震级", value: "3.2", level: "", detail: "发生于 6501 工作面，属于重点跟踪事件" },
  { label: "累计能量(J)", value: "36363", level: "", detail: "24 小时累计释放能量，当前高于周均值" },
  { label: "监测状态", value: "正常", level: "success", detail: "微震、应力与三维地图服务均在线" },
]
const stressBars = [
  { name: "S3-16-9002", value: 15, text: "3.1", color: "#33e6e8", threshold: 18, status: "稳定" },
  { name: "S3-04-2003", value: 26, text: "5.5", color: "#ffe22b", threshold: 18, status: "关注" },
  { name: "S3-04-2002", value: 39, text: "8.2", color: "#ffba22", threshold: 18, status: "关注" },
  { name: "S3-16-9001", value: 54, text: "11.4", color: "#ff9f1a", threshold: 18, status: "加强监测" },
  { name: "S2-14-1473", value: 65, text: "13.6", color: "#ffb31a", threshold: 18, status: "加强监测" },
  { name: "S2-14-1472", value: 89, text: "18.6", color: "#ff4d5f", threshold: 18, status: "超阈预警" },
]
const eventRows = [
  { time: "14:32:18", place: "5304 工作面", energy: "12400", level: "2.8", levelClass: "warning", status: "高能事件" },
  { time: "14:18:03", place: "5304 回风巷", energy: "3210", level: "1.6", levelClass: "", status: "一般事件" },
  { time: "13:55:41", place: "7301 工作面", energy: "8650", level: "2.3", levelClass: "warning", status: "重点关注" },
  { time: "12:48:30", place: "6501 工作面", energy: "21800", level: "3.1", levelClass: "danger", status: "危险预警" },
  { time: "12:14:55", place: "7301 切眼", energy: "540", level: "0.8", levelClass: "safe", status: "低能事件" },
]
const centerMetrics = [
  { label: "高风险区", value: "4" },
  { label: "重点监测点", value: "20" },
  { label: "稳定区", value: "16" },
]
const bottomMenu = computed(() => [
  { index: "overview", label: "态势总览" },
  { index: "cloud", label: "云图生成" },
  { index: "mine", label: "井下地图" },
  ...(isAdminUser.value ? [{ index: "users", label: "权限管理" }] : []),
])

onMounted(() => {
  autofit.init({
    dh: 1080,
    dw: 1920,
    el: "#large-screen",
    resize: true,
  })
  runBootSequence()
})

onBeforeUnmount(() => {
  if (autofit.off) autofit.off()
})

function runBootSequence() {
  const params = { progress: 0 }
  gsap.to(params, {
    progress: 100,
    duration: 1.4,
    ease: "power2.out",
    onUpdate: () => {
      state.progress = Math.floor(params.progress)
    },
    onComplete: async () => {
      await hideLoading()
      handleMapPlayComplete()
    },
  })
}

async function hideLoading() {
  return new Promise((resolve) => {
    const tl = gsap.timeline()
    tl.to(".loading-text span", {
      y: "200%",
      opacity: 0,
      ease: "power4.inOut",
      duration: 2,
      stagger: 0.2,
    })
    tl.to(".loading-progress", { opacity: 0, ease: "power4.inOut", duration: 2 }, "<")
    tl.to(
      ".loading",
      {
        opacity: 0,
        ease: "power4.inOut",
        onComplete: resolve,
      },
      "-=1"
    )
  })
}

function handleMapPlayComplete() {
  const tl = gsap.timeline({ paused: false })
  const leftCards = gsap.utils.toArray(".left-card")
  const rightCards = gsap.utils.toArray(".right-card")
  const countCards = gsap.utils.toArray(".count-card")
  tl.addLabel("start", 0.4)
  tl.addLabel("card", 1)
  tl.to(".m-header", { y: 0, opacity: 1, duration: 1.4, ease: "power4.out" }, "start")
  tl.to(".bottom-tray", { y: 0, opacity: 1, duration: 1.4, ease: "power4.out" }, "start")
  tl.to(".top-menu", { y: 0, opacity: 1, duration: 1.4, ease: "power4.out" }, "-=1")
  tl.to(".bottom-radar", { y: 0, opacity: 1, duration: 1.4, ease: "power4.out" }, "-=1.7")
  tl.to(leftCards, { x: 0, opacity: 1, stagger: 0.16, duration: 1.2, ease: "power4.out" }, "card")
  tl.to(rightCards, { x: 0, opacity: 1, stagger: 0.16, duration: 1.2, ease: "power4.out" }, "card")
  tl.to(countCards, { y: 0, opacity: 1, stagger: 0.18, duration: 1.2, ease: "power4.out" }, "card")
  tl.fromTo(".workbench", { opacity: 0, scale: 0.98 }, { opacity: 1, scale: 1, duration: 1.2, ease: "power4.out" }, "card+=0.3")
}

async function handleMenuSelect(index) {
  state.activeIndex = index
  if (index === "users") {
    await loadUsers()
  }
  await nextTick()
  gsap.fromTo(".center-panel", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" })
}

async function handleLogout() {
  await logout()
  router.replace("/login")
}

function showPanelTip(event, title, content) {
  panelTooltip.visible = true
  panelTooltip.title = title
  panelTooltip.content = content
  movePanelTip(event)
}

function movePanelTip(event) {
  const root = document.getElementById("large-screen")
  const rect = root ? root.getBoundingClientRect() : { left: 0, top: 0 }
  panelTooltip.x = event.clientX - rect.left + 18
  panelTooltip.y = event.clientY - rect.top + 18
}

function hidePanelTip() {
  panelTooltip.visible = false
}

function handleCloudPick(event) {
  const file = event.target.files && event.target.files[0]
  if (file) uploadCloudFile(file)
  event.target.value = ""
}

function handleCloudDrop(event) {
  state.dragOver = false
  const file = event.dataTransfer.files && event.dataTransfer.files[0]
  if (file) uploadCloudFile(file)
}

async function uploadCloudFile(file) {
  state.cloudFileName = file.name
  state.cloudStatus = "正在调用后端生成冲击危险云图..."
  try {
    const data = await generateSurferMap(file)
    state.cloudImageUrl = data.imageUrl
    state.cloudStatus = "云图生成完成"
    resetCloudView()
  } catch (error) {
    state.cloudImageUrl = ""
    state.cloudStatus = error.message || "云图生成失败，请检查后端服务"
  }
}

function resetCloudView() {
  state.cloudScale = 1
  state.cloudOffsetX = 0
  state.cloudOffsetY = 0
  state.cloudDragging = false
}

function zoomCloud(factor, originEvent = null) {
  if (!state.cloudImageUrl) return
  const prevScale = state.cloudScale
  const nextScale = Math.min(8, Math.max(0.25, prevScale * factor))
  if (nextScale === prevScale) return

  if (originEvent) {
    const rect = originEvent.currentTarget.getBoundingClientRect()
    const cx = originEvent.clientX - rect.left - rect.width / 2
    const cy = originEvent.clientY - rect.top - rect.height / 2
    const ratio = nextScale / prevScale
    state.cloudOffsetX = cx - (cx - state.cloudOffsetX) * ratio
    state.cloudOffsetY = cy - (cy - state.cloudOffsetY) * ratio
  }

  state.cloudScale = nextScale
}

function handleCloudWheel(event) {
  if (!state.cloudImageUrl) return
  zoomCloud(event.deltaY < 0 ? 1.12 : 0.9, event)
}

function startCloudPan(event) {
  if (!state.cloudImageUrl || event.button !== 0) return
  state.cloudDragging = true
  state.cloudDragStartX = event.clientX
  state.cloudDragStartY = event.clientY
  state.cloudStartOffsetX = state.cloudOffsetX
  state.cloudStartOffsetY = state.cloudOffsetY
  event.currentTarget.setPointerCapture && event.currentTarget.setPointerCapture(event.pointerId)
}

function moveCloudPan(event) {
  if (!state.cloudDragging) return
  state.cloudOffsetX = state.cloudStartOffsetX + event.clientX - state.cloudDragStartX
  state.cloudOffsetY = state.cloudStartOffsetY + event.clientY - state.cloudDragStartY
}

function endCloudPan(event) {
  if (!state.cloudDragging) return
  state.cloudDragging = false
  event.currentTarget.releasePointerCapture && event.currentTarget.releasePointerCapture(event.pointerId)
}

async function loadMineMeta() {
  try {
    const response = await fetch("/mine3d.json")
    if (!response.ok) throw new Error("模型元数据读取失败")
    const data = await response.json()
    const pointCount = Array.isArray(data.points) ? data.points.length : Array.isArray(data.markers) ? data.markers.length : "待配置"
    mineSummary.value = [
      { label: "模型文件", value: data.model || "hangdao.glb" },
      { label: "观测点位", value: pointCount },
      { label: "风险着色", value: "公式驱动" },
    ]
  } catch (error) {
    mineSummary.value = [
      { label: "模型文件", value: "hangdao.glb" },
      { label: "观测点位", value: "待配置" },
      { label: "风险着色", value: "公式驱动" },
    ]
  }
}

async function loadUsers() {
  if (!isAdminUser.value) return
  userMessage.value = "正在读取用户列表..."
  try {
    users.value = await fetchUsers()
    userMessage.value = `已加载 ${users.value.length} 个用户。`
  } catch (error) {
    userMessage.value = error.message || "用户列表读取失败"
  }
}

async function toggleRole(item) {
  const role = item.role === "admin" ? "user" : "admin"
  await updateUser(item.id || item.username, { ...item, role })
  await loadUsers()
}

async function toggleEnabled(item) {
  const enabled = item.enabled === false
  await updateUser(item.id || item.username, { ...item, enabled })
  await loadUsers()
}

async function removeUser(item) {
  if (item.username === currentUser.username) return
  await deleteUser(item.id || item.username)
  await loadUsers()
}
</script>

<style lang="scss">
@import "~@/assets/style/home.scss";

.dashboard-screen {
  color: #d8f7ff;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 22%, rgba(45, 187, 232, 0.2), transparent 30%),
    linear-gradient(180deg, #061526 0%, #031122 46%, #020915 100%);
}

.tech-background {
  position: absolute;
  inset: 0;
  z-index: 1;
  overflow: hidden;
  pointer-events: none;
  background:
    radial-gradient(circle at 50% 38%, rgba(35, 183, 229, 0.22), transparent 30%),
    radial-gradient(circle at 18% 68%, rgba(33, 128, 199, 0.12), transparent 24%),
    radial-gradient(circle at 82% 60%, rgba(27, 196, 211, 0.1), transparent 24%);
}

.tech-background::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(48, 220, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(48, 220, 255, 0.05) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: linear-gradient(to bottom, transparent 0%, #000 24%, #000 100%);
}

.tech-background::after {
  content: "";
  position: absolute;
  left: 50%;
  top: 68%;
  width: 1700px;
  height: 620px;
  transform: translate(-50%, -50%) perspective(780px) rotateX(62deg);
  transform-origin: center;
  background:
    linear-gradient(rgba(48, 220, 255, 0.18) 1px, transparent 1px),
    linear-gradient(90deg, rgba(48, 220, 255, 0.18) 1px, transparent 1px),
    radial-gradient(ellipse at center, rgba(48, 220, 255, 0.18), transparent 58%);
  background-size: 44px 44px, 44px 44px, 100% 100%;
  border: 1px solid rgba(48, 220, 255, 0.16);
  opacity: 0.72;
}

.tech-grid-plane {
  position: absolute;
  left: 50%;
  top: 58%;
  width: 980px;
  height: 980px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid rgba(48, 220, 255, 0.12);
  box-shadow:
    0 0 80px rgba(48, 220, 255, 0.14),
    inset 0 0 80px rgba(48, 220, 255, 0.08);
  animation: techPulse 4.8s ease-in-out infinite;
}

.tech-core {
  position: absolute;
  left: 50%;
  top: 48%;
  width: 340px;
  height: 340px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background:
    radial-gradient(circle, rgba(136, 244, 255, 0.45) 0%, rgba(44, 218, 255, 0.16) 22%, transparent 54%),
    conic-gradient(from 0deg, transparent, rgba(48, 220, 255, 0.5), transparent 32%, transparent 100%);
  filter: blur(0.2px);
  animation: rotate360Animate 18s linear infinite;
}

.tech-orbit {
  position: absolute;
  left: 50%;
  top: 48%;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  border: 1px solid rgba(95, 231, 255, 0.24);
  box-shadow: 0 0 22px rgba(48, 220, 255, 0.12);
}

.tech-orbit-1 {
  width: 620px;
  height: 220px;
  animation: techFloat 5.5s ease-in-out infinite;
}

.tech-orbit-2 {
  width: 900px;
  height: 320px;
  opacity: 0.52;
  animation: techFloat 6.8s ease-in-out infinite reverse;
}

.tech-beam {
  position: absolute;
  width: 220px;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(117, 232, 255, 0.8), transparent);
  filter: drop-shadow(0 0 8px rgba(117, 232, 255, 0.9));
  animation: beamMove 5.8s linear infinite;
}

.tech-beam-1 {
  left: 18%;
  top: 34%;
}

.tech-beam-2 {
  right: 16%;
  top: 62%;
  animation-delay: -2.6s;
}

.tech-node {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #75e8ff;
  box-shadow: 0 0 18px rgba(117, 232, 255, 0.95);
  animation: nodeBlink 3s ease-in-out infinite;
}

.tech-node-1 {
  left: 30%;
  top: 40%;
}

.tech-node-2 {
  left: 68%;
  top: 36%;
  animation-delay: -0.8s;
}

.tech-node-3 {
  left: 42%;
  top: 72%;
  animation-delay: -1.6s;
}

.tech-node-4 {
  left: 78%;
  top: 72%;
  animation-delay: -2.3s;
}

@keyframes techPulse {
  0%,
  100% {
    opacity: 0.45;
    transform: translate(-50%, -50%) scale(0.96);
  }
  50% {
    opacity: 0.8;
    transform: translate(-50%, -50%) scale(1.04);
  }
}

@keyframes techFloat {
  0%,
  100% {
    transform: translate(-50%, -50%) rotateX(58deg) rotateZ(-6deg);
  }
  50% {
    transform: translate(-50%, -51.5%) rotateX(58deg) rotateZ(6deg);
  }
}

@keyframes beamMove {
  0% {
    transform: translateX(-80px);
    opacity: 0;
  }
  18%,
  72% {
    opacity: 1;
  }
  100% {
    transform: translateX(180px);
    opacity: 0;
  }
}

@keyframes nodeBlink {
  0%,
  100% {
    opacity: 0.25;
    transform: scale(0.75);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

.header-left-status,
.header-user {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #c4f3fe;
  font-size: 14px;
  pointer-events: all;
}

.header-user-name {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-user-role {
  padding: 3px 10px;
  border: 1px solid rgba(48, 220, 255, 0.5);
  border-radius: 2px;
  color: #75e8ff;
  background: rgba(18, 74, 122, 0.42);
}

.top-menu {
  position: absolute;
  left: 0;
  right: 0;
  top: 82px;
  z-index: 5;
  display: flex;
  justify-content: center;

  .top-menu-mid-space {
    width: 640px;
  }
}

.dashboard-screen .m-header-title {
  max-width: 1060px;
  margin: 0 auto;
  font-size: 34px;
  line-height: 38px;
  white-space: nowrap;
}

.dashboard-screen .m-header-subtext {
  margin-top: 2px;
}

.bottom-radar {
  position: absolute;
  right: 500px;
  bottom: 100px;
  z-index: 3;
}

.bottom-svg-line-left,
.bottom-svg-line-right {
  position: absolute;
  right: 50%;
  width: 721px;
  height: 57px;
  margin-right: -5px;
  bottom: -21px;
}

.bottom-svg-line-right {
  transform: scaleX(-1);
  left: 50%;
  right: inherit;
  margin-right: inherit;
  margin-left: -5px;
}

.m-header,
.top-menu,
.count-card,
.bottom-tray,
.bottom-radar {
  opacity: 0;
}

.m-header {
  transform: translateY(-100%);
}

.top-menu {
  transform: translateY(-250%);
}

.count-card {
  transform: translateY(150%);
}

.left-card {
  transform: translateX(-150%);
  opacity: 0;
}

.right-card {
  transform: translateX(150%);
  opacity: 0;
}

.bottom-tray,
.bottom-radar {
  transform: translateY(100%);
}

.workbench {
  pointer-events: all;
  position: absolute;
  z-index: 4;
  left: 462px;
  right: 462px;
  top: 148px;
  bottom: 168px;
  opacity: 0;
}

.center-panel {
  position: relative;
  width: 100%;
  height: 100%;
  border: 1px solid rgba(48, 220, 255, 0.28);
  background:
    linear-gradient(rgba(20, 64, 97, 0.16) 1px, transparent 1px),
    linear-gradient(90deg, rgba(20, 64, 97, 0.16) 1px, transparent 1px),
    radial-gradient(circle at 50% 28%, rgba(122, 210, 255, 0.22), rgba(7, 23, 45, 0.48) 36%, rgba(3, 12, 24, 0.18));
  background-size: 40px 40px, 40px 40px, 100% 100%;
  box-shadow: inset 0 0 60px rgba(46, 163, 221, 0.18), 0 0 24px rgba(42, 181, 238, 0.12);
  box-sizing: border-box;
  overflow: hidden;
}

.center-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 0%, rgba(113, 240, 255, 0.12) 42%, transparent 60%);
  transform: translateX(-100%);
  animation: panelScan 4.8s linear infinite;
  pointer-events: none;
}

.panel-title {
  position: relative;
  z-index: 2;
  height: 46px;
  line-height: 46px;
  padding: 0 22px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #bdf6ff;
  background: linear-gradient(90deg, rgba(22, 111, 155, 0.55), rgba(22, 111, 155, 0.04));
}

.center-count-card {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: center;
  gap: 80px;
  padding-top: 54px;
}

.center-count-card .count-card {
  opacity: 1;
  transform: none;
}

.panel-metrics,
.mine-summary {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  padding: 80px 110px 26px;

  div {
    min-height: 122px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border: 1px solid rgba(48, 220, 255, 0.24);
    background: rgba(7, 31, 58, 0.52);
  }

  span {
    font-family: D-DIN, Arial, sans-serif;
    font-size: 46px;
    font-weight: 700;
    color: #ffffff;
    text-shadow: 0 0 22px rgba(117, 232, 255, 0.75);
  }

  small {
    margin-top: 10px;
    color: #75e8ff;
    font-size: 14px;
  }
}

.center-overview .panel-metrics {
  padding-top: 44px;
}

.panel-note,
.mine-note {
  position: relative;
  z-index: 2;
  margin: 18px auto 0;
  max-width: 720px;
  text-align: center;
  color: rgba(207, 246, 255, 0.78);
  font-size: 16px;
  line-height: 1.8;
}

.interactive-panel-item {
  cursor: pointer;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease,
    filter 0.18s ease;
}

.interactive-panel-item:hover {
  transform: translateY(-2px);
  border-color: rgba(117, 232, 255, 0.6);
  background-color: rgba(24, 94, 135, 0.22);
  box-shadow: 0 0 18px rgba(48, 220, 255, 0.18);
  filter: brightness(1.12);
}

.panel-tooltip {
  position: absolute;
  z-index: 30;
  width: 260px;
  padding: 10px 12px;
  border: 1px solid rgba(117, 232, 255, 0.58);
  background:
    linear-gradient(135deg, rgba(11, 44, 72, 0.96), rgba(5, 20, 38, 0.92));
  box-shadow: 0 0 24px rgba(48, 220, 255, 0.22);
  color: rgba(218, 248, 255, 0.88);
  font-size: 12px;
  line-height: 1.7;
  pointer-events: none;
}

.panel-tooltip strong {
  display: block;
  margin-bottom: 4px;
  color: #75e8ff;
  font-size: 14px;
}

.panel-tooltip span {
  display: block;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  height: 100%;
  padding: 12px 14px;
  box-sizing: border-box;
}

.kpi-item {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(15, 50, 92, 0.45);
  border: 1px solid rgba(48, 220, 255, 0.12);
}

.kpi-value {
  color: #43e9ff;
  font-family: D-DIN, Arial, sans-serif;
  font-size: 28px;
  font-weight: 700;
}

.kpi-value.success {
  color: #31f3c7;
}

.kpi-label {
  margin-top: 8px;
  color: rgba(174, 232, 244, 0.78);
  font-size: 12px;
}

.bar-list {
  padding: 14px 20px 10px;
}

.bar-row {
  display: grid;
  grid-template-columns: 88px 1fr 42px;
  align-items: center;
  gap: 8px;
  margin-bottom: 13px;
  font-family: D-DIN, Arial, sans-serif;
  color: #92e7ff;
}

.bar-name {
  font-size: 12px;
}

.bar-track {
  display: block;
  height: 8px;
  border-radius: 8px;
  background: rgba(72, 151, 190, 0.2);
  overflow: hidden;
}

.bar-track i {
  display: block;
  height: 100%;
  border-radius: 8px;
  box-shadow: 0 0 12px currentColor;
}

.bar-value {
  text-align: right;
  font-size: 12px;
  color: #c8f9ff;
}

.event-table {
  padding: 14px 18px 12px;
  font-family: D-DIN, Arial, sans-serif;
  font-size: 12px;
}

.event-head,
.event-row {
  display: grid;
  grid-template-columns: 64px 1fr 70px 36px;
  gap: 8px;
  height: 24px;
  align-items: center;
}

.event-head {
  color: #5ee7ff;
  background: rgba(11, 76, 116, 0.35);
}

.event-row {
  color: rgba(204, 242, 255, 0.78);
  border-bottom: 1px solid rgba(80, 196, 226, 0.08);
}

.event-row .warning {
  color: #ffd33d;
}

.event-row .danger {
  color: #ff4d5f;
}

.event-row .safe {
  color: #3eeac6;
}

.risk-donut {
  height: 100%;
  padding-top: 14px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.risk-ring {
  width: 112px;
  height: 112px;
  border-radius: 50%;
  background: conic-gradient(#ff4d5f 0 25%, #ffb31a 25% 52%, #ffdf36 52% 73%, #31f3c7 73% 100%);
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.risk-ring::after {
  content: "";
  position: absolute;
  inset: 18px;
  border-radius: 50%;
  background: #09213d;
}

.risk-number,
.risk-caption {
  position: relative;
  z-index: 1;
}

.risk-number {
  font-family: D-DIN, Arial, sans-serif;
  color: #75e8ff;
  font-size: 30px;
  font-weight: 700;
}

.risk-caption {
  color: rgba(197, 242, 252, 0.78);
  font-size: 12px;
}

.risk-legend,
.radar-state {
  display: flex;
  justify-content: center;
  gap: 14px;
  margin-top: 14px;
  color: rgba(216, 247, 255, 0.76);
  font-size: 12px;
}

.risk-legend i,
.radar-state i {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 2px;
  margin-right: 4px;
}

.risk-high {
  background: #ff4d5f;
}

.risk-warning {
  background: #ffb31a;
}

.risk-mid {
  background: #ffdf36;
}

.risk-low {
  background: #31f3c7;
}

.trend-chart {
  padding: 14px 22px 0;
}

.trend-chart svg {
  width: 100%;
  height: 112px;
  overflow: visible;
}

.trend-area {
  fill: url(#trendFill);
}

.trend-line {
  fill: none;
  stroke: #75e8ff;
  stroke-width: 4;
  filter: drop-shadow(0 0 6px rgba(117, 232, 255, 0.9));
}

.trend-axis {
  display: flex;
  justify-content: space-between;
  color: rgba(176, 230, 243, 0.65);
  font-size: 12px;
}

.radar-lite {
  position: relative;
  height: 100%;
  padding-top: 12px;
  box-sizing: border-box;
}

.radar-web {
  width: 118px;
  height: 118px;
  margin: 0 auto;
  background:
    radial-gradient(circle, transparent 0 28%, rgba(48, 220, 255, 0.2) 29% 30%, transparent 31% 56%, rgba(48, 220, 255, 0.2) 57% 58%, transparent 59%),
    conic-gradient(from 18deg, rgba(48, 220, 255, 0.5), transparent 14%, rgba(48, 220, 255, 0.5) 28%, transparent 44%, rgba(48, 220, 255, 0.5) 62%, transparent 80%, rgba(48, 220, 255, 0.5));
  clip-path: polygon(50% 0, 95% 32%, 78% 90%, 22% 90%, 5% 32%);
}

.radar-core {
  position: absolute;
  left: 50%;
  top: 43px;
  width: 74px;
  height: 74px;
  transform: translateX(-50%);
  background: rgba(255, 71, 88, 0.65);
  clip-path: polygon(50% 0, 94% 35%, 77% 90%, 23% 90%, 6% 35%);
  border: 1px solid rgba(255, 201, 46, 0.9);
}

.radar-label {
  position: absolute;
  color: rgba(209, 243, 253, 0.74);
  font-size: 12px;
}

.label-top {
  left: 50%;
  top: 8px;
  transform: translateX(-50%);
}

.label-right {
  right: 80px;
  top: 66px;
}

.label-bottom {
  left: 50%;
  top: 126px;
  transform: translateX(-50%);
}

.label-left {
  left: 80px;
  top: 66px;
}

.upload-zone {
  position: relative;
  z-index: 2;
  margin: 28px 28px 18px;
  height: 82px;
  border: 1px dashed rgba(117, 232, 255, 0.45);
  background: rgba(13, 58, 95, 0.38);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
}

.upload-zone.is-dragover {
  border-color: #75e8ff;
  background: rgba(18, 105, 148, 0.5);
}

.upload-zone input {
  display: none;
}

.cloud-tools {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin: -6px 28px 12px;
  color: rgba(207, 246, 255, 0.68);
  font-size: 12px;
}

.cloud-preview {
  position: relative;
  z-index: 2;
  margin: 0 28px 28px;
  height: calc(100% - 214px);
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgba(4, 17, 33, 0.48);
  border: 1px solid rgba(48, 220, 255, 0.16);
  touch-action: none;
  user-select: none;
}

.cloud-preview.has-image {
  cursor: grab;
}

.cloud-preview.is-panning {
  cursor: grabbing;
}

.cloud-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transform-origin: center center;
  transition: transform 0.08s linear;
  will-change: transform;
  pointer-events: none;
}

.empty-text {
  color: rgba(207, 246, 255, 0.72);
  font-size: 18px;
}

.mine-actions,
.user-toolbar {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 18px 28px 0;
}

.mine-actions {
  justify-content: center;
  padding-top: 44px;
}

.mine-panel {
  display: flex;
  flex-direction: column;
}

.mine-viewer {
  position: relative;
  z-index: 2;
  flex: 1;
  min-height: 0;
  margin: 0 28px 28px;
  border: 1px solid rgba(48, 220, 255, 0.16);
}

.user-toolbar {
  justify-content: space-between;
  color: rgba(207, 246, 255, 0.72);
}

.primary-btn,
.ghost-btn,
.tag-btn,
.danger-btn {
  height: 30px;
  padding: 0 14px;
  border: 1px solid rgba(48, 220, 255, 0.55);
  color: #c9f7ff;
  background: rgba(18, 74, 122, 0.42);
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-family: inherit;
}

.primary-btn {
  border-color: rgba(117, 232, 255, 0.85);
  background: linear-gradient(180deg, rgba(40, 184, 231, 0.7), rgba(16, 95, 144, 0.6));
  box-shadow: 0 0 18px rgba(48, 220, 255, 0.22);
}

.danger-btn {
  border-color: rgba(255, 77, 95, 0.55);
  color: #ffd6dc;
  background: rgba(128, 25, 45, 0.45);
}

.danger-btn:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.user-table {
  position: relative;
  z-index: 2;
  margin: 16px 28px 28px;
  height: calc(100% - 116px);
  overflow: auto;
  border: 1px solid rgba(48, 220, 255, 0.16);
  background: rgba(4, 17, 33, 0.44);
}

.user-table-row {
  display: grid;
  grid-template-columns: 1.1fr 1.1fr 0.8fr 0.8fr 0.9fr;
  min-height: 44px;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid rgba(48, 220, 255, 0.11);
  color: rgba(214, 246, 255, 0.82);
}

.user-table-head {
  color: #75e8ff;
  background: rgba(15, 84, 124, 0.4);
  font-weight: 700;
}

@keyframes panelScan {
  to {
    transform: translateX(100%);
  }
}
</style>
