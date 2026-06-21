<template>
    <nav class="tech-nav">
        <button
            v-for="item in items"
            :key="item.path"
            class="tech-nav-item"
            :class="{ active: activePath === item.path }"
            type="button"
            @click="$emit('select', item.path)"
        >
            {{ item.label }}
        </button>
    </nav>
</template>

<script>
export default {
    name: 'TechNav',
    props: {
        items: {
            type: Array,
            default: () => []
        },
        activePath: {
            type: String,
            default: ''
        }
    }
};
</script>

<style lang="less" scoped>
.tech-nav {
    display: flex;
    align-items: center;
    gap: 10px;
}

.tech-nav-item {
    position: relative;
    z-index: 1;
    width: 100px;
    height: 32px;
    color: rgba(255, 255, 255, 0.68);
    font-size: 14px;
    line-height: 32px;
    text-align: center;
    border: none;
    outline: none;
    background: url("../../assets/threemaps/images/menu-btn.png") center / 100% 100% no-repeat;
    cursor: pointer;
    transition: color 0.18s, filter 0.18s;

    &:hover,
    &.active {
        color: #ffffff;
        background-image: url("../../assets/threemaps/images/menu-btn-hover.png");
        filter: drop-shadow(0 0 8px rgba(48, 220, 255, 0.5));
    }

    &.active::after {
        content: "";
        position: absolute;
        left: 50%;
        top: 50%;
        z-index: -1;
        width: 96px;
        height: 28px;
        margin-left: -48px;
        margin-top: -14px;
        border-radius: 28px;
        background: rgba(0, 170, 255, 0.45);
        animation: techMenuPulse 1.4s ease-out infinite;
    }
}

@keyframes techMenuPulse {
    0% {
        transform: scale(0.95);
        opacity: 0.75;
    }
    100% {
        transform: scale(1.25, 1.35);
        opacity: 0;
    }
}
</style>
