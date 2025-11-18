import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  ArrowLeft,
  Mail,
  Paperclip,
  Download,
  User,
  Calendar,
} from 'lucide-react'

interface EmailDetail {
  _id: string
  from_email: string
  to_email: string
  subject: string
  body: string
  created_at: string
  sent_at?: string
  read_at?: string
  attachments?: Array<{
    file_id: string
    filename: string
    size: number
    content_type: string
  }>
  masking_decisions?: Record<string, any>
}

interface EmailDetailPageProps {
  emailId: string
  onBack: () => void
}

export function EmailDetailPage({ emailId, onBack }: EmailDetailPageProps) {
  const [email, setEmail] = useState<EmailDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadEmailDetail()
  }, [emailId])

  const loadEmailDetail = async () => {
    try {
      setLoading(true)
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
      const token = localStorage.getItem('auth_token')

      if (!token) {
        throw new Error('인증 토큰이 없습니다.')
      }

      const response = await fetch(`${API_BASE}/api/v1/emails/email/${emailId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('메일을 불러오는데 실패했습니다.')
      }

      const data = await response.json()
      setEmail(data)
      setError(null)
    } catch (err) {
      console.error('Error loading email detail:', err)
      setError(err instanceof Error ? err.message : '오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
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

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const handleDownloadAttachment = async (fileId: string, filename: string) => {
    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
      const token = localStorage.getItem('auth_token')

      const response = await fetch(
        `${API_BASE}/api/v1/emails/email/${emailId}/attachments/${fileId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (!response.ok) {
        throw new Error('파일 다운로드에 실패했습니다.')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      console.error('Error downloading attachment:', err)
      alert(err instanceof Error ? err.message : '파일 다운로드 중 오류가 발생했습니다.')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          뒤로 가기
        </Button>
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">메일을 불러오는 중...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error || !email) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          뒤로 가기
        </Button>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error || '메일을 찾을 수 없습니다.'}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          뒤로 가기
        </Button>
      </div>

      {/* 메일 정보 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">{email.subject}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 발신/수신 정보 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <User className="h-4 w-4" />
                <span className="font-semibold">보낸 사람:</span>
              </div>
              <p className="text-sm">{email.from_email}</p>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Mail className="h-4 w-4" />
                <span className="font-semibold">받는 사람:</span>
              </div>
              <p className="text-sm">{email.to_email}</p>
            </div>
          </div>

          {/* 날짜 정보 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span className="font-semibold">작성일:</span>
              </div>
              <p className="text-sm">{formatDate(email.created_at)}</p>
            </div>
            {email.sent_at && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span className="font-semibold">전송일:</span>
                </div>
                <p className="text-sm">{formatDate(email.sent_at)}</p>
              </div>
            )}
          </div>

          {/* 구분선 */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold mb-4">메일 본문</h3>
            <div className="prose prose-sm max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-sm">{email.body}</pre>
            </div>
          </div>

          {/* 첨부파일 */}
          {email.attachments && email.attachments.length > 0 && (
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Paperclip className="h-5 w-5" />
                첨부파일 ({email.attachments.length}개)
              </h3>
              <div className="space-y-2">
                {email.attachments.map((attachment, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{attachment.filename}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(attachment.size)} • {attachment.content_type}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownloadAttachment(attachment.file_id, attachment.filename)}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      다운로드
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
