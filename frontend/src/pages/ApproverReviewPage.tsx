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

interface PIICoordinate {
  pageIndex: number
  bbox: number[]
  field_text: string
}

interface DetectedPIIEntity {
  text: string
  type: string
  score: number
  start_char: number
  end_char: number
  coordinates?: PIICoordinate[]
}

interface PIIAnalysisResult {
  full_text: string
  pii_entities: DetectedPIIEntity[]
}

interface FileAnalysisResult {
  filename: string
  status: string
  analysis_data?: PIIAnalysisResult
  ocr_data?: any
}

export const ApproverReviewPage: React.FC<ApproverReviewPageProps> = ({
  emailData,
  onBack,
  onSendComplete,
}) => {
  const [activeTab, setActiveTab] = useState<'all' | string>('all')
  const [emailBodyParagraphs, setEmailBodyParagraphs] = useState<string[]>([])
  const [attachmentUrls, setAttachmentUrls] = useState<Map<string, string>>(new Map())
  const [maskingDecisions, setMaskingDecisions] = useState<Record<string, MaskingDecision>>({})

  // 통합된 모든 PII 목록 (체크박스용)
  const [allPIIList, setAllPIIList] = useState<Array<{
    id: string
    type: string
    value: string
    source: 'regex' | 'backend_body' | 'backend_attachment'
    filename?: string
    shouldMask: boolean
    maskingDecision?: MaskingDecision
  }>>([])
  const [showPIICheckboxList, setShowPIICheckboxList] = useState(false)
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
    // detectPII()는 AI 분석 시 실행되므로 초기화 시 제거
  }, [emailData])

  // 원본 이메일 데이터 로드 후에는 자동 분석하지 않음 (사용자가 커스텀 설정 후 분석 버튼 클릭)
  // useEffect 제거하여 자동 PII 분석 방지

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
      console.log('📧 원본 이메일 조회 시작:', email_id)
      const response = await fetch(`${API_BASE_URL}/api/v1/files/original_emails/${email_id}`)

      if (response.ok) {
        const result = await response.json()
        console.log('📦 API 응답 전체:', result)

        if (result.success && result.data) {
          console.log('✅ 원본 이메일 데이터:', {
            email_id: result.data.email_id,
            from_email: result.data.from_email,
            to_emails: result.data.to_emails,
            subject: result.data.subject,
            has_original_body: !!result.data.original_body,
            has_body: !!result.data.body,
            original_body_length: result.data.original_body?.length,
            body_length: result.data.body?.length,
            attachments_count: result.data.attachments?.length
          })
          setOriginalEmailData(result.data)
        }
      } else {
        console.error('❌ 원본 이메일 로드 실패:', response.status)
      }
    } catch (error) {
      console.error('❌ 원본 이메일 로드 중 오류:', error)
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

  // detectPII는 analyzeWithRAG 내부에서 실행되므로 별도 함수 불필요
  // (초기화 시 호출하던 부분은 제거)

  const analyzeWithRAG = async () => {
    if (!senderContext && !receiverContext) {
      toast.error('수신자 유형을 최소 하나 이상 선택해주세요.')
      return
    }

    if (!originalEmailData) {
      toast.error('원본 이메일 데이터를 불러오는 중입니다.')
      return
    }

    setIsAnalyzing(true)
    setAiSummary('1단계: 이메일 본문에서 PII 추출 중...')

    try {
      // ==================== 1단계: 이메일 본문 PII 추출 ====================
      const emailBody = originalEmailData?.original_body || originalEmailData?.body || ''

      let bodyPIIEntities: DetectedPIIEntity[] = []
      if (emailBody) {
        const bodyResponse = await fetch(`${API_BASE_URL}/api/v1/analyzer/analyze/text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text_content: emailBody,
            user_request: 'email_analysis'
          })
        })

        if (bodyResponse.ok) {
          const bodyResult: PIIAnalysisResult = await bodyResponse.json()
          bodyPIIEntities = bodyResult.pii_entities || []
          console.log('✅ 이메일 본문 PII:', bodyPIIEntities.length, '개')
        }
      }

      // ==================== 2단계: 첨부파일 PII 추출 ====================
      setAiSummary('2단계: 첨부파일에서 PII 추출 중...')

      let attachmentPIIList: Array<{ filename: string; entities: DetectedPIIEntity[] }> = []

      if (originalEmailData.attachments && originalEmailData.attachments.length > 0) {
        const attachmentPromises = originalEmailData.attachments.map(async (attachment: any) => {
          const filename = attachment.filename

          // Base64 → Blob
          const binaryString = atob(attachment.data)
          const bytes = new Uint8Array(binaryString.length)
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i)
          }
          const blob = new Blob([bytes], { type: attachment.content_type })

          // OCR
          const formData = new FormData()
          formData.append('file_content', blob)
          formData.append('file_name', filename)

          const ocrResponse = await fetch(`${API_BASE_URL}/api/v1/ocr/extract/ocr`, {
            method: 'POST',
            body: formData
          })

          if (!ocrResponse.ok) {
            console.error(`❌ OCR 실패: ${filename}`)
            return { filename, entities: [] }
          }

          const ocrResult = await ocrResponse.json()
          const extractedText = typeof ocrResult === 'string' ? ocrResult : ocrResult.full_text || ''

          // PII 분석
          const analysisResponse = await fetch(`${API_BASE_URL}/api/v1/analyzer/analyze/text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text_content: extractedText,
              user_request: 'attachment_analysis',
              ocr_data: ocrResult
            })
          })

          if (!analysisResponse.ok) {
            console.error(`❌ PII 분석 실패: ${filename}`)
            return { filename, entities: [] }
          }

          const analysisData: PIIAnalysisResult = await analysisResponse.json()

          return {
            filename,
            entities: analysisData.pii_entities || [],
            ocr_data: ocrResult,
            analysis_data: analysisData
          }
        })

        const attachmentResults = await Promise.all(attachmentPromises)
        attachmentPIIList = attachmentResults

        console.log('✅ 첨부파일 PII:', attachmentResults.reduce((sum, r) => sum + r.entities.length, 0), '개')
      }

      // ==================== 3단계: 정규식 기반 PII 검출 ====================
      setAiSummary('3단계: 정규식 기반 PII 검출 중...')

      // detectPII() 로직 재실행
      const text = (emailData.body || '').replace(/<[^>]*>/g, ' ')
      const patterns = {
        email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
        phone: /\b01[0-9]-?[0-9]{3,4}-?[0-9]{4}\b/g,
        jumin: /\b\d{6}-?[1-4]\d{6}\b/g,
        account: /\b\d{3,4}-?\d{2,6}-?\d{2,7}\b/g,
        passport: /\b[A-Z]\d{8}\b/g,
        driver_license: /\b\d{2}-\d{6,8}-\d{2}\b/g,
      }

      const regexPII: PIIItem[] = []
      for (const [type, regex] of Object.entries(patterns)) {
        const matches = text.match(regex)
        if (matches) {
          matches.forEach((value) => {
            if (!regexPII.some((item) => item.value === value)) {
              regexPII.push({ type, value })
            }
          })
        }
      }
      console.log('✅ 정규식 PII:', regexPII.length, '개')

      // ==================== 4단계: 모든 PII 통합 ====================
      setAiSummary('4단계: 모든 PII 통합 중...')

      const allPII: Array<{
        id: string
        type: string
        value: string
        source: 'regex' | 'backend_body' | 'backend_attachment'
        filename?: string
        shouldMask: boolean
        maskingDecision?: MaskingDecision
      }> = []

      // 정규식 PII
      regexPII.forEach((pii, idx) => {
        allPII.push({
          id: `regex_${idx}`,
          type: pii.type,
          value: pii.value,
          source: 'regex',
          shouldMask: false, // 기본값: 체크 해제
          maskingDecision: undefined
        })
      })

      // 백엔드 본문 PII
      bodyPIIEntities.forEach((entity, idx) => {
        allPII.push({
          id: `body_${idx}`,
          type: entity.type,
          value: entity.text,
          source: 'backend_body',
          shouldMask: false,
          maskingDecision: undefined
        })
      })

      // 백엔드 첨부파일 PII
      attachmentPIIList.forEach((fileResult) => {
        fileResult.entities.forEach((entity, idx) => {
          allPII.push({
            id: `attachment_${fileResult.filename}_${idx}`,
            type: entity.type,
            value: entity.text,
            source: 'backend_attachment',
            filename: fileResult.filename,
            shouldMask: false,
            maskingDecision: undefined
          })
        })
      })

      console.log('📊 통합 PII 목록:', allPII.length, '개')

      // ==================== 5단계: RAG로 마스킹 필요 여부 분석 ====================
      setAiSummary('5단계: AI가 가이드라인을 검색하고 마스킹 필요 여부 분석 중...')

      const context: AnalysisContext = {
        sender_type: senderContext,
        receiver_type: receiverContext,
        purpose: purposes,
        regulations: regulations,
      }

      // RAG API 호출 (기존 detectedPII 대신 allPII의 value만 전달)
      const ragResponse = await fetch(`${API_BASE_URL}/api/vectordb/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_body: emailData.body,
          email_subject: emailData.subject,
          detected_pii: allPII.map(pii => ({ type: pii.type, value: pii.value })),
          context: context,
          query: `${senderContext} to ${receiverContext} email masking analysis`,
        }),
      })

      if (!ragResponse.ok) throw new Error('RAG 분석 요청 실패')

      const ragResult = await ragResponse.json()

      if (ragResult.success && ragResult.data) {
        const decisions = ragResult.data.masking_decisions || {}
        setMaskingDecisions(decisions)
        setAiSummary(ragResult.data.summary || '분석이 완료되었습니다.')

        // ==================== 6단계: RAG 결과를 PII 리스트에 반영 ====================
        // RAG가 마스킹 필요하다고 판단한 PII는 shouldMask = true
        // 백엔드는 pii_0, pii_1, pii_2... 형식의 키를 사용하므로 인덱스 기반 매칭
        allPII.forEach((pii, index) => {
          const decisionKey = `pii_${index}`
          const matchingDecision = decisions[decisionKey]

          if (matchingDecision && matchingDecision.should_mask) {
            pii.shouldMask = true
            pii.maskingDecision = matchingDecision as MaskingDecision
            console.log(`✅ PII ${index} 마스킹 권장:`, pii.value, matchingDecision.reason)
          } else {
            console.log(`⚪ PII ${index} 마스킹 불필요:`, pii.value)
          }
        })

        setAllPIIList(allPII)
        setShowPIICheckboxList(true)

        toast.success(`AI 분석 완료! 총 ${allPII.length}개 PII 중 ${allPII.filter(p => p.shouldMask).length}개 마스킹 권장`)
      } else {
        throw new Error('분석 결과가 올바르지 않습니다.')
      }

    } catch (error) {
      console.error('❌ AI 분석 오류:', error)
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

  // 체크박스 토글 핸들러
  const togglePIIMask = (id: string) => {
    setAllPIIList(prev => prev.map(pii =>
      pii.id === id ? { ...pii, shouldMask: !pii.shouldMask } : pii
    ))
  }

  // 마스킹 적용 및 전송
  const handleSendMaskedEmail = async () => {
    if (!showPIICheckboxList || allPIIList.length === 0) {
      if (!confirm('마스킹 분석을 실행하지 않았습니다. 그대로 전송하시겠습니까?')) {
        return
      }
    }

    setIsSending(true)

    // contenteditable에서 수정된 본문 가져오기
    let maskedBody = emailBodyRef.current?.innerText || emailBodyParagraphs.join('\n')

    // 체크된 PII만 마스킹 적용
    const checkedPIIs = allPIIList.filter(pii => pii.shouldMask)

    for (const pii of checkedPIIs) {
      const masked = pii.maskingDecision?.masked_value || maskValue(pii.value, pii.type)
      maskedBody = maskedBody.replace(new RegExp(escapeRegex(pii.value), 'g'), masked)
    }

    const maskedCount = checkedPIIs.length

    toast.loading('이메일 전송 중...', { id: 'sending-email' })

    try {
      const token = localStorage.getItem('auth_token')

      if (!token) {
        throw new Error('인증이 필요합니다. 다시 로그인해주세요.')
      }

      // SMTP 전송 (DB 저장도 자동으로 처리됨)
      const smtpResponse = await fetch(`${API_BASE_URL}/api/v1/smtp/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
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
        throw new Error(smtpError.detail || 'SMTP 전송 실패')
      }

      const result = await smtpResponse.json()
      console.log('✅ SMTP 전송 성공:', result)
      toast.success(`이메일 전송 완료! (마스킹: ${maskedCount}개)`)

      if (onSendComplete) {
        onSendComplete()
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
    EMAIL: '이메일 주소',
    PHONE: '전화번호',
    PERSON: '개인명',
    BANK_ACCOUNT: '계좌 번호',
    CREDIT_CARD: '신용카드 번호',
    IP_ADDRESS: 'IP 주소',
    DATE_TIME: '날짜/시간',
    LOCATION: '위치 정보',
    ORGANIZATION: '조직명',
  }

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

          {/* AI 분석 진행 상황 */}
          {isAnalyzing && (
            <Card className="border-blue-200 bg-blue-50/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  AI 분석 진행 중
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">{aiSummary}</p>
              </CardContent>
            </Card>
          )}

          {/* AI 분석 요약 (완료 후) */}
          {!isAnalyzing && showPIICheckboxList && (
            <Card className="border-green-200 bg-green-50/30">
              <CardHeader>
                <CardTitle className="text-sm">📊 AI 분석 요약</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">{aiSummary}</p>
              </CardContent>
            </Card>
          )}

          {/* PII 체크박스 리스트 (AI 분석 완료 후 표시) */}
          {showPIICheckboxList && allPIIList.length > 0 && (
            <Card className="border-blue-500 bg-blue-50/50">
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-sm">
                  <span>✅ 마스킹 대상 PII</span>
                  <Badge variant="default" className="text-xs">
                    {allPIIList.filter(p => p.shouldMask).length} / {allPIIList.length}
                  </Badge>
                </CardTitle>
                <CardDescription className="text-xs">
                  AI가 마스킹이 필요하다고 판단한 항목은 체크되어 있습니다.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {allPIIList.map((pii) => (
                    <div
                      key={pii.id}
                      className={`p-2 border rounded-lg transition-all text-xs ${
                        pii.shouldMask
                          ? 'bg-yellow-50 border-yellow-300'
                          : 'bg-white border-gray-200'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {/* 체크박스 */}
                        <input
                          type="checkbox"
                          checked={pii.shouldMask}
                          onChange={() => togglePIIMask(pii.id)}
                          className="mt-1 h-4 w-4 cursor-pointer"
                        />

                        {/* PII 정보 */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1 mb-1 flex-wrap">
                            <Badge variant="outline" className="text-xs">
                              {typeNames[pii.type] || pii.type}
                            </Badge>
                            {pii.shouldMask && pii.maskingDecision?.risk_level && (
                              <Badge
                                variant={pii.maskingDecision.risk_level === 'high' ? 'destructive' : 'default'}
                                className="text-xs"
                              >
                                {pii.maskingDecision.risk_level}
                              </Badge>
                            )}
                          </div>

                          {/* PII 값 */}
                          <div className="font-mono text-xs bg-gray-100 p-1.5 rounded border mb-1 break-all">
                            {pii.value}
                            {pii.shouldMask && (
                              <div className="text-green-600 mt-1">
                                → {pii.maskingDecision?.masked_value || maskValue(pii.value, pii.type)}
                              </div>
                            )}
                          </div>

                          {/* AI 분석 근거 (마스킹 권장된 경우만) */}
                          {pii.shouldMask && pii.maskingDecision && (
                            <div className="text-xs space-y-1">
                              <p className="text-muted-foreground">
                                💡 {pii.maskingDecision.reason}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* 전체 선택/해제 버튼 */}
                <div className="flex gap-1 mt-3">
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs flex-1"
                    onClick={() => setAllPIIList(prev => prev.map(pii => ({ ...pii, shouldMask: true })))}
                  >
                    전체 선택
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs flex-1"
                    onClick={() => setAllPIIList(prev => prev.map(pii => ({ ...pii, shouldMask: false })))}
                  >
                    전체 해제
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}