/**
 * 실시간 백그라운드 작업 토스트 알림 시스템
 * - 백그라운드 작업 진행 상황을 실시간으로 표시
 * - 페이지 이동 시에도 알림 유지
 * - LocalStorage를 통한 작업 상태 추적
 */

class BackgroundTaskToast {
    constructor(apiBase, token) {
        this.apiBase = apiBase;
        this.token = token;
        this.tasks = new Map(); // taskId -> taskData
        this.pollInterval = 3000; // 3초마다 폴링
        this.activePolls = new Map(); // taskId -> intervalId

        this.init();
    }

    init() {
        // 토스트 컨테이너 생성
        this.createToastContainer();

        // LocalStorage에서 진행 중인 작업 복원
        this.restoreActiveTasks();

        // 페이지 언로드 시 상태 저장
        window.addEventListener('beforeunload', () => {
            this.saveActiveTasks();
        });
    }

    createToastContainer() {
        if (document.getElementById('bgTaskToastContainer')) return;

        const container = document.createElement('div');
        container.id = 'bgTaskToastContainer';
        container.innerHTML = `
            <style>
                #bgTaskToastContainer {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 999999;
                    max-width: 400px;
                    pointer-events: none;
                }

                .bg-toast {
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    margin-bottom: 12px;
                    padding: 16px;
                    pointer-events: all;
                    animation: slideIn 0.3s ease-out;
                    border-left: 4px solid #667eea;
                    min-width: 350px;
                }

                .bg-toast.success {
                    border-left-color: #10b981;
                }

                .bg-toast.error {
                    border-left-color: #ef4444;
                }

                .bg-toast.processing {
                    border-left-color: #667eea;
                }

                @keyframes slideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }

                @keyframes slideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                }

                .bg-toast.removing {
                    animation: slideOut 0.3s ease-out;
                }

                .bg-toast-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                }

                .bg-toast-title {
                    font-weight: 600;
                    color: #333;
                    font-size: 14px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .bg-toast-close {
                    background: none;
                    border: none;
                    font-size: 20px;
                    cursor: pointer;
                    color: #999;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 4px;
                    transition: all 0.2s;
                }

                .bg-toast-close:hover {
                    background: #f0f0f0;
                    color: #333;
                }

                .bg-toast-body {
                    font-size: 13px;
                    color: #666;
                    margin-bottom: 12px;
                }

                .bg-toast-progress {
                    height: 6px;
                    background: #e0e0e0;
                    border-radius: 3px;
                    overflow: hidden;
                    margin-bottom: 8px;
                }

                .bg-toast-progress-bar {
                    height: 100%;
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    transition: width 0.3s ease;
                    border-radius: 3px;
                }

                .bg-toast-progress-bar.success {
                    background: linear-gradient(90deg, #10b981, #059669);
                }

                .bg-toast-progress-bar.error {
                    background: linear-gradient(90deg, #ef4444, #dc2626);
                }

                .bg-toast-status {
                    font-size: 12px;
                    color: #999;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .bg-toast-time {
                    font-size: 11px;
                    color: #bbb;
                }

                .bg-toast-spinner {
                    display: inline-block;
                    width: 14px;
                    height: 14px;
                    border: 2px solid #f3f3f3;
                    border-top: 2px solid #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                .bg-toast-actions {
                    display: flex;
                    gap: 8px;
                    margin-top: 12px;
                }

                .bg-toast-btn {
                    padding: 6px 12px;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                    font-weight: 500;
                }

                .bg-toast-btn-primary {
                    background: #667eea;
                    color: white;
                }

                .bg-toast-btn-primary:hover {
                    background: #5568d3;
                }

                .bg-toast-btn-secondary {
                    background: #f0f0f0;
                    color: #333;
                }

                .bg-toast-btn-secondary:hover {
                    background: #e0e0e0;
                }
            </style>
        `;
        document.body.appendChild(container);
    }

    getToastContainer() {
        return document.getElementById('bgTaskToastContainer');
    }

    addTask(taskId, title, description = '') {
        const taskData = {
            taskId,
            title,
            description,
            status: 'processing',
            progress: 0,
            currentStep: '처리 중...',
            startTime: Date.now(),
            error: null
        };

        this.tasks.set(taskId, taskData);
        this.renderToast(taskData);
        this.startPolling(taskId);
        this.saveActiveTasks();
    }

    renderToast(taskData) {
        const container = this.getToastContainer();
        const existingToast = document.getElementById(`toast-${taskData.taskId}`);

        if (existingToast) {
            // 기존 토스트 업데이트
            this.updateToast(taskData);
            return;
        }

        // 새 토스트 생성
        const toast = document.createElement('div');
        toast.id = `toast-${taskData.taskId}`;
        toast.className = `bg-toast ${taskData.status}`;

        const icon = this.getStatusIcon(taskData.status);
        const elapsed = this.formatElapsedTime(Date.now() - taskData.startTime);

        toast.innerHTML = `
            <div class="bg-toast-header">
                <div class="bg-toast-title">
                    ${icon}
                    <span>${taskData.title}</span>
                </div>
                <button class="bg-toast-close" onclick="backgroundTaskToast.closeToast('${taskData.taskId}')">&times;</button>
            </div>
            <div class="bg-toast-body">${taskData.description || taskData.currentStep}</div>
            <div class="bg-toast-progress">
                <div class="bg-toast-progress-bar" style="width: ${taskData.progress}%"></div>
            </div>
            <div class="bg-toast-status">
                <span>${taskData.currentStep}</span>
                <span class="bg-toast-time">${elapsed}</span>
            </div>
        `;

        container.appendChild(toast);
    }

    updateToast(taskData) {
        const toast = document.getElementById(`toast-${taskData.taskId}`);
        if (!toast) return;

        toast.className = `bg-toast ${taskData.status}`;

        const icon = this.getStatusIcon(taskData.status);
        const elapsed = this.formatElapsedTime(Date.now() - taskData.startTime);
        const progressBar = toast.querySelector('.bg-toast-progress-bar');
        const statusText = toast.querySelector('.bg-toast-status span');
        const timeText = toast.querySelector('.bg-toast-time');
        const titleIcon = toast.querySelector('.bg-toast-title');
        const bodyText = toast.querySelector('.bg-toast-body');

        if (progressBar) {
            progressBar.style.width = `${taskData.progress}%`;
            progressBar.className = `bg-toast-progress-bar ${taskData.status}`;
        }

        if (statusText) {
            statusText.textContent = taskData.currentStep;
        }

        if (timeText) {
            timeText.textContent = elapsed;
        }

        if (titleIcon) {
            titleIcon.innerHTML = `${icon}<span>${taskData.title}</span>`;
        }

        if (bodyText) {
            bodyText.textContent = taskData.error || taskData.description || taskData.currentStep;
        }

        // 완료 또는 실패 시 액션 버튼 추가
        if (taskData.status === 'completed' || taskData.status === 'error') {
            let actionsDiv = toast.querySelector('.bg-toast-actions');
            if (!actionsDiv) {
                actionsDiv = document.createElement('div');
                actionsDiv.className = 'bg-toast-actions';

                if (taskData.status === 'completed') {
                    actionsDiv.innerHTML = `
                        <button class="bg-toast-btn bg-toast-btn-primary" onclick="window.location.href='./policy-management.html'">
                            정책 보기
                        </button>
                        <button class="bg-toast-btn bg-toast-btn-secondary" onclick="backgroundTaskToast.closeToast('${taskData.taskId}')">
                            닫기
                        </button>
                    `;
                } else {
                    actionsDiv.innerHTML = `
                        <button class="bg-toast-btn bg-toast-btn-secondary" onclick="backgroundTaskToast.closeToast('${taskData.taskId}')">
                            닫기
                        </button>
                    `;
                }

                toast.appendChild(actionsDiv);
            }
        }
    }

    getStatusIcon(status) {
        switch (status) {
            case 'processing':
                return '<span class="bg-toast-spinner"></span>';
            case 'completed':
                return '✅';
            case 'error':
                return '❌';
            default:
                return '⏳';
        }
    }

    formatElapsedTime(ms) {
        const seconds = Math.floor(ms / 1000);
        if (seconds < 60) return `${seconds}초 전`;
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}분 전`;
        const hours = Math.floor(minutes / 60);
        return `${hours}시간 전`;
    }

    async startPolling(taskId) {
        // 이미 폴링 중이면 중단
        if (this.activePolls.has(taskId)) {
            return;
        }

        const poll = async () => {
            try {
                const response = await fetch(`${this.apiBase}/api/policies/tasks/${taskId}/status`, {
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                });

                if (!response.ok) {
                    throw new Error('상태 조회 실패');
                }

                const result = await response.json();

                if (result.success && result.data) {
                    const task = result.data;
                    const taskData = this.tasks.get(taskId);

                    if (!taskData) return;

                    // 상태 업데이트
                    taskData.status = task.status;
                    taskData.progress = task.progress || 0;
                    taskData.currentStep = task.current_step || taskData.currentStep;
                    taskData.error = task.error || null;

                    this.updateToast(taskData);

                    // 완료 또는 실패 시 폴링 중지
                    if (task.status === 'completed' || task.status === 'failed') {
                        this.stopPolling(taskId);

                        // 완료/실패 상태를 최종으로 저장
                        if (task.status === 'completed') {
                            taskData.status = 'completed';
                            taskData.progress = 100;
                            taskData.currentStep = '완료!';
                        } else {
                            taskData.status = 'error';
                            taskData.currentStep = '실패';
                        }

                        this.updateToast(taskData);
                        this.saveActiveTasks();

                        // 10초 후 자동으로 완료된 토스트 제거
                        setTimeout(() => {
                            this.closeToast(taskId);
                        }, 10000);
                    } else {
                        this.saveActiveTasks();
                    }
                }
            } catch (error) {
                console.error(`Task ${taskId} polling error:`, error);
            }
        };

        // 즉시 한 번 실행
        await poll();

        // 주기적으로 실행
        const intervalId = setInterval(poll, this.pollInterval);
        this.activePolls.set(taskId, intervalId);
    }

    stopPolling(taskId) {
        const intervalId = this.activePolls.get(taskId);
        if (intervalId) {
            clearInterval(intervalId);
            this.activePolls.delete(taskId);
        }
    }

    closeToast(taskId) {
        const toast = document.getElementById(`toast-${taskId}`);
        if (toast) {
            toast.classList.add('removing');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }

        this.stopPolling(taskId);
        this.tasks.delete(taskId);
        this.saveActiveTasks();
    }

    saveActiveTasks() {
        const activeTasks = [];
        this.tasks.forEach((taskData, taskId) => {
            // 완료되지 않은 작업만 저장
            if (taskData.status === 'processing') {
                activeTasks.push({
                    taskId: taskData.taskId,
                    title: taskData.title,
                    description: taskData.description,
                    status: taskData.status,
                    progress: taskData.progress,
                    currentStep: taskData.currentStep,
                    startTime: taskData.startTime
                });
            }
        });

        localStorage.setItem('bgActiveTasks', JSON.stringify(activeTasks));
    }

    restoreActiveTasks() {
        try {
            const saved = localStorage.getItem('bgActiveTasks');
            if (!saved) return;

            const activeTasks = JSON.parse(saved);

            activeTasks.forEach(taskData => {
                // 24시간 이상 지난 작업은 무시
                const elapsed = Date.now() - taskData.startTime;
                if (elapsed > 24 * 60 * 60 * 1000) return;

                this.tasks.set(taskData.taskId, taskData);
                this.renderToast(taskData);
                this.startPolling(taskData.taskId);
            });

        } catch (error) {
            console.error('Failed to restore active tasks:', error);
            localStorage.removeItem('bgActiveTasks');
        }
    }

    clearAll() {
        this.tasks.forEach((_, taskId) => {
            this.stopPolling(taskId);
        });
        this.tasks.clear();
        this.saveActiveTasks();

        const container = this.getToastContainer();
        if (container) {
            const toasts = container.querySelectorAll('.bg-toast');
            toasts.forEach(toast => {
                toast.classList.add('removing');
                setTimeout(() => toast.remove(), 300);
            });
        }
    }
}

// 전역 인스턴스 생성 (모든 페이지에서 사용)
let backgroundTaskToast = null;

function initBackgroundTaskToast() {
    const API_BASE = 'http://127.0.0.1:8000';
    const token = localStorage.getItem('auth_token');

    if (!token) return null;

    if (!backgroundTaskToast) {
        backgroundTaskToast = new BackgroundTaskToast(API_BASE, token);
    }

    return backgroundTaskToast;
}

// 페이지 로드 시 자동 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBackgroundTaskToast);
} else {
    initBackgroundTaskToast();
}
