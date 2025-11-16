import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  FileText,
  CheckCircle,
  XCircle,
  Shield,
  Ban,
  Search,
  Download,
  RefreshCw,
  Clock,
  User,
  Building2,
  AlertTriangle
} from 'lucide-react';

interface LogItem {
  id: string;
  title: string;
  timestamp: string;
  type: 'approved' | 'rejected' | 'masked' | 'blocked';
  requester: string;
  department: string;
  approver?: string;
  policy: string;
  sensitiveInfo?: string;
  reason: string;
  details?: Record<string, any>;
}

export default function DecisionLogsPage() {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  const token = localStorage.getItem('token');

  useEffect(() => {
    loadLogs();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = logs.filter(log =>
        log.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.requester.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.reason.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredLogs(filtered);
    } else {
      setFilteredLogs(logs);
    }
  }, [searchTerm, logs]);

  const loadLogs = () => {
    // Mock data - 실제로는 API에서 가져와야 함
    const mockLogs: LogItem[] = [
      {
        id: '1',
        title: '외부 고객사 계약서 전송 승인',
        timestamp: '2024-03-20 14:32:45',
        type: 'approved',
        requester: '김철수 (대외협력팀)',
        department: '대외협력팀',
        approver: '박영희 (팀장)',
        policy: '외부 전송 승인 정책',
        sensitiveInfo: '계약금액, 개인정보 (마스킹됨)',
        reason: '정상적인 업무 진행을 위한 계약서 전송으로, 개인정보는 마스킹 처리되어 안전합니다. 계약 진행을 위해 필요한 문서로 판단되어 승인합니다.'
      },
      {
        id: '2',
        title: '급여 명세서 자동 마스킹',
        timestamp: '2024-03-20 11:15:23',
        type: 'masked',
        requester: '이영수 (인사팀)',
        department: '인사팀',
        policy: '개인정보 보호 정책',
        sensitiveInfo: '주민등록번호, 계좌번호',
        reason: '급여 명세서에 포함된 주민등록번호와 계좌번호를 자동으로 마스킹 처리했습니다. GDPR 및 개인정보보호법 준수를 위한 조치입니다.'
      },
      {
        id: '3',
        title: '고객 데이터베이스 외부 전송 반려',
        timestamp: '2024-03-19 16:48:12',
        type: 'rejected',
        requester: '정민호 (R&D팀)',
        department: 'R&D팀',
        approver: '최보안 (보안팀장)',
        policy: 'DLP 정책',
        reason: '고객 개인정보가 포함된 데이터베이스 파일의 외부 전송은 보안 정책에 위배됩니다. 필요한 경우 내부 승인 절차를 거쳐 마스킹된 데이터만 전송 가능합니다.'
      },
      {
        id: '4',
        title: '신용카드 정보 포함 메일 자동 차단',
        timestamp: '2024-03-19 09:22:37',
        type: 'blocked',
        requester: '홍길동 (재무팀)',
        department: '재무팀',
        policy: '금융 정보 보호 정책',
        sensitiveInfo: '신용카드 번호 (4건)',
        reason: '메일 본문에서 신용카드 번호가 4건 탐지되었습니다. 금융 정보 보호 정책에 따라 자동으로 전송이 차단되었으며, 발신자에게 알림이 전송되었습니다.'
      }
    ];
    setLogs(mockLogs);
    setFilteredLogs(mockLogs);
  };

  const getTypeIcon = (type: LogItem['type']) => {
    switch (type) {
      case 'approved':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'rejected':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'masked':
        return <Shield className="w-5 h-5 text-amber-600" />;
      case 'blocked':
        return <Ban className="w-5 h-5 text-rose-700" />;
    }
  };

  const getTypeBadge = (type: LogItem['type']) => {
    const variants = {
      approved: { label: '승인', className: 'bg-green-100 text-green-800 hover:bg-green-200' },
      rejected: { label: '반려', className: 'bg-red-100 text-red-800 hover:bg-red-200' },
      masked: { label: '마스킹', className: 'bg-amber-100 text-amber-800 hover:bg-amber-200' },
      blocked: { label: '차단', className: 'bg-rose-100 text-rose-800 hover:bg-rose-200' }
    };
    const { label, className } = variants[type];
    return <Badge className={className}>{label}</Badge>;
  };

  const getTypeColor = (type: LogItem['type']) => {
    switch (type) {
      case 'approved': return 'border-l-green-500';
      case 'rejected': return 'border-l-red-500';
      case 'masked': return 'border-l-amber-500';
      case 'blocked': return 'border-l-rose-700';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2 flex items-center gap-3">
            <FileText className="w-10 h-10 text-purple-600" />
            의사결정 로그
          </h1>
          <p className="text-slate-600">모든 메일 검토 및 처리 이력을 확인할 수 있습니다</p>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600 mb-1">승인</p>
                  <p className="text-3xl font-bold text-green-700">45건</p>
                </div>
                <CheckCircle className="w-12 h-12 text-green-500 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-red-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600 mb-1">반려</p>
                  <p className="text-3xl font-bold text-red-700">8건</p>
                </div>
                <XCircle className="w-12 h-12 text-red-500 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-amber-500">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600 mb-1">마스킹</p>
                  <p className="text-3xl font-bold text-amber-700">127건</p>
                </div>
                <Shield className="w-12 h-12 text-amber-500 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-rose-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600 mb-1">차단</p>
                  <p className="text-3xl font-bold text-rose-800">12건</p>
                </div>
                <Ban className="w-12 h-12 text-rose-700 opacity-20" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Actions */}
        <div className="flex gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
            <Input
              placeholder="사용자, 부서, 이유 등으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            내보내기
          </Button>
          <Button onClick={loadLogs} className="gap-2 bg-purple-600 hover:bg-purple-700">
            <RefreshCw className="w-4 h-4" />
            새로고침
          </Button>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-200" />

          {/* Log items */}
          <div className="space-y-6">
            {filteredLogs.map((log) => (
              <div key={log.id} className="relative pl-16">
                {/* Timeline dot */}
                <div className="absolute left-3.5 top-6 w-5 h-5 rounded-full bg-white border-4 border-purple-500 shadow-lg" />

                <Card className={`hover:shadow-xl transition-all border-l-4 ${getTypeColor(log.type)}`}>
                  <CardHeader>
                    <div className="flex justify-between items-start mb-2">
                      <CardTitle className="text-xl flex items-center gap-2">
                        {getTypeIcon(log.type)}
                        {log.title}
                      </CardTitle>
                      {getTypeBadge(log.type)}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <Clock className="w-4 h-4" />
                      {log.timestamp}
                    </div>
                  </CardHeader>

                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="flex items-start gap-2">
                        <User className="w-4 h-4 text-slate-400 mt-0.5" />
                        <div>
                          <p className="text-xs text-slate-500">요청자</p>
                          <p className="font-medium text-slate-900">{log.requester}</p>
                        </div>
                      </div>

                      {log.approver && (
                        <div className="flex items-start gap-2">
                          <User className="w-4 h-4 text-slate-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-slate-500">승인자/검토자</p>
                            <p className="font-medium text-slate-900">{log.approver}</p>
                          </div>
                        </div>
                      )}

                      <div className="flex items-start gap-2">
                        <Building2 className="w-4 h-4 text-slate-400 mt-0.5" />
                        <div>
                          <p className="text-xs text-slate-500">적용 정책</p>
                          <p className="font-medium text-slate-900">{log.policy}</p>
                        </div>
                      </div>

                      {log.sensitiveInfo && (
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="w-4 h-4 text-slate-400 mt-0.5" />
                          <div>
                            <p className="text-xs text-slate-500">민감 정보</p>
                            <p className="font-medium text-slate-900">{log.sensitiveInfo}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="bg-slate-50 border-l-4 border-purple-400 p-4 rounded-lg">
                      <p className="text-sm font-semibold text-slate-700 mb-1">
                        {log.type === 'approved' ? '승인 사유' :
                         log.type === 'rejected' ? '반려 사유' :
                         log.type === 'masked' ? '처리 사유' : '차단 사유'}:
                      </p>
                      <p className="text-sm text-slate-600 leading-relaxed">{log.reason}</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        </div>

        {filteredLogs.length === 0 && (
          <Card className="border-2 border-dashed mt-6">
            <CardContent className="flex flex-col items-center justify-center py-20">
              <FileText className="w-16 h-16 text-slate-300 mb-4" />
              <h3 className="text-xl font-semibold text-slate-700 mb-2">검색 결과가 없습니다</h3>
              <p className="text-slate-500">다른 검색어로 다시 시도해보세요</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
