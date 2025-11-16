import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Mail, Clock, CheckCircle, XCircle, Paperclip } from 'lucide-react'

interface Email {
  _id: string
  subject: string
  to_email: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  attachments?: any[]
}

interface UserDashboardPageProps {
  onNavigate?: (view: string, emailId?: string) => void
}

export function UserDashboardPage({ onNavigate }: UserDashboardPageProps) {
  const [emails, setEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (userData) {
      setUser(JSON.parse(userData))
    }
    loadEmails()
  }, [])

  const loadEmails = async () => {
    try {
      setLoading(true)
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
      const token = localStorage.getItem('auth_token')

      if (!token) {
        throw new Error('인증 토큰이 없습니다.')
      }

      const response = await fetch(`${API_BASE}/api/v1/emails/my-emails`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('메일을 불러오는데 실패했습니다.')
      }

      const data = await response.json()
      setEmails(data)
      setError(null)
    } catch (err) {
      console.error('Error loading emails:', err)
      setError(err instanceof Error ? err.message : '오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: { label: '승인 대기', variant: 'secondary' as const, icon: Clock },
      approved: { label: '승인 완료', variant: 'default' as const, icon: CheckCircle },
      rejected: { label: '반려', variant: 'destructive' as const, icon: XCircle },
    }
    const config = variants[status as keyof typeof variants] || variants.pending
    const Icon = config.icon

    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">🛡️ MASKIT</h1>
        <p className="text-muted-foreground">내 메일함</p>
      </div>

      {/* 메뉴 버튼 */}
      <div className="flex flex-wrap gap-3">
        <Button variant="default" onClick={() => loadEmails()}>
          대시보드
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('my-emails')}>
          보낸 메일함
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('received-emails')}>
          받은 메일함
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('my-statistics')}>
          내 통계
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('my-logs')}>
          내 로그
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('policy-view')}>
          정책 조회
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('entity-view')}>
          엔티티 조회
        </Button>
      </div>

      {/* 메일 목록 */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">메일을 불러오는 중...</p>
          </CardContent>
        </Card>
      ) : emails.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">메일이 없습니다</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>메일 목록</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {emails.map((email) => (
              <div
                key={email._id}
                className="flex items-start justify-between p-4 border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors"
                onClick={() => onNavigate?.('email-detail', email._id)}
              >
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-lg">{email.subject}</h3>
                    {getStatusBadge(email.status)}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>받는이: {email.to_email}</span>
                    <span>•</span>
                    <span>{formatDate(email.created_at)}</span>
                    {email.attachments && email.attachments.length > 0 && (
                      <>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Paperclip className="h-3 w-3" />
                          {email.attachments.length}개
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 메일 작성 버튼 (고정) */}
      <Button
        className="fixed bottom-8 right-8 rounded-full h-14 px-6 shadow-lg"
        size="lg"
        onClick={() => onNavigate?.('write-email')}
      >
        <Mail className="h-5 w-5 mr-2" />
        메일 작성
      </Button>
    </div>
  )
}
