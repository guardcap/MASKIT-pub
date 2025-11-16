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
import { Users, Trash2, Shield, UserCog, Loader2, AlertCircle } from 'lucide-react';

interface User {
  email: string;
  nickname: string;
  department?: string;
  team_name?: string;
  role: 'root_admin' | 'auditor' | 'policy_admin' | 'approver' | 'user';
  created_at: string;
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState<any>(null);

  const API_BASE = 'http://127.0.0.1:8001';
  const token = localStorage.getItem('token');

  const roleNames: Record<string, string> = {
    root_admin: 'ROOT 관리자',
    auditor: '감사자',
    policy_admin: '정책 관리자',
    approver: '승인자',
    user: '일반 사용자'
  };

  const roleColors: Record<string, string> = {
    root_admin: 'bg-blue-100 text-blue-800',
    auditor: 'bg-amber-100 text-amber-800',
    policy_admin: 'bg-purple-100 text-purple-800',
    approver: 'bg-green-100 text-green-800',
    user: 'bg-slate-100 text-slate-800'
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/users/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else {
        console.error('Failed to load users');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (email: string, newRole: string) => {
    if (!confirm(`${email}의 권한을 "${roleNames[newRole]}"(으)로 변경하시겠습니까?`)) {
      return;
    }

    try {
      const encodedEmail = encodeURIComponent(email);
      const url = `${API_BASE}/api/v1/users/${encodedEmail}/role?role=${encodeURIComponent(newRole)}`;

      const response = await fetch(url, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('권한이 변경되었습니다');
        await loadUsers();
      } else {
        const data = await response.json();
        alert('권한 변경 실패: ' + (data.detail || '오류가 발생했습니다'));
      }
    } catch (error: any) {
      alert('오류가 발생했습니다: ' + error.message);
    }
  };

  const handleDeleteUser = async (email: string) => {
    if (!confirm(`${email} 사용자를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) {
      return;
    }

    try {
      const encodedEmail = encodeURIComponent(email);
      const response = await fetch(`${API_BASE}/api/v1/users/${encodedEmail}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('사용자가 삭제되었습니다');
        await loadUsers();
      } else {
        const data = await response.json();
        alert('삭제 실패: ' + (data.detail || '오류가 발생했습니다'));
      }
    } catch (error: any) {
      alert('오류가 발생했습니다: ' + error.message);
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
              <li><strong>승인자 (Approver):</strong> 팀 소속 메일 승인/반려, 팀 통계/로그 읽기</li>
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
            </CardContent>
          </Card>
        )}

        {/* User Table */}
        {!loading && users.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>사용자 목록 ({users.length}명)</CardTitle>
              <CardDescription>등록된 모든 사용자의 정보와 권한을 확인할 수 있습니다</CardDescription>
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
                                  onValueChange={(value) => handleRoleChange(user.email, value)}
                                >
                                  <SelectTrigger className="w-[160px] h-9">
                                    <SelectValue placeholder="권한 변경" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="root_admin">ROOT 관리자</SelectItem>
                                    <SelectItem value="auditor">감사자</SelectItem>
                                    <SelectItem value="policy_admin">정책 관리자</SelectItem>
                                    <SelectItem value="approver">승인자</SelectItem>
                                    <SelectItem value="user">일반 사용자</SelectItem>
                                  </SelectContent>
                                </Select>
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  onClick={() => handleDeleteUser(user.email)}
                                  className="gap-1"
                                >
                                  <Trash2 className="w-4 h-4" />
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
