import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { toast } from 'sonner'
import { Send, ChevronDown, ChevronRight } from 'lucide-react'

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
  const [showEmailBody, setShowEmailBody] = useState(false)
  const [detectedPII, setDetectedPII] = useState<PIIItem[]>([])
  const [maskingDecisions, setMaskingDecisions] = useState<Record<string, MaskingDecision>>({})
  const [selectedContext, setSelectedContext] = useState<AnalysisContext>({
    sender_type: null,
    receiver_type: null,
    purpose: [],
    regulations: [],
  })
  const [aiSummary, setAiSummary] = useState('커스텀 설정을 선택하고 분석을 시작하세요.')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isSending, setIsSending] = useState(false)

  // Context 선택 상태
  const [senderContext, setSenderContext] = useState<string>('')
  const [receiverContext, setReceiverContext] = useState<string>('')
  const [purposes, setPurposes] = useState<string[]>([])
  const [regulations, setRegulations] = useState<string[]>([])

  // 초기 PII 탐지
  useEffect(() => {
    detectPII()
  }, [emailData])

  const detectPII = () => {
    const text = emailData.body.replace(/<[^>]*>/g, ' ')

    const patterns = {
      email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
      phone: /\b\d{2,3}-\d{3,4}-\d{4}\b/g,
      jumin: /\b\d{6}-\d{7}\b/g,
      account: /\b\d{3}-\d{2,6}-\d{2,6}\b/g,
    }

    const detected: PIIItem[] = []

    for (const [type, pattern] of Object.entries(patterns)) {
      const matches = text.match(pattern)
      if (matches) {
        matches.forEach((match) => {
          detected.push({ type, value: match })
        })
      }
    }

    setDetectedPII(detected)
  }

  // RAG 분석 실행
  const analyzeWithRAG = async () => {
    if (!receiverContext) {
      toast.error('사내/사외 구분을 선택해주세요')
      return
    }

    setIsAnalyzing(true)
    setAiSummary('AI가 가이드라인을 분석하고 있습니다...')

    const context: AnalysisContext = {
      sender_type: senderContext || 'internal',
      receiver_type: receiverContext,
      purpose: purposes,
      regulations: regulations,
    }

    setSelectedContext(context)

    try {
      const query = buildRAGQuery(context)

      const response = await fetch(`${API_BASE_URL}/api/vectordb/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email_body: emailData.body,
          email_subject: emailData.subject,
          context: context,
          detected_pii: detectedPII,
          query: query,
        }),
      })

      if (!response.ok) {
        throw new Error('RAG 분석 실패')
      }

      const result = await response.json()

      if (result.success && result.data) {
        applyMaskingDecisions(result.data)
        toast.success('AI 분석이 완료되었습니다')
      } else {
        throw new Error('분석 결과가 없습니다')
      }
    } catch (error) {
      console.error('RAG 분석 오류:', error)
      toast.error('분석 실패. 기본 규칙을 적용합니다.')
      applySimpleMaskingRules()
    } finally {
      setIsAnalyzing(false)
    }
  }

  const buildRAGQuery = (context: AnalysisContext) => {
    let query = ''

    if (context.receiver_type === 'external') {
      query = '외부 고객에게 이메일을 보낼 때 개인정보 마스킹 규정'
    } else {
      query = '내부 직원 간 이메일에서 개인정보 마스킹 규정'
    }

    if (context.purpose.length > 0) {
      query += ', ' + context.purpose.join(', ') + ' 관련'
    }

    return query
  }

  const applyMaskingDecisions = (data: any) => {
    setMaskingDecisions(data.masking_decisions || {})
    setAiSummary(
      data.summary || '분석이 완료되었습니다. 가이드라인에 따라 마스킹 항목이 자동 선택되었습니다.'
    )
  }

  const applySimpleMaskingRules = () => {
    const decisions: Record<string, MaskingDecision> = {}

    detectedPII.forEach((pii, idx) => {
      if (receiverContext === 'external') {
        decisions[`pii_${idx}`] = {
          type: pii.type,
          value: pii.value,
          should_mask: true,
          reason: '외부 전송 시 개인정보 마스킹 필수',
        }
      } else {
        if (pii.type === 'jumin' || pii.type === 'account') {
          decisions[`pii_${idx}`] = {
            type: pii.type,
            value: pii.value,
            should_mask: true,
            reason: '민감정보 마스킹 필수',
          }
        }
      }
    })

    setMaskingDecisions(decisions)
    setAiSummary('기본 규칙에 따라 마스킹 항목이 선택되었습니다.')
  }

  const toggleMasking = (piiId: string) => {
    setMaskingDecisions((prev) => ({
      ...prev,
      [piiId]: {
        ...prev[piiId],
        should_mask: !prev[piiId].should_mask,
      },
    }))
  }

  // 마스킹 적용 및 전송
  const handleSendMaskedEmail = async () => {
    if (Object.keys(maskingDecisions).length === 0) {
      if (!confirm('마스킹 분석을 실행하지 않았습니다. 그대로 전송하시겠습니까?')) {
        return
      }
    }

    setIsSending(true)

    // 마스킹 적용
    let maskedBody = emailData.body

    for (const decision of Object.values(maskingDecisions)) {
      if (decision.should_mask) {
        const masked = maskValue(decision.value, decision.type)
        maskedBody = maskedBody.replace(new RegExp(escapeRegex(decision.value), 'g'), masked)
      }
    }

    const maskedCount = Object.values(maskingDecisions).filter((d) => d.should_mask).length

    toast.loading('이메일 전송 중...', { id: 'sending-email' })

    try {
      // 인증 토큰 가져오기
      const token = localStorage.getItem('auth_token')

      if (!token) {
        throw new Error('인증이 필요합니다. 다시 로그인해주세요.')
      }

      // 1단계: DB 저장
      const saveResponse = await fetch(`${API_BASE_URL}/api/v1/emails/send-approved`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          from_email: emailData.from,
          to: emailData.to.join(', '),
          subject: emailData.subject,
          body: maskedBody,
          attachments: emailData.attachments,
          masking_decisions: maskingDecisions,
        }),
      })

      if (!saveResponse.ok) {
        const errorData = await saveResponse.json().catch(() => ({ detail: 'DB 저장 실패' }))
        throw new Error(errorData.detail || 'DB 저장 실패')
      }

      const saveResult = await saveResponse.json()
      console.log('✅ DB 저장 성공:', saveResult)

      // 2단계: SMTP 전송 (사용자 SMTP 설정 사용)
      toast.loading('SMTP로 이메일 전송 중...', { id: 'sending-email' })

      // localStorage에서 사용자 SMTP 설정 로드
      const smtpSettingsStr = localStorage.getItem('smtp_settings')
      let smtpConfig = null

      if (smtpSettingsStr) {
        try {
          smtpConfig = JSON.parse(smtpSettingsStr)
          console.log('✅ 사용자 SMTP 설정 사용:', {
            host: smtpConfig.smtp_host,
            port: smtpConfig.smtp_port,
            user: smtpConfig.smtp_user,
          })
        } catch (error) {
          console.warn('⚠️ SMTP 설정 파싱 실패, 기본 설정 사용')
        }
      }

      if (!smtpConfig) {
        toast.error('SMTP 설정이 없습니다', {
          id: 'sending-email',
          description: '마이페이지에서 SMTP 서버 설정을 먼저 등록하세요.',
          duration: 7000,
        })
        setIsSending(false)
        return
      }

      const smtpResponse = await fetch(`${API_BASE_URL}/api/v1/smtp/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from_email: emailData.from,
          to: emailData.to.join(', '),
          subject: emailData.subject,
          body: maskedBody,
          cc: null,
          bcc: null,
          smtp_config: smtpConfig, // 사용자 SMTP 설정 전달
        }),
      })

      const smtpResult = await smtpResponse.json()

      if (!smtpResponse.ok) {
        console.error('❌ SMTP 전송 실패:', {
          status: smtpResponse.status,
          statusText: smtpResponse.statusText,
          result: smtpResult,
        })

        // SMTP 전송 실패 - 상세 에러 정보 표시
        const errorDetail = smtpResult.detail || smtpResult.message || '알 수 없는 오류'

        toast.error('SMTP 전송 실패 (DB에는 저장됨)', {
          id: 'sending-email',
          description: errorDetail,
          duration: 10000,
        })

        // Backend 콘솔 확인 안내
        console.log('📋 SMTP 에러 상세:', errorDetail)
        console.log('💡 Backend 서버 콘솔 로그를 확인하여 SMTP 설정을 점검하세요')

        // 여전히 성공으로 간주 (DB 저장 완료)
        onSendComplete?.()
        setIsSending(false)
        return
      }

      console.log('✅ SMTP 전송 성공:', smtpResult)

      toast.success('이메일이 성공적으로 전송되었습니다!', {
        id: 'sending-email',
        description: `받는 사람: ${emailData.to.join(', ')}${maskedCount > 0 ? ` | 마스킹: ${maskedCount}개` : ''}`,
        duration: 5000,
      })

      onSendComplete?.()
    } catch (error) {
      console.error('❌ 전송 오류:', error)

      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류'

      toast.error('이메일 전송 실패', {
        id: 'sending-email',
        description: errorMessage + '\n\nBackend 서버와 MongoDB가 실행 중인지 확인하세요.',
        duration: 7000,
      })
    } finally {
      setIsSending(false)
    }
  }

  const maskValue = (value: string, type: string): string => {
    if (type === 'email') {
      const parts = value.split('@')
      if (parts.length === 2) {
        const masked = parts[0].substring(0, 2) + '***'
        return masked + '@' + parts[1]
      }
    } else if (type === 'phone') {
      return value.replace(/\d(?=\d{4})/g, '*')
    } else if (type === 'jumin') {
      return value.substring(0, 6) + '-*******'
    } else if (type === 'account') {
      const parts = value.split('-')
      return parts[0] + '-' + '*'.repeat(parts[1]?.length || 4) + '-' + parts[2]
    }

    return '***'
  }

  const escapeRegex = (str: string): string => {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
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

  return (
    <div className="container mx-auto max-w-7xl p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold">이메일 마스킹 검토</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 좌측: 이메일 정보 & 분석 결과 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 이메일 정보 */}
          <Card>
            <CardHeader>
              <CardTitle>이메일 정보</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <strong className="text-sm">보낸 사람:</strong>{' '}
                <span className="text-sm text-muted-foreground">{emailData.from}</span>
              </div>
              <div>
                <strong className="text-sm">받는 사람:</strong>{' '}
                <span className="text-sm text-muted-foreground">{emailData.to.join(', ')}</span>
              </div>
              <div>
                <strong className="text-sm">제목:</strong>{' '}
                <span className="text-sm text-muted-foreground">{emailData.subject}</span>
              </div>
              <div>
                <strong className="text-sm">첨부파일:</strong>{' '}
                <span className="text-sm text-muted-foreground">
                  {emailData.attachments.length > 0
                    ? emailData.attachments.map((a) => a.filename).join(', ')
                    : '없음'}
                </span>
              </div>
              <Button variant="outline" size="sm" onClick={() => setShowEmailBody(!showEmailBody)}>
                {showEmailBody ? (
                  <>
                    <ChevronDown className="mr-2 h-4 w-4" />
                    본문 숨기기
                  </>
                ) : (
                  <>
                    <ChevronRight className="mr-2 h-4 w-4" />
                    본문 보기
                  </>
                )}
              </Button>
              {showEmailBody && (
                <div className="mt-4 p-4 bg-muted/30 rounded-lg max-h-96 overflow-y-auto">
                  <div dangerouslySetInnerHTML={{ __html: emailData.body }} />
                </div>
              )}
            </CardContent>
          </Card>

          {/* 분석 결과 */}
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">AI 분석 결과</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{aiSummary}</p>
                {isAnalyzing && <Progress value={undefined} className="mt-4" />}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">PII 탐지 통계</CardTitle>
              </CardHeader>
              <CardContent>
                {Object.keys(piiStats).length === 0 ? (
                  <p className="text-sm text-muted-foreground">탐지된 PII 없음</p>
                ) : (
                  <div className="space-y-2">
                    {Object.entries(piiStats).map(([type, count]) => (
                      <div key={type} className="flex justify-between text-sm">
                        <span>{typeNames[type] || type}</span>
                        <Badge variant="secondary">{count}개</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* 우측: 커스텀 설정 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>커스텀 설정</CardTitle>
              <CardDescription>수신자 유형과 맥락을 선택하세요</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">수신자 유형</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="receiver"
                      value="internal"
                      checked={receiverContext === 'internal'}
                      onChange={(e) => setReceiverContext(e.target.value)}
                    />
                    <span className="text-sm">사내</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="receiver"
                      value="external"
                      checked={receiverContext === 'external'}
                      onChange={(e) => setReceiverContext(e.target.value)}
                    />
                    <span className="text-sm">사외 (고객사, 협력업체 등)</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">목적 (선택사항)</label>
                <div className="space-y-2">
                  {['세무 신고 / 재무 보고', '노동·고용 관련 보고', '개인정보·보안 규제 대응'].map(
                    (purpose) => (
                      <label key={purpose} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={purposes.includes(purpose)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setPurposes([...purposes, purpose])
                            } else {
                              setPurposes(purposes.filter((p) => p !== purpose))
                            }
                          }}
                        />
                        <span className="text-sm">{purpose}</span>
                      </label>
                    )
                  )}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">우선 규정</label>
                <div className="space-y-2">
                  {['사내 규칙 우선', '국내 법률 우선', 'GDPR 우선'].map((reg) => (
                    <label key={reg} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={regulations.includes(reg)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setRegulations([...regulations, reg])
                          } else {
                            setRegulations(regulations.filter((r) => r !== reg))
                          }
                        }}
                      />
                      <span className="text-sm">{reg}</span>
                    </label>
                  ))}
                </div>
              </div>

              <Button onClick={analyzeWithRAG} disabled={isAnalyzing} className="w-full">
                {isAnalyzing ? 'AI 분석 중...' : 'AI 분석 시작'}
              </Button>
            </CardContent>
          </Card>

          {/* 마스킹 리스트 */}
          <Card>
            <CardHeader>
              <CardTitle>마스킹 항목</CardTitle>
            </CardHeader>
            <CardContent className="max-h-[500px] overflow-y-auto">
              {Object.keys(maskingDecisions).length === 0 ? (
                <p className="text-sm text-muted-foreground">AI 분석을 실행하면 마스킹 항목이 표시됩니다</p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(maskingDecisions).map(([id, decision]) => (
                    <div
                      key={id}
                      className={`p-3 rounded-lg border ${
                        decision.should_mask ? 'bg-green-50 border-green-200' : 'bg-background'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <input
                          type="checkbox"
                          checked={decision.should_mask}
                          onChange={() => toggleMasking(id)}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-sm mb-1">
                            {typeNames[decision.type] || decision.type}
                            {decision.risk_level && (
                              <Badge
                                variant={decision.risk_level === 'high' ? 'destructive' : 'secondary'}
                                className="ml-2"
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
      </div>
    </div>
  )
}
