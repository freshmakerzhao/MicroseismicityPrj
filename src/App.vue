<template>
    <div id="app">
        <router-view/>
    </div>
</template>

<script>
export default {
    name: 'App',
    data() {
        return {
            resizeFn: null
        }
    },
    mounted() {
        // this.setScale();
        // this.resizeFn = this.$debounce(() => {
        //     this.setScale();
        // }, 200)
        // window.addEventListener('resize', this.resizeFn);
        // 但需要确保页面高度占满且不可溢出
        document.documentElement.style.overflow = 'hidden';
        document.body.style.overflow = 'hidden';
        document.body.style.width = '100%';
        document.body.style.height = '100vh'; // 强制高度占满视口
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.resizeFn);
    },
    methods: {
        setScale() {
            // 大屏设计稿基准尺寸
            const designWidth = 1920;
            const designHeight = 1080;
            
            // 获取实际屏幕尺寸
            const clientWidth = document.documentElement.clientWidth || document.body.clientWidth;
            const clientHeight = document.documentElement.clientHeight || document.body.clientHeight;
            
            // 计算缩放比例（等比缩放，使用较小值确保内容完全显示）
            const scale = Math.min(clientWidth / designWidth, clientHeight / designHeight);
            
            // 计算居中偏移量
            const offsetX = (clientWidth - designWidth * scale) / 2;
            const offsetY = (clientHeight - designHeight * scale) / 2;
            
            // 应用等比缩放并居中
            document.body.style.transform = `scale(${scale})`;
            document.body.style.transformOrigin = 'left top';
            document.body.style.width = `${designWidth}px`;
            document.body.style.height = `${designHeight}px`;
            document.body.style.position = 'absolute';
            document.body.style.left = `${offsetX}px`;
            document.body.style.top = `${offsetY}px`;
            
            // 设置html确保无滚动
            document.documentElement.style.width = '100%';
            document.documentElement.style.height = '100%';
            document.documentElement.style.overflow = 'hidden';
            document.body.style.overflow = 'hidden';
        }
    }
}
</script>

<style lang="less">
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html, body {
    height: 100%;
    width: 100%;
    padding: 0;
    margin: 0;
    overflow: hidden;
}

html {
    font-size: 20px;
}

body {
    background-size: 100% 100%;
    overflow: hidden;
}

#app {
    height: 100%;
    width: 100%;
    font-family: 'Avenir', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
</style>
