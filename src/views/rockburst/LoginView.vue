<template>
  <div class="auth-screen">
    <div class="auth-bg-grid"></div>
    <div class="auth-title">冲击地压矿井微震监测智能判识冲击危险等级及区划系统</div>
    <form class="auth-panel" @submit.prevent="handleLogin">
      <div class="auth-panel-title">系统登录</div>
      <label>
        <span>用户名</span>
        <input v-model.trim="form.username" autocomplete="username" placeholder="请输入用户名" />
      </label>
      <label>
        <span>密码</span>
        <input v-model="form.password" type="password" autocomplete="current-password" placeholder="请输入密码" />
      </label>
      <button class="primary-btn" type="submit" :disabled="loading">
        {{ loading ? "登录中..." : "登录" }}
      </button>
      <button class="ghost-btn" type="button" @click="router.push('/register')">注册新用户</button>
      <div v-if="message" class="auth-message">{{ message }}</div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { login } from "@/lib/apiClient"

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const message = ref("")
const form = reactive({
  username: "",
  password: "",
})

async function handleLogin() {
  if (!form.username || !form.password) {
    message.value = "请输入用户名和密码"
    return
  }
  try {
    loading.value = true
    message.value = ""
    await login(form)
    router.replace(route.query.redirect || "/dashboard")
  } catch (error) {
    message.value = error.message && error.message.startsWith("HTTP")
      ? "后端服务未启动或网络连接异常"
      : "用户名或密码错误"
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.auth-screen {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 34px;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 24%, rgba(48, 220, 255, 0.28), transparent 34%),
    url("@/assets/images/bg.png") center / cover no-repeat,
    #020b1d;
}

.auth-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(48, 220, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(48, 220, 255, 0.07) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(circle at center, #000 0%, transparent 76%);
  animation: gridMove 8s linear infinite;
}

.auth-title {
  position: relative;
  z-index: 1;
  max-width: 1180px;
  padding: 0 24px;
  color: #dffbff;
  font-size: 34px;
  font-weight: 800;
  line-height: 1.35;
  text-align: center;
  letter-spacing: 1px;
  text-shadow: 0 0 28px rgba(48, 220, 255, 0.72);
  background: linear-gradient(180deg, #ffffff, #75e8ff 62%, #ffffff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.auth-panel {
  position: relative;
  z-index: 1;
  width: 440px;
  padding: 32px 36px 28px;
  border: 1px solid rgba(48, 220, 255, 0.42);
  background: linear-gradient(180deg, rgba(16, 68, 96, 0.78), rgba(4, 16, 42, 0.9));
  box-shadow: inset 0 0 26px rgba(48, 220, 255, 0.1), 0 0 70px rgba(0, 155, 255, 0.18);
  overflow: hidden;

  &::after {
    content: "";
    position: absolute;
    left: -120px;
    top: 0;
    width: 90px;
    height: 100%;
    background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.24), transparent);
    transform: skewX(-18deg);
    animation: sweep 5.6s linear infinite;
    pointer-events: none;
  }

  label {
    display: block;
    margin-bottom: 16px;
    color: rgba(196, 243, 254, 0.78);
    font-size: 13px;
  }

  input {
    width: 100%;
    height: 40px;
    margin-top: 8px;
    padding: 0 12px;
    color: #dffbff;
    border: 1px solid rgba(48, 220, 255, 0.34);
    outline: none;
    background: rgba(3, 14, 33, 0.72);
  }
}

.auth-panel-title {
  margin-bottom: 22px;
  color: #dffbff;
  font-size: 20px;
  text-align: center;
}

.primary-btn,
.ghost-btn {
  width: 100%;
  height: 38px;
  margin-top: 8px;
  color: #dffbff;
  border: 1px solid rgba(48, 220, 255, 0.5);
  background: linear-gradient(180deg, rgba(21, 91, 127, 0.9), rgba(7, 30, 64, 0.9));
  cursor: pointer;
}

.ghost-btn {
  color: rgba(196, 243, 254, 0.8);
  background: rgba(5, 18, 42, 0.5);
}

.auth-message {
  margin-top: 14px;
  color: #ff9b9b;
  font-size: 13px;
  text-align: center;
}

@keyframes gridMove {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(44px, 44px, 0); }
}

@keyframes sweep {
  0% { transform: translateX(0) skewX(-18deg); opacity: 0; }
  12% { opacity: 0.85; }
  38% { transform: translateX(680px) skewX(-18deg); opacity: 0; }
  100% { transform: translateX(680px) skewX(-18deg); opacity: 0; }
}
</style>
