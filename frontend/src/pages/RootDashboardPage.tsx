import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Users,
  Building2,
  Mail,
  CheckCircle,
  XCircle,
  Clock,
  Settings,
  UserPlus,
  Plus,
  FileText,
  Shield
} from 'lucide-react';

interface DashboardStats {
  total_users: number;
  total_teams: number;
  pending_emails: number;
  approved_emails: number;
  rejected_emails: number;
  total_emails: number;
}

export default function RootDashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    total_users: 0,
    total_teams: 0,
    pending_emails: 0,
    approved_emails: 0,
    rejected_emails: 0,
    total_emails: 0
  });
  const [loading, setLoading] = useState(true);

  const API_BASE = 'http://127.0.0.1:8001';
  const token = localStorage.getItem('token');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/dashboard/root-admin/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        console.error('통계 로드 실패');
      }
    } catch (error) {
      console.error('통계 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: '전체 사용자',
      value: stats.total_users,
      icon: <Users className="w-6 h-6" />,
      color: 'blue',
      bgColor: 'bg-blue-100',
      textColor: 'text-blue-700',
      borderColor: 'border-l-blue-500'
    },
    {
      title: '전체 팀',
      value: stats.total_teams,
      icon: <Building2 className="w-6 h-6" />,
      color: 'purple',
      bgColor: 'bg-purple-100',
      textColor: 'text-purple-700',
      borderColor: 'border-l-purple-500'
    },
    {
      title: '승인 대기',
      value: stats.pending_emails,
      icon: <Clock className="w-6 h-6" />,
      color: 'amber',
      bgColor: 'bg-amber-100',
      textColor: 'text-amber-700',
      borderColor: 'border-l-amber-500'
    },
    {
      title: '승인 완료',
      value: stats.approved_emails,
      icon: <CheckCircle className="w-6 h-6" />,
      color: 'green',
      bgColor: 'bg-green-100',
      textColor: 'text-green-700',
      borderColor: 'border-l-green-500'
    },
    {
      title: '반려',
      value: stats.rejected_emails,
      icon: <XCircle className="w-6 h-6" />,
      color: 'red',
      bgColor: 'bg-red-100',
      textColor: 'text-red-700',
      borderColor: 'border-l-red-500'
    },
    {
      title: '전체 메일',
      value: stats.total_emails,
      icon: <Mail className="w-6 h-6" />,
      color: 'slate',
      bgColor: 'bg-slate-100',
      textColor: 'text-slate-700',
      borderColor: 'border-l-slate-500'
    }
  ];

  const quickActions = [
    {
      title: '사용자 관리',
      description: '사용자 계정 및 권한 관리',
      icon: <Users className="w-8 h-8 text-blue-600" />,
      action: () => {},
      bgColor: 'bg-blue-50 hover:bg-blue-100'
    },
    {
      title: '팀 관리',
      description: '팀 및 조직도 관리',
      icon: <Building2 className="w-8 h-8 text-purple-600" />,
      action: () => {},
      bgColor: 'bg-purple-50 hover:bg-purple-100'
    },
    {
      title: '시스템 설정',
      description: 'LLM, API 등 시스템 설정',
      icon: <Settings className="w-8 h-8 text-slate-600" />,
      action: () => {},
      bgColor: 'bg-slate-50 hover:bg-slate-100'
    },
    {
      title: '시스템 로그',
      description: '전체 시스템 로그 확인',
      icon: <FileText className="w-8 h-8 text-green-600" />,
      action: () => {},
      bgColor: 'bg-green-50 hover:bg-green-100'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2 flex items-center gap-3">
            <Shield className="w-10 h-10 text-purple-600" />
            ROOT 관리자 대시보드
          </h1>
          <p className="text-slate-600">시스템 전체를 관리하고 모니터링할 수 있습니다</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {statCards.map((card, idx) => (
            <Card key={idx} className={`border-l-4 ${card.borderColor} transition-all hover:shadow-lg`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-slate-600">{card.title}</h3>
                  <div className={`p-2 rounded-lg ${card.bgColor}`}>
                    {card.icon}
                  </div>
                </div>
                <p className={`text-4xl font-bold ${card.textColor}`}>
                  {loading ? '-' : card.value.toLocaleString()}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Actions */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-2xl">빠른 작업</CardTitle>
            <CardDescription>자주 사용하는 관리 기능에 빠르게 접근하세요</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {quickActions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={action.action}
                  className={`p-6 rounded-lg border-2 border-slate-200 ${action.bgColor} transition-all text-left hover:border-purple-400 hover:shadow-md`}
                >
                  <div className="mb-3">{action.icon}</div>
                  <h3 className="font-semibold text-slate-900 mb-1">{action.title}</h3>
                  <p className="text-sm text-slate-600">{action.description}</p>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>최근 사용자 활동</CardTitle>
              <CardDescription>최근 시스템에 접근한 사용자</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { name: '김철수', action: '메일 승인', time: '5분 전' },
                  { name: '이영희', action: '사용자 등록', time: '15분 전' },
                  { name: '박민수', action: '정책 수정', time: '1시간 전' },
                  { name: '최지영', action: '로그 확인', time: '2시간 전' }
                ].map((activity, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div>
                      <p className="font-medium text-slate-900">{activity.name}</p>
                      <p className="text-sm text-slate-600">{activity.action}</p>
                    </div>
                    <p className="text-xs text-slate-500">{activity.time}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>시스템 알림</CardTitle>
              <CardDescription>주요 시스템 이벤트 및 알림</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { type: 'success', message: '시스템 백업 완료', time: '오늘 03:00' },
                  { type: 'warning', message: '디스크 사용량 80% 초과', time: '어제 15:30' },
                  { type: 'info', message: '새 사용자 5명 등록', time: '어제 10:20' },
                  { type: 'success', message: '보안 업데이트 적용 완료', time: '2일 전' }
                ].map((notification, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      notification.type === 'success' ? 'bg-green-500' :
                      notification.type === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                    }`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-900">{notification.message}</p>
                      <p className="text-xs text-slate-500 mt-1">{notification.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
