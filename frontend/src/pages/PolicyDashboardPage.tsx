import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileText, Database, BarChart3, Shield } from 'lucide-react'
import { getPolicyStats, getPolicies } from '@/lib/api'

interface PolicyDashboardPageProps {
  onNavigate?: (page: string) => void
}

interface Stats {
  total_policies: number
  total_entities: number
  total_emails_processed?: number
  total_masking_events?: number
}

export const PolicyDashboardPage: React.FC<PolicyDashboardPageProps> = ({ onNavigate }) => {
  const [stats, setStats] = useState<Stats | null>(null)
  const [recentPolicies, setRecentPolicies] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [statsData, policiesData] = await Promise.all([
        getPolicyStats(),
        getPolicies(0, 5) // Get 5 most recent policies
      ])

      setStats(statsData)
      setRecentPolicies(policiesData)
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
      setError(err instanceof Error ? err.message : '대시보드 데이터를 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const statsCards = [
    { label: '등록된 정책', value: stats?.total_policies?.toString() || '0', icon: FileText },
    { label: '등록된 엔티티', value: stats?.total_entities?.toString() || '0', icon: Database },
    { label: '정책 적용 메일', value: stats?.total_emails_processed?.toString() || '0', icon: Shield },
    { label: '마스킹 건수', value: stats?.total_masking_events?.toString() || '0', icon: BarChart3 },
  ]

  return (
    <div className="container mx-auto max-w-6xl p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">정책 관리 대시보드</h1>
        <p className="text-muted-foreground">
          Policy Admin 권한으로 정책과 엔티티를 관리할 수 있습니다
        </p>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <Card className="border-red-200 bg-red-50 mb-6">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* 안내 정보 */}
      <Card className="mb-6 border-l-4 border-l-primary">
        <CardHeader>
          <CardTitle className="text-lg">📌 Policy Admin 권한 안내</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p>• 정책과 엔티티를 생성/수정/삭제할 수 있습니다.</p>
          <p>
            • 본인이 설정한 정책이 실제로 어떻게 적용되는지 DLP 통계와 결정 로그를 통해
            확인할 수 있습니다.
          </p>
        </CardContent>
      </Card>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {loading ? (
          <Card className="col-span-full">
            <CardContent className="py-6 text-center">
              <p className="text-muted-foreground">통계를 불러오는 중...</p>
            </CardContent>
          </Card>
        ) : (
          statsCards.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-primary">{stat.value}</div>
            </CardContent>
          </Card>
          ))
        )}
      </div>

      {/* 빠른 작업 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>빠른 작업</CardTitle>
          <CardDescription>자주 사용하는 기능에 빠르게 접근하세요</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4">
          <Button onClick={() => onNavigate?.('policy-add')}>➕ 정책 추가 (멀티모달)</Button>
          <Button onClick={() => onNavigate?.('policy-list')} variant="outline">
            📋 정책 목록 보기
          </Button>
          <Button onClick={() => onNavigate?.('policy-management')} variant="outline">
            🧪 정책 관리 (CRUD)
          </Button>
          <Button variant="outline">📊 DLP 통계</Button>
          <Button variant="outline">📝 승인/반려 로그</Button>
        </CardContent>
      </Card>

      {/* 최근 생성된 정책 */}
      <Card>
        <CardHeader>
          <CardTitle>📋 최근 생성된 정책</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-muted-foreground py-4">로딩 중...</p>
          ) : recentPolicies.length === 0 ? (
            <p className="text-center text-muted-foreground py-4">등록된 정책이 없습니다</p>
          ) : (
            <div className="space-y-4">
              {recentPolicies.map((policy) => (
                <div key={policy.policy_id} className="border-l-4 border-l-primary bg-muted p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">📄 {policy.title}</h4>
                  <p className="text-sm text-muted-foreground mb-2">기관: {policy.authority}</p>
                  {policy.description && (
                    <p className="text-xs text-muted-foreground">
                      {policy.description.substring(0, 100)}
                      {policy.description.length > 100 ? '...' : ''}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
