/**
 * 代码评审反馈插件
 * 用途：为评审报告添加反馈收集功能
 * 功能：标记问题有效性、添加备注、统计汇总、上报数据
 */
(function () {
    'use strict';

    // ============================================================================
    // 插件配置
    // ============================================================================
    const CONFIG = {
        apiEndpoint: 'http://agent-fe.bcc-szzj.baidu.com:8001/api/data/collect',
        timeout: 10000
    };

    // ============================================================================
    // 数据管理器
    // ============================================================================
    const feedbackManager = {
        data: new Map(),

        /**
         * 初始化：扫描所有问题并建立数据结构
         */
        init() {
            document.querySelectorAll('.issue').forEach((issue, index) => {
                const issueId = `issue-${index}`;
                issue.dataset.issueId = issueId;

                const h3 = issue.querySelector('h3');
                const title = h3 ? h3.textContent : '';
                const ruleId = this.extractRuleId(title);
                const priority = this.getPriorityFromParent(issue);
                const location = this.extractLocation(issue);

                this.data.set(issueId, {
                    issueId,
                    ruleId,
                    priority,
                    title: this.cleanTitle(title),
                    location,
                    isValid: null,
                    comment: '',
                    feedbackTime: null
                });
            });

            this.updateStats();
        },

        /**
         * 从标题中提取规则ID
         */
        extractRuleId(title) {
            const match = title.match(/\[([^\]]+)\]/);
            return match ? match[1] : '';
        },

        /**
         * 清理标题（移除规则ID部分）
         */
        cleanTitle(title) {
            return title.replace(/\s*\[.*?\]\s*$/, '').trim();
        },

        /**
         * 根据父容器 data-priority 判断优先级
         */
        getPriorityFromParent(issueElement) {
            return issueElement.parentElement?.dataset.priority || 'Unknown';
        },

        /**
         * 提取问题位置信息
         */
        extractLocation(issueElement) {
            const paragraphs = issueElement.querySelectorAll('p');
            for (let p of paragraphs) {
                const strong = p.querySelector('strong');
                if (strong && strong.textContent.includes('位置')) {
                    return p.textContent.replace(/位置[：:]\s*/, '').trim();
                }
            }
            return '';
        },

        /**
         * 设置反馈
         */
        setFeedback(issueId, isValid, comment = '') {
            const data = this.data.get(issueId);
            if (data) {
                data.isValid = isValid;
                data.comment = comment;
                data.feedbackTime = new Date().toISOString();
                this.updateStats();
            }
        },

        /**
         * 更新统计数字
         */
        updateStats() {
            const total = this.data.size;
            let marked = 0;
            let valid = 0;
            let invalid = 0;

            this.data.forEach(item => {
                if (item.isValid !== null) {
                    marked++;
                    item.isValid ? valid++ : invalid++;
                }
            });

            const totalEl = document.getElementById('totalCount');
            const markedEl = document.getElementById('markedCount');
            const validEl = document.getElementById('validCount');
            const invalidEl = document.getElementById('invalidCount');

            if (totalEl) {
                totalEl.textContent = total;
            }
            if (markedEl) {
                markedEl.textContent = marked;
            }
            if (validEl) {
                validEl.textContent = valid;
            }
            if (invalidEl) {
                invalidEl.textContent = invalid;
            }
        },

        getReportMeta() {
            return {
                reportId: `review-${Date.now()}`,
                reportTime: this.getMetaValue('review-time-value'),
                branch: this.getMetaValue('branch-value'),
                commit: this.getMetaValue('commit-value'),
                pageUrl: window.location.href
            };
        },

        collectReport() {
            const feedbacks = [];
            let validCount = 0;
            let invalidCount = 0;
            this.data.forEach(item => {
                if (item.isValid !== null) {
                    feedbacks.push({...item});
                    item.isValid ? validCount++ : invalidCount++;
                }
            });

            const total = this.data.size;
            const marked = feedbacks.length;

            return {
                reportMeta: {
                    ...this.getReportMeta(),
                    feedbackTime: new Date().toLocaleString('zh-CN', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    })
                },
                summary: {
                    totalCount: total,
                    markedCount: marked,
                    validCount,
                    invalidCount,
                    unmarkedCount: total - marked
                },
                feedbacks
            };
        },

        /**
         * 获取元数据值
         */
        getMetaValue(elementId) {
            const el = document.getElementById(elementId);
            return el ? el.textContent.trim() : '';
        }
    };

    // ============================================================================
    // UI 注入
    // ============================================================================
    const UI = {
        /**
         * 注入悬浮统计窗
         */
        injectFeedbackPanel() {
            const panel = document.createElement('div');
            panel.className = 'feedback-panel';
            panel.innerHTML = `
        <h3>📊 反馈统计</h3>
        <div class="stats">
          <div class="stat-item">
            <span class="stat-label">评审总数：</span>
            <span class="stat-value" id="totalCount">0</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已标记：</span>
            <span class="stat-value" id="markedCount">0</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">有效：</span>
            <span class="stat-value valid" id="validCount">0</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">无效：</span>
            <span class="stat-value invalid" id="invalidCount">0</span>
          </div>
        </div>
        <button class="submit-btn" id="submitFeedback">上报反馈</button>
        <div class="submit-status" id="submitStatus"></div>
      `;
            document.body.appendChild(panel);
        },

        /**
         * 为每个问题注入反馈区域
         */
        injectFeedbackSections() {
            document.querySelectorAll('.issue').forEach(issue => {
                const feedbackSection = document.createElement('div');
                feedbackSection.className = 'feedback-section';
                feedbackSection.innerHTML = `
          <div class="feedback-buttons">
            <button class="feedback-btn valid-btn" data-feedback="valid">✅ 有效</button>
            <button class="feedback-btn invalid-btn" data-feedback="invalid">❌ 无效</button>
          </div>
          <textarea class="feedback-comment" placeholder="备注说明（可选）..." rows="2"></textarea>
        `;
                issue.appendChild(feedbackSection);
            });
        }
    };

    // ============================================================================
    // 埋点上报（统一出口）
    // ============================================================================
    const Tracker = {
        sendDisplayEvent() {
            const data = {
                ...feedbackManager.getReportMeta(),
                displayTime: new Date().toISOString()
            };

            return fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({bucket: 'cr-display', data})
            });
        },

        sendFeedbackEvent(data, options = {}) {
            return fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({bucket: 'cr-feedback', data}),
                signal: options.signal
            });
        }
    };

    // ============================================================================
    // 事件处理
    // ============================================================================
    const EventHandler = {
        /**
         * 绑定所有事件
         */
        bindAll() {
            this.bindFeedbackButtons();
            this.bindCommentInputs();
            this.bindSubmitButton();
        },

        /**
         * 绑定反馈按钮事件（事件委托）
         */
        bindFeedbackButtons() {
            document.addEventListener('click', (e) => {
                const btn = e.target.closest('.feedback-btn');
                if (!btn) {
                    return;
                }

                const issue = btn.closest('.issue');
                const issueId = issue.dataset.issueId;
                const isValid = btn.dataset.feedback === 'valid';
                const textarea = issue.querySelector('.feedback-comment');

                const allBtns = issue.querySelectorAll('.feedback-btn');
                allBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                feedbackManager.setFeedback(issueId, isValid, textarea.value);
            });
        },

        /**
         * 绑定备注输入框事件（事件委托）
         */
        bindCommentInputs() {
            document.addEventListener('input', (e) => {
                const textarea = e.target.closest('.feedback-comment');
                if (!textarea) {
                    return;
                }

                const issue = textarea.closest('.issue');
                const issueId = issue.dataset.issueId;
                const data = feedbackManager.data.get(issueId);

                if (data && data.isValid !== null) {
                    data.comment = textarea.value;
                }
            });
        },

        /**
         * 绑定上报按钮事件
         */
        bindSubmitButton() {
            const btn = document.getElementById('submitFeedback');
            if (!btn) {
                return;
            }

            btn.addEventListener('click', async () => {
                await this.handleSubmit();
            });
        },

        /**
         * 处理上报
         */
        async handleSubmit() {
            const btn = document.getElementById('submitFeedback');

            const report = feedbackManager.collectReport();

            if (report.feedbacks.length === 0) {
                this.showStatus('error', '请至少标记一条评审反馈');
                return;
            }

            btn.disabled = true;
            this.showStatus('', '正在上报...');

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), CONFIG.timeout);

            try {
                const response = await Tracker.sendFeedbackEvent(report, {
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (response.ok) {
                    // 上报成功：保持禁用状态，修改按钮文本
                    btn.textContent = '✅ 上报成功';
                    btn.classList.add('submitted');
                    this.showStatus('success', `已提交 ${report.feedbacks.length} 条反馈`);
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            } catch (error) {
                clearTimeout(timeoutId);
                // 上报失败：重新启用按钮，允许用户重试
                btn.disabled = false;
                const message = error.name === 'AbortError' ? '请求超时，请重试' : error.message;
                this.showStatus('error', `❌ 上报失败: ${message}`);
                console.error('上报失败:', error);
            }
        },

        /**
         * 显示状态消息
         */
        showStatus(type, message) {
            const status = document.getElementById('submitStatus');
            if (!status) {
                return;
            }

            status.className = `submit-status ${type}`;
            status.textContent = message;
        }
    };

    // ============================================================================
    // 插件初始化
    // ============================================================================
    function init() {
        console.log('[反馈插件] 正在初始化...');

        UI.injectFeedbackPanel();
        UI.injectFeedbackSections();
        feedbackManager.init();
        EventHandler.bindAll();
        Tracker.sendDisplayEvent();

        console.log('[反馈插件] 初始化完成');
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
