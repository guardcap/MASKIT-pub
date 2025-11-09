// ==========================
// Data
// ==========================
let recipientsData = []; // API를 통해 동적으로 채워짐
let piiAnalysisResults = [];
let filesData = [];
let currentSelectedFile = 'all';
let emailMetaData = {};
let recipCollapsed = true;

// ==========================
// Helper Functions
// ==========================
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function getFileNameById(fileId) {
    const file = filesData.find(f => f.id === fileId);
    return file ? file.name : fileId;
}

const escapeHTML = (str) => str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// ==========================
// API Calls
// ==========================
async function fetchAndRenderFiles() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/v1/files/files");
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        filesData = await response.json();
        
        await processDocumentsAndAnalyzePII();
        await fetchAndRenderRecipients();

        await renderFileTabs(filesData);
        renderMaskingList(piiAnalysisResults, currentSelectedFile);
        
    } catch (error) {
        console.error("파일 목록을 불러오는 데 실패했습니다:", error);
    }
}

async function processDocumentsAndAnalyzePII() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/v1/process/documents", { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const processResult = await response.json();
        piiAnalysisResults = processResult.details || [];
        console.log("PII 분석 결과:", piiAnalysisResults);
    } catch (error) {
        console.error("PII 분석 처리 중 오류 발생:", error);
        piiAnalysisResults = [];
    }
}

async function fetchAndRenderRecipients() {
    try {
        const response = await fetch("http://127.0.0.1:8000/uploads/email_meta.json");
        if (response.ok) {
            emailMetaData = await response.json();
            recipientsData = emailMetaData.recipients || [];
        } else {
            recipientsData = ['(수신자 정보 없음)'];
        }
    } catch (e) {
        recipientsData = ['(수신자 정보 로딩 실패)'];
    }
    renderRecipients(recipCollapsed);
}

// ==========================
// Recipients chips
// ==========================
function renderRecipients(collapsed = true) {
    const recipWrap = $('#recipients');
    const recipToggle = $('#recipToggle');
    if (!recipWrap || !recipToggle) return;
    
    recipWrap.innerHTML = '';
    const maxVisible = 3;
    recipientsData.forEach((addr, idx) => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.innerHTML = `<span class="text">${addr}</span>`;
        if (collapsed && idx >= maxVisible) { 
            chip.style.display = 'none'; 
            chip.dataset.hidden = '1';
        }
        recipWrap.appendChild(chip);
    });

    if (recipientsData.length > maxVisible) {
        recipToggle.style.display = 'inline-flex';
        recipToggle.textContent = collapsed ? `+${recipientsData.length - maxVisible}` : '접기';
        recipWrap.appendChild(recipToggle);
    } else {
        recipToggle.style.display = 'none';
    }
}

// ==========================
// Content Building with Markers
// ==========================
async function buildContentWithMarkers() {
    // email_body.txt 파일을 직접 읽어서 표시
    try {
        const response = await fetch("http://127.0.0.1:8000/uploads/email_body.txt");
        if (response.ok) {
            const emailText = await response.text();
            return emailText.split('\n').map(p => 
                `<p contenteditable="true" class="editable-paragraph">${escapeHTML(p) || '&nbsp;'}</p>`
            ).join('');
        }
    } catch (error) {
        console.error("email_body.txt 읽기 실패:", error);
    }
    
    return "<p>표시할 이메일 본문이 없습니다.</p>";
}

// ==========================
// File Tabs Rendering
// ==========================
async function renderFileTabs(files) {
    const filebar = $('#filebar');
    const contentArea = $('.content');
    filebar.innerHTML = '';
    contentArea.innerHTML = '';

    // 전체 탭 버튼
    const allBtn = document.createElement('button');
    allBtn.className = 'tab active';
    allBtn.textContent = '전체';
    allBtn.dataset.id = 'all';
    filebar.appendChild(allBtn);

    // 각 파일 탭 버튼
    files.forEach((file) => {
        const tabBtn = document.createElement('button');
        tabBtn.className = 'tab';
        tabBtn.textContent = file.kind === 'email' ? "이메일 본문" : file.name;
        tabBtn.dataset.id = file.id;
        filebar.appendChild(tabBtn);
    });

    // === 전체 탭 뷰 ===
    const allView = document.createElement('div');
    allView.className = 'view active';
    allView.id = 'view-all';

    // 1. 이메일 본문 섹션
    const emailResult = piiAnalysisResults.find(r => r.filename === "email 본문");
    if (emailResult) {
        const emailContentHtml = await buildContentWithMarkers();
        const emailSection = document.createElement('div');
        emailSection.className = 'doc-container';

        const subject = emailMetaData.subject || "이메일 제목"; 
        
        emailSection.innerHTML = `
            <h3>${escapeHTML(subject)}</h3>
            <div class="editor">
                <div class="doc" id="doc">${emailContentHtml}</div>
            </div>
        `;
        allView.appendChild(emailSection);
    }

    // 2. 첨부파일(이미지, PDF 등)
    const attachmentsSection = document.createElement('div');
    attachmentsSection.className = 'attachments';
    files.forEach(file => {
        if (file.kind === 'image') {
            attachmentsSection.innerHTML += `<img class="embed-img" alt="${file.name} 미리보기" src="http://127.0.0.1:8000${file.path}" />`;
        } else if (file.kind === 'pdf') {
            attachmentsSection.innerHTML += `<object class="embed-pdf" type="application/pdf" data="http://127.0.0.1:8000${file.path}"></object>`;
        }
    });
    if (attachmentsSection.innerHTML) {
        allView.appendChild(attachmentsSection);
    }

    contentArea.appendChild(allView);

    // === 개별 파일 뷰 ===
    for (const file of files) {
        const view = document.createElement('div');
        view.className = 'view';
        view.id = `view-${file.id}`;
        if (file.kind === 'email') {
            const emailContentHtml = await buildContentWithMarkers();
            view.innerHTML = `<div class="editor"><div class="toolbar"><button class="tool" title="Bold"><strong>B</strong></button><button class="tool" title="Italic"><em>I</em></button></div><div class="doc" id="doc">${emailContentHtml}</div></div>`;
        } else if (file.kind === 'image') {
            view.innerHTML = `<img class="embed-img" alt="${file.name} 미리보기" src="http://127.0.0.1:8000${file.path}" />`;
        } else if (file.kind === 'pdf') {
            view.innerHTML = `<object class="embed-pdf" type="application/pdf" data="http://127.0.0.1:8000${file.path}"></object>`;
        }
        contentArea.appendChild(view);
    }

    // 탭 클릭 이벤트
    filebar.addEventListener('click', (e) => {
        const btn = e.target.closest('.tab');
        if (!btn) return;
        currentSelectedFile = btn.dataset.id;
        $$('.tab').forEach(t => t.classList.remove('active'));
        btn.classList.add('active');
        $$('.view').forEach(v => v.classList.remove('active'));
        const targetView = $(`#view-${currentSelectedFile}`);
        if (targetView) targetView.classList.add('active');
        renderMaskingList(piiAnalysisResults, currentSelectedFile);
    });
}

// 체크박스 클릭 시 이메일 본문의 텍스트를 즉시 마스킹 처리
function handleCheckboxToggle(checkbox, li) {
    const id = li?.getAttribute('data-ref');
    if (!id) return;
    
    const piiData = findPiiById(id);
    if (!piiData) return;
    
    const isChecked = checkbox.classList.contains('on');
    
    // 이메일 본문인 경우에만 즉시 마스킹 처리
    if (piiData.filename === "email 본문") {
        const activeView = document.querySelector('.view.active');
        const docElement = activeView?.querySelector('#doc');
        
        if (docElement) {
            const paragraphs = docElement.querySelectorAll('p.editable-paragraph');
            const fullText = Array.from(paragraphs).map(p => p.textContent).join('\n');
            
            const start = piiData.start_char;
            const end = piiData.end_char;
            const originalText = piiData.text;
            const maskText = '*'.repeat(originalText.length);
            
            if (isChecked) {
                // 체크됨 → 마스킹 (원본을 *로 치환)
                const newText = fullText.substring(0, start) + maskText + fullText.substring(end);
                updateEmailBodyUI(docElement, newText);
                console.log(`✅ [마스킹] "${originalText}" → "${maskText}"`);
            } else {
                // 체크 해제됨 → 원본 복원 (*를 원본으로 치환)
                const newText = fullText.substring(0, start) + originalText + fullText.substring(end);
                updateEmailBodyUI(docElement, newText);
                console.log(`✅ [복원] "${maskText}" → "${originalText}"`);
            }
        }
    }
}

// 이메일 본문 UI 업데이트 헬퍼 함수
function updateEmailBodyUI(docElement, newText) {
    docElement.innerHTML = newText.split('\n').map(p => 
        `<p contenteditable="true" class="editable-paragraph">${escapeHTML(p) || '&nbsp;'}</p>`
    ).join('');
}

// ==========================
// Masking List Rendering
// ==========================
function renderMaskingList(analysisResults, selectedFileId = 'all') {
    const sidebar = document.getElementById('sidebar');
    
    // 기존 그룹 내용만 제거
    const existingGroups = sidebar.querySelectorAll('.group');
    existingGroups.forEach(group => group.remove());
    
    const piiGroups = {};
    
    analysisResults.forEach((result, fileIndex) => {
        const fileInfo = filesData.find(f => f.name === result.filename || (result.filename === "email 본문" && f.kind === "email"));
        
        if (selectedFileId !== 'all' && (!fileInfo || fileInfo.id !== selectedFileId)) {
            return;
        }
        
        if (result.status === 'ANALYSIS_COMPLETED' && result.analysis_data && result.analysis_data.pii_entities) {
            result.analysis_data.pii_entities.forEach((entity, entityIndex) => {
                const entityId = `pii-${fileIndex}-${entityIndex}`;
                if (!piiGroups[entity.type]) {
                    piiGroups[entity.type] = [];
                }
                piiGroups[entity.type].push({
                    id: entityId,
                    text: entity.text,
                    score: entity.score,
                    filename: result.filename,
                    start_char: entity.start_char,
                    end_char: entity.end_char,
                    coordinates: entity.coordinates || [],
                    fileIndex: fileIndex,
                    entityIndex: entityIndex
                });
            });
        }
    });
    
    const typeLabels = {
        'EMAIL': '이메일 주소',
        'PHONE': '전화번호',
        'PERSON': '개인명',
        'BANK_ACCOUNT': '계좌 번호',
        'CREDIT_CARD': '신용카드 번호',
        'IP_ADDRESS': 'IP 주소',
        'DATE_TIME': '날짜/시간',
        'LOCATION': '위치 정보',
        'ORGANIZATION': '조직명'
    };
    
    Object.entries(piiGroups).forEach(([type, entities]) => {
        const group = document.createElement('div');
        group.className = 'group';
        group.setAttribute('data-type', type);
        group.innerHTML = `
            <button class="group-toggle" aria-expanded="false">
                <span>${typeLabels[type] || type}</span>
                <svg class="caret" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" stroke-width="2">
                    <polyline points="8 4 16 12 8 20" />
                </svg>
            </button>
            <ul class="items">
                ${entities.map(entity => `
                    <li class="item" data-ref="${entity.id}">
                        <button class="checkbox off" aria-checked="false" title="마스킹" data-check></button>
                        <span class="txt">${escapeHTML(entity.text)}</span>
                        <div class="meta">
                            <small>${entity.filename} (신뢰도: ${Math.round(entity.score * 100)}%)</small>
                        </div>
                        <div class="actions">
                            <button class="action-btn" data-jump title="위치로 이동">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M15 3h6v6M9 21l6-6M21 3l-7 7M3 21l7-7"/>
                                </svg>
                            </button>
                            <button class="action-btn" data-copy title="복사">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                                </svg>
                            </button>
                        </div>
                    </li>
                `).join('')}
            </ul>
        `;
        sidebar.appendChild(group);
    });
    
    if (Object.keys(piiGroups).length === 0) {
        const emptyGroup = document.createElement('div');
        emptyGroup.className = 'group';
        emptyGroup.innerHTML = `<div class="empty-state"><p>${selectedFileId === 'all' ? '개인정보가 발견되지 않았습니다.' : '선택한 파일에서 개인정보가 발견되지 않았습니다.'}</p></div>`;
        sidebar.appendChild(emptyGroup);
    }
    
    setupMaskingListEvents();
}

function setupMaskingListEvents() {
    // 그룹 토글 이벤트
    document.querySelectorAll('.sidebar .group').forEach(g => {
        const btn = g.querySelector('.group-toggle');
        const list = g.querySelector('.items');
        if (btn && list) {
            btn.addEventListener('click', () => {
                g.classList.toggle('collapsed');
                const isOpen = !g.classList.contains('collapsed');
                list.classList.toggle('hidden', !isOpen); 
                btn.setAttribute('aria-expanded', String(isOpen));
            });
        }
    });
    
    // 체크박스 이벤트
    document.querySelectorAll('.sidebar [data-check]').forEach(btn => {
        btn.addEventListener('click', e => {
            e.stopPropagation();
            const checkbox = e.currentTarget;
            const li = checkbox.closest('.item');
            const isOn = checkbox.classList.toggle('on');
            checkbox.classList.toggle('off', !isOn);
            checkbox.setAttribute('aria-checked', String(isOn));
            if (li) { li.classList.toggle('checked', isOn); }
            const id = li?.getAttribute('data-ref');
            const mark = id ? document.getElementById(id) : null;
            if (mark) { mark.classList.toggle('masked', isOn); }
            console.log(`PII 마스킹 ${isOn ? '활성화' : '비활성화'}:`, li?.querySelector('.txt')?.textContent);
            handleCheckboxToggle(checkbox, li);
        });
    });
    
    // 아이템 선택 이벤트
    document.querySelectorAll('.sidebar .item').forEach(li => {
        li.addEventListener('click', (e) => {
            if(e.target.closest('[data-check],[data-copy],[data-jump]')) return;
            selectMaskingItem(li);
        });
    });
    
    // 점프 버튼 이벤트
    document.querySelectorAll('.sidebar .item [data-jump]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const li = e.currentTarget.closest('.item');
            selectMaskingItem(li);
        });
    });
    
    // 복사 버튼 이벤트
    document.querySelectorAll('.sidebar .item [data-copy]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const text = e.currentTarget.closest('.item').querySelector('.txt').textContent.trim();
            try {
                await navigator.clipboard.writeText(text);
                btn.classList.add('ok');
                setTimeout(() => btn.classList.remove('ok'), 800);
            } catch(err) {
                console.error('복사 실패:', err);
            }
        });
    });
}

function selectMaskingItem(li) {
    $$('.sidebar .item').forEach(n => n.classList.remove('selected'));
    li.classList.add('selected');
    $$('.mark').forEach(m => m.classList.remove('active'));
    const mark = $(`#${li.getAttribute('data-ref')}`);
    if (mark) { 
        mark.classList.add('active'); 
        mark.scrollIntoView({ behavior: 'smooth', block: 'center' }); 
    }
}

// ==========================
// PII Finding Helper
// ==========================
function findPiiById(id) {
    const parts = id.split('-');
    if (parts.length !== 3 || parts[0] !== 'pii') {
        console.error('Invalid PII ID format:', id);
        return null;
    }
    
    const fileIndex = parseInt(parts[1]);
    const entityIndex = parseInt(parts[2]);
    
    if (fileIndex >= 0 && fileIndex < piiAnalysisResults.length) {
        const result = piiAnalysisResults[fileIndex];
        if (result.status === 'ANALYSIS_COMPLETED' && 
            result.analysis_data && 
            result.analysis_data.pii_entities &&
            entityIndex >= 0 && 
            entityIndex < result.analysis_data.pii_entities.length) {
            
            const entity = result.analysis_data.pii_entities[entityIndex];
            const coordinates = entity.coordinates || [];
            
            // instance_index 계산
            let instance_index = 0;
            for (let i = 0; i < result.analysis_data.pii_entities.length; i++) {
                const e = result.analysis_data.pii_entities[i];
                if (e.text === entity.text && e.type === entity.type) {
                    if (i === entityIndex) break;
                    instance_index++;
                }
            }
            
            if (coordinates.length > 0) {
                const firstCoord = coordinates[0];
                console.log(`[findPiiById] '${entity.text}' - 좌표 있음, instance: ${instance_index}`);
                
                return {
                    filename: result.filename,
                    pii_type: entity.type,
                    text: entity.text,
                    start_char: entity.start_char,
                    end_char: entity.end_char,
                    pageIndex: firstCoord.pageIndex || 0,
                    instance_index: instance_index,
                    bbox: firstCoord.bbox || null
                };
            } else {
                console.warn(`[findPiiById] '${entity.text}' - 좌표 없음, 파일: ${result.filename}`);
                
                return {
                    filename: result.filename,
                    pii_type: entity.type,
                    text: entity.text,
                    start_char: entity.start_char,
                    end_char: entity.end_char,
                    pageIndex: 0,
                    instance_index: instance_index,
                    bbox: null
                };
            }
        }
    }
    
    console.error('PII not found for ID:', id);
    return null;
}

// ==========================
// Custombar interactions
// ==========================
function selectCustomItem(li){
    $$('.custombar .item').forEach(n=>n.classList.remove('selected'));
    li.classList.add('selected');
}

// ==========================
// DOM Ready & Event Listeners
// ==========================
document.addEventListener('DOMContentLoaded', () => {
    // Custombar 이벤트
    $$('.custombar .group-toggle').forEach(btn => { 
        btn.addEventListener('click', () => btn.closest('.group').classList.toggle('collapsed')); 
    });
    
    $$('.custombar .item').forEach(li=>{ 
        li.addEventListener('click', (e)=>{ 
            if(e.target.closest('[data-check],[data-copy],[data-jump]')) return; 
            selectCustomItem(li); 
        }); 
    });
    
    $$('.custombar [data-check]').forEach(btn => { 
        btn.addEventListener('click', e => { 
            e.stopPropagation(); 
            const checkbox = e.currentTarget; 
            const li = checkbox.closest('.item'); 
            const isOn = checkbox.classList.toggle('on'); 
            checkbox.classList.toggle('off', !isOn); 
            if (li) li.classList.toggle('checked', isOn); 
            const subId = li?.dataset.sub; 
            if (subId) { 
                const sub = $(`#${subId}`); 
                if (sub) sub.hidden = !isOn; 
            } 
        }); 
    });

    // Edit button & modal
    const editBtn = $(".btn.edit");
    const modal = $("#modal");
    const modalClose = $("#modalClose");
    
    if (editBtn && modal && modalClose) { 
        editBtn.addEventListener("click", (e) => {
            const inside = $$('#group-inside .checkbox.on');
            const outside = $$('#group-outside .checkbox.on');
            if (inside.length === 0 && outside.length === 0) {
                e.preventDefault();
                modal.classList.remove("hidden");
            } else {
                console.log("커스텀 완료");
            }
        }); 
        modalClose.addEventListener("click", () => modal.classList.add("hidden")); 
    }

    // Masking button
    const maskingBtn = document.getElementById('maskingBtn');
    if (maskingBtn) {
        maskingBtn.addEventListener('click', async () => {
            const checkedItems = document.querySelectorAll('.sidebar .item.checked');
            const piiToMask = [];

            console.log('🔍 [디버그] 체크된 항목 수:', checkedItems.length);

            if (checkedItems.length === 0) {
                alert("마스킹할 PII 항목을 먼저 선택해주세요.");
                return;
            }

            checkedItems.forEach((item, index) => {
                const id = item.dataset.ref;
                console.log(`🔍 [디버그 ${index + 1}] PII ID:`, id);
                
                const piiData = findPiiById(id);
                console.log(`🔍 [디버그 ${index + 1}] PII Data:`, piiData);

                if (piiData) {
                    if (piiData.filename.toLowerCase().endsWith('.pdf') || 
                        piiData.filename.toLowerCase().endsWith('.png') ||
                        piiData.filename.toLowerCase().endsWith('.jpg') ||
                        piiData.filename.toLowerCase().endsWith('.jpeg')) {
                        
                        const maskData = {
                            filename: piiData.filename,
                            pii_type: piiData.pii_type,
                            text: piiData.text,
                            pageIndex: piiData.pageIndex,
                            instance_index: piiData.instance_index
                        };
                        
                        if (piiData.bbox && 
                            (piiData.filename.toLowerCase().endsWith('.png') ||
                            piiData.filename.toLowerCase().endsWith('.jpg') ||
                            piiData.filename.toLowerCase().endsWith('.jpeg'))) {
                            maskData.bbox = piiData.bbox;
                        }
                        
                        piiToMask.push(maskData);
                        console.log(`✅ [디버그] 마스킹 목록에 추가됨:`, maskData);
                    } else {
                        console.log(`⚠️ [디버그] 마스킹 대상이 아닌 파일:`, piiData.filename);
                    }
                } else {
                    console.error(`❌ [디버그] PII 데이터를 찾을 수 없음. ID:`, id);
                }
            });

            console.log('📋 [디버그] 최종 마스킹할 PII 목록:', piiToMask);

            if (piiToMask.length === 0) {
                alert("마스킹할 PDF/이미지 PII를 선택해주세요.\n\n현재 선택된 항목이 이메일 본문의 텍스트이거나, 좌표 정보가 없는 경우일 수 있습니다.");
                return;
            }

            try {
                const response = await fetch("http://127.0.0.1:8000/api/v1/process/masking/pdf", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(piiToMask)
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
                }

                const result = await response.json();
                console.log("PDF 마스킹 결과:", result);
                
                if (result.status === 'success') {
                    alert("마스킹이 완료되었습니다. `uploads` 폴더를 확인해주세요.");
                } else {
                    alert("마스킹 중 일부 오류가 발생했습니다. 콘솔을 확인해주세요.");
                }

            } catch (error) {
                console.error("마스킹 처리 중 오류 발생:", error);
                alert("마스킹 중 오류가 발생했습니다. 콘솔을 확인해주세요.");
            }
        });
    }

    // Approve button
    const approveBtn = $('#approveBtn');
    if (approveBtn) {
        approveBtn.addEventListener('click', async () => {
            console.log("승인 버튼 클릭됨");
            
            try {
                const metaResponse = await fetch("http://127.0.0.1:8000/uploads/email_meta.json");
                if (!metaResponse.ok) throw new Error("실제 수신자 정보를 불러오는 데 실패했습니다.");
                const metaData = await metaResponse.json();
                const recipients = metaData.recipients;
                const subject = metaData.subject;
                
                // ✅ 현재 활성화된 view에서만 editable-paragraph 찾기
                const activeView = document.querySelector('.view.active');
                if (!activeView) {
                    return alert("활성화된 뷰를 찾을 수 없습니다.");
                }
                
                const editableParagraphs = activeView.querySelectorAll('p.editable-paragraph');
                let finalBody;
                
                if (editableParagraphs.length > 0) {
                    // contenteditable로 수정된 내용 가져오기
                    finalBody = Array.from(editableParagraphs)
                        .map(p => p.textContent.trim())
                        .filter(text => text.length > 0)  // 빈 줄 제거
                        .join('\n');
                    console.log("✅ UI에서 수정된 본문 사용:", finalBody.substring(0, 100) + "...");
                } else {
                    // editable-paragraph가 없으면 전체 텍스트 사용
                    finalBody = activeView.innerText;
                    console.log("⚠️ 일반 텍스트 사용:", finalBody.substring(0, 100) + "...");
                }
                
                const attachments = [];
                for (const file of filesData.filter(f => f.kind !== 'email')) {
                    const maskedFileName = `masked_${file.name}`;
                    
                    try {
                        const checkResponse = await fetch(`http://127.0.0.1:8000/uploads/${maskedFileName}`, { method: 'HEAD' });
                        if (checkResponse.ok) {
                            attachments.push(maskedFileName);
                            console.log(`✅ 마스킹된 파일 사용: ${maskedFileName}`);
                        } else {
                            attachments.push(file.name);
                            console.log(`ℹ️ 원본 파일 사용: ${file.name}`);
                        }
                    } catch (error) {
                        attachments.push(file.name);
                        console.log(`⚠️ 파일 확인 실패, 원본 사용: ${file.name}`);
                    }
                }
                
                console.log("최종 발송될 내용:", { recipients, subject, finalBody, attachments });
                
                const response = await fetch("http://127.0.0.1:8000/api/v1/process/approve_and_send", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ recipients, subject, final_body: finalBody, attachments })
                });
                
                if (!response.ok) { 
                    const err = await response.json(); 
                    throw new Error(err.detail || '메일 발송 실패'); 
                }
                alert("최종 승인 메일이 성공적으로 발송되었습니다.\n✅ UI에서 수정한 내용이 반영되었습니다.\nuploads 폴더가 비워졌습니다.");
                
                filesData = [];
                piiAnalysisResults = [];
                recipientsData = [];
                currentSelectedFile = 'all';
                emailMetaData = {};
                
                location.reload();
            } catch (error) {
                console.error("최종 메일 발송 중 오류 발생:", error);
                alert(`메일 발송 중 오류가 발생했습니다: ${error.message}`);
            }
        });
    }
});

// ==========================
// Recipients toggle
// ==========================
const recipToggle = $('#recipToggle');
if(recipToggle) {
    recipToggle.addEventListener('click', ()=>{
        recipCollapsed = !recipCollapsed;
        renderRecipients(recipCollapsed);
    });
}

// ==========================
// Real-time File Change Detection (SSE)
// ==========================
let isUserEditing = false;
let editingTimeout = null;
let eventSource = null;

// 사용자 편집 상태 추적
document.addEventListener('DOMContentLoaded', () => {
    // 기존 DOMContentLoaded 내용은 그대로 두고, 아래 리스너만 추가
    document.addEventListener('input', (e) => {
        if (e.target.classList.contains('editable-paragraph')) {
            isUserEditing = true;
            console.log("✏️ 사용자 편집 중...");
            
            clearTimeout(editingTimeout);
            editingTimeout = setTimeout(() => {
                isUserEditing = false;
                console.log("✓ 편집 종료");
            }, 5000);
        }
    });
});

// ✅ SSE 연결 시작
function startFileWatcher() {
    if (eventSource) {
        eventSource.close();
    }
    
    console.log("🔌 파일 변경 감지 시작 (SSE)");
    eventSource = new EventSource("http://127.0.0.1:8000/api/v1/files/files/watch");
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.changed) {
            console.log("⚡ 실시간 파일 변경 감지!", data.timestamp);
            
            // 사용자가 편집 중이면 새로고침 연기
            if (isUserEditing) {
                console.log("⏸️ 사용자 편집 중 - 새로고침 연기");
                return;
            }
            
            console.log("🔄 UI 자동 새로고침");
            fetchAndRenderFiles();
        }
    };
    
    eventSource.onerror = (error) => {
        console.error("❌ SSE 연결 오류:", error);
        eventSource.close();
        
        // 5초 후 재연결 시도
        setTimeout(() => {
            console.log("🔄 SSE 재연결 시도...");
            startFileWatcher();
        }, 5000);
    };
}

// 페이지 종료 시 SSE 연결 해제
window.addEventListener('beforeunload', () => {
    if (eventSource) {
        eventSource.close();
    }
});

// ==========================
// Initial Execution
// ==========================
fetchAndRenderFiles().then(() => {
    startFileWatcher();
});