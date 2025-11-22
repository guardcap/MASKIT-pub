import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Mail, Paperclip, ArrowLeft, Inbox, Search, Filter, Send, ArrowUpRight, ArrowDownLeft } from 'lucide-react'

interface Email {
  _id: string
  subject: string
  from_email: string
  to_email: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  attachments?: any[]
  read?: boolean
  direction: 'sent' | 'received' // 추가: 이메일 방향
}

interface AllEmailsPageProps {
  onNavigate?: (view: string, emailId?: string) => void
  onBack?: () => void
  currentUserEmail?: string // 현재 로그인한 사용자 이메일
}

export function AllEmailsPage({ onNavigate, onBack, currentUserEmail }: AllEmailsPageProps) {
  const [emails, setEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [directionFilter, setDirectionFilter] = useState<string>('all') // 보낸/받은 필터
  const [readFilter, setReadFilter] = useState<string>('all')

  useEffect(() => {
    loadAllEmails()
  }, [])

  const loadAllEmails = async () => {
    try {
      setLoading(true)
      const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
      const token = localStorage.getItem('auth_token')

      if (!token) {
        throw new Error('인증 토큰이 없습니다.')
      }

      // 보낸 메일과 받은 메일을 모두 가져옴
      const [sentResponse, receivedResponse] = await Promise.all([
        fetch(`${API_BASE}/api/v1/emails/my-emails`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE}/api/v1/emails/received-emails`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ])

      if (!sentResponse.ok || !receivedResponse.ok) {
        throw new Error('메일을 불러오는데 실패했습니다.')
      }

      const sentData = await sentResponse.json()
      const receivedData = await receivedResponse.json()

      // 보낸 메일과 받은 메일을 구분하여 병합
      const sentEmails = sentData.map((email: any) => ({
        ...email,
        direction: 'sent' as const,
      }))

      const receivedEmails = receivedData.map((email: any) => ({
        ...email,
        direction: 'received' as const,
      }))

      // 모든 메일을 시간순으로 정렬 (최신순)
      const allEmails = [...sentEmails, ...receivedEmails].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )

      setEmails(allEmails)
      setError(null)
    } catch (err) {
      console.error('Error loading emails:', err)
      setError(err instanceof Error ? err.message : '오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }


  const getDirectionBadge = (direction: string) => {
    if (direction === 'sent') {
      return (
        <div className="flex items-center gap-1 text-blue-600">
          <ArrowUpRight className="h-3 w-3" />
          <span className="text-xs">보냄</span>
        </div>
      )
    }
    return (
      <div className="flex items-center gap-1 text-green-600">
        <ArrowDownLeft className="h-3 w-3" />
        <span className="text-xs">받음</span>
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // 필터링된 메일 목록
  const filteredEmails = emails.filter((email) => {
    const matchesSearch =
      email.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      email.from_email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      email.to_email.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesDirection = directionFilter === 'all' || email.direction === directionFilter
    const matchesRead =
      readFilter === 'all' ||
      (readFilter === 'read' && email.read) ||
      (readFilter === 'unread' && !email.read)
    return matchesSearch && matchesDirection && matchesRead
  })

  const sentCount = emails.filter((e) => e.direction === 'sent').length
  const receivedCount = emails.filter((e) => e.direction === 'received').length
  const unreadCount = emails.filter((e) => e.direction === 'received' && !e.read).length

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">전체 메일함</h1>
          <p className="text-muted-foreground">보낸 메일과 받은 메일 통합 보기</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => onNavigate?.('write-email')}>
            <Send className="h-4 w-4 mr-2" />
            메일 쓰기
          </Button>
          {onBack && (
            <Button variant="ghost" onClick={onBack}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              뒤로
            </Button>
          )}
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전체 메일</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{emails.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">보낸 메일</CardTitle>
            <ArrowUpRight className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{sentCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">받은 메일</CardTitle>
            <ArrowDownLeft className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{receivedCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">읽지 않음</CardTitle>
            <Inbox className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{unreadCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* 검색 및 필터 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="제목, 보낸 사람, 받는 사람으로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <Select value={directionFilter} onValueChange={setDirectionFilter}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="방향" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">전체</SelectItem>
                    <SelectItem value="sent">보낸 메일</SelectItem>
                    <SelectItem value="received">받은 메일</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={readFilter} onValueChange={setReadFilter}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="읽음" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">전체</SelectItem>
                    <SelectItem value="unread">읽지 않음</SelectItem>
                    <SelectItem value="read">읽음</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 메일 목록 */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">{error}</p>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">메일을 불러오는 중...</p>
          </CardContent>
        </Card>
      ) : emails.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <Inbox className="h-12 w-12 mx-auto text-muted-foreground" />
              <p className="text-muted-foreground">메일이 없습니다</p>
              <Button onClick={() => onNavigate?.('write-email')}>
                <Mail className="h-4 w-4 mr-2" />
                메일 작성하기
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : filteredEmails.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <Search className="h-12 w-12 mx-auto text-muted-foreground" />
              <p className="text-muted-foreground">검색 결과가 없습니다</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>메일 목록 ({filteredEmails.length}개)</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[3%]"></TableHead>
                  <TableHead className="w-[5%]">구분</TableHead>
                  <TableHead className="w-[35%]">제목</TableHead>
                  <TableHead className="w-[18%]">보낸이</TableHead>
                  <TableHead className="w-[18%]">받는이</TableHead>
                  <TableHead className="w-[15%]">날짜</TableHead>
                  <TableHead className="w-[6%]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEmails.map((email) => (
                  <TableRow
                    key={email._id}
                    className={`cursor-pointer ${
                      email.direction === 'received' && !email.read
                        ? 'bg-blue-50/30 hover:bg-blue-50/50'
                        : ''
                    }`}
                    onClick={() => onNavigate?.('email-detail', email._id)}
                  >
                    <TableCell>
                      {email.direction === 'received' && !email.read && (
                        <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                      )}
                    </TableCell>
                    <TableCell>{getDirectionBadge(email.direction)}</TableCell>
                    <TableCell
                      className={`font-medium ${
                        email.direction === 'received' && !email.read ? 'font-semibold' : ''
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="truncate">{email.subject}</span>
                        {email.attachments && email.attachments.length > 0 && (
                          <Paperclip className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span
                        className={`text-sm truncate block ${
                          email.direction === 'received' && !email.read
                            ? 'font-medium text-foreground'
                            : 'text-muted-foreground'
                        }`}
                      >
                        {email.from_email}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground truncate block">
                        {email.to_email}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {formatDate(email.created_at)}
                      </span>
                    </TableCell>
                    <TableCell>
                      {email.attachments && email.attachments.length > 0 && (
                        <Badge variant="secondary" className="text-xs">
                          {email.attachments.length}
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
