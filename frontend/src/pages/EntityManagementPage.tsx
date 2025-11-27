import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Shield,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Download,
  Database,
  Loader2,
  MoreHorizontal,
  Search,
} from 'lucide-react'
import { toast } from 'sonner'

interface Entity {
  entity_id: string
  name: string
  category: string
  description?: string
  regex_pattern?: string
  keywords?: string[]
  examples?: string[]
  masking_rule?: string
  sensitivity_level?: string
}

interface Recognizer {
  class_name: string
  entity_types: string[]
  regex_patterns: { name: string; pattern: string }[]
  keywords: string[]
  module_path: string
  doc?: string
}

export default function EntityManagementPage() {
  const [entities, setEntities] = useState<Entity[]>([])
  const [recognizers, setRecognizers] = useState<Recognizer[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [entityToDelete, setEntityToDelete] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [formData, setFormData] = useState({
    entity_id: '',
    name: '',
    category: '',
    description: '',
    regex_pattern: '',
    keywords: '',
    examples: '',
    masking_type: 'full',  // full, partial, custom
    masking_char: '*',
    masking_pattern: '',   // 커스텀 마스킹 패턴 (예: "###-##-*****")
  })

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [recognizersRes, entitiesRes] = await Promise.all([
        fetch(`${API_BASE}/api/entities/recognizers`),
        fetch(`${API_BASE}/api/entities/list`),
      ])

      const recognizersData = await recognizersRes.json()
      const entitiesData = await entitiesRes.json()

      if (recognizersData.success) {
        setRecognizers(recognizersData.data.recognizers || [])
      }
      if (entitiesData.success) {
        setEntities(entitiesData.data.entities || [])
      }
    } catch (error) {
      console.error('데이터 로드 실패:', error)
      toast.error('데이터를 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  const toggleRow = (id: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedRows(newExpanded)
  }


  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`${API_BASE}/api/entities/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(formData),
      })

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.message || '엔티티 생성 실패')
      }

      toast.success('엔티티가 성공적으로 생성되었습니다')
      setCreateModalOpen(false)
      setFormData({
        entity_id: '',
        name: '',
        category: '',
        description: '',
        regex_pattern: '',
        keywords: '',
        examples: '',
        masking_type: 'full',
        masking_char: '*',
        masking_pattern: '',
      })
      loadData()
    } catch (error: any) {
      toast.error('엔티티 생성 실패: ' + error.message)
    }
  }

  const handleDeleteClick = (entityId: string) => {
    setEntityToDelete(entityId)
    setDeleteDialogOpen(true)
  }

  const handleDeleteConfirm = async () => {
    if (!entityToDelete) return

    try {
      const response = await fetch(`${API_BASE}/api/entities/${entityToDelete}`, {
        method: 'DELETE',
      })

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.message || '엔티티 삭제 실패')
      }

      toast.success('엔티티가 삭제되었습니다')
      setDeleteDialogOpen(false)
      setEntityToDelete(null)
      loadData()
    } catch (error: any) {
      toast.error('엔티티 삭제 실패: ' + error.message)
    }
  }

  // 검색 필터링
  const filteredEntities = entities.filter(
    (entity) =>
      entity.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entity.entity_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entity.category.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const filteredRecognizers = recognizers.filter(
    (rec) =>
      rec.class_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rec.entity_types.some((et) => et.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div className="container mx-auto max-w-6xl p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">엔티티 관리</h1>
            <p className="text-muted-foreground">
              민감 정보 인식 엔티티를 관리하고 커스텀 엔티티를 추가할 수 있습니다
            </p>
          </div>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Shield className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">총 Recognizers</p>
                <p className="text-2xl font-bold">{recognizers.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Search className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">총 Regex 패턴</p>
                <p className="text-2xl font-bold">
                  {recognizers.reduce((sum, r) => sum + r.regex_patterns.length, 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Database className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">커스텀 엔티티</p>
                <p className="text-2xl font-bold">{entities.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 검색 및 액션 */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="엔티티 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={loadData}>
                <RefreshCw className="mr-2 h-4 w-4" />
                새로고침
              </Button>
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                내보내기
              </Button>
              <Button onClick={() => setCreateModalOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                새 엔티티
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 로딩 */}
      {loading && (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-orange-500" />
        </div>
      )}

      {/* 커스텀 엔티티 테이블 */}
      {!loading && entities.length > 0 && (
        <Card className="mb-6">
          <CardContent className="p-0">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Database className="h-5 w-5 text-orange-500" />
                커스텀 엔티티
                <Badge variant="secondary" className="ml-2">
                  {filteredEntities.length}
                </Badge>
              </h2>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10"></TableHead>
                  <TableHead>엔티티 ID</TableHead>
                  <TableHead>이름</TableHead>
                  <TableHead>카테고리</TableHead>
                  <TableHead>키워드</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEntities.map((entity) => (
                  <>
                    <TableRow
                      key={entity.entity_id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => toggleRow(entity.entity_id)}
                    >
                      <TableCell>
                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                          {expandedRows.has(entity.entity_id) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </Button>
                      </TableCell>
                      <TableCell className="font-mono text-sm">{entity.entity_id}</TableCell>
                      <TableCell className="font-medium">{entity.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{entity.category}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{entity.keywords?.length || 0} 키워드</Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={(e: React.MouseEvent) => {
                                e.stopPropagation()
                                handleDeleteClick(entity.entity_id)
                              }}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              삭제
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                    {expandedRows.has(entity.entity_id) && (
                      <TableRow key={`${entity.entity_id}-expanded`}>
                        <TableCell colSpan={6} className="bg-muted/30 p-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {entity.description && (
                              <div>
                                <p className="text-sm font-medium text-muted-foreground mb-1">
                                  설명
                                </p>
                                <p className="text-sm">{entity.description}</p>
                              </div>
                            )}
                            {entity.regex_pattern && (
                              <div>
                                <p className="text-sm font-medium text-muted-foreground mb-1">
                                  Regex 패턴
                                </p>
                                <code className="block bg-muted p-2 rounded text-xs font-mono">
                                  {entity.regex_pattern}
                                </code>
                              </div>
                            )}
                            {entity.keywords && entity.keywords.length > 0 && (
                              <div className="col-span-2">
                                <p className="text-sm font-medium text-muted-foreground mb-2">
                                  키워드
                                </p>
                                <div className="flex flex-wrap gap-1">
                                  {entity.keywords.map((kw, idx) => (
                                    <Badge key={idx} variant="outline" className="text-xs">
                                      {kw}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* 내장 Recognizers 테이블 */}
      {!loading && recognizers.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Shield className="h-5 w-5 text-orange-500" />
                내장 Recognizers
                <Badge variant="secondary" className="ml-2">
                  {filteredRecognizers.length}
                </Badge>
                <span className="text-xs text-muted-foreground ml-2">(읽기 전용)</span>
              </h2>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10"></TableHead>
                  <TableHead>클래스 이름</TableHead>
                  <TableHead>엔티티 타입</TableHead>
                  <TableHead>Regex 패턴</TableHead>
                  <TableHead>키워드</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRecognizers.map((rec) => (
                  <>
                    <TableRow
                      key={rec.class_name}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => toggleRow(rec.class_name)}
                    >
                      <TableCell>
                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                          {expandedRows.has(rec.class_name) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </Button>
                      </TableCell>
                      <TableCell className="font-medium">{rec.class_name}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {rec.entity_types.slice(0, 2).map((et, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {et}
                            </Badge>
                          ))}
                          {rec.entity_types.length > 2 && (
                            <Badge variant="secondary" className="text-xs">
                              +{rec.entity_types.length - 2}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{rec.regex_patterns.length} 패턴</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{rec.keywords.length} 키워드</Badge>
                      </TableCell>
                    </TableRow>
                    {expandedRows.has(rec.class_name) && (
                      <TableRow key={`${rec.class_name}-expanded`}>
                        <TableCell colSpan={5} className="bg-muted/30 p-4">
                          <div className="space-y-4">
                            {rec.doc && (
                              <div>
                                <p className="text-sm font-medium text-muted-foreground mb-1">
                                  설명
                                </p>
                                <p className="text-sm">{rec.doc}</p>
                              </div>
                            )}
                            {rec.entity_types.length > 0 && (
                              <div>
                                <p className="text-sm font-medium text-muted-foreground mb-2">
                                  엔티티 타입
                                </p>
                                <div className="flex flex-wrap gap-1">
                                  {rec.entity_types.map((et, idx) => (
                                    <Badge key={idx} variant="outline" className="text-xs">
                                      {et}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                            {rec.regex_patterns.length > 0 && (
                              <div>
                                <p className="text-sm font-medium text-muted-foreground mb-2">
                                  Regex 패턴
                                </p>
                                <div className="space-y-2 max-h-40 overflow-y-auto">
                                  {rec.regex_patterns.map((pattern, idx) => (
                                    <div key={idx} className="bg-muted p-2 rounded">
                                      <p className="text-xs text-muted-foreground mb-1">
                                        {pattern.name}
                                      </p>
                                      <code className="text-xs font-mono break-all">
                                        {pattern.pattern}
                                      </code>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {rec.keywords.length > 0 && (
                              <div>
                                <p className="text-sm font-medium text-muted-foreground mb-2">
                                  키워드
                                </p>
                                <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                                  {rec.keywords.map((kw, idx) => (
                                    <Badge key={idx} variant="outline" className="text-xs">
                                      {kw}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
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
            <DialogTitle>엔티티 삭제</DialogTitle>
            <DialogDescription>
              정말 이 엔티티를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
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

      {/* 생성 모달 */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>새 엔티티 추가</DialogTitle>
            <DialogDescription>
              커스텀 엔티티를 생성하여 민감 정보를 감지할 수 있습니다
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="entity_id">엔티티 ID *</Label>
                  <Input
                    id="entity_id"
                    value={formData.entity_id}
                    onChange={(e) => setFormData({ ...formData, entity_id: e.target.value })}
                    placeholder="예: business_id"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="name">엔티티 이름 *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="예: 사업자등록번호"
                    required
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="category">카테고리 *</Label>
                <Input
                  id="category"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  placeholder="예: 사업자정보"
                  required
                />
              </div>
              <div>
                <Label htmlFor="description">설명</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="엔티티 설명"
                  rows={2}
                />
              </div>
              <div>
                <Label htmlFor="regex_pattern">Regex 패턴 *</Label>
                <Input
                  id="regex_pattern"
                  value={formData.regex_pattern}
                  onChange={(e) => setFormData({ ...formData, regex_pattern: e.target.value })}
                  placeholder="예: \d{3}-\d{2}-\d{5}"
                  className="font-mono"
                  required
                />
              </div>
              <div>
                <Label htmlFor="keywords">키워드 (쉼표로 구분)</Label>
                <Input
                  id="keywords"
                  value={formData.keywords}
                  onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                  placeholder="예: 사업자번호, 사업자등록번호"
                />
              </div>
              <div>
                <Label htmlFor="examples">예시 (쉼표로 구분)</Label>
                <Input
                  id="examples"
                  value={formData.examples}
                  onChange={(e) => setFormData({ ...formData, examples: e.target.value })}
                  placeholder="예: 123-45-67890"
                />
              </div>

              {/* 마스킹 설정 섹션 */}
              <div className="border-t pt-4 mt-4">
                <h4 className="font-medium mb-3">마스킹 설정</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="masking_type">마스킹 방식</Label>
                    <Select
                      value={formData.masking_type}
                      onValueChange={(value) => setFormData({ ...formData, masking_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="마스킹 방식 선택" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="full">전체 마스킹 (***)</SelectItem>
                        <SelectItem value="partial">부분 마스킹 (홍*동)</SelectItem>
                        <SelectItem value="custom">커스텀 패턴</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="masking_char">마스킹 문자</Label>
                    <Select
                      value={formData.masking_char}
                      onValueChange={(value) => setFormData({ ...formData, masking_char: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="마스킹 문자 선택" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="*">* (별표)</SelectItem>
                        <SelectItem value="#"># (샵)</SelectItem>
                        <SelectItem value="X">X (엑스)</SelectItem>
                        <SelectItem value="●">● (원)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                {formData.masking_type === 'custom' && (
                  <div className="mt-3">
                    <Label htmlFor="masking_pattern">커스텀 마스킹 패턴</Label>
                    <Input
                      id="masking_pattern"
                      value={formData.masking_pattern}
                      onChange={(e) => setFormData({ ...formData, masking_pattern: e.target.value })}
                      placeholder="예: ###-##-***** (마스킹 문자 위치에 원본 유지)"
                      className="font-mono"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      # = 원본 유지, 마스킹 문자 = 마스킹 처리 (예: 123-45-67890 → 123-45-*****)
                    </p>
                  </div>
                )}
              </div>
            </div>
            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
                취소
              </Button>
              <Button type="submit">생성</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
