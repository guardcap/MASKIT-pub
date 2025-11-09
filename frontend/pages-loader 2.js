// ==========================
// 페이지 로더 (각 페이지 등록)
// ==========================

// 로그인 페이지
registerPage('login', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = '<p>로그인 페이지</p>';
  },
  cleanup: () => {}
});

// ==========================
// 대시보드
// ==========================
registerPage('dashboard', {
  init: async () => {
    document.querySelector('.main-content').innerHTML = '';
  },
  render: () => {
    const mainContent = document.getElementById('mainContent');
    const user = getCurrentUser();

    mainContent.innerHTML = `
      <div class="page-header">
        <h1>대시보드</h1>
        <p class="subtitle">환영합니다, ${user.name}님</p>
      </div>

      <div class="dashboard-grid">
        <div class="dashboard-card">
          <h3>역할</h3>
          <p class="card-value">${user.primaryRole}</p>
        </div>
        <div class="dashboard-card">
          <h3>팀</h3>
          <p class="card-value">${user.team}</p>
        </div>
        <div class="dashboard-card">
          <h3>이메일</h3>
          <p class="card-value">${user.email}</p>
        </div>
      </div>

      <section class="info-section">
        <h2>빠른 시작</h2>
        <div class="quick-links">
          <a href="#" class="quick-link" onclick="navigateTo('policy-list'); return false;">정책 조회</a>
          <a href="#" class="quick-link" onclick="navigateTo('mypage'); return false;">환경 설정</a>
        </div>
      </section>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 메일 목록 페이지
// ==========================
registerPage('mail-list', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>메일 목록</h1>
      </div>
      <div class="mail-list-container">
        <p>메일 목록이 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 메일 쓰기 페이지 (write-email.html 통합)
// ==========================
registerPage('mail-send', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    const user = getCurrentUser();

    mainContent.innerHTML = `
      <div class="page-header">
        <h1>메일 쓰기</h1>
      </div>

      <div class="compose-panel" style="background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); overflow: hidden;">
        <div class="action-bar" style="display: flex; gap: 0.5em; padding: 1em 1.5em; border-bottom: 1px solid #e0e0e0; flex-wrap: wrap;">
          <button type="button" class="btn btn-primary" id="sendEmailBtn" style="padding: 0.6em 1em; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 500;">전송</button>
          <button type="button" class="btn" id="saveDraftBtn" style="padding: 0.6em 1em; border: 1px solid #d0d0d0; background: white; border-radius: 4px; cursor: pointer;">임시 저장</button>
        </div>

        <form id="mail-form" class="form-content" style="padding: 0;">
          <div class="form-row" style="display: flex; align-items: center; padding: 0.8em 1.5em; border-bottom: 1px solid #f0f0f0;">
            <label class="form-label" style="min-width: 100px; font-size: 13px; font-weight: 500;">보내는 주소</label>
            <div class="form-input" style="flex: 1; display: flex; align-items: center;">
              <input type="email" id="from_email" name="from_email" required value="${user.email}" style="flex: 1; max-width: 300px; padding: 0.5em; border: 1px solid #e0e0e0; border-radius: 4px; font-size: 13px;">
            </div>
          </div>

          <div class="form-row" style="display: flex; align-items: center; padding: 0.8em 1.5em; border-bottom: 1px solid #f0f0f0;">
            <label class="form-label" style="min-width: 100px; font-size: 13px; font-weight: 500;">받는 주소</label>
            <div class="form-input" style="flex: 1; display: flex; align-items: center; gap: 0.5em; flex-wrap: wrap;">
              <div class="recipient-container" id="recipientContainer" style="flex: 1; display: flex; align-items: center; gap: 0.5em; flex-wrap: wrap; min-height: 32px;">
                <input type="email" class="recipient-input" id="recipientInput" placeholder="받는 주소 이메일 (Enter로 추가)" style="flex: 1; min-width: 200px; padding: 0.3em; border: none; font-size: 13px;">
              </div>
              <button type="button" class="btn" id="addressBtn" style="padding: 0.4em 0.8em; border: 1px solid #d0d0d0; background: white; border-radius: 4px; cursor: pointer; font-size: 13px;">주소록</button>
            </div>
          </div>

          <div class="form-row" style="display: flex; align-items: center; padding: 0.8em 1.5em; border-bottom: 1px solid #f0f0f0;">
            <label class="form-label" style="min-width: 100px; font-size: 13px; font-weight: 500;">제목</label>
            <div class="form-input" style="flex: 1;">
              <input type="text" id="subject" name="subject" required placeholder="제목을 입력하세요" style="flex: 1; padding: 0.5em; border: 1px solid #e0e0e0; border-radius: 4px; font-size: 13px;">
            </div>
          </div>

          <div class="file-attach-row" style="display: flex; align-items: flex-start; padding: 1em 1.5em; border-bottom: 1px solid #f0f0f0;">
            <label class="form-label" style="min-width: 100px; font-size: 13px; font-weight: 500;">파일 첨부</label>
            <div style="flex: 1;">
              <button type="button" class="btn" id="attachBtn" style="padding: 0.4em 0.8em; border: 1px solid #d0d0d0; background: white; border-radius: 4px; cursor: pointer; font-size: 13px;">내 PC</button>
              <div class="file-attach-area" id="fileAttachArea" style="padding: 2em; border: 2px dashed #d0d0d0; border-radius: 4px; text-align: center; cursor: pointer; margin-top: 1em; transition: all 0.2s;">
                <div style="color: #999; font-size: 14px;">📁 첨부할 파일을 마우스로 끌어 놓으세요</div>
                <input type="file" id="attachment" name="attachment" multiple style="display: none;">
              </div>
            </div>
          </div>

          <div class="file-list" id="fileList" style="padding: 0 1.5em; display: flex; flex-wrap: wrap; gap: 0.5em; margin-bottom: 1em;"></div>

          <div class="editor-section" style="border-bottom: 1px solid #f0f0f0;">
            <div class="editor-toolbar" style="display: flex; align-items: center; gap: 0.3em; padding: 0.8em 1.5em; background: #fafafa; border-bottom: 1px solid #e0e0e0; flex-wrap: wrap;">
              <div class="toolbar-group" style="display: flex; align-items: center; gap: 0.3em; padding-right: 0.5em; border-right: 1px solid #d0d0d0;">
                <button type="button" class="tool-btn" id="undoBtn" title="실행 취소" style="width: 28px; height: 28px; border: none; background: transparent; border-radius: 3px; cursor: pointer; font-weight: 600; color: #555;">⟲</button>
                <button type="button" class="tool-btn" id="redoBtn" title="다시 실행" style="width: 28px; height: 28px; border: none; background: transparent; border-radius: 3px; cursor: pointer; font-weight: 600; color: #555;">⟳</button>
              </div>

              <div class="toolbar-group" style="display: flex; align-items: center; gap: 0.3em; padding-right: 0.5em; border-right: 1px solid #d0d0d0;">
                <select id="fontSelect" style="padding: 0.3em 0.5em; border: 1px solid #d0d0d0; border-radius: 3px; font-size: 12px; cursor: pointer; background: white;">
                  <option value="">기본 서체</option>
                  <option value="Arial">Arial</option>
                  <option value="Georgia">Georgia</option>
                  <option value="Courier New">Courier New</option>
                </select>
                <select id="sizeSelect" style="padding: 0.3em 0.5em; border: 1px solid #d0d0d0; border-radius: 3px; font-size: 12px; cursor: pointer; background: white;">
                  <option value="3" selected>10pt</option>
                  <option value="1">8pt</option>
                  <option value="2">9pt</option>
                  <option value="4">12pt</option>
                  <option value="5">14pt</option>
                  <option value="6">18pt</option>
                </select>
              </div>

              <div class="toolbar-group" style="display: flex; align-items: center; gap: 0.3em; padding-right: 0.5em; border-right: 1px solid #d0d0d0;">
                <button type="button" class="tool-btn" id="boldBtn" title="굵게" style="width: 28px; height: 28px; border: none; background: transparent; border-radius: 3px; cursor: pointer; font-weight: 600; color: #555;"><strong>B</strong></button>
                <button type="button" class="tool-btn" id="italicBtn" title="기울임" style="width: 28px; height: 28px; border: none; background: transparent; border-radius: 3px; cursor: pointer; color: #555;"><em>I</em></button>
                <button type="button" class="tool-btn" id="underlineBtn" title="밑줄" style="width: 28px; height: 28px; border: none; background: transparent; border-radius: 3px; cursor: pointer; color: #555;"><u>U</u></button>
              </div>

              <div class="toolbar-group" style="display: flex; align-items: center; gap: 0.3em; padding-right: 0.5em; border-right: 1px solid #d0d0d0;">
                <button type="button" class="tool-btn" id="ulBtn" title="글머리 기호" style="width: 28px; height: 28px; border: none; background: transparent; border-radius: 3px; cursor: pointer; color: #555;">•</button>
                <button type="button" class="tool-btn" id="olBtn" title="번호 매기기" style="width: 28px; height: 28px; border: none; background: transparent; border-radius: 3px; cursor: pointer; color: #555;">1.</button>
              </div>
            </div>
            <div id="body" contenteditable="true" style="min-height: 350px; max-height: 600px; padding: 1.5em; font-size: 14px; line-height: 1.6; overflow-y: auto; background: white;" placeholder="메일 내용을 입력하세요"></div>
          </div>
        </form>

        <div id="status" class="status" style="text-align: center; padding: 1em; border-radius: 8px; font-weight: 500; display: none; margin: 1em 1.5em;"></div>
      </div>
    `;

    // 메일 쓰기 기능 초기화
    initMailCompose();
  },
  cleanup: () => {}
});

// 메일 쓰기 기능 함수들
function initMailCompose() {
  let recipients = [];
  let selectedFiles = [];

  const recipientInput = document.getElementById('recipientInput');
  const recipientContainer = document.getElementById('recipientContainer');
  const fileInput = document.getElementById('attachment');
  const fileAttachArea = document.getElementById('fileAttachArea');
  const fileList = document.getElementById('fileList');
  const statusDiv = document.getElementById('status');

  // 수신자 추가
  recipientInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addRecipient(recipientInput.value.trim());
      recipientInput.value = '';
    }
  });

  recipientInput.addEventListener('blur', () => {
    if (recipientInput.value.trim()) {
      addRecipient(recipientInput.value.trim());
      recipientInput.value = '';
    }
  });

  function addRecipient(email) {
    if (!email) return;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      alert('올바른 이메일 주소를 입력하세요.');
      return;
    }
    if (recipients.includes(email)) {
      alert('이미 추가된 이메일입니다.');
      return;
    }

    recipients.push(email);
    const chip = document.createElement('div');
    chip.className = 'recipient-chip';
    chip.style.cssText = 'display: inline-flex; align-items: center; gap: 0.3em; padding: 0.3em 0.6em; background: #e8eaf6; border: 1px solid #c5cae9; border-radius: 16px; font-size: 12px;';
    chip.innerHTML = `<span>${email}</span><button type="button" style="background: none; border: none; cursor: pointer; color: #666;">×</button>`;
    chip.querySelector('button').onclick = () => removeRecipient(email);
    recipientContainer.insertBefore(chip, recipientInput);
  }

  function removeRecipient(email) {
    recipients = recipients.filter(r => r !== email);
    document.querySelectorAll('.recipient-chip').forEach(chip => {
      if (chip.textContent.includes(email)) chip.remove();
    });
  }

  // 파일 첨부
  document.getElementById('attachBtn').onclick = () => fileInput.click();

  fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

  fileAttachArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileAttachArea.style.borderColor = '#667eea';
    fileAttachArea.style.background = '#f8f9ff';
  });

  fileAttachArea.addEventListener('dragleave', () => {
    fileAttachArea.style.borderColor = '#d0d0d0';
    fileAttachArea.style.background = '';
  });

  fileAttachArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileAttachArea.style.borderColor = '#d0d0d0';
    fileAttachArea.style.background = '';
    handleFiles(e.dataTransfer.files);
  });

  function handleFiles(files) {
    Array.from(files).forEach(file => {
      selectedFiles.push(file);
      const fileItem = document.createElement('div');
      fileItem.style.cssText = 'display: flex; align-items: center; gap: 0.5em; padding: 0.4em 0.8em; background: #f5f5f5; border: 1px solid #e0e0e0; border-radius: 4px; font-size: 12px;';
      fileItem.innerHTML = `<span>📄 ${file.name} (${formatFileSize(file.size)})</span><button type="button" style="background: none; border: none; cursor: pointer; color: #999;">×</button>`;
      fileItem.querySelector('button').onclick = () => removeFile(file.name);
      fileList.appendChild(fileItem);
    });
  }

  function removeFile(fileName) {
    selectedFiles = selectedFiles.filter(f => f.name !== fileName);
    document.querySelectorAll('div').forEach(el => {
      if (el.textContent.includes(fileName)) el.remove();
    });
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  // 텍스트 편집
  document.getElementById('boldBtn').onclick = () => { document.execCommand('bold'); document.getElementById('body').focus(); };
  document.getElementById('italicBtn').onclick = () => { document.execCommand('italic'); document.getElementById('body').focus(); };
  document.getElementById('underlineBtn').onclick = () => { document.execCommand('underline'); document.getElementById('body').focus(); };
  document.getElementById('ulBtn').onclick = () => { document.execCommand('insertUnorderedList'); document.getElementById('body').focus(); };
  document.getElementById('olBtn').onclick = () => { document.execCommand('insertOrderedList'); document.getElementById('body').focus(); };
  document.getElementById('undoBtn').onclick = () => { document.execCommand('undo'); document.getElementById('body').focus(); };
  document.getElementById('redoBtn').onclick = () => { document.execCommand('redo'); document.getElementById('body').focus(); };

  document.getElementById('fontSelect').addEventListener('change', (e) => {
    if (e.target.value) document.execCommand('fontName', false, e.target.value);
  });

  document.getElementById('sizeSelect').addEventListener('change', (e) => {
    document.execCommand('fontSize', false, e.target.value);
  });

  // 메일 전송
  document.getElementById('sendEmailBtn').onclick = async () => {
    if (recipients.length === 0) {
      alert('받는 주소를 입력하세요.');
      return;
    }

    showStatus('메일 전송 중...', 'loading');

    const formData = new FormData();
    formData.append('from_email', document.getElementById('from_email').value);
    formData.append('to', recipients.join(', '));
    formData.append('subject', document.getElementById('subject').value);
    formData.append('body', document.getElementById('body').innerHTML);

    selectedFiles.forEach(file => {
      formData.append('attachment', file);
    });

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/send-email', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        showStatus('✓ 메일이 전송되었습니다', 'success');
      } else {
        showStatus('✗ 전송 실패', 'error');
      }
    } catch (error) {
      showStatus('✗ 오류: ' + error.message, 'error');
    }
  };

  document.getElementById('saveDraftBtn').onclick = () => {
    showStatus('💾 임시 저장되었습니다', 'success');
  };

  function showStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = 'status show ' + type;
    statusDiv.style.display = 'block';
    if (type !== 'loading') {
      setTimeout(() => { statusDiv.style.display = 'none'; }, 3000);
    }
  }
}`

// ==========================
// 받은 메일함
// ==========================
registerPage('mail-inbox', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>받은 메일함</h1>
      </div>
      <div class="mailbox-container">
        <p>받은 메일이 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 보낸 메일함
// ==========================
registerPage('mail-outbox', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>보낸 메일함</h1>
      </div>
      <div class="mailbox-container">
        <p>보낸 메일이 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 승인 관리
// ==========================
registerPage('approval-manage', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>승인 관리</h1>
      </div>
      <div class="approval-container">
        <p>승인 대상이 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 승인 대기
// ==========================
registerPage('approval-pending', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>승인 대기</h1>
      </div>
      <div class="approval-pending-list">
        <p>승인 대기 중인 항목이 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 승인 완료
// ==========================
registerPage('approval-approved', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>승인 완료</h1>
      </div>
      <div class="approval-approved-list">
        <p>승인된 항목이 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 승인 반려
// ==========================
registerPage('approval-rejected', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>승인 반려</h1>
      </div>
      <div class="approval-rejected-list">
        <p>반려된 항목이 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 정책 조회
// ==========================
registerPage('policy-list', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>정책 조회</h1>
      </div>
      <div class="policy-list-container">
        <p>정책 목록이 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 정책 설정 (Policy Admin만)
// ==========================
registerPage('policy-settings', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>정책 설정</h1>
      </div>
      <div class="policy-settings-container">
        <p>정책 설정이 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 시스템 설정 (Sys Admin만)
// ==========================
registerPage('system-settings', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>시스템 설정</h1>
      </div>
      <div class="system-settings-container">
        <form class="settings-form">
          <div class="form-group">
            <label for="llmApi">LLM API</label>
            <input type="text" id="llmApi" placeholder="LLM API 설정" required>
          </div>
          <div class="form-group">
            <label for="smtpHost">SMTP 호스트</label>
            <input type="text" id="smtpHost" placeholder="SMTP 호스트" required>
          </div>
          <div class="form-group">
            <label for="smtpPort">SMTP 포트</label>
            <input type="number" id="smtpPort" placeholder="SMTP 포트" required>
          </div>
          <button type="submit" class="btn btn-primary">저장</button>
        </form>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 감사 대시보드 (Auditor만)
// ==========================
registerPage('audit-dashboard', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>감사 대시보드</h1>
      </div>
      <div class="audit-dashboard-container">
        <p>감사 정보가 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 직원 목록
// ==========================
registerPage('employee-list', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    const dataPermission = getDataPermission('employee-list');
    const user = getCurrentUser();

    let content = '<div class="page-header"><h1>직원 목록</h1></div>';

    if (dataPermission === 'readwrite-all') {
      content += '<p>모든 직원 조회 + 팀 변경 가능</p>';
    } else if (dataPermission === 'read-all') {
      content += '<p>모든 직원 조회 (읽기 전용)</p>';
    } else if (dataPermission === 'read-team') {
      content += `<p>${user.team} 팀 직원만 조회</p>`;
    }

    mainContent.innerHTML = content;
  },
  cleanup: () => {}
});

// ==========================
// 엔티티 조회
// ==========================
registerPage('entity-list', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `
      <div class="page-header">
        <h1>엔티티 조회</h1>
      </div>
      <div class="entity-list-container">
        <p>엔티티 정보가 표시됩니다.</p>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 환경 설정 (마이페이지)
// ==========================
registerPage('mypage', {
  init: async () => {},
  render: () => {
    const mainContent = document.getElementById('mainContent');
    const user = getCurrentUser();

    mainContent.innerHTML = `
      <div class="page-header">
        <h1>환경 설정</h1>
      </div>
      <div class="mypage-container">
        <form class="settings-form">
          <div class="form-group">
            <label for="displayName">이름</label>
            <input type="text" id="displayName" value="${user.name}" required>
          </div>
          <div class="form-group">
            <label for="displayEmail">이메일</label>
            <input type="email" id="displayEmail" value="${user.email}" required>
          </div>
          <div class="form-group">
            <label for="displayTeam">팀</label>
            <input type="text" id="displayTeam" value="${user.team}" required>
          </div>
          <button type="submit" class="btn btn-primary">저장</button>
        </form>
      </div>
    `;
  },
  cleanup: () => {}
});

// ==========================
// 이메일 마스킹 페이지 (기존 기능 통합)
// ==========================
registerPage('masking-editor', {
  init: async () => {
    // 기존 마스킹 페이지 초기화
    // script.js의 fetchAndRenderFiles() 함수 호출
    if (typeof fetchAndRenderFiles === 'function') {
      await fetchAndRenderFiles();
    }
  },
  render: () => {
    const mainContent = document.getElementById('mainContent');

    // 기존 index.html의 마스킹 레이아웃 렌더링
    mainContent.innerHTML = `
      <div class="masking-container">
        <div class="masking-header">
          <h1>이메일 마스킹</h1>
        </div>

        <section class="masking-panel">
          <div class="masking-top">
            <div class="recipients" id="recipients">
              <button class="more-btn" id="recipToggle" type="button">열기</button>
            </div>
            <div class="me">
              <div class="avatar" aria-hidden="true"></div>
              <div class="who">
                <span class="team" id="senderTeam">팀</span>
                <span class="nick" id="senderName">이름</span>
              </div>
            </div>
          </div>

          <div class="masking-row">
            <div class="grid2">
              <div class="card">
                <h4>AI 개요</h4>
                <p id="aiSummary">보내는 주소가 여러 개, 각기 다른 도메인을 가지고 있어 사외 전송으로 인식하였으며 해당 규정에 맞춰 마스킹했습니다. 개인정보 유출 방지 목적의 개별 전송 설정도 적용됩니다.</p>
              </div>
              <div class="card">
                <h4>통계</h4>
                <div class="legend" id="statsLegend">
                  <div class="row"><span class="bar c1"></span><span class="t">식별: 7개</span></div>
                  <div class="row"><span class="bar c2"></span><span class="t">마스킹: 2개</span></div>
                  <div class="row"><span class="bar c3"></span><span class="t">검토 필요: 1개</span></div>
                  <div class="row"><span class="bar c4"></span><span class="t">권한: DLP / 데이터 사일로</span></div>
                </div>
              </div>
            </div>
          </div>

          <div class="filebar" id="filebar">
            <!-- 파일 탭이 동적으로 생성됨 -->
          </div>

          <div class="content" id="maskingContent">
            <!-- 이메일 본문과 첨부파일이 표시됨 -->
          </div>
        </section>

        <aside class="masking-sidebar" id="maskingSidebar">
          <div class="sb-head">
            <div class="sb-title">마스킹 목록</div>
          </div>
          <div id="maskingList">
            <!-- 마스킹 목록이 동적으로 생성됨 -->
          </div>
        </aside>

        <header class="masking-topbar">
          <div class="masking-topbar-title">마스킹 편집기</div>
          <div class="masking-topbar-buttons">
            <button class="masking-topbar-button" id="approveBtn">승인</button>
            <button class="masking-topbar-button">반려</button>
          </div>
        </header>
      </div>
    `;

    // 사용자 정보 업데이트
    const user = getCurrentUser();
    const senderTeamEl = document.getElementById('senderTeam');
    const senderNameEl = document.getElementById('senderName');
    if (senderTeamEl) senderTeamEl.textContent = user.team;
    if (senderNameEl) senderNameEl.textContent = user.name;
  },
  cleanup: () => {
    // 마스킹 에디터 정리
  }
});
