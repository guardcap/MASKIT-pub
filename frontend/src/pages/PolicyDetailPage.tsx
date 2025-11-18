import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Trash2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { getPolicyDetail, deletePolicy } from '@/lib/api'

interface PolicyDetailPageProps {
  policyId: string
  onBack?: () => void
  onDelete?: (policyId: string) => void
}

export const PolicyDetailPage: React.FC<PolicyDetailPageProps> = ({
  policyId,
  onBack,
  onDelete,
}) => {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [policy, setPolicy] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPolicyDetail()
  }, [policyId])

  const loadPolicyDetail = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getPolicyDetail(policyId)
      setPolicy(data)
    } catch (err) {
      console.error('Failed to load policy detail:', err)
      setError(err instanceof Error ? err.message : '정책을 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    try {
      await deletePolicy(policyId)
      setDeleteDialogOpen(false)
      onDelete?.(policyId)
      onBack?.()
    } catch (err) {
      console.error('Failed to delete policy:', err)
      alert(err instanceof Error ? err.message : '정책 삭제에 실패했습니다.')
    }
  }

  const formatDateTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('ko-KR')
  }

  if (loading) {
    return (
      <div className="container mx-auto max-w-4xl p-6">
        <Button variant="outline" onClick={onBack} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          목록으로 돌아가기
        </Button>
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">정책을 불러오는 중...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error || !policy) {
    return (
      <div className="container mx-auto max-w-4xl p-6">
        <Button variant="outline" onClick={onBack} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          목록으로 돌아가기
        </Button>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error || '정책을 찾을 수 없습니다.'}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto max-w-4xl p-6">
      <div className="mb-6">
        <Button variant="outline" onClick={onBack} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          목록으로 돌아가기
        </Button>
      </div>

      {/* 정책 헤더 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-2xl mb-4">{policy.title}</CardTitle>
          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-4">
            <div className="flex items-center gap-2">
              <strong>기관:</strong> {policy.authority}
            </div>
            <div className="flex items-center gap-2">
              <strong>파일 타입:</strong>
              <Badge variant={policy.file_type === '.pdf' ? 'destructive' : 'secondary'}>
                {policy.file_type === '.pdf' ? 'PDF' : '이미지'}
              </Badge>
            </div>
            {policy.file_size_mb && (
              <div className="flex items-center gap-2">
                <strong>파일 크기:</strong> {policy.file_size_mb.toFixed(2)} MB
              </div>
            )}
            {policy.processing_method && (
              <div className="flex items-center gap-2">
                <strong>처리 방법:</strong> {policy.processing_method}
              </div>
            )}
            <div className="flex items-center gap-2">
              <strong>생성일:</strong> {formatDateTime(policy.created_at)}
            </div>
          </div>
          {policy.description && (
            <p className="text-muted-foreground">{policy.description}</p>
          )}
        </CardHeader>
        <CardContent>
          <div className="flex justify-end">
            <Button
              variant="destructive"
              onClick={() => setDeleteDialogOpen(true)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              삭제
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 메타데이터 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>정책 정보</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">정책 ID</div>
              <div className="font-mono text-sm">{policy.policy_id}</div>
            </div>
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">원본 파일명</div>
              <div className="text-sm">{policy.original_filename}</div>
            </div>
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">저장된 파일명</div>
              <div className="text-sm">{policy.saved_filename}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 요약 */}
      {policy.metadata?.summary && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>요약</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{policy.metadata.summary}</p>
          </CardContent>
        </Card>
      )}

      {/* 키워드 */}
      {policy.metadata?.keywords && policy.metadata.keywords.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>키워드</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {policy.metadata.keywords.map((keyword, idx) => (
                <Badge key={idx} variant="secondary">
                  {keyword}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 개인정보 유형 */}
      {policy.metadata?.entity_types && policy.metadata.entity_types.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>개인정보 유형</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {policy.metadata.entity_types.map((type, idx) => (
                <Badge key={idx} variant="outline">
                  {type}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 적용 시나리오 */}
      {policy.metadata?.scenarios && policy.metadata.scenarios.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>적용 시나리오</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-2">
              {policy.metadata.scenarios.map((scenario, idx) => (
                <li key={idx} className="text-muted-foreground">
                  {scenario}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* 실행 지침 */}
      {policy.metadata?.directives && policy.metadata.directives.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>실행 지침</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-2">
              {policy.metadata.directives.map((directive, idx) => (
                <li key={idx} className="text-muted-foreground">
                  {directive}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* 추출된 텍스트 */}
      <Card>
        <CardHeader>
          <CardTitle>추출된 텍스트</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-muted p-4 rounded-lg max-h-96 overflow-y-auto">
            <pre className="whitespace-pre-wrap text-sm">{policy.extracted_text}</pre>
          </div>
        </CardContent>
      </Card>

      {/* 삭제 확인 다이얼로그 */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>정책 삭제</DialogTitle>
            <DialogDescription>
              정말로 이 정책을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              취소
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              삭제
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
