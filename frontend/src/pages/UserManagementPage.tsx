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
import { Users, Trash2, Shield, Loader2, RefreshCw } from 'lucide-react';
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
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      toast.error('인증 토큰이 없습니다. 다시 로그인해주세요.');
      return;
    }

    if (!confirm(`${email}의 권한을 "${roleNames[newRole]}"(으)로 변경하시겠습니까?`)) {
      return;
    }

    setActionLoading(email);

    try {
      console.log('\n🔄 권한 변경 시도:', { email, newRole });
      
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
      
      toast.success(`${email}의 권한이 "${roleNames[newRole]}"(으)로 변경되었습니다`);
      
      // 목록 새로고침
      await loadUsers();
      
    } catch (error: any) {
      console.error('❌ 권한 변경 오류:', error);
      toast.error(error.message || '권한 변경에 실패했습니다');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteUser = async (email: string) => {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      toast.error('인증 토큰이 없습니다. 다시 로그인해주세요.');
      return;
    }

    if (!confirm(`${email} 사용자를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) {
      return;
    }

    setActionLoading(email);

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
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2 flex items-center gap-3">
            <Users className="w-10 h-10 text-purple-600" />
            사용자 계정 관리
          </h1>
          <p className="text-slate-600">사용자의 권한을 관리하고 계정을 관리할 수 있습니다</p>
        </div>

        {/* Role Description */}
        <Card className="mb-6 border-l-4 border-l-purple-500 bg-purple-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-purple-900">
              <Shield className="w-5 h-5" />
              권한 설명
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-purple-900">
              <li><strong>ROOT 관리자:</strong> 시스템 설정, 팀/사용자 관리, 모든 권한</li>
              <li><strong>감사자 (Auditor):</strong> 모든 로그, 통계, 설정 읽기 전용 (사후 감독)</li>
              <li><strong>정책 관리자 (Policy Admin):</strong> 엔티티, 정책 CRUD, 통계/로그 읽기</li>
              <li><strong>일반 사용자 (User):</strong> 메일 작성, 본인 통계/로그 읽기</li>
            </ul>
          </CardContent>
        </Card>

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
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b-2 border-slate-200">
                      <th className="text-left p-4 font-semibold text-slate-700">이메일</th>
                      <th className="text-left p-4 font-semibold text-slate-700">닉네임</th>
                      <th className="text-left p-4 font-semibold text-slate-700">부서</th>
                      <th className="text-left p-4 font-semibold text-slate-700">팀</th>
                      <th className="text-left p-4 font-semibold text-slate-700">권한</th>
                      <th className="text-left p-4 font-semibold text-slate-700">가입일</th>
                      <th className="text-left p-4 font-semibold text-slate-700">관리</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => {
                      const isCurrentUser = user.email === currentUser?.email;
                      const isActionPending = actionLoading === user.email;

                      return (
                        <tr key={user.email} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                          <td className="p-4">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-slate-900">{user.email}</span>
                              {isCurrentUser && (
                                <Badge className="bg-blue-100 text-blue-800 text-xs">본인</Badge>
                              )}
                            </div>
                          </td>
                          <td className="p-4 text-slate-700">{user.nickname}</td>
                          <td className="p-4 text-slate-700">{user.department || '-'}</td>
                          <td className="p-4 text-slate-700">{user.team_name || '-'}</td>
                          <td className="p-4">
                            <Badge className={roleColors[user.role]}>
                              {roleNames[user.role]}
                            </Badge>
                          </td>
                          <td className="p-4 text-slate-700">{formatDate(user.created_at)}</td>
                          <td className="p-4">
                            {isCurrentUser ? (
                              <span className="text-slate-400 text-sm">본인 계정</span>
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
                                  className="gap-1"
                                  disabled={isActionPending}
                                >
                                  {isActionPending ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <Trash2 className="w-4 h-4" />
                                  )}
                                  삭제
                                </Button>
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}