import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Mail, Users, CheckCircle, XCircle, AlertCircle, Building, Search, RefreshCw, Paperclip } from 'lucide-react'

interface AuditorStats {
  total_emails: number
  pending_emails: number
  approved_emails: number
  rejected_emails: number
  total_teams: number
  total_users: number
}

interface EmailLog {
  timestamp: string
  email_id: string
  team_name: string
  user_name: string
  from_email: string
  to_email: string
  subject: string
  status: string
  has_attachments: boolean
  attachment_count: number
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
  const [logs, setLogs] = useState<EmailLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [total, setTotal] = useState(0)
  const [skip, setSkip] = useState(0)
  const [limit] = useState(50)

  useEffect(() => {
    loadStats()
    loadEmailLogs()
  }, [skip])

  const loadStats = async () => {
    try {
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

      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Error loading stats:', err)
    }
  }

  const loadEmailLogs = async () => {
    try {
      setLoading(true)
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
      const token = localStorage.getItem('auth_token')

      if (!token) {
        throw new Error('인증 토큰이 없습니다.')
      }

      console.log(`📧 전체 메일 로그 조회 시작 (skip: ${skip}, limit: ${limit})`)

      const response = await fetch(
        `${API_BASE}/api/v1/emails/all-logs?skip=${skip}&limit=${limit}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (!response.ok) {
        throw new Error('메일 로그를 불러오는데 실패했습니다.')
      }

      const data = await response.json()

      if (data.success) {
        setLogs(data.logs || [])
        setTotal(data.total || 0)
        setError(null)
        console.log(`✅ ${data.logs.length}개 로그 조회 완료 (전체: ${data.total}개)`)
      } else {
        throw new Error('로그 조회 실패')
      }
    } catch (err) {
      console.error('Error loading email logs:', err)
      setError(err instanceof Error ? err.message : '오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: 'secondary' | 'default' | 'destructive'; label: string }> = {
      pending: { variant: 'secondary', label: '대기' },
      approved: { variant: 'default', label: '승인' },
      rejected: { variant: 'destructive', label: '반려' },
      sent: { variant: 'default', label: '전송' },
    }
    const config = variants[status] || { variant: 'secondary', label: status }

    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  // 검색 필터링
  const filteredLogs = logs.filter((log) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      log.user_name.toLowerCase().includes(query) ||
      log.team_name.toLowerCase().includes(query) ||
      log.from_email.toLowerCase().includes(query) ||
      log.to_email.toLowerCase().includes(query) ||
      log.subject.toLowerCase().includes(query)
    )
  })

  // 페이지네이션
  const handlePrevPage = () => {
    if (skip >= limit) {
      setSkip(skip - limit)
    }
  }

  const handleNextPage = () => {
    if (skip + limit < total) {
      setSkip(skip + limit)
    }
  }

  const statCards = [
    {
      title: '전체 메일',
      value: total.toLocaleString(),
      icon: Mail,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
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

      {/* 권한 안내 */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="text-blue-900">📌 Auditor 권한 안내</CardTitle>
        </CardHeader>
        <CardContent className="text-blue-800 space-y-2">
          <p>
            모든 로그, 통계, 메일, 정책을 <strong>읽기 전용</strong>으로 조회할 수 있습니다.
          </p>
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

      {/* 전체 메일 로그 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>📋 전체 메일 전송 로그</CardTitle>
            <Button variant="outline" size="sm" onClick={loadEmailLogs}>
              <RefreshCw className="h-4 w-4 mr-2" />
              새로고침
            </Button>
          </div>
          <div className="flex items-center gap-4 mt-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="사용자명, 팀, 이메일, 제목으로 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="text-sm text-muted-foreground">
              전체 {total.toLocaleString()}개 중 {filteredLogs.length}개 표시
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">로그를 불러오는 중...</div>
          ) : logs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">메일 로그가 없습니다</div>
          ) : (
            <>
              <div className="space-y-2">
                {filteredLogs.map((log) => (
                  <div
                    key={log.email_id}
                    className="px-4 py-2 bg-muted/30 rounded-md text-sm font-mono"
                  >
                    <span className="text-muted-foreground">
                      [{formatDate(log.timestamp)}]
                    </span>
                    {' '}
                    <span className="text-muted-foreground">
                      ({log.email_id.substring(0, 8)}...)
                    </span>
                    {' '}
                    <span className="font-semibold">{log.team_name}</span>
                    {' '}
                    <span>{log.user_name}</span>
                  </div>
                ))}
              </div>

              {/* 페이지네이션 */}
              <div className="flex items-center justify-between mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePrevPage}
                  disabled={skip === 0}
                >
                  이전
                </Button>
                <div className="text-sm text-muted-foreground">
                  {skip + 1} - {Math.min(skip + limit, total)} / {total}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNextPage}
                  disabled={skip + limit >= total}
                >
                  다음
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}