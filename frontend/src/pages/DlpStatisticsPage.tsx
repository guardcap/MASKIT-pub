import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Shield,
  Ban,
  CheckCircle,
  XCircle,
  Calendar,
  Download
} from 'lucide-react';

interface StatCard {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  color: string;
  icon: React.ReactNode;
}

interface TableRow {
  date: string;
  department: string;
  type: string;
  severity: 'high' | 'medium' | 'low';
  count: number;
  status: string;
}

export default function DlpStatisticsPage() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const token = localStorage.getItem('auth_token');

  useEffect(() => {

    // 기본 날짜 설정
    const today = new Date();
    const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    setEndDate(today.toISOString().split('T')[0]);
    setStartDate(lastWeek.toISOString().split('T')[0]);
  }, [token, navigate]);

  const stats: StatCard[] = [
    {
      title: '총 탐지 건수',
      value: '12,456',
      change: '+12.5%',
      trend: 'up',
      color: 'blue',
      icon: <BarChart3 className="w-6 h-6" />
    },
    {
      title: '차단된 전송',
      value: '342',
      change: '+8.3%',
      trend: 'up',
      color: 'red',
      icon: <Ban className="w-6 h-6" />
    },
    {
      title: '마스킹 처리',
      value: '8,234',
      change: '+15.2%',
      trend: 'up',
      color: 'amber',
      icon: <Shield className="w-6 h-6" />
    },
    {
      title: '승인 완료',
      value: '3,880',
      change: '+5.7%',
      trend: 'up',
      color: 'green',
      icon: <CheckCircle className="w-6 h-6" />
    }
  ];

  const tableData: TableRow[] = [
    { date: '2024-03-20', department: '인사팀', type: '주민등록번호', severity: 'high', count: 156, status: '마스킹 완료' },
    { date: '2024-03-20', department: '재무팀', type: '신용카드 번호', severity: 'high', count: 89, status: '마스킹 완료' },
    { date: '2024-03-19', department: 'R&D팀', type: '이메일 주소', severity: 'medium', count: 234, status: '승인 완료' },
    { date: '2024-03-19', department: '대외협력팀', type: '전화번호', severity: 'low', count: 67, status: '승인 완료' },
    { date: '2024-03-18', department: '인사팀', type: '계좌번호', severity: 'high', count: 45, status: '차단' },
    { date: '2024-03-18', department: '재무팀', type: '사업자등록번호', severity: 'medium', count: 123, status: '마스킹 완료' },
    { date: '2024-03-17', department: 'CS팀', type: '이메일 주소', severity: 'low', count: 345, status: '승인 완료' },
    { date: '2024-03-17', department: 'R&D팀', type: '주민등록번호', severity: 'high', count: 12, status: '차단' }
  ];

  const getSeverityBadge = (severity: 'high' | 'medium' | 'low') => {
    const variants = {
      high: { label: '높음', className: 'bg-red-100 text-red-800' },
      medium: { label: '중간', className: 'bg-amber-100 text-amber-800' },
      low: { label: '낮음', className: 'bg-blue-100 text-blue-800' }
    };
    const { label, className } = variants[severity];
    return <Badge className={className}>{label}</Badge>;
  };

  const getStatColor = (color: string) => {
    const colors: Record<string, string> = {
      blue: 'border-l-blue-500 text-blue-700',
      red: 'border-l-red-500 text-red-700',
      amber: 'border-l-amber-500 text-amber-700',
      green: 'border-l-green-500 text-green-700'
    };
    return colors[color] || 'border-l-slate-500 text-slate-700';
  };

  const getIconBgColor = (color: string) => {
    const colors: Record<string, string> = {
      blue: 'bg-blue-100 text-blue-600',
      red: 'bg-red-100 text-red-600',
      amber: 'bg-amber-100 text-amber-600',
      green: 'bg-green-100 text-green-600'
    };
    return colors[color] || 'bg-slate-100 text-slate-600';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2 flex items-center gap-3">
              <BarChart3 className="w-10 h-10 text-purple-600" />
              DLP 통계 대시보드
            </h1>
            <p className="text-slate-600">민감 정보 탐지 및 처리 통계를 확인할 수 있습니다</p>
          </div>
          <div className="flex gap-2 items-center">
            <Calendar className="w-5 h-5 text-slate-400" />
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-40"
            />
            <span className="text-slate-400">~</span>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-40"
            />
            <Button variant="outline" className="gap-2">
              조회
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, idx) => (
            <Card key={idx} className={`border-l-4 ${getStatColor(stat.color)}`}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm text-slate-600">{stat.title}</p>
                  <div className={`p-2 rounded-lg ${getIconBgColor(stat.color)}`}>
                    {stat.icon}
                  </div>
                </div>
                <p className={`text-3xl font-bold mb-2 ${getStatColor(stat.color).split(' ')[1]}`}>
                  {stat.value}
                </p>
                <div className="flex items-center gap-1 text-sm">
                  {stat.trend === 'up' ? (
                    <TrendingUp className="w-4 h-4 text-green-600" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-600" />
                  )}
                  <span className={stat.trend === 'up' ? 'text-green-600' : 'text-red-600'}>
                    {stat.change}
                  </span>
                  <span className="text-slate-500">지난 달 대비</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>일별 탐지 추이</CardTitle>
              <CardDescription>최근 7일간 민감 정보 탐지 건수</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gradient-to-br from-purple-100 to-purple-200 rounded-lg flex items-center justify-center text-purple-700 font-semibold">
                차트 영역 (Chart.js 연동 예정)
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>민감 정보 유형별 분포</CardTitle>
              <CardDescription>탐지된 민감 정보 유형 비율</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg flex items-center justify-center text-blue-700 font-semibold">
                원형 차트 영역 (Chart.js 연동 예정)
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Stats Sidebar */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>실시간 현황</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-slate-600 mb-1">오늘 탐지</p>
                <p className="text-2xl font-bold text-blue-700">456건</p>
              </div>
              <div className="p-3 bg-red-50 rounded-lg">
                <p className="text-xs text-slate-600 mb-1">대기 중</p>
                <p className="text-2xl font-bold text-red-700">12건</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-xs text-slate-600 mb-1">평균 처리 시간</p>
                <p className="text-2xl font-bold text-green-700">2.3분</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>상위 탐지 유형</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[
                  { name: '주민등록번호', percent: '28%' },
                  { name: '이메일 주소', percent: '22%' },
                  { name: '신용카드 번호', percent: '18%' },
                  { name: '전화번호', percent: '15%' },
                  { name: '기타', percent: '17%' }
                ].map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center p-2 bg-slate-50 rounded">
                    <span className="text-sm text-slate-700">{item.name}</span>
                    <span className="text-sm font-semibold text-purple-600">{item.percent}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>부서별 현황</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[
                  { dept: '인사팀', count: '1,234건' },
                  { dept: '재무팀', count: '987건' },
                  { dept: 'R&D팀', count: '756건' },
                  { dept: 'CS팀', count: '654건' }
                ].map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center p-2">
                    <span className="text-sm text-slate-700">{item.dept}</span>
                    <span className="text-sm font-semibold text-slate-900">{item.count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Table */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>상세 통계</CardTitle>
                <CardDescription>부서별 민감 정보 탐지 내역</CardDescription>
              </div>
              <Button variant="outline" className="gap-2">
                <Download className="w-4 h-4" />
                내보내기
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-slate-200">
                    <th className="text-left p-4 font-semibold text-slate-700">날짜</th>
                    <th className="text-left p-4 font-semibold text-slate-700">부서</th>
                    <th className="text-left p-4 font-semibold text-slate-700">탐지 유형</th>
                    <th className="text-left p-4 font-semibold text-slate-700">심각도</th>
                    <th className="text-left p-4 font-semibold text-slate-700">건수</th>
                    <th className="text-left p-4 font-semibold text-slate-700">처리 상태</th>
                  </tr>
                </thead>
                <tbody>
                  {tableData.map((row, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                      <td className="p-4 text-slate-700">{row.date}</td>
                      <td className="p-4 text-slate-700">{row.department}</td>
                      <td className="p-4 text-slate-700">{row.type}</td>
                      <td className="p-4">{getSeverityBadge(row.severity)}</td>
                      <td className="p-4 font-semibold text-slate-900">{row.count}</td>
                      <td className="p-4 text-slate-700">{row.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
