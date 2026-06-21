<template>
    <header class="tech-header">
        <div class="tech-header-frame"></div>
        <div class="tech-header-title-wrap">
            <div class="tech-header-title">{{ title }}</div>
            <div class="tech-header-subtitle">{{ subtitle }}</div>
        </div>
        <div class="tech-header-left">
            <slot name="left">
                <span>微震监测</span>
                <span>WebGL</span>
            </slot>
        </div>
        <div class="tech-header-right">
            <div class="user-line">
                <span class="user-name">{{ userName }}</span>
                <span class="role-tag">{{ roleLabel }}</span>
                <button class="logout-btn" type="button" @click="$emit('logout')">退出登录</button>
            </div>
            <slot name="nav"></slot>
        </div>
    </header>
</template>

<script>
export default {
    name: 'TechHeader',
    props: {
        title: {
            type: String,
            required: true
        },
        subtitle: {
            type: String,
            default: ''
        },
        userName: {
            type: String,
            default: ''
        },
        roleLabel: {
            type: String,
            default: ''
        }
    }
};
</script>

<style lang="less" scoped>
.tech-header {
    position: relative;
    height: 120px;
    flex-shrink: 0;
    z-index: 20;
    pointer-events: none;
}

.tech-header-frame {
    position: absolute;
    left: 50%;
    top: 0;
    width: 1920px;
    height: 90px;
    transform: translateX(-50%);
    background: url("../../assets/threemaps/images/header-bg.png") center top / 100% 90px no-repeat;
    opacity: 0.95;
}

.tech-header-title-wrap {
    position: absolute;
    left: 50%;
    top: 8px;
    width: 52vw;
    max-width: 840px;
    transform: translateX(-50%);
    text-align: center;
}

.tech-header-title {
    font-size: 32px;
    line-height: 42px;
    font-weight: 800;
    letter-spacing: 1px;
    color: #dff9ff;
    text-shadow: 0 0 18px rgba(48, 220, 255, 0.6);
    background: linear-gradient(180deg, #dffbff 0%, #6ce9ff 54%, #ffffff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.tech-header-subtitle {
    margin-top: -2px;
    color: rgba(196, 243, 254, 0.64);
    font-size: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
}

.tech-header-left {
    position: absolute;
    left: 30px;
    top: 46px;
    display: flex;
    gap: 14px;
    color: #c4f3fe;
    font-size: 13px;
}

.tech-header-right {
    position: absolute;
    right: 30px;
    top: 24px;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
    pointer-events: auto;
}

.user-line {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #c4f3fe;
    font-size: 13px;
}

.user-name {
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.role-tag {
    height: 22px;
    padding: 0 10px;
    line-height: 20px;
    color: #8ff5ff;
    border: 1px solid rgba(48, 220, 255, 0.55);
    border-radius: 2px;
    background: rgba(0, 178, 255, 0.12);
    box-shadow: inset 0 0 12px rgba(48, 220, 255, 0.16);
}

.logout-btn {
    height: 22px;
    padding: 0 10px;
    color: #c4f3fe;
    border: 1px solid rgba(48, 220, 255, 0.36);
    border-radius: 2px;
    background: rgba(8, 37, 76, 0.62);
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
        color: #ffffff;
        border-color: #30dcff;
        box-shadow: 0 0 12px rgba(48, 220, 255, 0.35);
    }
}

@media (max-width: 1280px) {
    .tech-header-title {
        font-size: 25px;
    }

    .tech-header-title-wrap {
        width: 58vw;
    }
}
</style>
