// ==========================
// 역할 기반 접근 제어 (RBAC) 시스템
// ==========================

// 역할 정의
const ROLES = {
  SYS_ADMIN: 'sys_admin',
  POLICY_ADMIN: 'policy_admin',
  AUDITOR: 'auditor',
  APPROVER: 'approver',
  USER: 'user'
};

// 현재 사용자 정보 (로그인 후 설정됨)
let currentUser = {
  id: null,
  name: null,
  email: null,
  team: null,
  roles: [], // 복수 역할 지원
  primaryRole: null // 기본 역할
};

// ==========================
// 페이지별 접근 권한 정의
// ==========================
const PAGE_PERMISSIONS = {
  'dashboard': {
    allowed: [ROLES.SYS_ADMIN, ROLES.POLICY_ADMIN, ROLES.AUDITOR, ROLES.APPROVER, ROLES.USER],
    redirect: null
  },
  'mail-list': {
    allowed: [ROLES.APPROVER, ROLES.USER],
    redirect: 'dashboard'
  },
  'mail-send': {
    allowed: [ROLES.APPROVER, ROLES.USER],
    redirect: 'dashboard'
  },
  'mail-inbox': {
    allowed: [ROLES.APPROVER, ROLES.USER],
    redirect: 'dashboard'
  },
  'mail-outbox': {
    allowed: [ROLES.APPROVER, ROLES.USER],
    redirect: 'dashboard'
  },
  'approval-manage': {
    allowed: [ROLES.APPROVER],
    redirect: 'dashboard'
  },
  'policy-list': {
    allowed: [ROLES.SYS_ADMIN, ROLES.POLICY_ADMIN, ROLES.AUDITOR, ROLES.APPROVER, ROLES.USER],
    redirect: 'dashboard'
  },
  'policy-settings': {
    allowed: [ROLES.POLICY_ADMIN],
    redirect: 'dashboard'
  },
  'system-settings': {
    allowed: [ROLES.SYS_ADMIN],
    redirect: 'dashboard'
  },
  'employee-list': {
    allowed: [ROLES.SYS_ADMIN, ROLES.POLICY_ADMIN, ROLES.AUDITOR, ROLES.APPROVER, ROLES.USER],
    redirect: 'dashboard'
  },
  'audit-dashboard': {
    allowed: [ROLES.AUDITOR],
    redirect: 'dashboard'
  },
  'mypage': {
    allowed: [ROLES.SYS_ADMIN, ROLES.POLICY_ADMIN, ROLES.AUDITOR, ROLES.APPROVER, ROLES.USER],
    redirect: 'dashboard'
  }
};

// ==========================
// 메인 페이지 정의 (역할별)
// ==========================
const MAIN_PAGE_BY_ROLE = {
  [ROLES.SYS_ADMIN]: 'system-settings',
  [ROLES.POLICY_ADMIN]: 'policy-settings',
  [ROLES.AUDITOR]: 'audit-dashboard',
  [ROLES.APPROVER]: 'mail-list',
  [ROLES.USER]: 'mail-list'
};

// ==========================
// 사이드바 메뉴 정의 (역할별)
// ==========================
const SIDEBAR_MENU_BY_ROLE = {
  [ROLES.SYS_ADMIN]: [
    { label: '시스템 설정', page: 'system-settings', icon: 'settings' }
  ],
  [ROLES.POLICY_ADMIN]: [
    { label: '정책 설정', page: 'policy-settings', icon: 'settings' },
    { label: '정책 조회', page: 'policy-list', icon: 'file' }
  ],
  [ROLES.AUDITOR]: [
    { label: '감사 대시보드', page: 'audit-dashboard', icon: 'dashboard' },
    { label: '정책 조회', page: 'policy-list', icon: 'file' }
  ],
  [ROLES.APPROVER]: [
    { label: '메일 쓰기', page: 'mail-send', icon: 'compose' },
    { label: '받은 메일함', page: 'mail-inbox', icon: 'inbox' },
    { label: '보낸 메일함', page: 'mail-outbox', icon: 'sent' },
    { label: '승인 관리', page: 'approval-manage', icon: 'check', submenu: [
      { label: '대기 목록', page: 'approval-pending' },
      { label: '승인 목록', page: 'approval-approved' },
      { label: '반려 목록', page: 'approval-rejected' }
    ]},
    { label: '대시보드', page: 'dashboard', icon: 'dashboard' },
    { label: '정책 조회', page: 'policy-list', icon: 'file' },
    { label: '엔티티 조회', page: 'entity-list', icon: 'users' },
    { label: '환경 설정', page: 'mypage', icon: 'user' }
  ],
  [ROLES.USER]: [
    { label: '메일 쓰기', page: 'mail-send', icon: 'compose' },
    { label: '받은 메일함', page: 'mail-inbox', icon: 'inbox' },
    { label: '보낸 메일함', page: 'mail-outbox', icon: 'sent', submenu: [
      { label: '승인 대기', page: 'approval-pending' },
      { label: '승인 목록', page: 'approval-approved' },
      { label: '반려 목록', page: 'approval-rejected' }
    ]},
    { label: '대시보드', page: 'dashboard', icon: 'dashboard' },
    { label: '정책 조회', page: 'policy-list', icon: 'file' },
    { label: '엔티티 조회', page: 'entity-list', icon: 'users' },
    { label: '환경 설정', page: 'mypage', icon: 'user' }
  ]
};

// ==========================
// 세부 권한 정의 (데이터 접근 등)
// ==========================
const DATA_PERMISSIONS = {
  'employee-list': {
    [ROLES.SYS_ADMIN]: 'readwrite-all', // 모든 직원 조회 + team 변경 가능
    [ROLES.POLICY_ADMIN]: 'read-all', // 모든 직원 조회 (읽기 전용)
    [ROLES.AUDITOR]: 'read-all', // 모든 직원 조회 (읽기 전용)
    [ROLES.APPROVER]: 'read-team', // 본인 팀만 조회
    [ROLES.USER]: 'read-team' // 본인 팀만 조회
  },
  'policy-list': {
    [ROLES.SYS_ADMIN]: 'read',
    [ROLES.POLICY_ADMIN]: 'readwrite',
    [ROLES.AUDITOR]: 'read',
    [ROLES.APPROVER]: 'read',
    [ROLES.USER]: 'read'
  },
  'system-settings': {
    [ROLES.SYS_ADMIN]: 'readwrite'
  }
};

// ==========================
// 인증 함수
// ==========================

/**
 * 사용자 로그인 (모의 로그인)
 * @param {string} userId - 사용자 ID
 * @param {string} name - 사용자 이름
 * @param {string} email - 사용자 이메일
 * @param {string} team - 사용자 팀
 * @param {string|string[]} roles - 역할 (단일 또는 배열)
 */
function loginUser(userId, name, email, team, roles) {
  currentUser = {
    id: userId,
    name: name,
    email: email,
    team: team,
    roles: Array.isArray(roles) ? roles : [roles],
    primaryRole: Array.isArray(roles) ? roles[0] : roles
  };
  saveUserToLocalStorage();
  return currentUser;
}

/**
 * 사용자 로그아웃
 */
function logoutUser() {
  currentUser = {
    id: null,
    name: null,
    email: null,
    team: null,
    roles: [],
    primaryRole: null
  };
  localStorage.removeItem('currentUser');
  return true;
}

/**
 * 현재 사용자 정보 가져오기
 */
function getCurrentUser() {
  return currentUser;
}

/**
 * 사용자가 로그인되어 있는지 확인
 */
function isLoggedIn() {
  return currentUser.id !== null;
}

/**
 * 로컬스토리지에 사용자 정보 저장
 */
function saveUserToLocalStorage() {
  localStorage.setItem('currentUser', JSON.stringify(currentUser));
}

/**
 * 로컬스토리지에서 사용자 정보 복구
 */
function restoreUserFromLocalStorage() {
  const saved = localStorage.getItem('currentUser');
  if (saved) {
    currentUser = JSON.parse(saved);
  }
  return currentUser;
}

// ==========================
// 권한 확인 함수
// ==========================

/**
 * 사용자가 특정 역할을 가지고 있는지 확인
 * @param {string} role - 확인할 역할
 */
function hasRole(role) {
  return currentUser.roles.includes(role);
}

/**
 * 사용자가 특정 역할 중 하나를 가지고 있는지 확인
 * @param {string[]} roles - 확인할 역할 배열
 */
function hasAnyRole(roles) {
  return roles.some(role => currentUser.roles.includes(role));
}

/**
 * 사용자가 특정 역할 모두를 가지고 있는지 확인
 * @param {string[]} roles - 확인할 역할 배열
 */
function hasAllRoles(roles) {
  return roles.every(role => currentUser.roles.includes(role));
}

/**
 * 페이지 접근 권한 확인
 * @param {string} pageName - 페이지 이름
 * @returns {Object} { allowed: boolean, redirect?: string, reason?: string }
 */
function checkPagePermission(pageName) {
  if (!isLoggedIn()) {
    return { allowed: false, redirect: 'login', reason: '로그인이 필요합니다.' };
  }

  const permission = PAGE_PERMISSIONS[pageName];
  if (!permission) {
    return { allowed: true }; // 권한 정의가 없으면 접근 허용
  }

  const allowed = permission.allowed.some(role => currentUser.roles.includes(role));
  if (!allowed) {
    return {
      allowed: false,
      redirect: permission.redirect || 'dashboard',
      reason: `이 페이지에 접근할 권한이 없습니다. (필요 역할: ${permission.allowed.join(', ')})`
    };
  }

  return { allowed: true };
}

/**
 * 데이터 접근 권한 확인
 * @param {string} dataType - 데이터 타입 (예: 'employee-list')
 * @returns {string|null} 권한 수준 또는 null
 */
function getDataPermission(dataType) {
  const permission = DATA_PERMISSIONS[dataType];
  if (!permission) return null;

  for (const role of currentUser.roles) {
    if (permission[role]) {
      return permission[role];
    }
  }
  return null;
}

/**
 * 메인 페이지 경로 가져오기
 */
function getMainPage() {
  if (!isLoggedIn()) return 'login';
  return MAIN_PAGE_BY_ROLE[currentUser.primaryRole] || 'dashboard';
}

/**
 * 사이드바 메뉴 가져오기
 */
function getSidebarMenu() {
  if (!isLoggedIn()) return [];
  return SIDEBAR_MENU_BY_ROLE[currentUser.primaryRole] || [];
}

// ==========================
// 상단바 정보 가져오기
// ==========================
function getTopBarInfo() {
  if (!isLoggedIn()) return null;
  return {
    name: currentUser.name,
    team: currentUser.team,
    role: currentUser.primaryRole
  };
}
