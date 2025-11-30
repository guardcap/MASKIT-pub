// ==========================
// 라우팅 및 페이지 관리 시스템
// ==========================

// 페이지 저장소
const pages = {};
let currentPage = null;
let navigationHistory = [];

// ==========================
// 인증 체크 (로그인 필요 여부)
// ==========================

/**
 * 현재 페이지 접근 전 인증 확인
 * 로그인되지 않았으면 로그인 페이지로 리다이렉트
 */
function ensureAuthBeforeNavigation() {
  const token = localStorage.getItem('auth_token');
  const user = JSON.parse(localStorage.getItem('user') || 'null');

  if (!token || !user) {
    console.log('No auth token found, redirecting to login');
    window.location.href = 'pages/login.html';
    return false;
  }

  return true;
}

// ==========================
// 페이지 등록
// ==========================

/**
 * 페이지 등록
 * @param {string} name - 페이지 이름
 * @param {Object} handlers - { init, render, cleanup }
 */
function registerPage(name, handlers) {
  pages[name] = handlers;
}

/**
 * 페이지 렌더링
 * @param {string} pageName - 페이지 이름
 * @param {Object} params - 페이지 파라미터
 */
async function navigateTo(pageName, params = {}) {
  // 권한 확인
  const permission = checkPagePermission(pageName);
  if (!permission.allowed) {
    showAccessDeniedModal(permission.reason);
    if (permission.redirect) {
      navigateTo(permission.redirect);
    }
    return;
  }

  // 현재 페이지 정리
  if (currentPage && pages[currentPage].cleanup) {
    pages[currentPage].cleanup();
  }

  // 네비게이션 히스토리 저장
  navigationHistory.push(pageName);

  // 새 페이지 로드
  currentPage = pageName;
  const pageHandler = pages[pageName];

  if (!pageHandler) {
    console.error(`Page not found: ${pageName}`);
    showErrorModal(`페이지를 찾을 수 없습니다: ${pageName}`);
    return;
  }

  try {
    // 초기화
    if (pageHandler.init) {
      await pageHandler.init(params);
    }

    // 렌더링
    if (pageHandler.render) {
      pageHandler.render(params);
    }

    // 메뉴 활성화
    updateActiveMenu(pageName);

    // 스크롤 상단으로
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
      mainContent.scrollTop = 0;
    }
  } catch (error) {
    console.error(`Error loading page ${pageName}:`, error);
    showErrorModal(`페이지 로딩 중 오류가 발생했습니다: ${error.message}`);
  }
}

/**
 * 이전 페이지로 이동
 */
function goBack() {
  if (navigationHistory.length > 1) {
    navigationHistory.pop(); // 현재 페이지 제거
    const previousPage = navigationHistory[navigationHistory.length - 1];
    navigateTo(previousPage);
  }
}

/**
 * 메뉴 활성화 상태 업데이트
 */
function updateActiveMenu(pageName) {
  // 사이드바 메뉴 활성화 상태 업데이트
  document.querySelectorAll('.sidebar-menu-item').forEach(item => {
    item.classList.remove('active');
    if (item.dataset.page === pageName) {
      item.classList.add('active');
    }
  });

  // 서브메뉴 활성화 상태 업데이트
  document.querySelectorAll('.sidebar-submenu-item').forEach(item => {
    item.classList.remove('active');
    if (item.dataset.page === pageName) {
      item.classList.add('active');
    }
  });
}

// ==========================
// 모달 표시
// ==========================

/**
 * 접근 거부 모달 표시
 */
function showAccessDeniedModal(reason) {
  const modal = document.getElementById('modal') || createModal();
  const content = modal.querySelector('.modal-content');
  content.innerHTML = `
    <div class="modal-header">
      <h3>접근 권한 없음</h3>
    </div>
    <div class="modal-body">
      <p>${reason}</p>
    </div>
    <div class="modal-footer">
      <button id="modalClose" class="btn btn-primary">확인</button>
    </div>
  `;
  modal.classList.remove('hidden');

  document.getElementById('modalClose').addEventListener('click', () => {
    modal.classList.add('hidden');
  });
}

/**
 * 오류 모달 표시
 */
function showErrorModal(message) {
  const modal = document.getElementById('modal') || createModal();
  const content = modal.querySelector('.modal-content');
  content.innerHTML = `
    <div class="modal-header">
      <h3>오류 발생</h3>
    </div>
    <div class="modal-body">
      <p>${message}</p>
    </div>
    <div class="modal-footer">
      <button id="modalClose" class="btn btn-primary">확인</button>
    </div>
  `;
  modal.classList.remove('hidden');

  document.getElementById('modalClose').addEventListener('click', () => {
    modal.classList.add('hidden');
  });
}

/**
 * 모달 생성 (없을 경우)
 */
function createModal() {
  const modal = document.createElement('div');
  modal.id = 'modal';
  modal.className = 'modal hidden';
  modal.innerHTML = `
    <div class="modal-content">
      <p>메시지</p>
      <button id="modalClose">확인</button>
    </div>
  `;
  document.body.appendChild(modal);
  return modal;
}

// ==========================
// 현재 페이지 정보
// ==========================

/**
 * 현재 페이지명 가져오기
 */
function getCurrentPageName() {
  return currentPage;
}

/**
 * 현재 페이지가 주어진 페이지인지 확인
 */
function isCurrentPage(pageName) {
  return currentPage === pageName;
}

// ==========================
// 로그아웃 및 세션 관리
// ==========================

/**
 * 사용자 로그아웃
 */
function logoutCurrentUser() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user');
  window.location.href = 'pages/login.html';
}

/**
 * 토큰 갱신 (필요시)
 */
function refreshAuthToken() {
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
  const token = localStorage.getItem('auth_token');

  if (!token) {
    logoutCurrentUser();
    return false;
  }

  return true;
}
