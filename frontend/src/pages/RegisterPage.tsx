import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

// API 기본 URL 추가 (LoginPage.tsx 참고)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface RegisterFormData {
  email: string
  nickname: string
  department: string
  password: string
  confirmPassword: string
}

interface RegisterPageProps {
  onRegister?: (data: RegisterFormData) => void // 이건 이제 사용하지 않을 수 있습니다.
  onShowLogin?: () => void
}

export const RegisterPage: React.FC<RegisterPageProps> = ({
  onRegister, // onRegister prop은 이제 로직이 여기로 옮겨졌으므로 사용되지 않을 수 있습니다.
  onShowLogin,
}) => {
  const [formData, setFormData] = useState<RegisterFormData>({
    email: '',
    nickname: '',
    department: '',
    password: '',
    confirmPassword: '',
  })

  const [message, setMessage] = useState<{
    type: 'success' | 'error'
    text: string
  } | null>(null)
  
  // 로딩 상태 추가
  const [isLoading, setIsLoading] = useState(false)

  // handleSubmit을 async 함수로 변경
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage(null)

    // 비밀번호 확인
    if (formData.password !== formData.confirmPassword) {
      setMessage({
        type: 'error',
        text: '비밀번호가 일치하지 않습니다.',
      })
      return
    }

    // 비밀번호 길이 확인
    if (formData.password.length < 8) {
      setMessage({
        type: 'error',
        text: '비밀번호는 최소 8자 이상이어야 합니다.',
      })
      return
    }

    setIsLoading(true)

    try {
      // API 호출 (백엔드의 회원가입 엔드포인트로)
      // '/api/auth/register'는 예시이며, 실제 백엔드 엔드포인트 주소로 변경해야 합니다.
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          nickname: formData.nickname,
          team_name: formData.department, // 백엔드 모델에 맞게 키 이름 조정 (예: department -> team_name)
          password: formData.password,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || '회원가입에 실패했습니다.')
      }

      // 회원가입 성공
      setMessage({
        type: 'success',
        text: '회원가입 성공! 로그인 페이지로 이동합니다.',
      })

      // 2초 후 로그인 페이지로 자동 이동
      setTimeout(() => {
        onShowLogin?.()
      }, 2000)

    } catch (error) {
      console.error('회원가입 오류:', error)
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
      })
    } finally {
      setIsLoading(false)
    }
    
    // 이 onRegister는 부모의 prop이므로, 실제 API 호출은 여기서 수행해야 합니다.
    // onRegister?.(formData) // 이 줄은 제거하거나, API 호출 로직을 이 함수로 대체
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary/10 via-background to-primary/5 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-2 text-center">
          <CardTitle className="text-3xl font-bold text-primary">MASKIT</CardTitle>
          <CardDescription className="text-base">이메일 마스킹 시스템</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">이메일</Label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                required
                disabled={isLoading} 
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="nickname">이름</Label>
              <Input
                id="nickname"
                placeholder="이름"
                value={formData.nickname}
                onChange={(e) =>
                  setFormData({ ...formData, nickname: e.target.value })
                }
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="department">팀</Label>
              <Select
                value={formData.department}
                onValueChange={(value) =>
                  setFormData({ ...formData, department: value })
                }
                required
                disabled={isLoading}
              >
                <SelectTrigger id="department">
                  <SelectValue placeholder="팀을 선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="개발팀">개발팀</SelectItem>
                  <SelectItem value="기획팀">기획팀</SelectItem>
                  <SelectItem value="디자인팀">디자인팀</SelectItem>
                  <SelectItem value="마케팅팀">마케팅팀</SelectItem>
                  <SelectItem value="영업팀">영업팀</SelectItem>
                  <SelectItem value="인사팀">인사팀</SelectItem>
                  <SelectItem value="사무팀">사무팀</SelectItem>
                  <SelectItem value="경영지원팀">경영지원팀</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">비밀번호</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">비밀번호 확인</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={formData.confirmPassword}
                onChange={(e) =>
                  setFormData({ ...formData, confirmPassword: e.target.value })
                }
                required
                disabled={isLoading}
              />
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? '가입 중...' : '회원가입'}
            </Button>
          </form>

          {/* 메시지 표시 */}
          {message && (
            <div
              className={`mt-4 rounded-lg p-3 text-center text-sm ${
                message.type === 'success'
                  ? 'bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                  : 'bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-400'
              }`}
            >
              {message.text}
            </div>
          )}

          <div className="mt-6 text-center text-sm">
            <span className="text-muted-foreground">
              이미 계정이 있으신가요?{' '}
            </span>
            <button
              type="button"
              onClick={onShowLogin}
              className="font-semibold text-primary hover:underline"
              disabled={isLoading}
            >
              로그인
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}