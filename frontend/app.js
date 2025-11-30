// ==========================
// 앱 초기화 및 메인 로직
// ==========================

// 테스트 사용자 데이터
const TEST_USERS = {
  admin: {
    userId: 'admin001',
    name: '김관리',
    email: 'admin@maskit.kr',
    team: '관리팀',
    role: 'sys_admin'
  },
  policy: {
    userId: 'policy001',
    name: '이정책',
    email: 'policy@maskit.kr',
    team: '정책팀',
    role: 'policy_admin'
  },
  auditor: {
    userId: 'audit001',
    name: '박감사',
    email: 'audit@maskit.kr',
    team: '감사팀',
    role: 'auditor'
  },
  approver: {
    userId: 'appr001',
    name: '최승인',
    email: 'approver@maskit.kr',
    team: '마케팅팀',
    role: 'approver'
  },
  user: {
    userId: 'user001',
    name: '이사용',
    email: 'user@maskit.kr',
    team: '인사팀',
    role: 'user'
  }
};

// ==========================
// 초기화
// ==========================

document.addEventListener('DOMContentLoaded', () => {
  // 저장된 사용자 복구
  restoreUserFromLocalStorage();

  if (isLoggedIn()) {
    // 이미 로그인된 경우
    showAppPage();
  } else {
    // 로그인 페이지 표시
    showLoginPage();
  }
});

// ==========================
// 로그인 페이지 처리
// ==========================

function showLoginPage() {
  const loginPage = document.getElementById('loginPage');
  const registerPage = document.getElementById('registerPage');
  const appContainer = document.querySelector('.app');

  loginPage.style.display = 'flex';
  registerPage.style.display = 'none';
  appContainer.style.display = 'none';

  setupLoginForm();
  setupTestUserButtons();
  setupRegisterLinks();
}

function showAppPage() {
  const loginPage = document.getElementById('loginPage');
  const appContainer = document.querySelector('.app');

  loginPage.style.display = 'none';
  appContainer.style.display = 'flex';

  initializeApp();
}

function setupLoginForm() {
  const form = document.getElementById('loginForm');
  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const userId = document.getElementById('userId').value;
    const userName = document.getElementById('userName').value;
    const userEmail = document.getElementById('userEmail').value;
    const userTeam = document.getElementById('userTeam').value;
    const userRole = document.getElementById('userRole').value;

    loginUser(userId, userName, userEmail, userTeam, userRole);
    showAppPage();
  });
}

function setupTestUserButtons() {
  document.querySelectorAll('.btn-test').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const userKey = btn.dataset.user;
      const user = TEST_USERS[userKey];

      loginUser(user.userId, user.name, user.email, user.team, user.role);
      showAppPage();
    });
  });
}

function setupRegisterLinks() {
  const showRegisterLink = document.getElementById('showRegisterLink');
  const showLoginLink = document.getElementById('showLoginLink');
  const loginPage = document.getElementById('loginPage');
  const registerPage = document.getElementById('registerPage');

  if (showRegisterLink) {
    showRegisterLink.addEventListener('click', (e) => {
      e.preventDefault();
      loginPage.style.display = 'none';
      registerPage.style.display = 'flex';
      setupRegisterForm();
    });
  }

  if (showLoginLink) {
    showLoginLink.addEventListener('click', (e) => {
      e.preventDefault();
      registerPage.style.display = 'none';
      loginPage.style.display = 'flex';
    });
  }
}

// ==========================
// 앱 초기화
// ==========================

function initializeApp() {
  const user = getCurrentUser();
  updateTopBar(user);
  renderSidebar(user);
  setupLogout();
  goToMainPage();
}

function updateTopBar(user) {
  const userNameEl = document.getElementById('userName');
  const userTeamEl = document.getElementById('userTeam');

  userNameEl.textContent = user.name;
  userTeamEl.textContent = user.team;
}

function renderSidebar(user) {
  const sidebarNav = document.getElementById('sidebarNav');
  const menu = getSidebarMenu();

  sidebarNav.innerHTML = '';

  menu.forEach(item => {
    const li = document.createElement('li');
    li.className = 'sidebar-menu-item';
    li.dataset.page = item.page;

    const button = document.createElement('button');
    button.className = 'sidebar-menu-btn';
    button.innerHTML = `<span class="icon">📄</span><span class="label">${item.label}</span>`;

    button.addEventListener('click', (e) => {
      e.preventDefault();
      navigateTo(item.page);
    });

    li.appendChild(button);

    // 서브메뉴 처리
    if (item.submenu && item.submenu.length > 0) {
      const submenuToggle = document.createElement('button');
      submenuToggle.className = 'submenu-toggle';
      submenuToggle.innerHTML = '▼';
      submenuToggle.addEventListener('click', (e) => {
        e.preventDefault();
        const ul = li.querySelector('ul');
        ul.classList.toggle('expanded');
      });
      button.appendChild(submenuToggle);

      const ul = document.createElement('ul');
      ul.className = 'sidebar-submenu';

      item.submenu.forEach(subitem => {
        const subli = document.createElement('li');
        subli.className = 'sidebar-submenu-item';
        subli.dataset.page = subitem.page;

        const subbtn = document.createElement('button');
        subbtn.className = 'sidebar-submenu-btn';
        subbtn.textContent = subitem.label;
        subbtn.addEventListener('click', (e) => {
          e.preventDefault();
          navigateTo(subitem.page);
        });

        subli.appendChild(subbtn);
        ul.appendChild(subli);
      });

      li.appendChild(ul);
    }

    sidebarNav.appendChild(li);
  });
}

function setupLogout() {
  const logoutBtn = document.getElementById('logoutBtn');
  logoutBtn.addEventListener('click', () => {
    logoutUser();
    showLoginPage();
  });
}

function goToMainPage() {
  const mainPage = getMainPage();
  navigateTo(mainPage);
}

// ==========================
// 회원가입 폼 처리
// ==========================

function setupRegisterForm() {
  const registerForm = document.getElementById('registerForm');
  const regMessage = document.getElementById('regMessage');

  if (!registerForm) return;

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('regEmail').value;
    const nickname = document.getElementById('regNickname').value;
    const department = document.getElementById('regDepartment').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;

    if (password !== confirmPassword) {
      showRegisterMessage('비밀번호가 일치하지 않습니다', 'error');
      return;
    }

    if (password.length < 6) {
      showRegisterMessage('비밀번호는 6자 이상이어야 합니다', 'error');
      return;
    }

    showRegisterMessage('회원가입 중...', 'loading');

    try {
      // 실제 API 호출 (현재는 테스트 모드)
      // const response = await fetch('http://127.0.0.1:8000/api/v1/auth/register', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ email, nickname, department, password })
      // });

      // 테스트: 회원가입 성공 시뮬레이션
      setTimeout(() => {
        showRegisterMessage('✓ 회원가입 성공! 로그인 페이지로 이동합니다...', 'success');
        setTimeout(() => {
          document.getElementById('registerPage').style.display = 'none';
          document.getElementById('loginPage').style.display = 'flex';
          registerForm.reset();
          regMessage.style.display = 'none';
        }, 2000);
      }, 1000);
    } catch (error) {
      showRegisterMessage('✗ 오류: ' + error.message, 'error');
    }
  });
}

function showRegisterMessage(message, type) {
  const regMessage = document.getElementById('regMessage');
  regMessage.textContent = message;
  regMessage.className = 'message show ' + type;
  regMessage.style.display = 'block';

  if (type === 'success' || type === 'error') {
    if (type !== 'loading') {
      setTimeout(() => {
        regMessage.style.display = 'none';
      }, 3000);
    }
  }
}

// ==========================
// 모달 폐쇄 처리
// ==========================

document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('modal');
  if (modal) {
    const closeBtn = modal.querySelector('#modalClose');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
      });
    }

    // 모달 배경 클릭 시 폐쇄
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.add('hidden');
      }
    });
  }
});
