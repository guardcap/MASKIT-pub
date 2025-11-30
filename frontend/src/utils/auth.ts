/**
 * 인증 관련 유틸리티 함수
 */

/**
 * 401 Unauthorized 응답 처리
 * - 로컬 스토리지에서 인증 정보 제거
 * - 에러 메시지 반환
 */
export function handle401Error(): string {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user')
  return '인증이 만료되었습니다. 다시 로그인해주세요.'
}

/**
 * 로그인 페이지로 리다이렉트 (3초 후)
 */
export function redirectToLogin(delay: number = 3000): void {
  setTimeout(() => {
    window.location.href = '/login'
  }, delay)
}

/**
 * fetch 응답을 체크하고 401 에러를 처리
 */
export async function handleResponse(response: Response): Promise<any> {
  if (!response.ok) {
    if (response.status === 401) {
      const errorMessage = handle401Error()
      redirectToLogin()
      throw new Error(errorMessage)
    }

    // 다른 HTTP 에러
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || errorData.message || `요청 실패 (${response.status})`)
  }

  return response.json()
}

/**
 * 인증된 fetch 요청
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<any> {
  const token = localStorage.getItem('auth_token')

  if (!token) {
    throw new Error('인증 토큰이 없습니다. 로그인해주세요.')
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  })

  return handleResponse(response)
}
