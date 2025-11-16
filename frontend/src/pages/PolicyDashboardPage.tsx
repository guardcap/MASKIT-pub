import React from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileText, Database, BarChart3, Shield } from 'lucide-react'

interface PolicyDashboardPageProps {
  onNavigate?: (page: string) => void
}

export const PolicyDashboardPage: React.FC<PolicyDashboardPageProps> = ({ onNavigate }) => {
  const stats = [
    { label: '등록된 정책', value: '12', icon: FileText },
    { label: '등록된 엔티티', value: '45', icon: Database },
    { label: '정책 적용 메일', value: '1,234', icon: Shield },
    { label: '마스킹 건수', value: '567', icon: BarChart3 },
  ]

  return (
    <div className="container mx-auto max-w-6xl p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">정책 관리 대시보드</h1>
        <p className="text-muted-foreground">
          Policy Admin 권한으로 정책과 엔티티를 관리할 수 있습니다
        </p>
      </div>

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
        {stats.map((stat, index) => (
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
        ))}
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
          <div className="space-y-4">
            <div className="border-l-4 border-l-primary bg-muted p-4 rounded-lg">
              <h4 className="font-semibold mb-2">📄 개인정보 처리 방침 2024</h4>
              <p className="text-sm text-muted-foreground mb-2">정책 수: 5개</p>
              <p className="text-xs text-muted-foreground">
                첫 번째 정책: 개인정보의 수집 및 이용 목적을 명확히 하고...
              </p>
            </div>
            <div className="border-l-4 border-l-primary bg-muted p-4 rounded-lg">
              <h4 className="font-semibold mb-2">📄 금융 보안 가이드</h4>
              <p className="text-sm text-muted-foreground mb-2">정책 수: 3개</p>
              <p className="text-xs text-muted-foreground">
                첫 번째 정책: 금융 정보는 암호화하여 저장해야 합니다...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
