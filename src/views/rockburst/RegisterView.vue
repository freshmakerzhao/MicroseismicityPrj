<template>
  <div class="auth-screen">
    <div class="auth-bg-grid"></div>
    <div class="auth-title">冲击地压矿井微震监测智能判识冲击危险等级及区划系统</div>
    <form class="auth-panel" @submit.prevent="handleRegister">
      <div class="auth-panel-title">用户注册</div>
      <label><span>用户名</span><input v-model.trim="form.username" placeholder="至少 3 个字符" /></label>
      <label><span>姓名</span><input v-model.trim="form.display_name" placeholder="请输入姓名或显示名称" /></label>
      <label><span>密码</span><input v-model="form.password" type="password" placeholder="至少 6 个字符" /></label>
      <label><span>确认密码</span><input v-model="confirmPassword" type="password" placeholder="请再次输入密码" /></label>
      <button class="primary-btn" type="submit" :disabled="loading">{{ loading ? "注册中..." : "注册" }}</button>
      <button class="ghost-btn" type="button" @click="router.push('/login')">返回登录</button>
      <div v-if="message" class="auth-message" :class="{ ok: success }">{{ message }}</div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue"
import { useRouter } from "vue-router"
import { register } from "@/lib/apiClient"

const router = useRouter()
const loading = ref(false)
const message = ref("")
const success = ref(false)
const confirmPassword = ref("")
const form = reactive({
  username: "",
  display_name: "",
  password: "",
})

async function handleRegister() {
  if (!form.username || !form.password) {
    message.value = "请填写用户名和密码"
    success.value = false
    return
  }
  if (form.password !== confirmPassword.value) {
    message.value = "两次密码输入不一致"
    success.value = false
    return
  }
  try {
    loading.value = true
    await register(form)
    success.value = true
    message.value = "注册成功，请登录"
    setTimeout(() => router.replace("/login"), 700)
  } catch (error) {
    success.value = false
    message.value = error.message || "注册失败"
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
@import "./auth-shared.scss";
</style>
