<template>
    <div class="page5">
        <!-- 左看板 -->
        <aside
            class="side-panel left-panel"
            :style="{ width: leftWidth + 'px' }"
        >
            <!-- 1. 实时监测概览 -->
            <section class="panel-card">
                <div class="panel-title">实时监测概览</div>
                <span class="angle1"></span><span class="angle2"></span>
                <span class="angle3"></span><span class="angle4"></span>
                <div class="kpi-grid">
                    <div class="kpi-item">
                        <div class="kpi-value">{{ mockData.kpi.todayCount }}</div>
                        <div class="kpi-label">今日事件次数</div>
                    </div>
                    <div class="kpi-item">
                        <div class="kpi-value">{{ mockData.kpi.maxMag }}</div>
                        <div class="kpi-label">最大震级</div>
                    </div>
                    <div class="kpi-item">
                        <div class="kpi-value">{{ mockData.kpi.totalEnergy }}</div>
                        <div class="kpi-label">累计能量(kJ)</div>
                    </div>
                    <div class="kpi-item">
                        <div class="kpi-value status-ok">
                            <span class="status-dot"></span>{{ mockData.kpi.status }}
                        </div>
                        <div class="kpi-label">监测状态</div>
                    </div>
                </div>
            </section>

            <!-- 2. 工作面应力监测 -->
            <section class="panel-card">
                <div class="panel-title">工作面应力监测 (MPa)</div>
                <span class="angle1"></span><span class="angle2"></span>
                <span class="angle3"></span><span class="angle4"></span>
                <div id="stressChart" class="chart-box"></div>
            </section>

            <!-- 3. 实时事件列表 -->
            <section class="panel-card">
                <div class="panel-title">实时微震事件</div>
                <span class="angle1"></span><span class="angle2"></span>
                <span class="angle3"></span><span class="angle4"></span>
                <div class="event-table-wrap">
                    <div class="event-table-head">
                        <span class="col-time">时间</span>
                        <span class="col-loc">位置</span>
                        <span class="col-energy">能量(J)</span>
                        <span class="col-mag">震级</span>
                    </div>
                    <div class="event-table-body">
                        <div class="event-scroll">
                            <div
                                v-for="(item, idx) in mockData.events.concat(mockData.events)"
                                :key="idx"
                                class="event-row"
                            >
                                <span class="col-time">{{ item.time }}</span>
                                <span class="col-loc">{{ item.loc }}</span>
                                <span class="col-energy">{{ item.energy }}</span>
                                <span class="col-mag" :style="{ color: magColor(item.mag) }">
                                    {{ item.mag }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </aside>

        <!-- 左拖拽手柄 -->
        <div
            class="resize-handle"
            :class="{ active: resizing === 'left' }"
            @mousedown.prevent="startResize('left', $event)"
        >
            <div class="resize-grip"></div>
        </div>

        <!-- 中央 Surfer 图区 -->
        <main class="center-stage">
            <div class="toolbar">
                <Button
                    class="surfer-btn"
                    :disabled="isProcessing"
                    @click="openGlobalConfig"
                >
                    设置
                </Button>
                <input
                    ref="fileInput"
                    type="file"
                    accept=".xls"
                    style="display: none"
                    @change="handleUpload"
                >
                <Button
                    type="primary"
                    icon="ios-cloud-upload-outline"
                    class="surfer-btn"
                    :loading="isProcessing"
                    :disabled="isProcessing"
                    @click="$refs.fileInput.click()"
                >
                    上传文件
                </Button>
                <Button
                    v-if="surferImgUrl"
                    class="surfer-btn"
                    :disabled="isProcessing"
                    @click="resetView"
                >
                    重置视图
                </Button>
                <Button
                    v-if="surferImgUrl"
                    class="surfer-btn"
                    :disabled="isProcessing"
                    @click="closeImage"
                >
                    关闭图片
                </Button>
            </div>

            <div
                ref="stage"
                class="stage"
                @wheel.prevent="handleWheel"
                @mousedown="startDrag"
                @mousemove="onDrag"
                @mouseup="stopDrag"
                @mouseleave="stopDrag"
            >
                <div v-if="!surferImgUrl" class="placeholder">
                    <p>请点击上方「上传文件」生成 W 等值图</p>
                </div>
                <img
                    v-else
                    ref="surferImage"
                    :src="surferImgUrl"
                    class="surfer-image"
                    :style="imageStyle"
                    alt="surfer result"
                    draggable="false"
                    @load="resetView"
                    @error="handleImageError"
                >
            </div>
        </main>

        <!-- 右拖拽手柄 -->
        <div
            class="resize-handle"
            :class="{ active: resizing === 'right' }"
            @mousedown.prevent="startResize('right', $event)"
        >
            <div class="resize-grip"></div>
        </div>

        <!-- 右看板 -->
        <aside
            class="side-panel right-panel"
            :style="{ width: rightWidth + 'px' }"
        >
            <section class="panel-card">
                <div class="panel-title">风险等级分布</div>
                <span class="angle1"></span><span class="angle2"></span>
                <span class="angle3"></span><span class="angle4"></span>
                <div id="riskChart" class="chart-box"></div>
            </section>

            <section class="panel-card">
                <div class="panel-title">事件类型统计</div>
                <span class="angle1"></span><span class="angle2"></span>
                <span class="angle3"></span><span class="angle4"></span>
                <div id="eventTypeChart" class="chart-box"></div>
            </section>

            <section class="panel-card">
                <div class="panel-title">24 小时事件趋势</div>
                <span class="angle1"></span><span class="angle2"></span>
                <span class="angle3"></span><span class="angle4"></span>
                <div id="trendChart" class="chart-box"></div>
            </section>

            <section class="panel-card">
                <div class="panel-title">冲击危险指标</div>
                <span class="angle1"></span><span class="angle2"></span>
                <span class="angle3"></span><span class="angle4"></span>
                <div id="radarChart" class="chart-box"></div>
            </section>
        </aside>

        <div v-if="isProcessing" class="processing-mask">
            <div class="processing-card">
                <Spin size="large"></Spin>
                <p>处理中，请稍候...</p>
            </div>
        </div>
    </div>
</template>

<script>
import { generateSurferMap } from "@/lib/surfer.js";

const RISK_COLORS = {
    extreme: '#ff4d4f',
    high: '#faad14',
    medium: '#fadb14',
    low: '#36cfc9'
};

export default {
    name: "page5",
    data() {
        return {
            surferImgUrl: "",
            scale: 1,
            minScale: 0.2,
            maxScale: 8,
            offsetX: 0,
            offsetY: 0,
            dragging: false,
            dragStartX: 0,
            dragStartY: 0,
            originOffsetX: 0,
            originOffsetY: 0,
            isProcessing: false,
            charts: {},
            resizeHandler: null,
            leftWidth: 320,
            rightWidth: 320,
            minPanelWidth: 280,
            maxPanelWidth: 500,
            resizing: null,
            resizeStartX: 0,
            resizeStartWidth: 0,
            chartResizeTimer: null,
            mockData: {
                kpi: {
                    todayCount: 45,
                    maxMag: 3.2,
                    totalEnergy: 36363,
                    status: '正常'
                },
                stress: [
                    { name: 'S2-14-1472', value: 18.6 },
                    { name: 'S2-14-1473', value: 13.6 },
                    { name: 'S3-16-9001', value: 11.4 },
                    { name: 'S3-04-2002', value: 8.2 },
                    { name: 'S3-04-2003', value: 5.5 },
                    { name: 'S3-16-9002', value: 3.1 }
                ],
                events: [
                    { time: '14:32:18', loc: '5304 工作面', energy: 12400, mag: 2.8 },
                    { time: '14:18:02', loc: '5304 回风巷', energy: 3210, mag: 1.6 },
                    { time: '13:55:41', loc: '7301 工作面', energy: 8650, mag: 2.3 },
                    { time: '13:32:09', loc: '5304 运输巷', energy: 1240, mag: 1.2 },
                    { time: '12:48:30', loc: '6501 工作面', energy: 21800, mag: 3.1 },
                    { time: '12:14:55', loc: '7301 切眼', energy: 540, mag: 0.8 },
                    { time: '11:50:21', loc: '5304 工作面', energy: 4920, mag: 1.9 },
                    { time: '11:22:07', loc: '7301 回风巷', energy: 2160, mag: 1.4 }
                ],
                riskLevel: [
                    { name: '极高', value: 1, color: RISK_COLORS.extreme },
                    { name: '高', value: 2, color: RISK_COLORS.high },
                    { name: '中', value: 5, color: RISK_COLORS.medium },
                    { name: '低', value: 12, color: RISK_COLORS.low }
                ],
                eventType: [
                    { name: '顶板', value: 18 },
                    { name: '底板', value: 9 },
                    { name: '煤体', value: 12 },
                    { name: '支架', value: 3 },
                    { name: '其他', value: 3 }
                ],
                trend: {
                    hours: Array.from({ length: 24 }, (_, i) =>
                        String(i).padStart(2, '0') + ':00'
                    ),
                    counts: [1, 0, 1, 2, 0, 1, 2, 3, 5, 4, 3, 6, 4, 5, 7, 8, 6, 4, 3, 5, 2, 1, 0, 1]
                },
                radar: {
                    indicators: [
                        { name: '应力', max: 100 },
                        { name: '能量', max: 100 },
                        { name: '频次', max: 100 },
                        { name: '位移', max: 100 },
                        { name: '温度', max: 100 },
                        { name: '瓦斯', max: 100 }
                    ],
                    current: [78, 65, 72, 45, 30, 55],
                    threshold: [80, 80, 80, 80, 80, 80]
                }
            }
        };
    },
    computed: {
        imageStyle() {
            return {
                transform: `translate(${this.offsetX}px, ${this.offsetY}px) scale(${this.scale})`
            };
        }
    },
    mounted() {
        try {
            const cached = localStorage.getItem('page5.lastImageUrl');
            if (cached) this.surferImgUrl = cached;
            const lw = parseInt(localStorage.getItem('page5.leftWidth'), 10);
            const rw = parseInt(localStorage.getItem('page5.rightWidth'), 10);
            if (lw >= this.minPanelWidth && lw <= this.maxPanelWidth) this.leftWidth = lw;
            if (rw >= this.minPanelWidth && rw <= this.maxPanelWidth) this.rightWidth = rw;
        } catch (e) { /* ignore */ }

        this.$nextTick(() => {
            this.initStressChart();
            this.initRiskChart();
            this.initEventTypeChart();
            this.initTrendChart();
            this.initRadarChart();
        });
        this.resizeHandler = () => {
            Object.values(this.charts).forEach(c => c && c.resize());
        };
        window.addEventListener('resize', this.resizeHandler);
    },
    beforeDestroy() {
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
        }
        document.removeEventListener('mousemove', this.onResizeMove);
        document.removeEventListener('mouseup', this.stopResize);
        Object.values(this.charts).forEach(c => c && c.dispose && c.dispose());
    },
    methods: {
        magColor(mag) {
            if (mag >= 3) return RISK_COLORS.extreme;
            if (mag >= 2) return RISK_COLORS.high;
            if (mag >= 1) return RISK_COLORS.medium;
            return RISK_COLORS.low;
        },
        stressColor(value) {
            if (value >= 15) return RISK_COLORS.extreme;
            if (value >= 10) return RISK_COLORS.high;
            if (value >= 5) return RISK_COLORS.medium;
            return RISK_COLORS.low;
        },
        initStressChart() {
            const el = document.getElementById('stressChart');
            if (!el) return;
            const chart = this.$echarts(el);
            const data = this.mockData.stress;
            chart.setOption({
                grid: { left: 70, right: 30, top: 10, bottom: 20 },
                tooltip: {
                    trigger: 'axis',
                    backgroundColor: '#11367a',
                    borderColor: '#1a3c58',
                    textStyle: { color: '#6dd0e3', fontSize: 11 },
                    axisPointer: { type: 'shadow' }
                },
                xAxis: {
                    type: 'value',
                    axisLine: { lineStyle: { color: '#1a3c58' } },
                    axisLabel: { color: '#75deef', fontSize: 10 },
                    splitLine: { lineStyle: { color: 'rgba(26,60,88,0.4)' } }
                },
                yAxis: {
                    type: 'category',
                    data: data.map(d => d.name),
                    axisLine: { lineStyle: { color: '#1a3c58' } },
                    axisLabel: { color: '#75deef', fontSize: 10 },
                    axisTick: { show: false }
                },
                series: [{
                    type: 'bar',
                    data: data.map(d => ({
                        value: d.value,
                        itemStyle: { color: this.stressColor(d.value), borderRadius: [0, 4, 4, 0] }
                    })),
                    barWidth: 12,
                    label: {
                        show: true,
                        position: 'right',
                        color: '#75deef',
                        fontSize: 10
                    }
                }]
            });
            this.charts.stress = chart;
        },
        initRiskChart() {
            const el = document.getElementById('riskChart');
            if (!el) return;
            const chart = this.$echarts(el);
            const data = this.mockData.riskLevel;
            const total = data.reduce((s, d) => s + d.value, 0);
            chart.setOption({
                tooltip: {
                    trigger: 'item',
                    backgroundColor: '#11367a',
                    borderColor: '#1a3c58',
                    textStyle: { color: '#6dd0e3', fontSize: 11 },
                    formatter: '{b}: {c} ({d}%)'
                },
                legend: {
                    bottom: 0,
                    textStyle: { color: '#75deef', fontSize: 10 },
                    itemWidth: 10,
                    itemHeight: 10
                },
                title: {
                    text: total,
                    subtext: '事件总数',
                    left: 'center',
                    top: '38%',
                    textStyle: { color: '#6EDDF1', fontSize: 22, fontWeight: 'bold' },
                    subtextStyle: { color: '#68C6D6', fontSize: 10 }
                },
                series: [{
                    type: 'pie',
                    radius: ['46%', '64%'],
                    center: ['50%', '46%'],
                    avoidLabelOverlap: true,
                    label: { show: false },
                    labelLine: { show: false },
                    data: data.map(d => ({
                        name: d.name,
                        value: d.value,
                        itemStyle: { color: d.color }
                    }))
                }]
            });
            this.charts.risk = chart;
        },
        initEventTypeChart() {
            const el = document.getElementById('eventTypeChart');
            if (!el) return;
            const chart = this.$echarts(el);
            const palette = ['#2c7bfe', '#36cfc9', '#a262f2', '#feed2c', '#fe672c'];
            chart.setOption({
                tooltip: {
                    trigger: 'item',
                    backgroundColor: '#11367a',
                    borderColor: '#1a3c58',
                    textStyle: { color: '#6dd0e3', fontSize: 11 },
                    formatter: '{b}: {c} ({d}%)'
                },
                legend: {
                    bottom: 0,
                    textStyle: { color: '#75deef', fontSize: 10 },
                    itemWidth: 10,
                    itemHeight: 10
                },
                series: [{
                    type: 'pie',
                    radius: ['40%', '62%'],
                    center: ['50%', '46%'],
                    roseType: 'radius',
                    label: {
                        color: '#75deef',
                        fontSize: 10,
                        formatter: '{b}\n{d}%'
                    },
                    labelLine: { lineStyle: { color: 'rgb(57,63,90)' }, length: 6, length2: 6 },
                    data: this.mockData.eventType.map((d, i) => ({
                        ...d,
                        itemStyle: { color: palette[i % palette.length] }
                    }))
                }]
            });
            this.charts.eventType = chart;
        },
        initTrendChart() {
            const el = document.getElementById('trendChart');
            if (!el) return;
            const chart = this.$echarts(el);
            const { hours, counts } = this.mockData.trend;
            chart.setOption({
                grid: { left: 40, right: 20, top: 20, bottom: 30 },
                tooltip: {
                    trigger: 'axis',
                    backgroundColor: '#11367a',
                    borderColor: '#1a3c58',
                    textStyle: { color: '#6dd0e3', fontSize: 11 }
                },
                xAxis: {
                    type: 'category',
                    data: hours,
                    axisLine: { lineStyle: { color: '#1a3c58' } },
                    axisLabel: {
                        color: '#75deef',
                        fontSize: 9,
                        interval: 3
                    }
                },
                yAxis: {
                    type: 'value',
                    axisLine: { lineStyle: { color: '#1a3c58' } },
                    axisLabel: { color: '#75deef', fontSize: 10 },
                    splitLine: { lineStyle: { color: 'rgba(26,60,88,0.4)' } }
                },
                series: [{
                    type: 'line',
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 5,
                    data: counts,
                    lineStyle: { color: '#75deef', width: 2 },
                    itemStyle: { color: '#75deef' },
                    areaStyle: {
                        color: {
                            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                            colorStops: [
                                { offset: 0, color: 'rgba(117,222,239,0.5)' },
                                { offset: 1, color: 'rgba(117,222,239,0)' }
                            ]
                        }
                    }
                }]
            });
            this.charts.trend = chart;
        },
        initRadarChart() {
            const el = document.getElementById('radarChart');
            if (!el) return;
            const chart = this.$echarts(el);
            const { indicators, current, threshold } = this.mockData.radar;
            chart.setOption({
                tooltip: {
                    backgroundColor: '#11367a',
                    borderColor: '#1a3c58',
                    textStyle: { color: '#6dd0e3', fontSize: 11 }
                },
                legend: {
                    bottom: 0,
                    textStyle: { color: '#75deef', fontSize: 10 },
                    itemWidth: 10,
                    itemHeight: 10,
                    data: ['当前值', '预警阈值']
                },
                radar: {
                    indicator: indicators,
                    center: ['50%', '46%'],
                    radius: '60%',
                    axisName: { color: '#75deef', fontSize: 10 },
                    axisLine: { lineStyle: { color: 'rgba(26,60,88,0.6)' } },
                    splitLine: { lineStyle: { color: 'rgba(26,60,88,0.6)' } },
                    splitArea: {
                        areaStyle: {
                            color: ['rgba(13,36,81,0.3)', 'rgba(13,36,81,0.1)']
                        }
                    }
                },
                series: [{
                    type: 'radar',
                    data: [
                        {
                            value: current,
                            name: '当前值',
                            lineStyle: { color: '#ff4d4f', width: 2 },
                            itemStyle: { color: '#ff4d4f' },
                            areaStyle: { color: 'rgba(255,77,79,0.25)' }
                        },
                        {
                            value: threshold,
                            name: '预警阈值',
                            lineStyle: { color: '#faad14', width: 2, type: 'dashed' },
                            itemStyle: { color: '#faad14' },
                            areaStyle: { color: 'rgba(250,173,20,0.1)' }
                        }
                    ]
                }]
            });
            this.charts.radar = chart;
        },
        async handleUpload(event) {
            if (this.isProcessing) return;
            const file = event.target.files && event.target.files[0];
            if (!file) return;

            this.isProcessing = true;
            try {
                const res = await generateSurferMap(file);
                if (res.code === 200 && res.imageUrl) {
                    this.surferImgUrl = res.imageUrl;
                    try {
                        localStorage.setItem('page5.lastImageUrl', res.imageUrl);
                    } catch (e) { /* ignore */ }
                    if (this.$Message) this.$Message.success("图片已生成");
                } else if (this.$Message) {
                    this.$Message.error("后端返回异常，请检查服务日志");
                }
            } catch (error) {
                if (this.$Message) this.$Message.error("生成失败，请检查后端服务和输入文件");
            } finally {
                this.isProcessing = false;
                event.target.value = "";
            }
        },
        resetView() {
            this.scale = 1;
            this.offsetX = 0;
            this.offsetY = 0;
        },
        handleWheel(event) {
            if (!this.surferImgUrl) return;
            const zoomIn = event.deltaY < 0;
            const factor = zoomIn ? 1.1 : 0.9;
            const nextScale = this.scale * factor;
            this.scale = Math.min(this.maxScale, Math.max(this.minScale, nextScale));
        },
        startDrag(event) {
            if (!this.surferImgUrl) return;
            this.dragging = true;
            this.dragStartX = event.clientX;
            this.dragStartY = event.clientY;
            this.originOffsetX = this.offsetX;
            this.originOffsetY = this.offsetY;
        },
        onDrag(event) {
            if (!this.dragging) return;
            this.offsetX = this.originOffsetX + (event.clientX - this.dragStartX);
            this.offsetY = this.originOffsetY + (event.clientY - this.dragStartY);
        },
        stopDrag() {
            this.dragging = false;
        },
        closeImage() {
            this.surferImgUrl = "";
            try {
                localStorage.removeItem('page5.lastImageUrl');
            } catch (e) { /* ignore */ }
            this.resetView();
        },
        handleImageError() {
            this.surferImgUrl = "";
            try {
                localStorage.removeItem('page5.lastImageUrl');
            } catch (e) { /* ignore */ }
        },
        openGlobalConfig() {
            this.$root.$emit('open-global-config');
        },
        startResize(side, event) {
            this.resizing = side;
            this.resizeStartX = event.clientX;
            this.resizeStartWidth = side === 'left' ? this.leftWidth : this.rightWidth;
            document.addEventListener('mousemove', this.onResizeMove);
            document.addEventListener('mouseup', this.stopResize);
            document.body.style.cursor = 'ew-resize';
            document.body.style.userSelect = 'none';
        },
        onResizeMove(event) {
            if (!this.resizing) return;
            const delta = event.clientX - this.resizeStartX;
            const signed = this.resizing === 'left' ? delta : -delta;
            const next = Math.max(
                this.minPanelWidth,
                Math.min(this.maxPanelWidth, this.resizeStartWidth + signed)
            );
            if (this.resizing === 'left') {
                this.leftWidth = next;
            } else {
                this.rightWidth = next;
            }
            if (this.chartResizeTimer) cancelAnimationFrame(this.chartResizeTimer);
            this.chartResizeTimer = requestAnimationFrame(() => {
                Object.values(this.charts).forEach(c => c && c.resize());
            });
        },
        stopResize() {
            if (!this.resizing) return;
            try {
                localStorage.setItem('page5.leftWidth', String(this.leftWidth));
                localStorage.setItem('page5.rightWidth', String(this.rightWidth));
            } catch (e) { /* ignore */ }
            this.resizing = null;
            document.removeEventListener('mousemove', this.onResizeMove);
            document.removeEventListener('mouseup', this.stopResize);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    }
};
</script>

<style lang="less" scoped>
.page5 {
    position: relative;
    height: 100%;
    width: 100%;
    background: radial-gradient(circle at 50% 20%, #0a1d66 0%, #03044a 50%, #02022f 100%);
    overflow: hidden;
    display: flex;
    flex-direction: row;
    gap: 12px;
    padding: 12px;
    box-sizing: border-box;
}

.side-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
    flex-shrink: 0;
}

.resize-handle {
    width: 6px;
    flex-shrink: 0;
    cursor: ew-resize;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    transition: background 0.15s;

    .resize-grip {
        width: 2px;
        height: 40px;
        background: rgba(110, 221, 241, 0.25);
        border-radius: 1px;
        transition: background 0.15s, height 0.15s;
    }

    &:hover .resize-grip,
    &.active .resize-grip {
        background: #6EDDF1;
        height: 60px;
        box-shadow: 0 0 8px rgba(110, 221, 241, 0.6);
    }
}

.panel-card {
    position: relative;
    flex: 1;
    background: linear-gradient(180deg, rgba(13, 36, 81, 0.45) 0%, rgba(6, 14, 50, 0.65) 100%);
    border: 1px solid #0D2451;
    border-radius: 4px;
    padding: 36px 12px 12px 12px;
    overflow: hidden;
    box-sizing: border-box;
}

.panel-title {
    position: absolute;
    top: 6px;
    left: 50%;
    transform: translateX(-50%);
    color: #6EDDF1;
    font-size: 13px;
    letter-spacing: 1px;
    padding: 4px 14px;
    background: radial-gradient(55% 55% ellipse, rgba(7, 9, 34, 0.95) 60%, rgb(21, 67, 145));
    white-space: nowrap;
    z-index: 2;
}

.angle1, .angle2, .angle3, .angle4 {
    display: inline-block;
    position: absolute;
    width: 10px;
    height: 10px;
}
.angle1 { top: 0; left: 0; border-top: 1px solid #1C5AB3; border-left: 1px solid #1C5AB3; }
.angle2 { top: 0; right: 0; border-top: 1px solid #1C5AB3; border-right: 1px solid #1C5AB3; }
.angle3 { bottom: 0; left: 0; border-bottom: 1px solid #1C5AB3; border-left: 1px solid #1C5AB3; }
.angle4 { bottom: 0; right: 0; border-bottom: 1px solid #1C5AB3; border-right: 1px solid #1C5AB3; }

.chart-box {
    width: 100%;
    height: 100%;
    min-height: 140px;
}

/* KPI 网格 */
.kpi-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 10px;
    height: 100%;
}

.kpi-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(7, 19, 50, 0.55);
    border: 1px solid rgba(28, 90, 179, 0.4);
    border-radius: 4px;
}

.kpi-value {
    color: #6EDDF1;
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 1px;
    text-shadow: 0 0 12px rgba(110, 221, 241, 0.4);
}

.kpi-value.status-ok {
    color: #36cfc9;
    font-size: 18px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #36cfc9;
    box-shadow: 0 0 8px #36cfc9;
    display: inline-block;
}

.kpi-label {
    color: #68C6D6;
    font-size: 11px;
    margin-top: 4px;
}

/* 实时事件表格 */
.event-table-wrap {
    height: 100%;
    display: flex;
    flex-direction: column;
    color: #75deef;
    font-size: 11px;
}

.event-table-head, .event-row {
    display: flex;
    align-items: center;
    padding: 6px 4px;
}

.event-table-head {
    color: #6EDDF1;
    border-bottom: 1px solid rgba(28, 90, 179, 0.5);
    font-weight: bold;
    flex-shrink: 0;
}

.col-time { width: 26%; }
.col-loc { width: 34%; }
.col-energy { width: 22%; text-align: right; }
.col-mag { width: 18%; text-align: right; font-weight: bold; }

.event-table-body {
    flex: 1;
    overflow: hidden;
    position: relative;
}

.event-scroll {
    animation: scrollUp 20s linear infinite;
}

.event-table-body:hover .event-scroll {
    animation-play-state: paused;
}

.event-row {
    border-bottom: 1px dashed rgba(26, 60, 88, 0.5);
}

@keyframes scrollUp {
    0%   { transform: translateY(0); }
    100% { transform: translateY(-50%); }
}

/* 中央 stage */
.center-stage {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    position: relative;
    background: rgba(3, 4, 74, 0.3);
    border: 1px solid #0D2451;
    border-radius: 4px;
    overflow: hidden;
}

.toolbar {
    position: relative;
    z-index: 5;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 10px 14px;
    border-bottom: 1px solid rgba(28, 90, 179, 0.35);
    background: rgba(7, 19, 50, 0.45);
}

.surfer-btn {
    background: linear-gradient(135deg, #1a3c58 0%, #0d2451 100%);
    border: 1px solid #6eddf1;
    color: #6eddf1;
}

.stage {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: grab;
    user-select: none;
    overflow: hidden;
}

.stage:active {
    cursor: grabbing;
}

.placeholder {
    text-align: center;
    color: #7fcde8;
    line-height: 1.9;
    font-size: 18px;
    letter-spacing: 1px;
    opacity: 0.9;
}

.surfer-image {
    max-width: 90%;
    max-height: 90%;
    object-fit: contain;
    transform-origin: center center;
    transition: transform 0.05s linear;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.45);
}

/* 处理中蒙层 */
.processing-mask {
    position: absolute;
    inset: 0;
    background: rgba(1, 4, 44, 0.7);
    z-index: 30;
    display: flex;
    align-items: center;
    justify-content: center;

    .processing-card {
        width: 280px;
        padding: 24px 18px;
        border: 1px solid #2c6aa1;
        border-radius: 8px;
        background: rgba(6, 26, 77, 0.95);
        text-align: center;
        color: #9cdaee;

        p {
            margin-top: 10px;
        }
    }
}
</style>
