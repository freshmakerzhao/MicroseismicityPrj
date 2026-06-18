<template>
    <div class="auth-page">
        <div class="system-title">冲击地压矿井微震监测智能判识冲击危险等级及区划系统</div>
        <div class="auth-card">
            <div class="card-title">用户登录</div>
            <Form :model="form" label-position="top">
                <FormItem label="用户名">
                    <Input v-model="form.username" placeholder="请输入用户名" @on-enter="handleLogin" />
                </FormItem>
                <FormItem label="密码">
                    <Input v-model="form.password" type="password" placeholder="请输入密码" @on-enter="handleLogin" />
                </FormItem>
                <Button type="primary" long :loading="loading" @click="handleLogin">登录</Button>
                <Button long class="secondary-btn" @click="$router.push('/register')">注册新用户</Button>
            </Form>
        </div>
    </div>
</template>

<script>
import { login } from '@/lib/auth';

export default {
    name: 'login',
    data() {
        return {
            loading: false,
            form: {
                username: '',
                password: ''
            }
        };
    },
    methods: {
        async handleLogin() {
            if (!this.form.username || !this.form.password) {
                this.$Message && this.$Message.warning('请输入用户名和密码');
                return;
            }
            try {
                this.loading = true;
                await login(this.form);
                this.$Message && this.$Message.success('登录成功');
                const redirect = this.$route.query.redirect || '/page5';
                this.$router.replace(redirect);
            } catch (error) {
                this.$Message && this.$Message.error('用户名或密码错误');
            } finally {
                this.loading = false;
            }
        }
    }
};
</script>

<style lang="less" scoped>
.auth-page {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 32px;
    padding: 40px 24px;
    background: radial-gradient(circle at 50% 20%, #0b2560 0%, #06143a 44%, #020617 100%);
}

.auth-card {
    width: 440px;
    padding: 34px 36px 30px;
    border: 1px solid rgba(117, 222, 239, 0.42);
    border-radius: 8px;
    background: rgba(5, 16, 46, 0.92);
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.42);
}

.system-title {
    color: #75deef;
    font-size: 30px;
    font-weight: 700;
    line-height: 1.35;
    text-align: center;
    max-width: 1120px;
    padding: 0 18px;
    text-shadow: 0 0 22px rgba(117, 222, 239, 0.42);
}

.card-title {
    color: #d8f3ff;
    font-size: 20px;
    margin-bottom: 18px;
    text-align: center;
}

.secondary-btn {
    margin-top: 12px;
}

@media (max-width: 768px) {
    .auth-page {
        gap: 24px;
        padding: 28px 16px;
    }

    .system-title {
        font-size: 22px;
    }

    .auth-card {
        width: 100%;
        max-width: 440px;
        padding: 28px 24px 26px;
    }
}

</style>
