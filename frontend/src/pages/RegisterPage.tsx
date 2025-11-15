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

interface RegisterFormData {
  email: string
  nickname: string
  department: string
  password: string
  confirmPassword: string
}

interface RegisterPageProps {
  onRegister?: (data: RegisterFormData) => void
  onShowLogin?: () => void
}

export const RegisterPage: React.FC<RegisterPageProps> = ({
  onRegister,
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

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

    setMessage(null)
    onRegister?.(formData)
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
              />
            </div>

            <Button type="submit" className="w-full">
              회원가입
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
            >
              로그인
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
