<template>
    <div class="page6">
        <div class="toolbar">
            <input
                ref="fileInput"
                class="file-input"
                type="file"
                accept=".xls"
                @change="handleFileChange"
            />
            <div class="tool-item">
                <Button size="small" type="primary" :loading="loading" @click="chooseFile">读取微震Excel</Button>
                <Button size="small" :disabled="!selectedFile || loading" @click="calculateWarning">重新计算</Button>
                <span class="file-name">{{ selectedFileName || "未读取事件文件" }}</span>
            </div>
            <div class="tool-item">
                <span>显示微震点</span>
                <i-switch v-model="showEvents" />
            </div>
            <div class="tool-item">
                <Button size="small" @click="fitView">重置视图</Button>
                <Button size="small" :loading="loading" @click="reloadData">刷新</Button>
            </div>
            <div v-if="summary" class="summary">
                中心线 {{ summary.centerline_points }} 点
                <template v-if="summary.event_count">，事件 {{ summary.event_count }} 条，Q*={{ formatNumber(summary.q_r100_star) }}</template>
            </div>
        </div>
        <div ref="chartWrap" class="chart-wrap"></div>
    </div>
</template>

<script>
import { calculateMicroseismicWarning, getMicroseismicCenterline } from "@/lib/surfer";

export default {
    name: "page6",
    data() {
        return {
            chart: null,
            warningData: null,
            selectedFile: null,
            selectedFileName: "",
            loading: false,
            showEvents: true,
            resizeHandler: null
        };
    },
    computed: {
        summary() {
            return this.warningData && this.warningData.meta;
        }
    },
    mounted() {
        this.chart = this.$echarts(this.$refs.chartWrap);
        this.resizeHandler = () => this.chart && this.chart.resize();
        window.addEventListener("resize", this.resizeHandler);
        this.chart.on("restore", this.onChartRestore);
        this.loadCenterline();
    },
    beforeDestroy() {
        if (this.chart) {
            this.chart.off("restore", this.onChartRestore);
            this.chart.dispose();
        }
        window.removeEventListener("resize", this.resizeHandler);
    },
    watch: {
        showEvents() {
            this.renderChart();
        }
    },
    methods: {
        async loadCenterline() {
            try {
                this.loading = true;
                this.warningData = await getMicroseismicCenterline();
                this.renderChart();
            } catch (e) {
                if (this.$Message) {
                    this.$Message.error("加载巷道中心线失败");
                }
            } finally {
                this.loading = false;
            }
        },
        chooseFile() {
            this.$refs.fileInput.click();
        },
        handleFileChange(event) {
            const file = event.target.files && event.target.files[0];
            if (!file) {
                return;
            }
            this.selectedFile = file;
            this.selectedFileName = file.name;
            this.calculateWarning();
        },
        async calculateWarning() {
            if (!this.selectedFile) {
                return;
            }
            try {
                this.loading = true;
                this.warningData = await calculateMicroseismicWarning(this.selectedFile);
                this.renderChart();
                if (this.$Message) {
                    this.$Message.success("W计算完成");
                }
            } catch (e) {
                if (this.$Message) {
                    this.$Message.error("微震文件计算失败");
                }
            } finally {
                this.loading = false;
            }
        },
        reloadData() {
            if (this.selectedFile) {
                this.calculateWarning();
            } else {
                this.loadCenterline();
            }
        },
        fitView() {
            if (!this.chart || !this.warningData) {
                return;
            }
            const b = this.warningData.meta.bounds;
            this.chart.setOption({
                xAxis: { min: b.xmin, max: b.xmax },
                yAxis: { min: b.ymin, max: b.ymax }
            });
        },
        onChartRestore() {
            this.fitView();
        },
        formatNumber(value) {
            if (value == null || !Number.isFinite(Number(value))) {
                return "-";
            }
            const num = Number(value);
            if (Math.abs(num) >= 10000 || Math.abs(num) < 0.001) {
                return num.toExponential(3);
            }
            return num.toFixed(3);
        },
        riskColor(w) {
            if (w >= 0.75) return "#ff4d4f";
            if (w >= 0.5) return "#faad14";
            if (w >= 0.25) return "#fadb14";
            return "#36cfc9";
        },
        buildCenterlineSeries() {
            const segment = this.warningData.centerline.segment;
            return {
                type: "line",
                name: "巷道中心线",
                data: segment,
                symbol: "none",
                lineStyle: {
                    color: "#69f0ae",
                    width: 3
                },
                z: 2
            };
        },
        buildEventSeries() {
            if (!this.showEvents || !this.warningData.events || this.warningData.events.length === 0) {
                return null;
            }
            const events = this.warningData.events.map((event) => ({
                value: [event.x, event.y, event.w],
                ...event
            }));
            return {
                type: "scatter",
                name: "微震点",
                data: events,
                z: 3,
                symbolSize: (val) => {
                    const w = Math.max(Number(val[2]) || 0, 0);
                    return Math.max(6, Math.min(22, 7 + Math.sqrt(w) * 8));
                },
                itemStyle: {
                    color: (params) => this.riskColor(params.data.w),
                    opacity: 0.82
                },
                emphasis: {
                    itemStyle: {
                        borderColor: "#fff",
                        borderWidth: 1
                    }
                }
            };
        },
        renderChart() {
            if (!this.chart || !this.warningData) {
                return;
            }
            const b = this.warningData.meta.bounds;
            const series = [this.buildCenterlineSeries()];
            const eventSeries = this.buildEventSeries();
            if (eventSeries) {
                series.push(eventSeries);
            }

            this.chart.setOption({
                backgroundColor: "transparent",
                animation: false,
                tooltip: {
                    trigger: "item",
                    formatter: (params) => {
                        if (params.seriesType === "scatter") {
                            const d = params.data;
                            return [
                                `事件: ${d.event_id}`,
                                `X: ${Number(d.x).toFixed(2)}`,
                                `Y: ${Number(d.y).toFixed(2)}`,
                                `Z: ${d.z == null ? "-" : Number(d.z).toFixed(2)}`,
                                `能量: ${this.formatNumber(d.energy_j)} J`,
                                `R: ${this.formatNumber(d.r)} m`,
                                `W: ${this.formatNumber(d.w)}`,
                                `等级: ${d.risk_level}`
                            ].join("<br/>");
                        }
                        return "由database/centerline_points.csv拟合的巷道中心线";
                    }
                },
                legend: {
                    top: 8,
                    textStyle: { color: "#9adcf0" },
                    data: ["巷道中心线", "微震点"]
                },
                toolbox: {
                    right: 12,
                    feature: {
                        restore: {},
                        saveAsImage: {}
                    },
                    iconStyle: { borderColor: "#8fdcf7" }
                },
                xAxis: {
                    type: "value",
                    min: b.xmin,
                    max: b.xmax,
                    axisLabel: { color: "#8fdcf7" },
                    splitLine: { lineStyle: { color: "rgba(143,220,247,0.12)" } }
                },
                yAxis: {
                    type: "value",
                    min: b.ymin,
                    max: b.ymax,
                    axisLabel: { color: "#8fdcf7" },
                    splitLine: { lineStyle: { color: "rgba(143,220,247,0.12)" } }
                },
                grid: {
                    left: 50,
                    right: 28,
                    top: 55,
                    bottom: 35
                },
                dataZoom: [
                    { type: "inside", xAxisIndex: 0, yAxisIndex: 0, zoomOnMouseWheel: true, moveOnMouseMove: true },
                    { type: "inside", xAxisIndex: 0, yAxisIndex: 0, zoomOnMouseWheel: "shift" }
                ],
                series
            }, true);
        }
    }
};
</script>

<style lang="less" scoped>
.page6 {
    height: 100%;
    width: 100%;
    background: radial-gradient(circle at 30% 20%, #0a1d66 0%, #03044a 60%, #02022f 100%);
    display: flex;
    flex-direction: column;
}

.toolbar {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(126, 199, 255, 0.25);
    color: #9adcf0;

    .tool-item {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-shrink: 0;
    }
}

.file-input {
    display: none;
}

.file-name {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #d6f6ff;
    font-size: 13px;
}

.summary {
    margin-left: auto;
    color: #d6f6ff;
    font-size: 13px;
    white-space: nowrap;
}

.chart-wrap {
    flex: 1;
    min-height: 0;
}
</style>
