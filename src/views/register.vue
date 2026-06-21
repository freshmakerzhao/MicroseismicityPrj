<template>
    <div class="auth-page">
        <div class="system-title">冲击地压矿井微震监测智能判识冲击危险等级及区划系统</div>
        <div class="auth-card">
            <div class="card-title">用户注册</div>
            <Form :model="form" label-position="top">
                <FormItem label="用户名">
                    <Input v-model="form.username" placeholder="至少 3 个字符" />
                </FormItem>
                <FormItem label="姓名">
                    <Input v-model="form.display_name" placeholder="请输入姓名或显示名称" />
                </FormItem>
                <FormItem label="密码">
                    <Input v-model="form.password" type="password" placeholder="至少 6 个字符" />
                </FormItem>
                <FormItem label="确认密码">
                    <Input v-model="confirmPassword" type="password" placeholder="请再次输入密码" @on-enter="handleRegister" />
                </FormItem>
                <Button type="primary" long :loading="loading" @click="handleRegister">注册</Button>
                <Button long class="secondary-btn" @click="$router.push('/login')">返回登录</Button>
            </Form>
            <div class="hint">新注册用户默认为普通用户，管理员可在人员管理中调整权限。</div>
        </div>
    </div>
</template>

<script>
import { register } from '@/lib/auth';

export default {
    name: 'register',
    data() {
        return {
            loading: false,
            confirmPassword: '',
            form: {
                username: '',
                display_name: '',
                password: ''
            }
        };
    },
    methods: {
        async handleRegister() {
            if (!this.form.username || !this.form.password) {
                this.$Message && this.$Message.warning('请填写用户名和密码');
                return;
            }
            if (this.form.password !== this.confirmPassword) {
                this.$Message && this.$Message.warning('两次密码输入不一致');
                return;
            }
            try {
                this.loading = true;
                await register(this.form);
                this.$Message && this.$Message.success('注册成功，请登录');
                this.$router.replace('/login');
            } catch (error) {
                const detail = error.response && error.response.data && error.response.data.detail;
                this.$Message && this.$Message.error(detail || '注册失败');
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
    background:
        radial-gradient(circle at 50% 20%, rgba(25, 91, 142, 0.45) 0%, rgba(3, 20, 46, 0.96) 44%, #020617 100%),
        url("../assets/threemaps/images/bg.png") center / cover no-repeat;
}

.auth-card {
    width: 440px;
    padding: 34px 36px 30px;
    border: 1px solid rgba(117, 222, 239, 0.42);
    border-radius: 8px;
    background: linear-gradient(180deg, rgba(13, 55, 80, 0.84), rgba(5, 16, 46, 0.92));
    box-shadow: inset 0 0 24px rgba(48, 220, 255, 0.08), 0 24px 70px rgba(0, 0, 0, 0.42);
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

.hint {
    margin-top: 16px;
    color: #8db5c7;
    font-size: 12px;
    text-align: center;
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
