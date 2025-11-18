import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Mail, Users, CheckCircle, XCircle, AlertCircle, Building } from 'lucide-react'

interface AuditorStats {
  total_emails: number
  pending_emails: number
  approved_emails: number
  rejected_emails: number
  total_teams: number
  total_users: number
}

interface LogEntry {
  timestamp: string
  actor_email: string
  action: string
}

interface AuditorDashboardPageProps {
  onNavigate?: (view: string, emailId?: string) => void
}

export function AuditorDashboardPage({ onNavigate }: AuditorDashboardPageProps) {
  const [stats, setStats] = useState<AuditorStats>({
    total_emails: 0,
    pending_emails: 0,
    approved_emails: 0,
    rejected_emails: 0,
    total_teams: 0,
    total_users: 0,
  })
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
    loadRecentLogs()
  }, [])

  const loadStats = async () => {
    try {
      setLoading(true)
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
      const token = localStorage.getItem('auth_token')

      if (!token) {
        throw new Error('인증 토큰이 없습니다.')
      }

      const response = await fetch(`${API_BASE}/api/v1/dashboard/auditor/stats`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('통계를 불러오는데 실패했습니다.')
      }

      const data = await response.json()
      setStats(data)
      setError(null)
    } catch (err) {
      console.error('Error loading stats:', err)
      setError(err instanceof Error ? err.message : '오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const loadRecentLogs = async () => {
    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
      const token = localStorage.getItem('auth_token')

      if (!token) {
        return
      }

      const response = await fetch(`${API_BASE}/api/v1/logs/recent?limit=10`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setLogs(data)
      }
    } catch (err) {
      console.error('Error loading logs:', err)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const statCards = [
    {
      title: '전체 메일',
      value: stats.total_emails,
      icon: Mail,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
    },
    {
      title: '승인 대기',
      value: stats.pending_emails,
      icon: AlertCircle,
      color: 'text-orange-500',
      bgColor: 'bg-orange-50',
    },
    {
      title: '승인 완료',
      value: stats.approved_emails,
      icon: CheckCircle,
      color: 'text-green-500',
      bgColor: 'bg-green-50',
    },
    {
      title: '반려',
      value: stats.rejected_emails,
      icon: XCircle,
      color: 'text-red-500',
      bgColor: 'bg-red-50',
    },
    {
      title: '전체 팀',
      value: stats.total_teams,
      icon: Building,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50',
    },
    {
      title: '전체 사용자',
      value: stats.total_users,
      icon: Users,
      color: 'text-indigo-500',
      bgColor: 'bg-indigo-50',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">🔍 MASKIT - Auditor</h1>
        <p className="text-muted-foreground">시스템 감사 및 모니터링</p>
      </div>

      {/* 메뉴 버튼 */}
      <div className="flex flex-wrap gap-3">
        <Button variant="default" onClick={() => window.location.reload()}>
          대시보드
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('all-logs')}>
          전체 로그
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('all-emails')}>
          전체 메일
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('all-statistics')}>
          전체 통계
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('policy-view')}>
          정책 조회
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('entity-view')}>
          엔티티 조회
        </Button>
      </div>

      {/* 권한 안내 */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-blue-900">📌 Auditor 권한 안내</CardTitle>
        </CardHeader>
        <CardContent className="text-blue-800 space-y-2">
          <p>모든 로그, 통계, 메일, 정책을 <strong>읽기 전용</strong>으로 조회할 수 있습니다.</p>
          <p>시스템의 투명성과 사후 감독을 위한 역할입니다.</p>
        </CardContent>
      </Card>

      {/* 통계 카드 */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">로딩 중...</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">-</div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {statCards.map((stat, index) => {
            const Icon = stat.icon
            return (
              <Card key={index}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                  <div className={`${stat.bgColor} p-2 rounded-lg`}>
                    <Icon className={`h-4 w-4 ${stat.color}`} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* 최근 활동 로그 */}
      <Card>
        <CardHeader>
          <CardTitle>📋 최근 활동 로그</CardTitle>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <p className="text-center text-muted-foreground py-4">최근 로그가 없습니다</p>
          ) : (
            <div className="space-y-3">
              {logs.map((log, index) => (
                <div
                  key={index}
                  className="p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-blue-600">
                        {formatDate(log.timestamp)}
                      </p>
                      <p className="text-sm text-muted-foreground">{log.actor_email}</p>
                    </div>
                    <p className="text-sm text-muted-foreground">{log.action}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
