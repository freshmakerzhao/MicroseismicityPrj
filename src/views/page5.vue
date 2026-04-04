<template>
    <div class="page5">
        <div class="toolbar">
            <Button
                class="setting-btn"
                :disabled="isProcessing"
                @click="openGlobalConfig"
            >
                设置
            </Button>
            <input
                ref="fileInput"
                type="file"
                accept=".xls,.xlsx,.csv,.txt"
                style="display: none"
                @change="handleUpload"
            >
            <Button
                type="primary"
                icon="ios-cloud-upload-outline"
                class="upload-btn"
                :loading="isProcessing"
                :disabled="isProcessing"
                @click="$refs.fileInput.click()"
            >
                上传文件
            </Button>
            <Button
                v-if="surferImgUrl"
                class="reset-btn"
                :disabled="isProcessing"
                @click="resetView"
            >
                重置视图
            </Button>
            <Button
                v-if="surferImgUrl"
                class="close-btn"
                :disabled="isProcessing"
                @click="closeImage"
            >
                关闭图片
            </Button>
        </div>

        <div v-if="isProcessing" class="processing-mask">
            <div class="processing-card">
                <Spin size="large"></Spin>
                <p>处理中，请稍候...</p>
            </div>
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
                <p>请点击右上角上传文件后查看结果</p>
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
            >
        </div>
    </div>
</template>

<script>
import { generateSurferMap } from "@/lib/surfer.js";

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
            isProcessing: false
        };
    },
    computed: {
        imageStyle() {
            return {
                transform: `translate(${this.offsetX}px, ${this.offsetY}px) scale(${this.scale})`
            };
        }
    },
    methods: {
        async handleUpload(event) {
            if (this.isProcessing) {
                return;
            }

            const file = event.target.files && event.target.files[0];
            if (!file) {
                return;
            }

            this.isProcessing = true;
            try {
                const res = await generateSurferMap(file);
                if (res.code === 200 && res.imageUrl) {
                    this.surferImgUrl = res.imageUrl;
                    if (this.$Message) {
                        this.$Message.success("图片已生成");
                    }
                } else if (this.$Message) {
                    this.$Message.error("后端返回异常，请检查服务日志");
                }
            } catch (error) {
                if (this.$Message) {
                    this.$Message.error("生成失败，请检查后端服务和输入文件");
                }
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
            if (!this.surferImgUrl) {
                return;
            }

            const zoomIn = event.deltaY < 0;
            const factor = zoomIn ? 1.1 : 0.9;
            const nextScale = this.scale * factor;
            this.scale = Math.min(this.maxScale, Math.max(this.minScale, nextScale));
        },
        startDrag(event) {
            if (!this.surferImgUrl) {
                return;
            }
            this.dragging = true;
            this.dragStartX = event.clientX;
            this.dragStartY = event.clientY;
            this.originOffsetX = this.offsetX;
            this.originOffsetY = this.offsetY;
        },
        onDrag(event) {
            if (!this.dragging) {
                return;
            }
            this.offsetX = this.originOffsetX + (event.clientX - this.dragStartX);
            this.offsetY = this.originOffsetY + (event.clientY - this.dragStartY);
        },
        stopDrag() {
            this.dragging = false;
        },
        closeImage() {
            this.surferImgUrl = "";
            this.resetView();
        },
        openGlobalConfig() {
            this.$root.$emit('open-global-config');
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
}

.toolbar {
    position: absolute;
    top: 20px;
    right: 24px;
    z-index: 20;
    display: flex;
    gap: 10px;
}

.setting-btn,
.upload-btn,
.reset-btn,
.close-btn {
    background: linear-gradient(135deg, #1a3c58 0%, #0d2451 100%);
    border: 1px solid #6eddf1;
    color: #6eddf1;
}

.stage {
    height: 100%;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: grab;
    user-select: none;
}

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
    max-width: 80vw;
    max-height: 80vh;
    object-fit: contain;
    transform-origin: center center;
    transition: transform 0.05s linear;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.45);
}
</style>
