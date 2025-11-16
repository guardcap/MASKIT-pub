import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  Shield,
  Plus,
  Trash2,
  Edit,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Download,
  Database,
  Loader2
} from 'lucide-react';

interface Entity {
  entity_id: string;
  name: string;
  category: string;
  description?: string;
  regex_pattern?: string;
  keywords?: string[];
  examples?: string[];
  masking_rule?: string;
  sensitivity_level?: string;
}

interface Recognizer {
  class_name: string;
  entity_types: string[];
  regex_patterns: { name: string; pattern: string }[];
  keywords: string[];
  module_path: string;
  doc?: string;
}

export default function EntityManagementPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [recognizers, setRecognizers] = useState<Recognizer[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    entity_id: '',
    name: '',
    category: '',
    description: '',
    regex_pattern: '',
    keywords: '',
    examples: ''
  });

  const API_BASE = 'http://127.0.0.1:8000';
  const token = localStorage.getItem('auth_token');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [recognizersRes, entitiesRes] = await Promise.all([
        fetch(`${API_BASE}/api/entities/recognizers`),
        fetch(`${API_BASE}/api/entities/list`)
      ]);

      const recognizersData = await recognizersRes.json();
      const entitiesData = await entitiesRes.json();

      if (recognizersData.success) {
        setRecognizers(recognizersData.data.recognizers || []);
      }
      if (entitiesData.success) {
        setEntities(entitiesData.data.entities || []);
      }
    } catch (error) {
      console.error('데이터 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();

    const params = new URLSearchParams();
    Object.entries(formData).forEach(([key, value]) => {
      params.append(key, value);
    });

    try {
      const response = await fetch(`${API_BASE}/api/entities/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: params.toString()
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message || '엔티티 생성 실패');
      }

      alert('엔티티가 성공적으로 생성되었습니다!');
      setCreateModalOpen(false);
      setFormData({
        entity_id: '',
        name: '',
        category: '',
        description: '',
        regex_pattern: '',
        keywords: '',
        examples: ''
      });
      loadData();
    } catch (error: any) {
      alert('엔티티 생성에 실패했습니다: ' + error.message);
    }
  };

  const handleDelete = async (entityId: string) => {
    if (!confirm(`정말 이 엔티티를 삭제하시겠습니까?\n\nID: ${entityId}`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/entities/${entityId}`, {
        method: 'DELETE'
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message || '엔티티 삭제 실패');
      }

      alert('엔티티가 성공적으로 삭제되었습니다.');
      loadData();
    } catch (error: any) {
      alert('엔티티 삭제에 실패했습니다: ' + error.message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2 flex items-center gap-3">
            <Shield className="w-10 h-10 text-purple-600" />
            엔티티 관리
          </h1>
          <p className="text-slate-600">민감 정보 인식 엔티티를 관리하고 커스텀 엔티티를 추가할 수 있습니다</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card className="border-l-4 border-l-purple-500">
            <CardContent className="p-6">
              <p className="text-sm text-slate-600 mb-1">총 Recognizers</p>
              <p className="text-3xl font-bold text-purple-700">{recognizers.length}</p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="p-6">
              <p className="text-sm text-slate-600 mb-1">총 Regex 패턴</p>
              <p className="text-3xl font-bold text-blue-700">
                {recognizers.reduce((sum, r) => sum + r.regex_patterns.length, 0)}
              </p>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="p-6">
              <p className="text-sm text-slate-600 mb-1">커스텀 엔티티</p>
              <p className="text-3xl font-bold text-green-700">{entities.length}</p>
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <div className="flex gap-4 mb-6">
          <Button onClick={() => setCreateModalOpen(true)} className="bg-purple-600 hover:bg-purple-700 gap-2">
            <Plus className="w-4 h-4" />
            새 엔티티 추가
          </Button>
          <Button variant="outline" onClick={loadData} className="gap-2">
            <RefreshCw className="w-4 h-4" />
            새로고침
          </Button>
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            내보내기
          </Button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </div>
        )}

        {/* Custom Entities */}
        {!loading && entities.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Database className="w-6 h-6 text-pink-600" />
              커스텀 엔티티
            </h2>
            <div className="space-y-4">
              {entities.map((entity) => (
                <Card key={entity.entity_id} className="border-l-4 border-l-pink-500">
                  <CardHeader className="cursor-pointer" onClick={() => toggleExpand(entity.entity_id)}>
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <CardTitle className="text-xl">{entity.name}</CardTitle>
                        <CardDescription>
                          {entity.entity_id} - {entity.category}
                        </CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">
                          {entity.keywords?.length || 0} 키워드
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(entity.entity_id);
                          }}
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </Button>
                        {expandedItems.has(entity.entity_id) ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  {expandedItems.has(entity.entity_id) && (
                    <CardContent>
                      {entity.description && (
                        <div className="mb-4">
                          <p className="text-sm font-semibold text-slate-700 mb-1">설명</p>
                          <p className="text-sm text-slate-600">{entity.description}</p>
                        </div>
                      )}
                      {entity.regex_pattern && (
                        <div className="mb-4">
                          <p className="text-sm font-semibold text-slate-700 mb-1">Regex 패턴</p>
                          <code className="block bg-slate-100 p-2 rounded text-sm">
                            {entity.regex_pattern}
                          </code>
                        </div>
                      )}
                      {entity.keywords && entity.keywords.length > 0 && (
                        <div className="mb-4">
                          <p className="text-sm font-semibold text-slate-700 mb-2">키워드</p>
                          <div className="flex flex-wrap gap-2">
                            {entity.keywords.map((kw, idx) => (
                              <Badge key={idx} variant="outline">{kw}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Built-in Recognizers */}
        {!loading && recognizers.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Shield className="w-6 h-6 text-purple-600" />
              내장 Recognizers (읽기 전용)
            </h2>
            <div className="space-y-4">
              {recognizers.map((rec, idx) => (
                <Card key={idx} className="border-l-4 border-l-purple-500">
                  <CardHeader className="cursor-pointer" onClick={() => toggleExpand(rec.class_name)}>
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <CardTitle className="text-xl">{rec.class_name}</CardTitle>
                        <CardDescription>{rec.entity_types.join(', ')}</CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">{rec.regex_patterns.length} Regex</Badge>
                        <Badge variant="secondary">{rec.keywords.length} 키워드</Badge>
                        {expandedItems.has(rec.class_name) ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  {expandedItems.has(rec.class_name) && (
                    <CardContent>
                      {rec.doc && (
                        <div className="mb-4">
                          <p className="text-sm font-semibold text-slate-700 mb-1">설명</p>
                          <p className="text-sm text-slate-600">{rec.doc}</p>
                        </div>
                      )}
                      <div className="mb-4">
                        <p className="text-sm font-semibold text-slate-700 mb-2">Regex 패턴</p>
                        <div className="space-y-2">
                          {rec.regex_patterns.map((pattern, idx) => (
                            <div key={idx} className="bg-slate-100 p-2 rounded">
                              <p className="text-xs text-slate-500">{pattern.name}</p>
                              <code className="text-sm text-slate-800">{pattern.pattern}</code>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-700 mb-2">키워드</p>
                        <div className="flex flex-wrap gap-2">
                          {rec.keywords.map((kw, idx) => (
                            <Badge key={idx} variant="outline">{kw}</Badge>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>새 엔티티 추가</DialogTitle>
            <DialogDescription>커스텀 엔티티를 생성하여 민감 정보를 감지할 수 있습니다</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4">
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
                />
              </div>
              <div>
                <Label htmlFor="regex_pattern">Regex 패턴 *</Label>
                <Input
                  id="regex_pattern"
                  value={formData.regex_pattern}
                  onChange={(e) => setFormData({ ...formData, regex_pattern: e.target.value })}
                  placeholder="예: \d{3}-\d{2}-\d{5}"
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
            </div>
            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
                취소
              </Button>
              <Button type="submit" className="bg-purple-600 hover:bg-purple-700">
                생성
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
