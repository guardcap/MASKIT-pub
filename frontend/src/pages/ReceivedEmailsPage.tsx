import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Mail, Clock, CheckCircle, XCircle, Paperclip, ArrowLeft, Inbox } from 'lucide-react'

interface Email {
  _id: string
  subject: string
  from_email: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  attachments?: any[]
  read?: boolean
}

interface ReceivedEmailsPageProps {
  onNavigate?: (view: string, emailId?: string) => void
  onBack?: () => void
}

export function ReceivedEmailsPage({ onNavigate, onBack }: ReceivedEmailsPageProps) {
  const [emails, setEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadReceivedEmails()
  }, [])

  const loadReceivedEmails = async () => {
    try {
      setLoading(true)
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
      const token = localStorage.getItem('auth_token')

      if (!token) {
        throw new Error('인증 토큰이 없습니다.')
      }

      // 받은 메일함 API 엔드포인트 (백엔드에 구현 필요)
      const response = await fetch(`${API_BASE}/api/v1/emails/received-emails`, {
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
      console.error('Error loading received emails:', err)
      setError(err instanceof Error ? err.message : '오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: { label: '승인 대기', variant: 'secondary' as const, icon: Clock },
      approved: { label: '수신 완료', variant: 'default' as const, icon: CheckCircle },
      rejected: { label: '반려됨', variant: 'destructive' as const, icon: XCircle },
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
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">받은 메일함</h1>
          <p className="text-muted-foreground">받은 메일 목록</p>
        </div>
        {onBack && (
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            뒤로 가기
          </Button>
        )}
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전체 메일</CardTitle>
            <Inbox className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{emails.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">읽지 않음</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {emails.filter((e) => !e.read).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">수신 완료</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {emails.filter((e) => e.status === 'approved').length}
            </div>
          </CardContent>
        </Card>
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
            <div className="text-center space-y-4">
              <Inbox className="h-12 w-12 mx-auto text-muted-foreground" />
              <p className="text-muted-foreground">받은 메일이 없습니다</p>
            </div>
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
                className={`flex items-start justify-between p-4 border rounded-lg hover:bg-accent/50 cursor-pointer transition-colors ${
                  !email.read ? 'bg-blue-50/50 border-blue-200' : ''
                }`}
                onClick={() => onNavigate?.('email-detail', email._id)}
              >
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className={`font-semibold text-lg ${!email.read ? 'text-blue-900' : ''}`}>
                      {email.subject}
                    </h3>
                    {!email.read && (
                      <Badge variant="default" className="bg-blue-500">
                        New
                      </Badge>
                    )}
                    {getStatusBadge(email.status)}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>보낸이: {email.from_email}</span>
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
    </div>
  )
}
