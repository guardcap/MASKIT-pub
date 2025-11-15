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

interface LoginFormData {
  userId: string
  userName: string
  userEmail: string
  userTeam: string
  userRole: string
}

interface LoginPageProps {
  onLogin?: (data: LoginFormData) => void
  onShowRegister?: () => void
}

export const LoginPage: React.FC<LoginPageProps> = ({
  onLogin,
  onShowRegister,
}) => {
  const [formData, setFormData] = useState<LoginFormData>({
    userId: '',
    userName: '',
    userEmail: '',
    userTeam: '',
    userRole: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onLogin?.(formData)
  }

  const handleTestUserLogin = (role: string) => {
    const testUsers: Record<string, LoginFormData> = {
      admin: {
        userId: 'admin',
        userName: '시스템관리자',
        userEmail: 'admin@example.com',
        userTeam: 'IT팀',
        userRole: 'sys_admin',
      },
      policy: {
        userId: 'policy',
        userName: '정책관리자',
        userEmail: 'policy@example.com',
        userTeam: '보안팀',
        userRole: 'policy_admin',
      },
      auditor: {
        userId: 'auditor',
        userName: '감사자',
        userEmail: 'auditor@example.com',
        userTeam: '감사팀',
        userRole: 'auditor',
      },
      approver: {
        userId: 'approver',
        userName: '승인자',
        userEmail: 'approver@example.com',
        userTeam: '관리팀',
        userRole: 'approver',
      },
      user: {
        userId: 'user',
        userName: '일반사용자',
        userEmail: 'user@example.com',
        userTeam: '개발팀',
        userRole: 'user',
      },
    }

    const userData = testUsers[role]
    if (userData) {
      onLogin?.(userData)
    }
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
              <Label htmlFor="userId">사용자 ID</Label>
              <Input
                id="userId"
                placeholder="사용자 ID"
                value={formData.userId}
                onChange={(e) =>
                  setFormData({ ...formData, userId: e.target.value })
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="userName">이름</Label>
              <Input
                id="userName"
                placeholder="이름"
                value={formData.userName}
                onChange={(e) =>
                  setFormData({ ...formData, userName: e.target.value })
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="userEmail">이메일</Label>
              <Input
                id="userEmail"
                type="email"
                placeholder="이메일"
                value={formData.userEmail}
                onChange={(e) =>
                  setFormData({ ...formData, userEmail: e.target.value })
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="userTeam">팀</Label>
              <Input
                id="userTeam"
                placeholder="팀"
                value={formData.userTeam}
                onChange={(e) =>
                  setFormData({ ...formData, userTeam: e.target.value })
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="userRole">역할</Label>
              <Select
                value={formData.userRole}
                onValueChange={(value) =>
                  setFormData({ ...formData, userRole: value })
                }
                required
              >
                <SelectTrigger id="userRole">
                  <SelectValue placeholder="역할 선택" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sys_admin">시스템 관리자</SelectItem>
                  <SelectItem value="policy_admin">정책 관리자</SelectItem>
                  <SelectItem value="auditor">감사자</SelectItem>
                  <SelectItem value="approver">승인자</SelectItem>
                  <SelectItem value="user">사용자</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button type="submit" className="w-full">
              로그인
            </Button>
          </form>

          {/* 테스트 사용자 빠른 로그인 */}
          <div className="mt-6 space-y-3">
            <p className="text-center text-sm text-muted-foreground">
              테스트 사용자 로그인:
            </p>
            <div className="grid grid-cols-2 gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleTestUserLogin('admin')}
              >
                시스템 관리자
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleTestUserLogin('policy')}
              >
                정책 관리자
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleTestUserLogin('auditor')}
              >
                감사자
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleTestUserLogin('approver')}
              >
                승인자
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="col-span-2"
                onClick={() => handleTestUserLogin('user')}
              >
                사용자
              </Button>
            </div>
          </div>

          <div className="mt-6 text-center text-sm">
            <span className="text-muted-foreground">
              아직 계정이 없으신가요?{' '}
            </span>
            <button
              type="button"
              onClick={onShowRegister}
              className="font-semibold text-primary hover:underline"
            >
              회원가입
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
