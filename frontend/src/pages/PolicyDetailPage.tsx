import React from 'react'
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
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false)

  // 샘플 데이터 (실제로는 API에서 가져옴)
  const policy = {
    policy_id: policyId,
    title: '개인정보 처리 방침 2024',
    authority: '개인정보보호위원회',
    description: '개인정보 보호법에 따른 처리 방침',
    file_type: '.pdf',
    file_size_mb: 2.5,
    processing_method: 'PDF 텍스트 추출',
    created_at: '2024-01-15T10:30:00',
    original_filename: 'privacy_policy_2024.pdf',
    saved_filename: 'policy_20240115_103000.pdf',
    extracted_text: `제1조 (개인정보의 처리 목적)
회사는 다음의 목적을 위하여 개인정보를 처리합니다. 처리하고 있는 개인정보는 다음의 목적 이외의 용도로는 이용되지 않으며, 이용 목적이 변경되는 경우에는 개인정보 보호법 제18조에 따라 별도의 동의를 받는 등 필요한 조치를 이행할 예정입니다.

1. 회원 가입 및 관리
회원 가입의사 확인, 회원제 서비스 제공에 따른 본인 식별·인증, 회원자격 유지·관리, 서비스 부정이용 방지, 각종 고지·통지 목적으로 개인정보를 처리합니다.

2. 재화 또는 서비스 제공
물품배송, 서비스 제공, 계약서·청구서 발송, 콘텐츠 제공, 맞춤서비스 제공, 본인인증, 요금결제·정산을 목적으로 개인정보를 처리합니다.`,
    metadata: {
      keywords: ['개인정보', '보호', '처리', '동의', '수집'],
      entity_types: ['이름', '이메일', '전화번호', '주소'],
      summary: '개인정보 보호법에 따른 처리 방침 및 이용자의 권리에 관한 내용',
      scenarios: [
        '회원 가입 시 개인정보 수집',
        '서비스 제공을 위한 개인정보 이용',
        '마케팅 활용을 위한 개인정보 처리',
      ],
      directives: [
        '개인정보는 목적 외 용도로 사용하지 않습니다',
        '개인정보 수집 시 동의를 받아야 합니다',
        '개인정보는 안전하게 보관되어야 합니다',
      ],
    },
  }

  const handleDelete = () => {
    onDelete?.(policyId)
    setDeleteDialogOpen(false)
  }

  const formatDateTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('ko-KR')
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
            <div className="flex items-center gap-2">
              <strong>파일 크기:</strong> {policy.file_size_mb.toFixed(2)} MB
            </div>
            <div className="flex items-center gap-2">
              <strong>처리 방법:</strong> {policy.processing_method}
            </div>
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
      {policy.metadata.summary && (
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
      {policy.metadata.keywords && policy.metadata.keywords.length > 0 && (
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
      {policy.metadata.entity_types && policy.metadata.entity_types.length > 0 && (
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
      {policy.metadata.scenarios && policy.metadata.scenarios.length > 0 && (
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
      {policy.metadata.directives && policy.metadata.directives.length > 0 && (
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
