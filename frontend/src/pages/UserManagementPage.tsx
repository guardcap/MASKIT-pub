import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Users, Trash2, Shield, Loader2, RefreshCw, Info } from 'lucide-react';
import { toast } from 'sonner';

interface User {
  email: string;
  nickname: string;
  department?: string;
  team_name?: string;
  role: 'root_admin' | 'auditor' | 'policy_admin' | 'user';
  created_at: string;
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [roleChangeDialogOpen, setRoleChangeDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<{ email: string; role?: string } | null>(null);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const roleNames: Record<string, string> = {
    root_admin: 'ROOT 관리자',
    auditor: '감사자',
    policy_admin: '정책 관리자',
    user: '일반 사용자'
  };

  const roleColors: Record<string, string> = {
    root_admin: 'bg-blue-100 text-blue-800',
    auditor: 'bg-amber-100 text-amber-800',
    policy_admin: 'bg-purple-100 text-purple-800',
    user: 'bg-slate-100 text-slate-800'
  };

  useEffect(() => {
    // 현재 로그인한 사용자 정보 로드
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        setCurrentUser(user);
      } catch (error) {
        console.error('사용자 정보 파싱 오류:', error);
      }
    }
    
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      toast.error('인증 토큰이 없습니다. 다시 로그인해주세요.');
      setLoading(false);
      return;
    }

    try {
      console.log('📋 사용자 목록 로딩 시작...');
      
      const response = await fetch(`${API_BASE}/api/users/`, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('📋 응답 상태:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: 사용자 목록을 불러올 수 없습니다`);
      }

      const data = await response.json();
      console.log('✅ 로드된 사용자 수:', data.length);
      
      setUsers(data);
      toast.success(`${data.length}명의 사용자를 불러왔습니다`);
    } catch (error: any) {
      console.error('❌ 사용자 목록 로드 오류:', error);
      toast.error(error.message || '사용자 목록을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (email: string, newRole: string) => {
    setSelectedUser({ email, role: newRole });
    setRoleChangeDialogOpen(true);
  };

  const confirmRoleChange = async () => {
    if (!selectedUser?.email || !selectedUser?.role) return;

    const { email, role: newRole } = selectedUser;
    const token = localStorage.getItem('auth_token');

    if (!token) {
      toast.error('인증 토큰이 없습니다. 다시 로그인해주세요.');
      setRoleChangeDialogOpen(false);
      return;
    }

    // 이전 권한 찾기
    const targetUser = users.find(u => u.email === email);
    const oldRole = targetUser?.role;

    setActionLoading(email);
    setRoleChangeDialogOpen(false);

    try {
      console.log('\n🔄 권한 변경 시도:', { email, oldRole, newRole });

      const response = await fetch(`${API_BASE}/api/users/${encodeURIComponent(email)}/role`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ role: newRole })
      });

      console.log('📡 응답 상태:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('❌ 오류 응답:', errorData);
        throw new Error(errorData.detail || '권한 변경에 실패했습니다');
      }

      const result = await response.json();
      console.log('✅ 권한 변경 결과:', result);

      // 감사 로그 기록
      try {
        await fetch(`${API_BASE}/api/audit/logs`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            event_type: 'user_role_change',
            severity: 'info',
            action: `사용자 권한 변경: ${email}`,
            resource_type: 'user',
            resource_id: email,
            details: {
              target_user: email,
              old_role: oldRole,
              new_role: newRole,
              changed_by: currentUser?.email
            },
            success: true
          })
        });
        console.log('📝 감사 로그 기록 완료');
      } catch (logError) {
        console.warn('⚠️ 감사 로그 기록 실패 (권한 변경은 성공):', logError);
      }

      toast.success(`${email}의 권한이 "${roleNames[newRole]}"(으)로 변경되었습니다`);

      // 목록 새로고침
      await loadUsers();

    } catch (error: any) {
      console.error('❌ 권한 변경 오류:', error);

      // 실패 시에도 감사 로그 기록
      try {
        await fetch(`${API_BASE}/api/audit/logs`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            event_type: 'user_role_change',
            severity: 'error',
            action: `사용자 권한 변경 실패: ${email}`,
            resource_type: 'user',
            resource_id: email,
            details: {
              target_user: email,
              old_role: oldRole,
              new_role: newRole,
              changed_by: currentUser?.email
            },
            success: false,
            error_message: error.message
          })
        });
      } catch (logError) {
        console.warn('⚠️ 실패 감사 로그 기록 실패:', logError);
      }

      toast.error(error.message || '권한 변경에 실패했습니다');
    } finally {
      setActionLoading(null);
      setSelectedUser(null);
    }
  };

  const handleDeleteUser = (email: string) => {
    setSelectedUser({ email });
    setDeleteDialogOpen(true);
  };

  const confirmDeleteUser = async () => {
    if (!selectedUser?.email) return;

    const { email } = selectedUser;
    const token = localStorage.getItem('auth_token');

    if (!token) {
      toast.error('인증 토큰이 없습니다. 다시 로그인해주세요.');
      setDeleteDialogOpen(false);
      return;
    }

    setActionLoading(email);
    setDeleteDialogOpen(false);

    try {
      console.log('🗑️ 사용자 삭제 시도:', email);

      const response = await fetch(`${API_BASE}/api/users/${encodeURIComponent(email)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('📡 응답 상태:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || '사용자 삭제에 실패했습니다');
      }

      toast.success('사용자가 삭제되었습니다');
      await loadUsers();

    } catch (error: any) {
      console.error('❌ 사용자 삭제 오류:', error);
      toast.error(error.message || '사용자 삭제에 실패했습니다');
    } finally {
      setActionLoading(null);
      setSelectedUser(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  const getDepartmentDisplay = (user: User) => {
    return user.department || user.team_name || '-';
  };

  return (
    <div>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2 flex items-center gap-3">
            사용자 계정 관리
          </h1>
          <p className="text-slate-600">사용자의 권한을 관리하고 계정을 관리할 수 있습니다</p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </div>
        )}

        {/* Empty State */}
        {!loading && users.length === 0 && (
          <Card className="border-2 border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-20">
              <Users className="w-16 h-16 text-slate-300 mb-4" />
              <h3 className="text-xl font-semibold text-slate-700 mb-2">등록된 사용자가 없습니다</h3>
              <Button onClick={loadUsers} className="mt-4">
                다시 시도
              </Button>
            </CardContent>
          </Card>
        )}

        {/* User Table */}
        {!loading && users.length > 0 && (
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>사용자 목록 ({users.length}명)</CardTitle>
                  <CardDescription>등록된 모든 사용자의 정보와 권한을 확인할 수 있습니다</CardDescription>
                </div>
                <Button onClick={loadUsers} variant="outline" disabled={loading}>
                  <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  새로고침
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>이메일</TableHead>
                    <TableHead>닉네임</TableHead>
                    <TableHead>부서</TableHead>
                    <TableHead>권한</TableHead>
                    <TableHead>가입일</TableHead>
                    <TableHead>관리</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => {
                    const isCurrentUser = user.email === currentUser?.email;
                    const isActionPending = actionLoading === user.email;

                    return (
                      <TableRow key={user.email}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{user.email}</span>
                            {isCurrentUser && (
                              <Badge variant="secondary" className="text-xs">본인</Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{user.nickname}</TableCell>
                        <TableCell>{getDepartmentDisplay(user)}</TableCell>
                        <TableCell>
                          <Badge className={roleColors[user.role]}>
                            {roleNames[user.role]}
                          </Badge>
                        </TableCell>
                        <TableCell>{formatDate(user.created_at)}</TableCell>
                        <TableCell>
                          {isCurrentUser ? (
                            <span className="text-muted-foreground text-sm">본인 계정</span>
                          ) : (
                            <div className="flex gap-2">
                              <Select
                                value={user.role}
                                onValueChange={(value) => handleRoleChange(user.email, value)}
                                disabled={isActionPending}
                              >
                                <SelectTrigger className="w-[160px] h-9">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="root_admin">ROOT 관리자</SelectItem>
                                  <SelectItem value="auditor">감사자</SelectItem>
                                  <SelectItem value="policy_admin">정책 관리자</SelectItem>
                                  <SelectItem value="user">일반 사용자</SelectItem>
                                </SelectContent>
                              </Select>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleDeleteUser(user.email)}
                                disabled={isActionPending}
                              >
                                {isActionPending ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Trash2 className="w-4 h-4" />
                                )}
                              </Button>
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Role Change Confirmation Dialog */}
      <AlertDialog open={roleChangeDialogOpen} onOpenChange={setRoleChangeDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>권한 변경 확인</AlertDialogTitle>
            <AlertDialogDescription>
              {selectedUser?.email}의 권한을 "{selectedUser?.role && roleNames[selectedUser.role]}"(으)로 변경하시겠습니까?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction onClick={confirmRoleChange}>변경</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete User Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>사용자 삭제 확인</AlertDialogTitle>
            <AlertDialogDescription>
              {selectedUser?.email} 사용자를 삭제하시겠습니까?
              <br />
              <span className="text-destructive font-semibold">이 작업은 되돌릴 수 없습니다.</span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDeleteUser} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}