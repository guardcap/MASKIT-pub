import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ArrowLeft, Save, Edit2, X, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { getPolicyDetail, deletePolicy, updatePolicyText } from '@/lib/api'


interface PolicyDetailPageProps {
  policyId: string
  onBack?: () => void
  onDelete?: (policyId: string) => void
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