/**
 * API 클라이언트
 * 백엔드 API와 통신하는 함수들
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * API 요청 헬퍼 함수
 */
async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }))
      throw new Error(error.detail || `API 요청 실패: ${response.statusText}`)
    }

    const data = await response.json()

    // 백엔드 응답 형식: { success: true, data: ... }
    if (data.success && data.data !== undefined) {
      return data.data as T
    }

    return data as T
  } catch (error) {
    console.error('API 요청 오류:', error)
    throw error
  }
}

/**
 * 정책 목록 조회
 */
export async function getPolicies(
  skip: number = 0,
  limit: number = 50,
  authority?: string
): Promise<any[]> {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  })

  if (authority && authority !== 'all') {
    params.append('authority', authority)
  }

  console.log('[API] 정책 목록 조회:', `${API_BASE_URL}/api/policies/list?${params.toString()}`)

  try {
    const response = await fetch(`${API_BASE_URL}/api/policies/list?${params.toString()}`)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('[API] 정책 목록 조회 실패:', response.status, errorText)
      throw new Error(`정책 목록 조회 실패: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    console.log('[API] 정책 목록 조회 성공:', data)

    // 응답 구조 확인
    if (data.success && data.data && data.data.policies) {
      return data.data.policies
    } else if (Array.isArray(data)) {
      // 직접 배열이 반환되는 경우
      return data
    } else {
      console.warn('[API] 예상치 못한 응답 구조:', data)
      return []
    }
  } catch (error) {
    console.error('[API] 정책 목록 조회 오류:', error)
    throw error
  }
}

/**
 * 정책 상세 조회
 */
export async function getPolicyDetail(policyId: string): Promise<any> {
  return await apiRequest<any>(`/api/policies/${policyId}`)
}

/**
 * 정책 삭제
 */
export async function deletePolicy(policyId: string): Promise<void> {
  console.log('🗑️ [API] deletePolicy 호출:', policyId)

  const token = localStorage.getItem('auth_token')
  if (!token) {
    throw new Error('인증 토큰이 없습니다.')
  }

  const response = await fetch(`${API_BASE_URL}/api/policies/${policyId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  console.log('📥 [API] 삭제 응답:', response.status)

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    console.error('❌ [API] 삭제 실패:', errorData)
    throw new Error(errorData.detail || errorData.message || '정책 삭제 실패')
  }

  const data = await response.json()
  console.log('✅ [API] 삭제 성공:', data)

  if (!data.success) {
    throw new Error(data.message || '정책 삭제 실패')
  }
}

/**
 * 정책 텍스트 수정
 */
export async function updatePolicyText(
  policyId: string,
  extractedText: string
): Promise<any> {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const token = localStorage.getItem('auth_token')

  if (!token) {
    throw new Error('인증 토큰이 없습니다. 다시 로그인해주세요.')
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/policies/${policyId}/text`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        extracted_text: extractedText,
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }))
      throw new Error(error.detail || '텍스트 수정에 실패했습니다')
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('텍스트 수정 오류:', error)
    throw error
  }
}

/**
 * 정책 통계 조회
 */
export async function getPolicyStats(): Promise<{
  total_policies: number
  total_entities: number
  by_authority?: Record<string, number>
  by_file_type?: Record<string, number>
}> {
  return await apiRequest<{
    total_policies: number
    total_entities: number
    by_authority?: Record<string, number>
    by_file_type?: Record<string, number>
  }>('/api/policies/stats/summary')
}

/**
 * 정책 파일 업로드
 */
export async function uploadPolicyFile(
  file: File,
  title: string,
  authority: string,
  description: string
): Promise<any> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('title', title)
  formData.append('authority', authority)
  formData.append('description', description)

  console.log('📤 [API] uploadPolicyFile 호출:', {
    filename: file.name,
    size: file.size,
    title,
    authority,
  })

  const token = localStorage.getItem('auth_token')
  if (!token) {
    throw new Error('인증 토큰이 없습니다. 다시 로그인해주세요.')
  }

  const response = await fetch(`${API_BASE_URL}/api/policies/upload`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  console.log('📥 [API] 응답 상태:', response.status)

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    console.error('❌ [API] 업로드 실패:', errorData)
    throw new Error(errorData.detail || errorData.message || '정책 업로드 실패')
  }

  const data = await response.json()
  console.log('✅ [API] 업로드 성공:', data)

  if (!data.success) {
    throw new Error(data.message || '정책 업로드 실패')
  }

  return data.data
}

/**
 * 정책 스키마 목록 조회
 */
export async function getPolicySchemas(
  skip: number = 0,
  limit: number = 50,
  refreshCache: boolean = false
): Promise<{
  total: number
  schemas: any[]
  cached: boolean
  cache_expires_in: number
}> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
    refresh_cache: refreshCache.toString(),
  })

  return await apiRequest<{
    total: number
    schemas: any[]
    cached: boolean
    cache_expires_in: number
  }>(`/api/policies/schemas?${params.toString()}`)
}

/**
 * 백그라운드 작업 상태 조회
 */
export async function getTaskStatus(taskId: string): Promise<any> {
  return await apiRequest<any>(`/api/policies/tasks/${taskId}/status`)
}

/**
 * 백그라운드 작업 상태를 폴링하여 완료될 때까지 추적
 */
export async function pollTaskStatus(
  taskId: string,
  onProgress?: (progress: number, message: string) => void,
  interval: number = 2000
): Promise<any> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getTaskStatus(taskId)

        // 진행 상황 콜백 호출
        if (onProgress && status.progress !== undefined) {
          onProgress(status.progress, status.message || '')
        }

        // 완료된 경우
        if (status.status === 'completed') {
          resolve(status)
          return
        }

        // 실패한 경우
        if (status.status === 'failed') {
          reject(new Error(status.error || '작업이 실패했습니다'))
          return
        }

        // 아직 진행 중이면 다시 폴링
        if (status.status === 'processing' || status.status === 'pending') {
          setTimeout(poll, interval)
        }
      } catch (error) {
        reject(error)
      }
    }

    poll()
  })
}

/**
 * Vector Store 동기화 상태 조회
 */
export async function getSyncStatus(): Promise<{
  mongodb: {
    total_policies: number
    synced_to_vector_store: number
    not_synced: number
  }
  vector_store: {
    id: string
    name: string
    status: string
    file_counts: {
      total: number
      completed: number
      in_progress: number
      failed: number
    }
  } | null
  sync_needed: boolean
}> {
  return await apiRequest<{
    mongodb: {
      total_policies: number
      synced_to_vector_store: number
      not_synced: number
    }
    vector_store: {
      id: string
      name: string
      status: string
      file_counts: {
        total: number
        completed: number
        in_progress: number
        failed: number
      }
    } | null
    sync_needed: boolean
  }>('/api/policies/sync/status')
}

/**
 * 모든 정책을 Vector Store에 동기화
 */
export async function syncPoliciesToVectorStore(): Promise<{
  synced: Array<{ policy_id: string; title: string; file_id: string }>
  skipped: Array<{ policy_id: string; title: string; reason: string }>
  failed: Array<{ policy_id: string; title: string; reason: string }>
  total_in_mongodb: number
  total_in_vector_store: number
  vector_store_id: string
}> {
  const token = localStorage.getItem('auth_token')

  const response = await fetch(`${API_BASE_URL}/api/policies/sync/vector-store`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }))
    throw new Error(error.detail || '동기화 실패')
  }

  const data = await response.json()
  return data.data
}

/**
 * Vector Store에서 정책 제거
 */
export async function removePolicyFromVectorStore(policyId: string): Promise<void> {
  const token = localStorage.getItem('auth_token')

  const response = await fetch(`${API_BASE_URL}/api/policies/sync/vector-store/${policyId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }))
    throw new Error(error.detail || 'Vector Store에서 정책 제거 실패')
  }
}

/**
 * 정책 가이드라인 수정
 */
export async function updatePolicyGuidelines(
  policyId: string,
  guidelines: any[]
): Promise<any> {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const token = localStorage.getItem('auth_token')

  if (!token) {
    throw new Error('인증 토큰이 없습니다. 다시 로그인해주세요.')
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/policies/${policyId}/guidelines`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        guidelines: guidelines,
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }))
      throw new Error(error.detail || '가이드라인 수정에 실패했습니다')
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('가이드라인 수정 오류:', error)
    throw error
  }
}
