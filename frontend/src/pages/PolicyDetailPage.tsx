import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ArrowLeft, Save, Edit2, X, Trash2, Cloud, CloudOff, ChevronDown, ChevronRight } from 'lucide-react'
import { toast } from 'sonner'
import { getPolicyDetail, deletePolicy, updatePolicyText } from '@/lib/api'


interface PolicyDetailPageProps {
  policyId: string
  onBack?: () => void
  onDelete?: (policyId: string) => void
}

interface Guideline {
  guide_id: string
  scenario: string
  context?: {
    sender_type?: string
    receiver_type?: string
    email_purpose?: string
    pii_types?: string[]
  }
  interpretation?: string
  actionable_directive: string
  keywords?: string[]
  related_law_ids?: string[]
  examples?: Array<{
    case_description: string
    masking_decision: string
    reasoning: string
  }>
  confidence_score?: number
}

interface PolicyData {
  policy_id: string
  title: string
  authority: string
  description?: string
  file_type: string
  file_size_mb: number
  processing_method: string
  extracted_text: string
  metadata?: {
    summary?: string
    keywords?: string[]
    entity_types?: string[]
    scenarios?: string[]
    directives?: string[]
  }
  guidelines?: Guideline[]
  guidelines_count?: number
  vector_store_file_id?: string
  vector_store_synced_at?: string
  created_at: string
  updated_at: string
}

export function PolicyDetailPage({ policyId, onBack, onDelete }: PolicyDetailPageProps) {
  const [policy, setPolicy] = useState<PolicyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editedText, setEditedText] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    loadPolicyDetail()
  }, [policyId])

  const loadPolicyDetail = async () => {
    try {
      setLoading(true)
      const data = await getPolicyDetail(policyId)
      setPolicy(data)
      setEditedText(data.extracted_text || '')
      setError(null)
    } catch (err) {
      console.error('Error loading policy detail:', err)
      setError(err instanceof Error ? err.message : '정책을 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveText = async () => {
    if (!policy) return

    try {
      setIsSaving(true)

      // API 함수 사용
      const result = await updatePolicyText(policyId, editedText)

      if (result.success) {
        toast.success('텍스트가 저장되었습니다')
        setPolicy({ ...policy, extracted_text: editedText })
        setIsEditing(false)
      } else {
        throw new Error(result.message || '저장 실패')
      }
    } catch (err) {
      console.error('Error saving text:', err)
      toast.error(err instanceof Error ? err.message : '텍스트 저장에 실패했습니다')
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancelEdit = () => {
    setEditedText(policy?.extracted_text || '')
    setIsEditing(false)
  }

  const handleDelete = async () => {
    if (!policy) return

    if (!confirm('정말 이 정책을 삭제하시겠습니까?')) {
      return
    }

    try {
      await deletePolicy(policyId)
      toast.success('정책이 삭제되었습니다')
      onDelete?.(policyId)
      onBack?.()
    } catch (err) {
      console.error('Error deleting policy:', err)
      toast.error('정책 삭제에 실패했습니다')
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

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">정책 상세</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">정책을 불러오는 중...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error || !policy) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">정책 상세</h1>
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            뒤로 가기
          </Button>
        </div>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{policy.title}</h1>
          <p className="text-muted-foreground">{policy.authority}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            뒤로 가기
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="h-4 w-4 mr-2" />
            삭제
          </Button>
        </div>
      </div>

      {/* 기본 정보 */}
      <Card>
        <CardHeader>
          <CardTitle>기본 정보</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">정책 ID</p>
              <p className="font-mono text-sm">{policy.policy_id}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">발행 기관</p>
              <p className="font-medium">{policy.authority}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">파일 형식</p>
              <Badge variant="outline">{policy.file_type}</Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">파일 크기</p>
              <p className="font-medium">{policy.file_size_mb.toFixed(2)} MB</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">처리 방법</p>
              <Badge variant="secondary">{policy.processing_method}</Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">생성일</p>
              <p className="text-sm">{formatDate(policy.created_at)}</p>
            </div>
          </div>

          {policy.description && (
            <>
              <Separator />
              <div>
                <p className="text-sm text-muted-foreground mb-2">설명</p>
                <p className="text-sm">{policy.description}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Vector Store 동기화 상태 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {policy.vector_store_file_id ? (
              <Cloud className="h-5 w-5 text-green-500" />
            ) : (
              <CloudOff className="h-5 w-5 text-gray-400" />
            )}
            Vector Store 동기화
          </CardTitle>
          <CardDescription>OpenAI Vector Store 동기화 상태</CardDescription>
        </CardHeader>
        <CardContent>
          {policy.vector_store_file_id ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="default" className="bg-green-500">동기화됨</Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                File ID: <code className="text-xs bg-muted px-1 rounded">{policy.vector_store_file_id}</code>
              </p>
              {policy.vector_store_synced_at && (
                <p className="text-sm text-muted-foreground">
                  동기화 일시: {formatDate(policy.vector_store_synced_at)}
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              <Badge variant="outline">동기화 안됨</Badge>
              <p className="text-sm text-muted-foreground">
                이 정책은 아직 OpenAI Vector Store에 동기화되지 않았습니다.
                정책 관리 페이지에서 동기화를 실행하세요.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 메타데이터 */}
      {policy.metadata && (
        <Card>
          <CardHeader>
            <CardTitle>메타데이터</CardTitle>
            <CardDescription>AI가 추출한 정책 메타데이터</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {policy.metadata.summary && (
              <div>
                <p className="text-sm font-medium mb-2">요약</p>
                <p className="text-sm text-muted-foreground">{policy.metadata.summary}</p>
              </div>
            )}

            {policy.metadata.keywords && policy.metadata.keywords.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">키워드</p>
                <div className="flex flex-wrap gap-2">
                  {policy.metadata.keywords.map((keyword, index) => (
                    <Badge key={index} variant="secondary">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {policy.metadata.entity_types && policy.metadata.entity_types.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">개인정보 유형</p>
                <div className="flex flex-wrap gap-2">
                  {policy.metadata.entity_types.map((type, index) => (
                    <Badge key={index} variant="outline">
                      {type}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 가이드라인/스키마 */}
      {policy.guidelines && policy.guidelines.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>추출된 가이드라인 ({policy.guidelines.length}개)</CardTitle>
            <CardDescription>AI가 정책 문서에서 추출한 실무 가이드라인</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {policy.guidelines.map((guide, index) => (
              <GuidelineItem key={guide.guide_id || index} guide={guide} index={index} />
            ))}
          </CardContent>
        </Card>
      )}

      {/* 가이드라인이 아직 추출되지 않은 경우 */}
      {(!policy.guidelines || policy.guidelines.length === 0) && (
        <Card className="border-dashed">
          <CardContent className="pt-6">
            <div className="text-center text-muted-foreground">
              <p className="mb-2">아직 가이드라인이 추출되지 않았습니다.</p>
              <p className="text-sm">
                정책 업로드 후 백그라운드에서 가이드라인이 추출됩니다.
                잠시 후 새로고침해 주세요.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 추출된 텍스트 (수정 가능) */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>추출된 텍스트</CardTitle>
              <CardDescription>
                {isEditing
                  ? '텍스트를 수정하고 저장하세요'
                  : '정책 문서에서 추출된 전체 텍스트'}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {isEditing ? (
                <>
                  <Button variant="outline" size="sm" onClick={handleCancelEdit}>
                    <X className="h-4 w-4 mr-2" />
                    취소
                  </Button>
                  <Button size="sm" onClick={handleSaveText} disabled={isSaving}>
                    <Save className="h-4 w-4 mr-2" />
                    {isSaving ? '저장 중...' : '저장'}
                  </Button>
                </>
              ) : (
                <Button size="sm" onClick={() => setIsEditing(true)}>
                  <Edit2 className="h-4 w-4 mr-2" />
                  수정
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isEditing ? (
            <Textarea
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              className="min-h-[500px] font-mono text-sm"
              placeholder="추출된 텍스트를 입력하세요..."
            />
          ) : (
            <div className="bg-muted/30 rounded-lg p-4">
              <pre className="whitespace-pre-wrap text-sm font-mono max-h-[500px] overflow-y-auto">
                {policy.extracted_text}
              </pre>
            </div>
          )}

          <div className="mt-4 text-sm text-muted-foreground">
            {editedText.length.toLocaleString()} 자
            {isEditing && editedText !== policy.extracted_text && (
              <span className="ml-2 text-orange-600">• 수정됨</span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 가이드라인 아이템 컴포넌트
function GuidelineItem({ guide, index }: { guide: Guideline; index: number }) {
  const [isExpanded, setIsExpanded] = useState(false)

  const getMaskingDecisionColor = (decision: string) => {
    switch (decision) {
      case 'mask':
        return 'bg-red-100 text-red-800'
      case 'partial_mask':
        return 'bg-yellow-100 text-yellow-800'
      case 'no_mask':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="border rounded-lg p-4 space-y-3">
      {/* 헤더 */}
      <div
        className="flex items-start justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
            <span className="text-sm font-medium text-muted-foreground">
              #{index + 1}
            </span>
            {guide.confidence_score && (
              <Badge variant="outline" className="text-xs">
                신뢰도 {(guide.confidence_score * 100).toFixed(0)}%
              </Badge>
            )}
          </div>
          <p className="font-medium">{guide.scenario}</p>
        </div>
      </div>

      {/* 실행 지침 (항상 표시) */}
      <div className="pl-6">
        <p className="text-sm text-blue-700 bg-blue-50 p-2 rounded">
          <strong>지침:</strong> {guide.actionable_directive}
        </p>
      </div>

      {/* 확장된 상세 내용 */}
      {isExpanded && (
        <div className="pl-6 space-y-3 pt-2 border-t">
          {/* 컨텍스트 */}
          {guide.context && (
            <div>
              <p className="text-sm font-medium mb-1">적용 컨텍스트</p>
              <div className="flex flex-wrap gap-2">
                {guide.context.sender_type && (
                  <Badge variant="secondary">발신: {guide.context.sender_type}</Badge>
                )}
                {guide.context.receiver_type && (
                  <Badge variant="secondary">수신: {guide.context.receiver_type}</Badge>
                )}
                {guide.context.email_purpose && (
                  <Badge variant="outline">목적: {guide.context.email_purpose}</Badge>
                )}
              </div>
              {guide.context.pii_types && guide.context.pii_types.length > 0 && (
                <div className="mt-2">
                  <span className="text-xs text-muted-foreground">PII 유형: </span>
                  {guide.context.pii_types.map((pii, i) => (
                    <Badge key={i} variant="outline" className="text-xs mr-1">
                      {pii}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 해석 */}
          {guide.interpretation && (
            <div>
              <p className="text-sm font-medium mb-1">법적 해석</p>
              <p className="text-sm text-muted-foreground">{guide.interpretation}</p>
            </div>
          )}

          {/* 키워드 */}
          {guide.keywords && guide.keywords.length > 0 && (
            <div>
              <p className="text-sm font-medium mb-1">키워드</p>
              <div className="flex flex-wrap gap-1">
                {guide.keywords.map((kw, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {kw}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 관련 법률 */}
          {guide.related_law_ids && guide.related_law_ids.length > 0 && (
            <div>
              <p className="text-sm font-medium mb-1">관련 법률</p>
              <div className="flex flex-wrap gap-1">
                {guide.related_law_ids.map((law, i) => (
                  <Badge key={i} variant="outline" className="text-xs">
                    {law}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 예시 */}
          {guide.examples && guide.examples.length > 0 && (
            <div>
              <p className="text-sm font-medium mb-2">적용 예시</p>
              <div className="space-y-2">
                {guide.examples.map((ex, i) => (
                  <div key={i} className="bg-muted/50 p-3 rounded text-sm">
                    <p className="mb-1">{ex.case_description}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge className={getMaskingDecisionColor(ex.masking_decision)}>
                        {ex.masking_decision === 'mask' && '마스킹'}
                        {ex.masking_decision === 'partial_mask' && '부분 마스킹'}
                        {ex.masking_decision === 'no_mask' && '마스킹 안함'}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{ex.reasoning}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}