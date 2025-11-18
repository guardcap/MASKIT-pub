import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertCircle, CheckCircle, XCircle, Mail, Users, Calendar } from 'lucide-react'

interface DashboardStats {
  pending_count: number
  approved_count: number
  rejected_count: number
  total_emails: number
  today_emails: number
  total_users: number
}

interface AdminDashboardPageProps {
  onNavigate?: (view: string, emailId?: string) => void
}

export function AdminDashboardPage({ onNavigate }: AdminDashboardPageProps) {
  const [stats, setStats] = useState<DashboardStats>({
    pending_count: 0,
    approved_count: 0,
    rejected_count: 0,
    total_emails: 0,
    today_emails: 0,
    total_users: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      setLoading(true)
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
      const token = localStorage.getItem('auth_token')

      if (!token) {
        throw new Error('인증 토큰이 없습니다.')
      }

      const response = await fetch(`${API_BASE}/api/v1/emails/dashboard/stats`, {
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

  const statCards = [
    {
      title: '승인 대기',
      value: stats.pending_count,
      icon: AlertCircle,
      color: 'text-orange-500',
      bgColor: 'bg-orange-50',
    },
    {
      title: '승인 완료',
      value: stats.approved_count,
      icon: CheckCircle,
      color: 'text-green-500',
      bgColor: 'bg-green-50',
    },
    {
      title: '반려',
      value: stats.rejected_count,
      icon: XCircle,
      color: 'text-red-500',
      bgColor: 'bg-red-50',
    },
    {
      title: '전체 메일',
      value: stats.total_emails,
      icon: Mail,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
    },
    {
      title: '오늘 접수',
      value: stats.today_emails,
      icon: Calendar,
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
        <h1 className="text-3xl font-bold tracking-tight">🛡️ 관리자 대시보드</h1>
        <p className="text-muted-foreground">시스템 전체 현황을 관리합니다</p>
      </div>

      {/* 메뉴 버튼 */}
      <div className="flex flex-wrap gap-3">
        <Button variant="default" onClick={() => window.location.reload()}>
          대시보드
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('pending-approvals')}>
          승인 대기
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('approval-history')}>
          승인 이력
        </Button>
        <Button variant="outline" onClick={() => onNavigate?.('user-management')}>
          직원 관리
        </Button>
      </div>

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
    </div>
  )
}
