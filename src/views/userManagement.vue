<template>
    <div class="user-page">
        <div class="page-head">
            <div>
                <div class="title">人员管理</div>
                <div class="sub">管理员可维护用户状态并分配管理员或普通用户权限</div>
            </div>
            <Button type="primary" :loading="loading" @click="loadUsers">刷新</Button>
        </div>

        <Table :columns="columns" :data="users" :loading="loading" class="user-table"></Table>

        <Modal v-model="editVisible" title="编辑用户" @on-ok="saveUser">
            <Form :model="editForm" label-position="top">
                <FormItem label="姓名">
                    <Input v-model="editForm.display_name" />
                </FormItem>
                <FormItem label="角色">
                    <Select v-model="editForm.role">
                        <Option value="admin">管理员</Option>
                        <Option value="user">用户</Option>
                    </Select>
                </FormItem>
                <FormItem label="状态">
                    <i-switch v-model="editForm.enabled">
                        <span slot="open">启用</span>
                        <span slot="close">停用</span>
                    </i-switch>
                </FormItem>
                <FormItem label="重置密码">
                    <Input v-model="editForm.password" type="password" placeholder="留空则不修改密码" />
                </FormItem>
            </Form>
        </Modal>
    </div>
</template>

<script>
import { deleteUser, fetchUsers, updateUser } from '@/lib/auth';

export default {
    name: 'userManagement',
    data() {
        return {
            loading: false,
            users: [],
            editVisible: false,
            editForm: {
                id: '',
                display_name: '',
                role: 'user',
                enabled: true,
                password: ''
            },
            columns: [
                { title: '用户名', key: 'username', minWidth: 140 },
                { title: '姓名', key: 'display_name', minWidth: 140 },
                {
                    title: '角色',
                    key: 'role',
                    width: 120,
                    render: (h, params) => h('Tag', {
                        props: { color: params.row.role === 'admin' ? 'blue' : 'green' }
                    }, params.row.role === 'admin' ? '管理员' : '用户')
                },
                {
                    title: '状态',
                    key: 'enabled',
                    width: 100,
                    render: (h, params) => h('Tag', {
                        props: { color: params.row.enabled ? 'success' : 'error' }
                    }, params.row.enabled ? '启用' : '停用')
                },
                { title: '创建时间', key: 'created_at', minWidth: 170 },
                {
                    title: '操作',
                    key: 'actions',
                    width: 180,
                    render: (h, params) => h('div', [
                        h('Button', {
                            props: { size: 'small', type: 'primary' },
                            style: { marginRight: '8px' },
                            on: { click: () => this.openEdit(params.row) }
                        }, '编辑'),
                        h('Button', {
                            props: { size: 'small', type: 'error' },
                            on: { click: () => this.removeUser(params.row) }
                        }, '删除')
                    ])
                }
            ]
        };
    },
    mounted() {
        this.loadUsers();
    },
    methods: {
        async loadUsers() {
            try {
                this.loading = true;
                const res = await fetchUsers();
                this.users = res.users || [];
            } catch (error) {
                this.$Message && this.$Message.error('读取用户列表失败');
            } finally {
                this.loading = false;
            }
        },
        openEdit(row) {
            this.editForm = {
                id: row.id,
                display_name: row.display_name,
                role: row.role,
                enabled: row.enabled,
                password: ''
            };
            this.editVisible = true;
        },
        async saveUser() {
            const payload = {
                display_name: this.editForm.display_name,
                role: this.editForm.role,
                enabled: this.editForm.enabled
            };
            if (this.editForm.password) {
                payload.password = this.editForm.password;
            }
            try {
                await updateUser(this.editForm.id, payload);
                this.$Message && this.$Message.success('用户已更新');
                this.loadUsers();
            } catch (error) {
                this.$Message && this.$Message.error('保存失败');
            }
        },
        removeUser(row) {
            this.$Modal.confirm({
                title: '确认删除',
                content: `确定删除用户 ${row.username} 吗？`,
                onOk: async () => {
                    try {
                        await deleteUser(row.id);
                        this.$Message && this.$Message.success('用户已删除');
                        this.loadUsers();
                    } catch (error) {
                        this.$Message && this.$Message.error('删除失败');
                    }
                }
            });
        }
    }
};
</script>

<style lang="less" scoped>
.user-page {
    width: 100%;
    height: 100%;
    padding: 24px;
    background: transparent;
    color: #1f2d3d;
    overflow: auto;
}

.page-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
}

.title {
    font-size: 22px;
    font-weight: 700;
    color: white; /* --- IGNORE --- */
    background: transparent; /* --- IGNORE --- */
}

.sub {
    margin-top: 6px;
    font-size: 13px;
    color: #64748b;
}

.user-table {
    background: #fff;
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
</style>
