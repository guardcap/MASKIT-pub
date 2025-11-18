import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'
import { Send } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface ApproverReviewPageProps {
  emailData: EmailData
  onBack?: () => void
  onSendComplete?: () => void
}

interface EmailData {
  from: string
  to: string[]
  subject: string
  body: string
  attachments: AttachmentInfo[]
  email_id?: string // MongoDB에 저장된 원본 이메일 ID
}

interface AttachmentInfo {
  file_id: string
  filename: string
  size: number
  content_type: string
}

interface PIIItem {
  type: string
  value: string
}

interface MaskingDecision {
  type: string
  value: string
  should_mask: boolean
  reason: string
  masked_value?: string
  risk_level?: string
  reasoning?: string
  cited_guidelines?: string[]
}

interface AnalysisContext {
  sender_type: string | null
  receiver_type: string | null
  purpose: string[]
  regulations: string[]
}

export const ApproverReviewPage: React.FC<ApproverReviewPageProps> = ({
  emailData,
  onBack,
  onSendComplete,
}) => {
  const [activeTab, setActiveTab] = useState<'all' | string>('all')
  const [emailBodyParagraphs, setEmailBodyParagraphs] = useState<string[]>([])
  const [attachmentUrls, setAttachmentUrls] = useState<Map<string, string>>(new Map())
  const [detectedPII, setDetectedPII] = useState<PIIItem[]>([])
  const [maskingDecisions, setMaskingDecisions] = useState<Record<string, MaskingDecision>>({})
  const [aiSummary, setAiSummary] = useState('커스텀 설정을 선택하고 분석을 시작하세요.')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isSending, setIsSending] = useState(false)

  // 원본 이메일 데이터 (MongoDB에서 불러온)
  const [originalEmailData, setOriginalEmailData] = useState<any>(null)
  const [isLoadingOriginal, setIsLoadingOriginal] = useState(false)

  // Context 선택 상태
  const [senderContext, setSenderContext] = useState<string>('')
  const [receiverContext, setReceiverContext] = useState<string>('')
  const [purposes, setPurposes] = useState<string[]>([])
  const [regulations, setRegulations] = useState<string[]>([])

  const emailBodyRef = useRef<HTMLDivElement>(null)

  // MongoDB에서 원본 이메일 불러오기
  useEffect(() => {
    if (emailData.email_id) {
      loadOriginalEmail(emailData.email_id)
    }
  }, [emailData.email_id])

  // 초기화
  useEffect(() => {
    loadEmailBody()
    loadAttachments()
    detectPII()
  }, [emailData])

  // 원본 데이터 로드 후 첨부파일 다시 로드
  useEffect(() => {
    if (originalEmailData) {
      loadAttachments()
    }
  }, [originalEmailData])

  // MongoDB에서 원본 이메일 데이터 불러오기
  const loadOriginalEmail = async (email_id: string) => {
    setIsLoadingOriginal(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/files/original_emails/${email_id}`)

      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          setOriginalEmailData(result.data)
          console.log('✅ 원본 이메일 로드 성공:', result.data)
        }
      } else {
        console.error('원본 이메일 로드 실패:', response.status)
      }
    } catch (error) {
      console.error('원본 이메일 로드 중 오류:', error)
    } finally {
      setIsLoadingOriginal(false)
    }
  }

  // 이메일 본문 로드
  const loadEmailBody = () => {
    const bodyText = emailData.body || ''
    const paragraphs = bodyText.split('\n').filter(p => p.trim().length > 0)
    setEmailBodyParagraphs(paragraphs)
  }

  // 첨부파일 Blob URL 생성 (MongoDB에서 Base64 디코딩)
  const loadAttachments = async () => {
    const urlMap = new Map<string, string>()

    // MongoDB에서 불러온 원본 데이터가 있으면 그것을 사용
    if (originalEmailData?.attachments) {
      for (const attachment of originalEmailData.attachments) {
        try {
          // Base64 데이터를 Blob으로 변환
          const binaryString = atob(attachment.data)
          const bytes = new Uint8Array(binaryString.length)
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i)
          }
          const blob = new Blob([bytes], { type: attachment.content_type })
          const url = URL.createObjectURL(blob)

          // filename을 키로 사용
          urlMap.set(attachment.filename, url)
          console.log(`✅ 첨부파일 로드 성공: ${attachment.filename}`)
        } catch (error) {
          console.error(`첨부파일 로드 실패: ${attachment.filename}`, error)
        }
      }
    } else {
      // 기존 방식 (file_id 사용)
      for (const attachment of emailData.attachments) {
        if ((attachment as any).file_id) {
          try {
            const token = localStorage.getItem('auth_token')
            const response = await fetch(`${API_BASE_URL}/api/v1/emails/attachments/${(attachment as any).file_id}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            })

            if (response.ok) {
              const blob = await response.blob()
              const url = URL.createObjectURL(blob)
              urlMap.set((attachment as any).file_id, url)
            }
          } catch (error) {
            console.error(`첨부파일 로드 실패:`, error)
          }
        }
      }
    }

    setAttachmentUrls(urlMap)
  }

  // 컴포넌트 언마운트 시 Blob URL 해제
  useEffect(() => {
    return () => {
      attachmentUrls.forEach(url => URL.revokeObjectURL(url))
    }
  }, [attachmentUrls])

  const detectPII = () => {
    const text = (emailData.body || '').replace(/<[^>]*>/g, ' ')

    const patterns = {
      email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
      phone: /\b01[0-9]-?[0-9]{3,4}-?[0-9]{4}\b/g,
      jumin: /\b\d{6}-?[1-4]\d{6}\b/g,
      account: /\b\d{3,4}-?\d{2,6}-?\d{2,7}\b/g,
      passport: /\b[A-Z]\d{8}\b/g,
      driver_license: /\b\d{2}-\d{6,8}-\d{2}\b/g,
    }

    const found: PIIItem[] = []
    for (const [type, regex] of Object.entries(patterns)) {
      const matches = text.match(regex)
      if (matches) {
        matches.forEach((value) => {
          if (!found.some((item) => item.value === value)) {
            found.push({ type, value })
          }
        })
      }
    }

    setDetectedPII(found)
  }

  const analyzeWithRAG = async () => {
    if (!senderContext && !receiverContext) {
      toast.error('수신자 유형을 최소 하나 이상 선택해주세요.')
      return
    }

    setIsAnalyzing(true)
    setAiSummary('AI가 가이드라인을 검색하고 분석 중입니다...')

    const context: AnalysisContext = {
      sender_type: senderContext,
      receiver_type: receiverContext,
      purpose: purposes,
      regulations: regulations,
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/vectordb/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_body: emailData.body,
          email_subject: emailData.subject,
          detected_pii: detectedPII,
          context: context,
          query: `${senderContext} to ${receiverContext} email masking analysis`,
        }),
      })

      if (!response.ok) throw new Error('분석 요청 실패')

      const result = await response.json()

      // 백엔드 응답 구조: { success, data: { masking_decisions, summary, ... } }
      if (result.success && result.data) {
        const decisions = result.data.masking_decisions || {}
        setMaskingDecisions(decisions)
        setAiSummary(result.data.summary || '분석이 완료되었습니다.')
      } else {
        throw new Error('분석 결과가 올바르지 않습니다.')
      }
      toast.success('AI 분석이 완료되었습니다!')
    } catch (error) {
      console.error('AI 분석 오류:', error)
      toast.error('AI 분석 중 오류가 발생했습니다.')
      setAiSummary('분석 중 오류가 발생했습니다.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const maskValue = (value: string, type: string): string => {
    switch (type) {
      case 'email':
        const [local, domain] = value.split('@')
        return `${local.substring(0, 2)}***@${domain}`
      case 'phone':
        return value.substring(0, 3) + '-****-' + value.substring(value.length - 4)
      case 'jumin':
        return value.substring(0, 6) + '-*******'
      case 'account':
        return '****-****-****'
      case 'passport':
        return value.substring(0, 2) + '******'
      case 'driver_license':
        return '**-******-**'
      default:
        return '***'
    }
  }

  const escapeRegex = (str: string): string => {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  }

  const escapeHTML = (str: string): string => {
    const div = document.createElement('div')
    div.textContent = str
    return div.innerHTML
  }

  // 마스킹 적용 및 전송
  const handleSendMaskedEmail = async () => {
    if (Object.keys(maskingDecisions).length === 0) {
      if (!confirm('마스킹 분석을 실행하지 않았습니다. 그대로 전송하시겠습니까?')) {
        return
      }
    }

    setIsSending(true)

    // contenteditable에서 수정된 본문 가져오기
    let maskedBody = emailBodyRef.current?.innerText || emailBodyParagraphs.join('\n')

    // 마스킹 적용
    for (const decision of Object.values(maskingDecisions)) {
      if (decision.should_mask) {
        const masked = decision.masked_value || maskValue(decision.value, decision.type)
        maskedBody = maskedBody.replace(new RegExp(escapeRegex(decision.value), 'g'), masked)
      }
    }

    const maskedCount = Object.values(maskingDecisions).filter((d) => d.should_mask).length

    toast.loading('이메일 전송 중...', { id: 'sending-email' })

    try {
      const token = localStorage.getItem('auth_token')

      if (!token) {
        throw new Error('인증이 필요합니다. 다시 로그인해주세요.')
      }

      // 1단계: DB 저장
      const dbResponse = await fetch(`${API_BASE_URL}/api/v1/emails/send-approved`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          from_email: emailData.from,
          to: emailData.to,
          subject: emailData.subject,
          body: emailData.body,
          masked_body: maskedBody,
          attachments: emailData.attachments.map((att) => ({
            filename: att.filename,
            size: att.size,
            content_type: att.content_type,
          })),
          masking_count: maskedCount,
        }),
      })

      if (!dbResponse.ok) {
        const errorData = await dbResponse.json()
        throw new Error(errorData.detail || 'DB 저장 실패')
      }

      console.log('✅ DB 저장 성공')

      // 2단계: SMTP 전송
      const smtpResponse = await fetch(`${API_BASE_URL}/api/v1/smtp/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from_email: emailData.from,
          to: emailData.to.join(','),
          subject: emailData.subject,
          body: maskedBody,
          attachments: emailData.attachments.map((att) => att.filename),
        }),
      })

      toast.dismiss('sending-email')

      if (!smtpResponse.ok) {
        const smtpError = await smtpResponse.json()
        console.error('❌ SMTP 전송 실패:', smtpError)
        toast.warning('이메일이 DB에 저장되었으나 SMTP 전송에 실패했습니다.')
      } else {
        console.log('✅ SMTP 전송 성공')
        toast.success(`이메일 전송 완료! (마스킹: ${maskedCount}개)`)
        
        if (onSendComplete) {
          onSendComplete()
        }
      }
    } catch (error: any) {
      toast.dismiss('sending-email')
      console.error('❌ 이메일 전송 오류:', error)
      toast.error(`전송 실패: ${error.message}`)
    } finally {
      setIsSending(false)
    }
  }

  const typeNames: Record<string, string> = {
    email: '이메일',
    phone: '전화번호',
    jumin: '주민등록번호',
    account: '계좌번호',
    passport: '여권번호',
    driver_license: '운전면허번호',
  }

  const piiStats = detectedPII.reduce((acc, pii) => {
    acc[pii.type] = (acc[pii.type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  // 첨부파일 렌더링 (MongoDB 데이터 사용)
  const renderAttachment = (attachment: AttachmentInfo | any) => {
    // filename을 키로 사용 (MongoDB 데이터의 경우)
    const url = attachmentUrls.get(attachment.filename) || attachmentUrls.get(attachment.file_id)

    if (!url) {
      console.log('첨부파일 URL 없음:', attachment.filename, 'Available keys:', Array.from(attachmentUrls.keys()))
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

  return (
    <div className="container mx-auto max-w-7xl p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold">🛡️ MASKIT - 이메일 마스킹 검토</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 좌측: 이메일 내용 (FE UI 구조) */}
        <div className="lg:col-span-2 space-y-6">

          {/* 원본 이메일 데이터 (MongoDB) */}
          {originalEmailData && (
            <Card className="border-blue-200 bg-blue-50/50">
              <CardContent className="space-y-3">
                <div className="bg-white p-4 rounded-lg border border-blue-200">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <strong className="text-blue-900">발신자:</strong>
                      <p className="text-muted-foreground">{originalEmailData.from_email}</p>
                    </div>
                    <div>
                      <strong className="text-blue-900">수신자:</strong>
                      <p className="text-muted-foreground">{originalEmailData.to_emails?.join(', ')}</p>
                    </div>
                    <div>
                      <strong className="text-blue-900">제목:</strong>
                      <p className="text-muted-foreground">{originalEmailData.subject}</p>
                    </div>
                    <div>
                      <strong className="text-blue-900">저장 시간:</strong>
                      <p className="text-muted-foreground">
                        {new Date(originalEmailData.created_at).toLocaleString('ko-KR')}
                      </p>
                    </div>
                  </div>


                  {originalEmailData.attachments && originalEmailData.attachments.length > 0 && (
                    <div className="mt-4">
                      <strong className="text-sm text-blue-900">
                        첨부파일 ({originalEmailData.attachments.length}개):
                      </strong>
                      <div className="mt-2 space-y-2">
                        {originalEmailData.attachments.map((att: any, idx: number) => (
                          <div key={idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded text-sm">
                            <span className="font-medium">{att.filename}</span>
                            <Badge variant="outline">{att.content_type}</Badge>
                            <span className="text-muted-foreground">
                              ({(att.size / 1024).toFixed(2)} KB)
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {isLoadingOriginal && (
            <Card className="border-blue-200">
              <CardContent className="p-6 text-center text-blue-700">
                원본 이메일 데이터를 불러오는 중...
              </CardContent>
            </Card>
          )}

          {/* 파일 탭 (FE 방식) */}
          <Card>
            <CardHeader>
              <div className="flex gap-2 border-b pb-2">
                <button
                  onClick={() => setActiveTab('all')}
                  className={`px-4 py-2 text-sm font-medium rounded-t ${
                    activeTab === 'all'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  전체
                </button>
                {(originalEmailData?.attachments || emailData.attachments).map((att: any, idx: number) => (
                  <button
                    key={att.filename || att.file_id || idx}
                    onClick={() => setActiveTab(att.filename || att.file_id)}
                    className={`px-4 py-2 text-sm font-medium rounded-t ${
                      activeTab === (att.filename || att.file_id)
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 hover:bg-gray-200'
                    }`}
                  >
                    {att.filename}
                  </button>
                ))}
              </div>
            </CardHeader>
            <CardContent className="min-h-[400px]">
              {/* 전체 탭 */}
              {activeTab === 'all' && (
                <div className="space-y-6">
                  {/* 이메일 본문 (contenteditable) */}
                  <div>
                    <h3 className="font-semibold mb-3">{emailData.subject}</h3>
                    <div
                      ref={emailBodyRef}
                      contentEditable
                      suppressContentEditableWarning
                      className="border rounded p-4 min-h-[200px] focus:outline-none focus:ring-2 focus:ring-blue-500"
                      style={{ whiteSpace: 'pre-wrap' }}
                    >
                      {emailBodyParagraphs.map((para, idx) => (
                        <p key={idx} className="mb-2">
                          {para}
                        </p>
                      ))}
                    </div>
                  </div>

                  {/* 첨부파일 표시 */}
                  {(originalEmailData?.attachments || emailData.attachments).map((att: any, idx: number) => (
                    <div key={att.filename || att.file_id || idx} className="border-t pt-4">
                      <h4 className="font-medium mb-2">📎 {att.filename}</h4>
                      {renderAttachment(att)}
                    </div>
                  ))}
                </div>
              )}

              {/* 개별 파일 탭 */}
              {activeTab !== 'all' && (
                <div>
                  {(originalEmailData?.attachments || emailData.attachments)
                    .filter((att: any) => (att.filename || att.file_id) === activeTab)
                    .map((att: any, idx: number) => (
                      <div key={att.filename || att.file_id || idx}>
                        <h3 className="font-semibold mb-4">{att.filename}</h3>
                        {renderAttachment(att)}
                      </div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* PII 탐지 결과 */}
          <Card>
            <CardHeader>
              <CardTitle>개인정보 탐지</CardTitle>
              <CardDescription>
                총 {detectedPII.length}개의 개인정보가 발견되었습니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              {detectedPII.length === 0 ? (
                <p className="text-sm text-muted-foreground">개인정보가 발견되지 않았습니다.</p>
              ) : (
                <div className="space-y-2">
                  {Object.entries(piiStats).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <span className="text-sm">{typeNames[type] || type}</span>
                      <Badge variant="secondary">{count}개</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* AI 분석 결과 */}
          <Card>
            <CardHeader>
              <CardTitle>AI 분석 결과</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm mb-4">{aiSummary}</p>
              {Object.keys(maskingDecisions).length > 0 && (
                <div className="space-y-3">
                  {Object.entries(maskingDecisions).map(([piiId, decision]) => (
                    <div
                      key={piiId}
                      className={`p-3 border rounded-lg ${
                        decision.should_mask ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline">{typeNames[decision.type]}</Badge>
                            {decision.risk_level && (
                              <Badge
                                variant={decision.risk_level === 'high' ? 'destructive' : 'secondary'}
                              >
                                {decision.risk_level}
                              </Badge>
                            )}
                          </div>
                          <div className="text-xs font-mono bg-muted p-2 rounded mb-1">
                            {decision.value}
                            {decision.masked_value && (
                              <div className="text-green-600 mt-1">→ {decision.masked_value}</div>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground">{decision.reason}</div>
                          {decision.cited_guidelines && decision.cited_guidelines.length > 0 && (
                            <div className="mt-2 text-xs bg-blue-50 p-2 rounded border-l-2 border-blue-500">
                              <div className="font-semibold mb-1">📚 인용 법령</div>
                              {decision.cited_guidelines.map((guideline, idx) => (
                                <div key={idx}>• {guideline}</div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* 전송 버튼 */}
          <Button onClick={handleSendMaskedEmail} disabled={isSending} className="w-full" size="lg">
            <Send className="mr-2 h-4 w-4" />
            {isSending ? '전송 중...' : '마스킹 완료 & 전송'}
          </Button>
        </div>

        {/* 우측: 컨텍스트 설정 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>커스텀</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 사내 그룹 */}
              <div className="border-b pb-4">
                <button 
                  className="flex items-center justify-between w-full text-sm font-medium mb-3"
                  onClick={() => {/* 토글 기능은 유지 */}}
                >
                  <span>사내</span>
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="8 4 16 12 8 20" />
                  </svg>
                </button>
                <div className="space-y-2 pl-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={purposes.includes('인사팀(HR)')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPurposes([...purposes, '인사팀(HR)'])
                          setSenderContext('사내')
                        } else {
                          setPurposes(purposes.filter((p) => p !== '인사팀(HR)'))
                          // 사내 항목이 모두 해제되면 senderContext 초기화
                          if (!purposes.some(p => ['고객지원팀(CS)', 'R&D팀', '대외협력팀'].includes(p))) {
                            setSenderContext('')
                          }
                        }
                      }}
                    />
                    <span className="text-sm">인사팀(HR)</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={purposes.includes('고객지원팀(CS)')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPurposes([...purposes, '고객지원팀(CS)'])
                          setSenderContext('사내')
                        } else {
                          setPurposes(purposes.filter((p) => p !== '고객지원팀(CS)'))
                          if (!purposes.some(p => ['인사팀(HR)', 'R&D팀', '대외협력팀'].includes(p))) {
                            setSenderContext('')
                          }
                        }
                      }}
                    />
                    <span className="text-sm">고객지원팀(CS)</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={purposes.includes('R&D팀')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPurposes([...purposes, 'R&D팀'])
                          setSenderContext('사내')
                        } else {
                          setPurposes(purposes.filter((p) => p !== 'R&D팀'))
                          if (!purposes.some(p => ['인사팀(HR)', '고객지원팀(CS)', '대외협력팀'].includes(p))) {
                            setSenderContext('')
                          }
                        }
                      }}
                    />
                    <span className="text-sm">R&D팀</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={purposes.includes('대외협력팀')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPurposes([...purposes, '대외협력팀'])
                          setSenderContext('사내')
                        } else {
                          setPurposes(purposes.filter((p) => p !== '대외협력팀'))
                          if (!purposes.some(p => ['인사팀(HR)', '고객지원팀(CS)', 'R&D팀'].includes(p))) {
                            setSenderContext('')
                          }
                        }
                      }}
                    />
                    <span className="text-sm">대외협력팀</span>
                  </label>
                </div>
              </div>

              {/* 사외 그룹 */}
              <div className="border-b pb-4">
                <button 
                  className="flex items-center justify-between w-full text-sm font-medium mb-3"
                  onClick={() => {/* 토글 기능은 유지 */}}
                >
                  <span>사외</span>
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="8 4 16 12 8 20" />
                  </svg>
                </button>
                <div className="space-y-2 pl-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={purposes.includes('협력 업체')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPurposes([...purposes, '협력 업체'])
                          setReceiverContext('사외')
                        } else {
                          setPurposes(purposes.filter((p) => p !== '협력 업체'))
                          if (!purposes.some(p => ['고객사', '정부 기관'].includes(p))) {
                            setReceiverContext('')
                          }
                        }
                      }}
                    />
                    <span className="text-sm">협력 업체</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={purposes.includes('고객사')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPurposes([...purposes, '고객사'])
                          setReceiverContext('사외')
                        } else {
                          setPurposes(purposes.filter((p) => p !== '고객사'))
                          if (!purposes.some(p => ['협력 업체', '정부 기관'].includes(p))) {
                            setReceiverContext('')
                          }
                        }
                      }}
                    />
                    <span className="text-sm">고객사</span>
                  </label>

                  {/* 정부 기관 (서브 드롭다운) */}
                  <div>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={purposes.includes('정부 기관')}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setPurposes([...purposes, '정부 기관'])
                            setReceiverContext('사외')
                          } else {
                            setPurposes(purposes.filter((p) => p !== '정부 기관'))
                            if (!purposes.some(p => ['협력 업체', '고객사'].includes(p))) {
                              setReceiverContext('')
                            }
                          }
                        }}
                      />
                      <span className="text-sm">정부 기관</span>
                    </label>
                    {purposes.includes('정부 기관') && (
                      <div className="ml-6 mt-2 space-y-2 border-l-2 border-gray-200 pl-3">
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={purposes.includes('세무 신고 / 재무 보고')}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setPurposes([...purposes, '세무 신고 / 재무 보고'])
                              } else {
                                setPurposes(purposes.filter((p) => p !== '세무 신고 / 재무 보고'))
                              }
                            }}
                          />
                          <span className="text-sm">세무 신고 / 재무 보고</span>
                        </label>
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={purposes.includes('노동·고용 관련 보고')}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setPurposes([...purposes, '노동·고용 관련 보고'])
                              } else {
                                setPurposes(purposes.filter((p) => p !== '노동·고용 관련 보고'))
                              }
                            }}
                          />
                          <span className="text-sm">노동·고용 관련 보고</span>
                        </label>
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={purposes.includes('개인정보·보안 규제 대응')}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setPurposes([...purposes, '개인정보·보안 규제 대응'])
                              } else {
                                setPurposes(purposes.filter((p) => p !== '개인정보·보안 규제 대응'))
                              }
                            }}
                          />
                          <span className="text-sm">개인정보·보안 규제 대응</span>
                        </label>
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={purposes.includes('정부 지원사업 / 과제 보고')}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setPurposes([...purposes, '정부 지원사업 / 과제 보고'])
                              } else {
                                setPurposes(purposes.filter((p) => p !== '정부 지원사업 / 과제 보고'))
                              }
                            }}
                          />
                          <span className="text-sm">정부 지원사업 / 과제 보고</span>
                        </label>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 세부 커스텀 그룹 */}
              <div className="pb-4">
                <button 
                  className="flex items-center justify-between w-full text-sm font-medium mb-3"
                  onClick={() => {/* 토글 기능은 유지 */}}
                >
                  <span>세부 커스텀</span>
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="8 4 16 12 8 20" />
                  </svg>
                </button>
                <div className="space-y-2 pl-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={regulations.includes('사내 규칙 우선')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setRegulations([...regulations, '사내 규칙 우선'])
                        } else {
                          setRegulations(regulations.filter((r) => r !== '사내 규칙 우선'))
                        }
                      }}
                    />
                    <span className="text-sm">사내 규칙 우선</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={regulations.includes('국내 법률 우선')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setRegulations([...regulations, '국내 법률 우선'])
                        } else {
                          setRegulations(regulations.filter((r) => r !== '국내 법률 우선'))
                        }
                      }}
                    />
                    <span className="text-sm">국내 법률 우선</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={regulations.includes('GDPR 우선')}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setRegulations([...regulations, 'GDPR 우선'])
                        } else {
                          setRegulations(regulations.filter((r) => r !== 'GDPR 우선'))
                        }
                      }}
                    />
                    <span className="text-sm">GDPR 우선</span>
                  </label>
                </div>
              </div>

              <div className="pt-4 space-y-2">
                <Button onClick={analyzeWithRAG} disabled={isAnalyzing} className="w-full">
                  {isAnalyzing ? 'AI 분석 중...' : 'AI 분석 시작'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}