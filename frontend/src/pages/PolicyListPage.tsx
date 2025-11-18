import React, { useState, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from '@/components/ui/input-group'
import { Search, Plus, Trash2, Eye } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { getPolicies, deletePolicy } from '@/lib/api'

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
  const [policies, setPolicies] = useState<Policy[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPolicies()
  }, [authorityFilter])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  }

  const loadPolicies = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getPolicies(0, 50, authorityFilter)
      setPolicies(data)
    } catch (err) {
      console.error('Failed to load policies:', err)
      setError(err instanceof Error ? err.message : '정책 목록을 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

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

  const handleDeleteConfirm = async () => {
    if (!policyToDelete) return

    try {
      await deletePolicy(policyToDelete)
      setDeleteDialogOpen(false)
      setPolicyToDelete(null)
      // Reload policies after deletion
      await loadPolicies()
    } catch (err) {
      console.error('Failed to delete policy:', err)
      alert(err instanceof Error ? err.message : '정책 삭제에 실패했습니다.')
    }
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
            <InputGroup className="flex-1">
              <InputGroupInput
                placeholder="정책 제목 또는 키워드 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <InputGroupAddon>
                <Search className="h-4 w-4" />
              </InputGroupAddon>
              <InputGroupAddon align="inline-end">
                {filteredPolicies.length}개 결과
              </InputGroupAddon>
            </InputGroup>
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

      {/* 에러 메시지 */}
      {error && (
        <Card className="border-red-200 bg-red-50 mb-6">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* 정책 목록 */}
      {loading ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">정책을 불러오는 중...</p>
          </CardContent>
        </Card>
      ) : filteredPolicies.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">등록된 정책이 없습니다</p>
            <Button onClick={onAddPolicy}>첫 번째 정책 추가하기</Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>정책명</TableHead>
                  <TableHead>기관</TableHead>
                  <TableHead>파일 타입</TableHead>
                  <TableHead>등록일</TableHead>
                  <TableHead>키워드</TableHead>
                  <TableHead className="text-right">작업</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPolicies.map((policy) => (
                  <TableRow key={policy.policy_id}>
                    <TableCell className="font-medium">
                      <div>
                        <div className="font-semibold">{policy.title}</div>
                        {policy.description && (
                          <div className="text-sm text-muted-foreground mt-1">
                            {policy.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{policy.authority}</TableCell>
                    <TableCell>
                      <Badge variant={policy.file_type === '.pdf' ? 'destructive' : 'secondary'}>
                        {policy.file_type === '.pdf' ? 'PDF' : '이미지'}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(policy.created_at)}</TableCell>
                    <TableCell>
                      {policy.metadata?.keywords && policy.metadata.keywords.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {policy.metadata.keywords.slice(0, 3).map((keyword, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {keyword}
                            </Badge>
                          ))}
                          {policy.metadata.keywords.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{policy.metadata.keywords.length - 3}
                            </Badge>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
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
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

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
