/**
 * 백그라운드 작업 알림 시스템
 * 우측 하단에 토스트 알림 표시
 */

class NotificationManager {
    constructor() {
        this.container = null;
        this.notifications = new Map();
        this.storageKey = 'guardcap_notifications';
        this.init();
        this.restoreNotifications();
    }

    init() {
        // 알림 컨테이너 생성
        if (!document.getElementById('notification-container')) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 400px;
            `;
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('notification-container');
        }
    }

    /**
     * localStorage에서 알림 복원
     */
    restoreNotifications() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                const notifications = JSON.parse(stored);
                notifications.forEach(notif => {
                    this.show(
                        notif.id,
                        notif.title,
                        notif.message,
                        notif.type,
                        0, // 자동으로 닫히지 않음
                        notif.progress
                    );
                });
            }
        } catch (e) {
            console.error('알림 복원 실패:', e);
        }
    }

    /**
     * localStorage에 알림 저장
     */
    saveNotifications() {
        try {
            const notifications = [];
            this.notifications.forEach((element, id) => {
                const titleEl = element.querySelector('.notification-title');
                const messageEl = element.querySelector('.notification-message');
                const progressBar = element.querySelector('.notification-progress-bar');

                const notif = {
                    id: id,
                    title: titleEl ? titleEl.textContent : '',
                    message: messageEl ? messageEl.textContent : '',
                    type: element.className.split(' ').find(c => c.startsWith('notification-'))?.replace('notification-', '') || 'info',
                    progress: progressBar ? parseInt(progressBar.style.width) || 0 : 0
                };

                notifications.push(notif);
            });

            localStorage.setItem(this.storageKey, JSON.stringify(notifications));
        } catch (e) {
            console.error('알림 저장 실패:', e);
        }
    }

    /**
     * 알림 표시
     * @param {string} id - 알림 고유 ID
     * @param {string} title - 제목
     * @param {string} message - 메시지
     * @param {string} type - success, error, info, warning, processing
     * @param {number} duration - 표시 시간 (ms), 0이면 자동으로 닫히지 않음
     * @param {number} initialProgress - 초기 진행률 (복원 시 사용)
     */
    show(id, title, message, type = 'info', duration = 5000, initialProgress = 0) {
        // 기존 알림이 있으면 제거
        this.remove(id, false); // localStorage는 업데이트하지 않음

        const notification = document.createElement('div');
        notification.id = `notification-${id}`;
        notification.className = `notification notification-${type}`;

        const icons = {
            success: '✅',
            error: '❌',
            info: 'ℹ️',
            warning: '⚠️',
            processing: '⏳'
        };

        const icon = icons[type] || icons.info;

        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-header">
                    <span class="notification-icon">${icon}</span>
                    <span class="notification-title">${title}</span>
                    <button class="notification-close" onclick="notificationManager.remove('${id}', true)">×</button>
                </div>
                <div class="notification-message">${message}</div>
                ${type === 'processing' ? `
                    <div class="notification-progress">
                        <div class="notification-progress-bar" id="progress-${id}" style="width: ${initialProgress}%"></div>
                    </div>
                ` : ''}
            </div>
        `;

        this.container.appendChild(notification);
        this.notifications.set(id, notification);

        // 애니메이션
        setTimeout(() => {
            notification.classList.add('notification-show');
        }, 10);

        // localStorage에 저장 (모든 타입)
        this.saveNotifications();

        // 자동 닫기는 하지 않음 (모든 알림은 X 버튼으로만 닫기)
    }

    /**
     * 진행률 업데이트
     * @param {string} id - 알림 ID
     * @param {number} progress - 진행률 (0-100)
     */
    updateProgress(id, progress) {
        const progressBar = document.getElementById(`progress-${id}`);
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            // 진행률 업데이트 시 localStorage에 저장
            this.saveNotifications();
        }
    }

    /**
     * 메시지 업데이트
     * @param {string} id - 알림 ID
     * @param {string} message - 새 메시지
     */
    updateMessage(id, message) {
        const notification = document.getElementById(`notification-${id}`);
        if (notification) {
            const messageEl = notification.querySelector('.notification-message');
            if (messageEl) {
                messageEl.textContent = message;
                // 메시지 업데이트 시 localStorage에 저장
                this.saveNotifications();
            }
        }
    }

    /**
     * 알림 제거
     * @param {string} id - 알림 ID
     * @param {boolean} updateStorage - localStorage 업데이트 여부
     */
    remove(id, updateStorage = true) {
        const notification = document.getElementById(`notification-${id}`);
        if (notification) {
            notification.classList.remove('notification-show');
            notification.classList.add('notification-hide');

            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                this.notifications.delete(id);

                // localStorage 업데이트
                if (updateStorage) {
                    this.saveNotifications();
                }
            }, 300);
        }
    }

    /**
     * 모든 알림 제거
     */
    clearAll() {
        this.notifications.forEach((_, id) => {
            this.remove(id, false);
        });
        // 모든 알림 삭제 후 localStorage 한번에 업데이트
        this.saveNotifications();
    }
}

// CSS 스타일 추가
const style = document.createElement('style');
style.textContent = `
.notification {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    padding: 16px;
    min-width: 300px;
    max-width: 400px;
    opacity: 0;
    transform: translateX(400px);
    transition: all 0.3s ease;
}

.notification-show {
    opacity: 1;
    transform: translateX(0);
}

.notification-hide {
    opacity: 0;
    transform: translateX(400px);
}

.notification-content {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.notification-header {
    display: flex;
    align-items: center;
    gap: 10px;
}

.notification-icon {
    font-size: 20px;
}

.notification-title {
    flex: 1;
    font-weight: 600;
    font-size: 14px;
    color: #333;
}

.notification-close {
    background: none;
    border: none;
    font-size: 24px;
    line-height: 1;
    cursor: pointer;
    color: #999;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.notification-close:hover {
    color: #666;
}

.notification-message {
    font-size: 13px;
    color: #666;
    margin-left: 30px;
}

.notification-progress {
    margin-top: 8px;
    margin-left: 30px;
    height: 4px;
    background: #f0f0f0;
    border-radius: 2px;
    overflow: hidden;
}

.notification-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    width: 0%;
    transition: width 0.3s ease;
}

.notification-success {
    border-left: 4px solid #4caf50;
}

.notification-error {
    border-left: 4px solid #f44336;
}

.notification-warning {
    border-left: 4px solid #ff9800;
}

.notification-info {
    border-left: 4px solid #2196f3;
}

.notification-processing {
    border-left: 4px solid #667eea;
}
`;
document.head.appendChild(style);

// 전역 인스턴스 생성
const notificationManager = new NotificationManager();


/**
 * 백그라운드 작업 폴링 시스템
 */
class BackgroundTaskMonitor {
    constructor(apiBase, token) {
        this.apiBase = apiBase;
        this.token = token;
        this.activeTasks = new Map();
        this.pollingInterval = 2000; // 2초마다 체크
    }

    /**
     * 작업 모니터링 시작
     * @param {string} taskId - 작업 ID
     * @param {string} title - 작업 제목
     */
    async monitorTask(taskId, title) {
        // 이미 모니터링 중이면 무시
        if (this.activeTasks.has(taskId)) {
            return;
        }

        // 초기 알림 표시
        notificationManager.show(
            taskId,
            title,
            '가이드라인 추출 및 임베딩을 시작합니다...',
            'processing',
            0 // 자동으로 닫히지 않음
        );

        // 폴링 시작
        const intervalId = setInterval(async () => {
            await this.checkTaskStatus(taskId, title);
        }, this.pollingInterval);

        this.activeTasks.set(taskId, intervalId);
    }

    /**
     * 작업 상태 확인
     * @param {string} taskId - 작업 ID
     * @param {string} title - 작업 제목
     */
    async checkTaskStatus(taskId, title) {
        try {
            const response = await fetch(`${this.apiBase}/api/policies/tasks/${taskId}/status`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                // 작업을 찾을 수 없으면 모니터링 중지
                this.stopMonitoring(taskId);
                return;
            }

            const result = await response.json();

            if (result.success) {
                const status = result.data;

                // 진행률 업데이트
                notificationManager.updateProgress(taskId, status.progress);

                // 메시지 업데이트
                notificationManager.updateMessage(taskId, status.message);

                // 완료 또는 실패 시
                if (status.status === 'completed') {
                    this.stopMonitoring(taskId);

                    // 기존 알림 제거 (localStorage도 업데이트)
                    notificationManager.remove(taskId, true);

                    // 완료 알림 표시 (자동으로 닫히지 않음, X 버튼으로만 닫기)
                    notificationManager.show(
                        `${taskId}-complete`,
                        '✅ ' + title,
                        status.message,
                        'success',
                        0  // 자동으로 닫히지 않음
                    );

                    // 사운드 재생 (선택사항)
                    this.playNotificationSound();

                } else if (status.status === 'failed') {
                    this.stopMonitoring(taskId);

                    // 기존 알림 제거 (localStorage도 업데이트)
                    notificationManager.remove(taskId, true);

                    // 실패 알림 표시 (자동으로 닫히지 않음, X 버튼으로만 닫기)
                    notificationManager.show(
                        `${taskId}-failed`,
                        '❌ ' + title,
                        status.message,
                        'error',
                        0  // 자동으로 닫히지 않음
                    );
                }
            }

        } catch (error) {
            console.error('작업 상태 확인 실패:', error);
        }
    }

    /**
     * 모니터링 중지
     * @param {string} taskId - 작업 ID
     */
    stopMonitoring(taskId) {
        const intervalId = this.activeTasks.get(taskId);
        if (intervalId) {
            clearInterval(intervalId);
            this.activeTasks.delete(taskId);
        }
    }

    /**
     * 알림 사운드 재생
     */
    playNotificationSound() {
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIGmi7792fTRANUKrj8LVhGgU7k9n11IAZC0CfwtmxkiIaHHuvuuqqeToTNJjW8sR0LAUrgc7y14k4CBlouOvhmFARD1Oo5O+1YRkGOpLY8tOKPAgZarrt25hOEQ5PoePwumQ=');
            audio.volume = 0.3;
            audio.play().catch(() => {});
        } catch (e) {
            // 사운드 재생 실패 무시
        }
    }

    /**
     * 모든 모니터링 중지
     */
    stopAll() {
        this.activeTasks.forEach((intervalId) => {
            clearInterval(intervalId);
        });
        this.activeTasks.clear();
    }
}

// 전역 모니터 인스턴스 (사용 시 초기화 필요)
let backgroundTaskMonitor = null;

// 모니터 초기화 함수
function initBackgroundMonitor(apiBase, token) {
    backgroundTaskMonitor = new BackgroundTaskMonitor(apiBase, token);
    return backgroundTaskMonitor;
}
