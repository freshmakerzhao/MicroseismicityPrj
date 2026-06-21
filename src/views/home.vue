<template>
    <div class="home-container">
        <TechHeader
            title="冲击地压矿井微震监测智能判识冲击危险等级及区划系统"
            subtitle="MICROSEISMIC ROCKBURST RISK IDENTIFICATION PLATFORM"
            :user-name="currentUserLabel"
            :role-label="currentRoleLabel"
            @logout="handleLogout"
        >
            <template slot="left">
                <span>在线监测</span>
                <span>智能判识</span>
            </template>
            <template slot="nav">
                <TechNav
                    :items="visibleFeatureTabs"
                    :active-path="$route.path"
                    @select="goFeature"
                />
            </template>
        </TechHeader>
        <Modal
            v-model="modal"
            title="全局配置"
            :mask-closable="false"
            :loading="saving"
            @on-ok="saveConfig"
        >
            <div class="config-form">
                <div class="row-item">
                    <span class="label">输出目录</span>
                    <Input v-model="configForm.output_folder" placeholder="例如 D:/surfer_output"></Input>
                    <Button size="small" @click="chooseOutputFolder">选择</Button>
                </div>
                <div class="row-item">
                    <span class="label">上传目录</span>
                    <Input v-model="configForm.upload_folder" placeholder="例如 uploads"></Input>
                    <Button size="small" @click="chooseUploadFolder">选择</Button>
                </div>
                <div class="row-item">
                    <span class="label">上传大小限制(MB)</span>
                    <InputNumber :min="1" :max="1024" v-model="configForm.max_upload_mb"></InputNumber>
                </div>
                <div class="row-item">
                    <span class="label">Surfer 安装目录</span>
                    <Input v-model="configForm.surfer.install_dir" placeholder="例如 E:/Application_surfer11"></Input>
                    <Button size="small" @click="chooseInstallDir">选择</Button>
                </div>
                <div class="row-item">
                    <span class="label">Surfer EXE 路径</span>
                    <Input v-model="configForm.surfer.exe_path" placeholder="可选"></Input>
                    <Button size="small" @click="chooseExePath">选择</Button>
                </div>
                <div class="row-item">
                    <span class="label">色阶文件路径</span>
                    <Input v-model="configForm.surfer.clr_path" placeholder="留空则自动推断 Terrain.clr"></Input>
                    <Button size="small" @click="chooseClrPath">选择</Button>
                </div>
            </div>
        </Modal>
        <div class="page-content">
            <router-view v-if="flag" :selectRangeDate="selectRangeDate"></router-view>
        </div>
    </div>
</template>

<script>
import TechHeader from '@/components/tech/TechHeader.vue';
import TechNav from '@/components/tech/TechNav.vue';
import { getGlobalConfig, pickDirectory, pickFile, updateGlobalConfig } from "@/lib/globalConfig";
import { getCurrentUser, isAdmin, logout } from "@/lib/auth";

export default {
    name: 'home',
    components: {
        TechHeader,
        TechNav
    },
    data() {
        return {
            modal: false,
            flag: true,
            selectRangeDate: [],
            featureTabs: [
                { label: '冲击危险云图', path: '/page5' },
                // { label: '微震预警', path: '/page6' },
                // { label: '3D Viewer', path: '/page7' },
                { label: '三维井下地图', path: '/page8' },
                { label: '人员管理', path: '/users', adminOnly: true },
                // { label: '功能B', path: '/page1' },
                // { label: '功能C', path: '/page2' }
            ],
            currentUser: null,
            configForm: {
                output_folder: '',
                upload_folder: '',
                max_upload_mb: 30,
                surfer: {
                    install_dir: '',
                    exe_path: '',
                    clr_path: ''
                }
            },
            saving: false,
            resizeFn: null
        }
    },
    computed: {
        visibleFeatureTabs() {
            return this.featureTabs.filter((item) => !item.adminOnly || isAdmin());
        },
        currentUserLabel() {
            if (!this.currentUser) {
                return '未登录';
            }
            return this.currentUser.display_name || this.currentUser.username;
        },
        currentRoleLabel() {
            return this.currentUser && this.currentUser.role === 'admin' ? '管理员' : '用户';
        }
    },
    mounted() {
        this.currentUser = getCurrentUser();
        this.loadConfig();
        this.$root.$on('open-global-config', this.openConfigModal);
    },
    beforeDestroy() {
        this.$root.$off('open-global-config', this.openConfigModal);
    },
    methods: {
        goFeature(path) {
            if (this.$route.path !== path) {
                this.$router.push(path);
            }
        },
        async handleLogout() {
            await logout();
            this.$router.replace('/login');
        },
        async loadConfig() {
            try {
                const res = await getGlobalConfig();
                const raw = res.raw || {};
                this.configForm.output_folder = raw.output_folder || '';
                this.configForm.upload_folder = raw.upload_folder || '';
                this.configForm.max_upload_mb = raw.max_upload_mb || 30;
                this.configForm.surfer.install_dir = (raw.surfer && raw.surfer.install_dir) || '';
                this.configForm.surfer.exe_path = (raw.surfer && raw.surfer.exe_path) || '';
                this.configForm.surfer.clr_path = (raw.surfer && raw.surfer.clr_path) || '';
            } catch (error) {
                if (this.$Message) {
                    this.$Message.error('读取全局配置失败');
                }
            }
        },
        openConfigModal() {
            this.loadConfig();
            this.modal = true;
        },
        async chooseOutputFolder() {
            const res = await pickDirectory('选择输出目录', this.configForm.output_folder || '');
            if (res.path) {
                this.configForm.output_folder = res.path;
            }
        },
        async chooseUploadFolder() {
            const res = await pickDirectory('选择上传目录', this.configForm.upload_folder || '');
            if (res.path) {
                this.configForm.upload_folder = res.path;
            }
        },
        async chooseInstallDir() {
            const res = await pickDirectory('选择 Surfer 安装目录', this.configForm.surfer.install_dir || '');
            if (res.path) {
                this.configForm.surfer.install_dir = res.path;
            }
        },
        async chooseExePath() {
            const res = await pickFile(
                '选择 Surfer EXE 文件',
                this.configForm.surfer.install_dir || '',
                [['Executable Files', '*.exe'], ['All Files', '*.*']]
            );
            if (res.path) {
                this.configForm.surfer.exe_path = res.path;
            }
        },
        async chooseClrPath() {
            const res = await pickFile(
                '选择色阶文件',
                this.configForm.surfer.install_dir || '',
                [['Color Scale Files', '*.clr'], ['All Files', '*.*']]
            );
            if (res.path) {
                this.configForm.surfer.clr_path = res.path;
            }
        },
        async saveConfig() {
            const payload = {
                output_folder: this.configForm.output_folder,
                upload_folder: this.configForm.upload_folder,
                max_upload_mb: this.configForm.max_upload_mb,
                surfer: {
                    install_dir: this.configForm.surfer.install_dir,
                    exe_path: this.configForm.surfer.exe_path,
                    clr_path: this.configForm.surfer.clr_path
                }
            };

            try {
                this.saving = true;
                await updateGlobalConfig(payload);
                if (this.$Message) {
                    this.$Message.success('配置已保存，后续上传立即按新配置执行');
                }
            } catch (error) {
                if (this.$Message) {
                    this.$Message.error('保存配置失败');
                }
            } finally {
                this.saving = false;
            }
        },
    },
}
</script>

<style lang="less" scoped>
.home-container {
    height: 100%;
    width: 100%;
    position: relative;
    display: flex;
    flex-direction: column;
    background:
        radial-gradient(circle at 50% 20%, rgba(25, 91, 142, 0.38) 0%, rgba(3, 20, 46, 0.95) 42%, #020814 100%);
    overflow: hidden;

    &::before {
        content: "";
        position: absolute;
        inset: 0;
        z-index: 0;
        background: url("../assets/threemaps/images/bg.png") center / cover no-repeat;
        opacity: 0.42;
        pointer-events: none;
    }

    &::after {
        content: "";
        position: absolute;
        inset: 0;
        z-index: 0;
        background-image:
            linear-gradient(rgba(48, 220, 255, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(48, 220, 255, 0.08) 1px, transparent 1px);
        background-size: 44px 44px;
        mask-image: linear-gradient(to bottom, transparent 0%, #000 18%, #000 100%);
        pointer-events: none;
    }
}

.settings-bar {
    display: flex;
    align-items: center;
    gap: 10px;

    .filter-item {
        color: #75deef;
        font-size: 14px;
        padding: 8px 16px;
        cursor: pointer;
        border: 1px solid transparent;
        border-radius: 4px;
        transition: all 0.3s;

        &:hover {
            border-color: #264e5e;
            background: rgba(38, 78, 94, 0.3);
        }

        &.active {
            border-color: #75deef;
            background: rgba(117, 222, 239, 0.1);
        }

        &.setting-icon {
            font-size: 18px;
            padding: 8px 12px;
        }
    }
}

.config-form {
    display: flex;
    flex-direction: column;
    gap: 12px;
    text-align: left;

    .row-item {
        display: flex;
        align-items: center;
        gap: 12px;

        .label {
            width: 140px;
            color: #75deef;
            flex-shrink: 0;
        }
    }
}

.page-content {
    position: relative;
    z-index: 2;
    flex: 1;
    height: calc(100% - 120px);
    overflow: hidden;
}

// Modal样式覆盖
.ivu-modal {
    .ivu-modal-content {
        background: #071332;

        .ivu-modal-header {
            border-bottom: 1px solid #1a3c58;

            .ivu-modal-header-inner {
                color: #75deef;
            }
        }

        .ivu-modal-body {
            text-align: center;

            .ivu-icon {
                color: #75deef
            }

            .ivu-modal-confirm-body {
                padding-left: 0;
                color: #75deef
            }

            .ivu-input {
                background-color: rgba(0, 0, 0, 0);
                border: 1px solid #1a3c58;
                color: #75deef;

                &::-webkit-input-placeholder {
                    color: #75deef;
                }

                &::-moz-placeholder {
                    color: #75deef;
                }

                &::-moz-placeholder {
                    color: #75deef;
                }

                &::-ms-input-placeholder {
                    color: #75deef;
                }
            }

            .ivu-picker-panel-body {
                background: #071332;

                .ivu-date-picker-header {
                    color: #75deef;
                    border-bottom: 1px solid #1a3c58
                }

                .ivu-date-picker-cells-cell {
                    color: #75deef;

                    &:hover em {
                        background: #1a3c58;
                    }
                }

                .ivu-date-picker-cells-cell-disabled {
                    background: rgba(0, 0, 0, 0);
                    color: #eee
                }

                .ivu-date-picker-cells-focused em {
                    box-shadow: 0 0 0 1px #1a3c58 inset;

                    &::after {
                        background: #1a3c58;
                    }
                }
            }
        }

        .ivu-modal-footer {
            border-top: 1px solid #1a3c58;

            .ivu-btn-primary {
                color: #75deef;
                background: #1a3c58;
            }

            .ivu-btn-text {
                color: #ddd;

                &:hover {
                    color: #75deef;
                    background: #1a3c58;
                }
            }
        }
    }
}
</style>
