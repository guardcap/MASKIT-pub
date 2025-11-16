import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Search, Plus, Trash2, Eye } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface Policy {
  policy_id: string
  title: string
  authority: string
  description?: string
  file_type: string
  created_at: string
  metadata?: {
    keywords?: string[]
  }
}

interface PolicyListPageProps {
  onAddPolicy?: () => void
  onViewPolicy?: (policyId: string) => void
}

export const PolicyListPage: React.FC<PolicyListPageProps> = ({
  onAddPolicy,
  onViewPolicy,
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [authorityFilter, setAuthorityFilter] = useState('all')
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [policyToDelete, setPolicyToDelete] = useState<string | null>(null)

  // 샘플 데이터 (실제로는 API에서 가져옴)
  const [policies] = useState<Policy[]>([
    {
      policy_id: '1',
      title: '개인정보 처리 방침 2024',
      authority: '개인정보보호위원회',
      description: '개인정보 보호법에 따른 처리 방침',
      file_type: '.pdf',
      created_at: '2024-01-15',
      metadata: {
        keywords: ['개인정보', '보호', '처리'],
      },
    },
    {
      policy_id: '2',
      title: '금융 보안 가이드',
      authority: '금융보안원',
      description: '금융 정보 보안 관련 가이드라인',
      file_type: '.pdf',
      created_at: '2024-01-10',
      metadata: {
        keywords: ['금융', '보안', '가이드'],
      },
    },
  ])

  const filteredPolicies = policies.filter((policy) => {
    const matchesSearch =
      policy.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      policy.description?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesAuthority = authorityFilter === 'all' || policy.authority === authorityFilter
    return matchesSearch && matchesAuthority
  })

  const handleDeleteClick = (policyId: string) => {
    setPolicyToDelete(policyId)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = () => {
    console.log('Deleting policy:', policyToDelete)
    setDeleteDialogOpen(false)
    setPolicyToDelete(null)
  }

  return (
    <div className="container mx-auto max-w-6xl p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">정책 목록</h1>
        <p className="text-muted-foreground">등록된 정책 문서를 관리합니다</p>
      </div>

      {/* 검색 및 필터 */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="정책 제목 또는 키워드 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={authorityFilter || undefined} onValueChange={setAuthorityFilter}>
              <SelectTrigger className="w-full md:w-[200px]">
                <SelectValue placeholder="모든 기관" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">모든 기관</SelectItem>
                <SelectItem value="내부">내부 정책</SelectItem>
                <SelectItem value="개인정보보호위원회">개인정보보호위원회</SelectItem>
                <SelectItem value="금융보안원">금융보안원</SelectItem>
                <SelectItem value="KISA">KISA</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={onAddPolicy}>
              <Plus className="mr-2 h-4 w-4" />
              정책 추가
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 정책 목록 */}
      <div className="space-y-4">
        {filteredPolicies.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground mb-4">등록된 정책이 없습니다</p>
              <Button onClick={onAddPolicy}>첫 번째 정책 추가하기</Button>
            </CardContent>
          </Card>
        ) : (
          filteredPolicies.map((policy) => (
            <Card key={policy.policy_id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="mb-2">{policy.title}</CardTitle>
                    <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
                      <span>🏛️ {policy.authority}</span>
                      <span>•</span>
                      <span>📅 {policy.created_at}</span>
                      <span>•</span>
                      <Badge variant={policy.file_type === '.pdf' ? 'destructive' : 'secondary'}>
                        {policy.file_type === '.pdf' ? 'PDF' : '이미지'}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {policy.description && (
                  <p className="text-sm text-muted-foreground mb-4">{policy.description}</p>
                )}
                {policy.metadata?.keywords && policy.metadata.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {policy.metadata.keywords.map((keyword, idx) => (
                      <Badge key={idx} variant="outline">
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                )}
                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onViewPolicy?.(policy.policy_id)}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    상세보기
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteClick(policy.policy_id)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    삭제
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

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
            <Button variant="destructive" onClick={handleDeleteConfirm}>
              삭제
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
