<template>
    <div class="home-container">
        <div class="header">
            <div class="header-title">
                大数据可视化平台
            </div>
            <div class="header-right">
                <div class="time-filter">
                    <span 
                        class="filter-item" 
                        :class="{ active: activeName === 'day' }"
                        @click="handleSelect('day')"
                    >昨日</span>
                    <span 
                        class="filter-item" 
                        :class="{ active: activeName === 'week' }"
                        @click="handleSelect('week')"
                    >近一周</span>
                    <span 
                        class="filter-item" 
                        :class="{ active: activeName === 'month' }"
                        @click="handleSelect('month')"
                    >近一月</span>
                    <span class="filter-item setting-icon" @click="modal = true">
                        <i class="ivu-icon ivu-icon-ios-settings-outline"></i>
                    </span>
                </div>
            </div>
        </div>
        <Modal
            v-model="modal"
            title="选择时间"
            :mask-closable="false"
            @on-ok="getMonthBetween(startTime, endTime)"
        >
            <DatePicker 
                @on-change="pickStartDate" 
                :options="optionStart" 
                type="date" 
                placeholder="选择开始日期"
                style="width: 200px"
            ></DatePicker>
            <span style="padding: 0 20px; color: #75deef">至</span>
            <DatePicker 
                @on-change="pickEndDate" 
                :options="optionEnd" 
                type="date" 
                placeholder="选择结束日期"
                style="width: 200px"
            ></DatePicker>
        </Modal>
        <div class="page-content">
            <router-view v-if="flag" :selectRangeDate="selectRangeDate"></router-view>
        </div>
    </div>
</template>

<script>
export default {
    name: 'home',
    data() {
        return {
            activeName: 'month',
            modal: false,
            flag: false,
            selectRangeDate: [],
            startTime: '',
            endTime: '',
            optionStart: {
                disabledDate(date) {
                    return date && date.valueOf() > Date.now() - 86400000;
                }
            },
            optionEnd: {},
            resizeFn: null
        }
    },
    mounted() {
        this.handleSelect(this.activeName);
    },
    methods: {
        pickStartDate(date) {
            this.startTime = date;
            this.optionEnd = {
                disabledDate(d) {
                    return d && d.valueOf() < new Date(date).valueOf() - 86400000;
                }
            }
        },
        pickEndDate(date) {
            this.endTime = date;
        },
        getMonthBetween(start, end) {
            this.selectRangeDate = [];
            let s = start.split("-");
            let e = end.split("-");
            let date = new Date();
            let min = date.setFullYear(s[0], s[1] - 1);
            let max = date.setFullYear(e[0], e[1] - 1);
            let curr = min;
            while (curr <= max) {
                var month = curr.getMonth();
                var arr = [curr.getFullYear(), month + 1];
                this.selectRangeDate.push(arr);
                curr.setMonth(month + 1);
            }
        },
        getDays(day) {
            let arr = [];
            for (let i = -day; i < 0; i++) {
                let today = new Date();
                let targetday_milliseconds = today.getTime() + 1000 * 60 * 60 * 24 * i;
                today.setTime(targetday_milliseconds);
                let tYear = today.getFullYear();
                let tMonth = today.getMonth();
                let tDate = today.getDate();
                let date = [tYear, tMonth + 1, tDate];
                arr.push(date);
            }
            return arr
        },
        handleSelect(name) {
            this.activeName = name;
            switch (name) {
                case 'day':
                    this.selectRangeDate = this.getDays(1);
                    this.flag = true;
                    break;
                case 'week':
                    this.selectRangeDate = this.getDays(7);
                    this.flag = true;
                    break;
                case 'month':
                    this.selectRangeDate = this.getDays(30);
                    this.flag = true;
                    break;
                case 'filter':
                    this.modal = true;
                    break;
                default:
                    break;
            }
        }
    },
}
</script>

<style lang="less" scoped>
.home-container {
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
    background: #03044A;
}

.header {
    height: 80px;
    background: linear-gradient(180deg, #0a0f3a 0%, #03044a 100%);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 40px;
    border-bottom: 1px solid #1a3c58;
    flex-shrink: 0;

    &-title {
        color: #75deef;
        font-size: 32px;
        font-weight: bold;
        letter-spacing: 8px;
        text-shadow: 0 0 20px rgba(117, 222, 239, 0.5);
    }

    &-right {
        display: flex;
        align-items: center;
    }
}

.time-filter {
    display: flex;
    align-items: center;
    gap: 20px;

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

.page-content {
    flex: 1;
    height: calc(100% - 80px);
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