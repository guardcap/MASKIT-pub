import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'
import { ArrowLeft, Mail, Calendar, Paperclip, Users, Eye, EyeOff } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface SentEmailDetailPageProps {
  emailId: string
  onBack?: () => void
}

interface EmailData {
  _id: string
  from_email: string
  to_emails?: string[]
  to_email?: string
  subject: string
  body?: string
  original_body?: string
  attachments?: AttachmentInfo[]
  created_at: string
  sent_at?: string
  status?: string
  masking_decisions?: any
  pii_masked_count?: number
}

interface AttachmentInfo {
  filename: string
  content_type: string
  size: number
  data?: string  // Base64 데이터
}

interface MaskedEmailData {
  email_id: string
  from_email: string
  to_emails: string[]
  subject: string
  masked_body: string
  masked_attachments: AttachmentInfo[]
  masking_decisions: any
  pii_masked_count: number
  created_at: string
}

export const SentEmailDetailPage: React.FC<SentEmailDetailPageProps> = ({
  emailId,
  onBack,
}) => {
  const [originalEmail, setOriginalEmail] = useState<EmailData | null>(null)
  const [maskedEmail, setMaskedEmail] = useState<MaskedEmailData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState<'compare' | 'original' | 'masked'>('compare')
  const [originalAttachmentUrls, setOriginalAttachmentUrls] = useState<Map<string, string>>(new Map())
  const [maskedAttachmentUrls, setMaskedAttachmentUrls] = useState<Map<string, string>>(new Map())

  useEffect(() => {
    loadEmailDetails()
    return () => {
      // Cleanup blob URLs
      originalAttachmentUrls.forEach(url => URL.revokeObjectURL(url))
      maskedAttachmentUrls.forEach(url => URL.revokeObjectURL(url))
    }
  }, [emailId])

  const loadEmailDetails = async () => {
    setLoading(true)
    let hasMaskedData = false
    try {
      const token = localStorage.getItem('auth_token')

      // 1. 원본 이메일 데이터 로드
      const emailResponse = await fetch(`${API_BASE_URL}/api/v1/files/original_emails/${emailId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (!emailResponse.ok) {
        throw new Error('원본 이메일을 불러오는데 실패했습니다.')
      }

      const emailResult = await emailResponse.json()
      if (emailResult.success && emailResult.data) {
        setOriginalEmail(emailResult.data)

        // 원본 첨부파일 Blob URL 생성
        if (emailResult.data.attachments) {
          const urlMap = new Map<string, string>()
          for (const attachment of emailResult.data.attachments) {
            try {
              const binaryString = atob(attachment.data)
              const bytes = new Uint8Array(binaryString.length)
              for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i)
              }
              const blob = new Blob([bytes], { type: attachment.content_type })
              const url = URL.createObjectURL(blob)
              urlMap.set(attachment.filename, url)
            } catch (error) {
              console.error(`원본 첨부파일 로드 실패: ${attachment.filename}`, error)
            }
          }
          setOriginalAttachmentUrls(urlMap)
        }
      }

      // 2. 마스킹된 이메일 데이터 로드
      const maskedResponse = await fetch(`${API_BASE_URL}/api/v1/files/masked_emails/${emailId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (maskedResponse.ok) {
        const maskedResult = await maskedResponse.json()
        if (maskedResult.success && maskedResult.data) {
          setMaskedEmail(maskedResult.data)
          hasMaskedData = true

          // 마스킹된 첨부파일 Blob URL 생성
          if (maskedResult.data.masked_attachments) {
            const urlMap = new Map<string, string>()
            for (const attachment of maskedResult.data.masked_attachments) {
              try {
                const binaryString = atob(attachment.data)
                const bytes = new Uint8Array(binaryString.length)
                for (let i = 0; i < binaryString.length; i++) {
                  bytes[i] = binaryString.charCodeAt(i)
                }
                const blob = new Blob([bytes], { type: attachment.content_type })
                const url = URL.createObjectURL(blob)
                urlMap.set(attachment.filename, url)
              } catch (error) {
                console.error(`마스킹 첨부파일 로드 실패: ${attachment.filename}`, error)
              }
            }
            setMaskedAttachmentUrls(urlMap)
          }
        }
      } else {
        console.log('마스킹된 이메일이 없습니다.')
      }

    } catch (error: any) {
      console.error('이메일 조회 오류:', error)
      toast.error(error.message || '이메일을 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
      // 마스킹 데이터가 없으면 원본 보기로 설정
      if (!hasMaskedData) {
        setActiveView('original')
      }
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

  // HTML을 텍스트로 변환하는 함수
  const htmlToText = (html: string): string => {
    if (!html) return ''

    // 임시 div 엘리먼트 생성
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = html

    // <br>, <div>, <p> 태그를 줄바꿈으로 변환
    tempDiv.innerHTML = tempDiv.innerHTML
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/div>/gi, '\n')
      .replace(/<\/p>/gi, '\n\n')
      .replace(/<div>/gi, '')
      .replace(/<p>/gi, '')

    // 텍스트 추출
    return tempDiv.textContent || tempDiv.innerText || ''
  }

  const renderAttachment = (attachment: AttachmentInfo, urlMap: Map<string, string>) => {
    const url = urlMap.get(attachment.filename)

    if (!url) {
      return <div className="text-sm text-gray-500">로딩 중...</div>
    }

    const isImage = attachment.content_type.startsWith('image/')
    const isPDF = attachment.content_type === 'application/pdf'

    if (isImage) {
      return (
        <img
          src={url}
          alt={`${attachment.filename} 미리보기`}
          className="max-w-full h-auto border rounded"
        />
      )
    } else if (isPDF) {
      return (
        <object
          data={url}
          type="application/pdf"
          className="w-full h-[600px] border rounded"
        >
          <p className="text-sm text-gray-500">
            PDF를 표시할 수 없습니다.
            <a href={url} download={attachment.filename} className="text-blue-500 underline ml-1">
              다운로드
            </a>
          </p>
        </object>
      )
    }

    return (
      <div className="p-4 border rounded bg-gray-50">
        <p className="text-sm">📄 {attachment.filename}</p>
        <a href={url} download={attachment.filename} className="text-blue-500 text-sm underline">
          다운로드
        </a>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="container mx-auto max-w-7xl p-6">
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-muted-foreground">이메일을 불러오는 중...</p>
        </div>
      </div>
    )
  }

  if (!originalEmail) {
    return (
      <div className="container mx-auto max-w-7xl p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800 text-center">이메일을 찾을 수 없습니다.</p>
            {onBack && (
              <Button onClick={onBack} className="mt-4 mx-auto block">
                <ArrowLeft className="mr-2 h-4 w-4" />
                뒤로 가기
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto max-w-7xl p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">📧 이메일 상세보기</h2>
          <p className="text-sm text-muted-foreground mt-1">원본과 마스킹 결과를 비교할 수 있습니다</p>
        </div>
        {onBack && (
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            뒤로 가기
          </Button>
        )}
      </div>

      {/* 이메일 기본 정보 */}
      <Card className="border-blue-200 bg-blue-50/50">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="text-lg">{originalEmail.subject}</span>
            {maskedEmail && (
              <Badge variant="default" className="bg-green-600">
                마스킹 완료
              </Badge>
            )}
          </CardTitle>
          <CardDescription>
            <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                <div>
                  <span className="font-medium">발신:</span>{' '}
                  <span className="text-foreground">{originalEmail.from_email}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                <div>
                  <span className="font-medium">수신:</span>{' '}
                  <span className="text-foreground">
                    {originalEmail.to_emails?.join(', ') || originalEmail.to_email}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                <div>
                  <span className="font-medium">작성:</span>{' '}
                  <span className="text-foreground">{formatDate(originalEmail.created_at)}</span>
                </div>
              </div>
              {originalEmail.attachments && originalEmail.attachments.length > 0 && (
                <div className="flex items-center gap-2">
                  <Paperclip className="h-4 w-4" />
                  <div>
                    <span className="font-medium">첨부파일:</span>{' '}
                    <span className="text-foreground">{originalEmail.attachments.length}개</span>
                  </div>
                </div>
              )}
            </div>
          </CardDescription>
        </CardHeader>
      </Card>

      {/* 마스킹 통계 (마스킹된 이메일이 있는 경우) */}
      {maskedEmail && (
        <Card className="border-green-200 bg-green-50/30">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Eye className="h-4 w-4" />
              마스킹 정보
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center p-3 bg-white rounded-lg border">
                <div className="text-2xl font-bold text-green-600">{maskedEmail.pii_masked_count || 0}</div>
                <div className="text-xs text-muted-foreground mt-1">마스킹된 PII</div>
              </div>
              <div className="text-center p-3 bg-white rounded-lg border">
                <div className="text-2xl font-bold text-blue-600">
                  {maskedEmail.masked_attachments?.length || 0}
                </div>
                <div className="text-xs text-muted-foreground mt-1">첨부파일</div>
              </div>
              <div className="text-center p-3 bg-white rounded-lg border">
                <div className="text-2xl font-bold text-orange-600">
                  {Object.keys(maskedEmail.masking_decisions || {}).length}
                </div>
                <div className="text-xs text-muted-foreground mt-1">적용된 규칙</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 마스킹 없음 안내 */}
      {!maskedEmail && (
        <Card className="border-yellow-200 bg-yellow-50/50">
          <CardContent className="pt-4 text-center">
            <p className="text-sm text-muted-foreground">
              ⚠️ 이 이메일은 마스킹 처리되지 않았습니다. 원본만 확인할 수 있습니다.
            </p>
          </CardContent>
        </Card>
      )}

      {/* 뷰 선택 버튼 */}
      {maskedEmail && (
        <div className="flex gap-2 justify-center">
          <Button
            variant={activeView === 'compare' ? 'default' : 'outline'}
            onClick={() => setActiveView('compare')}
          >
            <Eye className="mr-2 h-4 w-4" />
            비교 보기
          </Button>
          <Button
            variant={activeView === 'original' ? 'default' : 'outline'}
            onClick={() => setActiveView('original')}
          >
            원본만
          </Button>
          <Button
            variant={activeView === 'masked' ? 'default' : 'outline'}
            onClick={() => setActiveView('masked')}
          >
            마스킹만
          </Button>
        </div>
      )}

      {/* 비교 보기 */}
      {activeView === 'compare' && maskedEmail && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 원본 */}
          <Card className="border-blue-300 shadow-lg">
            <CardHeader className="bg-blue-50 border-b border-blue-200">
              <CardTitle className="text-base flex items-center gap-2">
                <EyeOff className="h-5 w-5 text-blue-600" />
                원본 (마스킹 전)
              </CardTitle>
              <CardDescription className="text-xs">
                실제 전송되지 않은 원본 데이터입니다
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              {/* 본문 */}
              <div>
                <h4 className="font-semibold text-sm mb-2">📝 본문</h4>
                <div className="bg-gray-50 border rounded p-4 text-sm whitespace-pre-wrap max-h-[400px] overflow-y-auto">
                  {htmlToText(originalEmail.original_body || originalEmail.body || '')}
                </div>
              </div>

              {/* 첨부파일 */}
              {originalEmail.attachments && originalEmail.attachments.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-2">
                    📎 첨부파일 ({originalEmail.attachments.length}개)
                  </h4>
                  <div className="space-y-3">
                    {originalEmail.attachments.map((att, idx) => (
                      <div key={idx} className="border rounded p-3 bg-white">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-sm">{att.filename}</span>
                          <Badge variant="outline" className="text-xs">{att.content_type}</Badge>
                        </div>
                        {renderAttachment(att, originalAttachmentUrls)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 마스킹 */}
          <Card className="border-green-300 shadow-lg">
            <CardHeader className="bg-green-50 border-b border-green-200">
              <CardTitle className="text-base flex items-center gap-2">
                <Eye className="h-5 w-5 text-green-600" />
                마스킹 결과 (전송됨)
              </CardTitle>
              <CardDescription className="text-xs">
                실제 수신자에게 전송된 마스킹 처리된 데이터입니다
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              {/* 본문 */}
              <div>
                <h4 className="font-semibold text-sm mb-2">📝 본문</h4>
                <div className="bg-green-50 border border-green-200 rounded p-4 text-sm whitespace-pre-wrap max-h-[400px] overflow-y-auto">
                  {htmlToText(maskedEmail.masked_body || '본문이 없습니다')}
                </div>
              </div>

              {/* 첨부파일 */}
              {maskedEmail.masked_attachments && maskedEmail.masked_attachments.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-2">
                    📎 첨부파일 ({maskedEmail.masked_attachments.length}개)
                  </h4>
                  <div className="space-y-3">
                    {maskedEmail.masked_attachments.map((att, idx) => (
                      <div key={idx} className="border border-green-200 rounded p-3 bg-white">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-sm">{att.filename}</span>
                          <Badge variant="outline" className="text-xs bg-green-50">{att.content_type}</Badge>
                        </div>
                        {renderAttachment(att, maskedAttachmentUrls)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* 원본만 보기 */}
      {activeView === 'original' && (
        <Card className="border-blue-300">
          <CardHeader className="bg-blue-50">
            <CardTitle className="text-sm flex items-center gap-2">
              <EyeOff className="h-4 w-4" />
              원본 이메일
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 space-y-4">
            {/* 본문 */}
            <div>
              <h4 className="font-semibold mb-2">📝 본문</h4>
              <div className="bg-gray-50 border rounded p-4 text-sm whitespace-pre-wrap max-h-[600px] overflow-y-auto">
                {htmlToText(originalEmail.original_body || originalEmail.body || '본문이 없습니다')}
              </div>
            </div>

            {/* 첨부파일 */}
            {originalEmail.attachments && originalEmail.attachments.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">
                  📎 첨부파일 ({originalEmail.attachments.length}개)
                </h4>
                <div className="space-y-4">
                  {originalEmail.attachments.map((att, idx) => (
                    <div key={idx} className="border rounded p-4 bg-white">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-medium">{att.filename}</span>
                        <Badge variant="outline">{att.content_type}</Badge>
                      </div>
                      {renderAttachment(att, originalAttachmentUrls)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 마스킹만 보기 */}
      {activeView === 'masked' && maskedEmail && (
        <Card className="border-green-300">
          <CardHeader className="bg-green-50">
            <CardTitle className="text-sm flex items-center gap-2">
              <Eye className="h-4 w-4" />
              마스킹된 이메일
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 space-y-4">
            {/* 본문 */}
            <div>
              <h4 className="font-semibold mb-2">📝 본문</h4>
              <div className="bg-green-50 border border-green-200 rounded p-4 text-sm whitespace-pre-wrap max-h-[600px] overflow-y-auto">
                {htmlToText(maskedEmail.masked_body || '본문이 없습니다')}
              </div>
            </div>

            {/* 첨부파일 */}
            {maskedEmail.masked_attachments && maskedEmail.masked_attachments.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">
                  📎 첨부파일 ({maskedEmail.masked_attachments.length}개)
                </h4>
                <div className="space-y-4">
                  {maskedEmail.masked_attachments.map((att, idx) => (
                    <div key={idx} className="border border-green-200 rounded p-4 bg-white">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-medium">{att.filename}</span>
                        <Badge variant="outline" className="bg-green-50">{att.content_type}</Badge>
                      </div>
                      {renderAttachment(att, maskedAttachmentUrls)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
