import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, Eye, Mail, Calendar, Paperclip, Loader2 } from 'lucide-react';

interface Email {
  _id: string;
  subject: string;
  from_email: string;
  to_email: string;
  original_body: string;
  created_at: string;
  attachments?: any[];
}

export default function PendingApprovalsPage() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [currentEmailId, setCurrentEmailId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const API_BASE = 'http://127.0.0.1:8001';
  const token = localStorage.getItem('token');

  useEffect(() => {
    loadPendingEmails();
  }, []);

  const loadPendingEmails = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/emails/pending`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setEmails(data);
      } else {
        console.error('Failed to load emails');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (emailId: string) => {
    if (!confirm('이 메일을 승인하시겠습니까?')) return;

    setActionLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/emails/${emailId}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        alert('메일이 승인되었습니다');
        loadPendingEmails();
      } else {
        const data = await response.json();
        alert('승인 실패: ' + (data.detail || '오류가 발생했습니다'));
      }
    } catch (error) {
      alert('오류가 발생했습니다');
      console.error('Error:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const openRejectModal = (emailId: string) => {
    setCurrentEmailId(emailId);
    setRejectModalOpen(true);
  };

  const closeRejectModal = () => {
    setCurrentEmailId(null);
    setRejectReason('');
    setRejectModalOpen(false);
  };

  const confirmReject = async () => {
    if (!rejectReason.trim()) {
      alert('반려 사유를 입력하세요');
      return;
    }

    if (!currentEmailId) return;

    setActionLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/emails/${currentEmailId}/reject`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reason: rejectReason })
      });

      if (response.ok) {
        alert('메일이 반려되었습니다');
        closeRejectModal();
        loadPendingEmails();
      } else {
        const data = await response.json();
        alert('반려 실패: ' + (data.detail || '오류가 발생했습니다'));
      }
    } catch (error) {
      alert('오류가 발생했습니다');
      console.error('Error:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2 flex items-center gap-3">
            <Mail className="w-10 h-10 text-purple-600" />
            승인 대기 메일
          </h1>
          <p className="text-slate-600">검토가 필요한 메일을 확인하고 승인하거나 반려할 수 있습니다</p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          </div>
        )}

        {/* Empty State */}
        {!loading && emails.length === 0 && (
          <Card className="border-2 border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-20">
              <Mail className="w-16 h-16 text-slate-300 mb-4" />
              <h3 className="text-xl font-semibold text-slate-700 mb-2">승인 대기 중인 메일이 없습니다</h3>
              <p className="text-slate-500">모든 메일이 처리되었습니다</p>
            </CardContent>
          </Card>
        )}

        {/* Email List */}
        {!loading && emails.length > 0 && (
          <div className="space-y-4">
            {emails.map((email) => (
              <Card key={email._id} className="hover:shadow-lg transition-shadow border-l-4 border-l-purple-500">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-2xl mb-2">{email.subject}</CardTitle>
                      <CardDescription className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Mail className="w-4 h-4" />
                          <span>발신: {email.from_email}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Mail className="w-4 h-4" />
                          <span>수신: {email.to_email}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4" />
                          <span>{formatDate(email.created_at)}</span>
                        </div>
                        {email.attachments && email.attachments.length > 0 && (
                          <div className="flex items-center gap-2">
                            <Paperclip className="w-4 h-4" />
                            <Badge variant="secondary">
                              첨부파일 {email.attachments.length}개
                            </Badge>
                          </div>
                        )}
                      </CardDescription>
                    </div>
                    <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-200">
                      대기중
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="bg-slate-50 rounded-lg p-4 mb-4 max-h-40 overflow-y-auto">
                    <p className="text-slate-700 whitespace-pre-wrap">{email.original_body}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleApprove(email._id)}
                      disabled={actionLoading}
                      className="bg-green-600 hover:bg-green-700 gap-2"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      승인
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={() => openRejectModal(email._id)}
                      disabled={actionLoading}
                      className="gap-2"
                    >
                      <XCircle className="w-4 h-4" />
                      반려
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Reject Modal */}
      <Dialog open={rejectModalOpen} onOpenChange={setRejectModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>반려 사유</DialogTitle>
            <DialogDescription>
              메일을 반려하는 이유를 입력해주세요
            </DialogDescription>
          </DialogHeader>
          <Textarea
            placeholder="반려 사유를 입력하세요"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            className="min-h-[100px]"
          />
          <DialogFooter>
            <Button variant="outline" onClick={closeRejectModal}>
              취소
            </Button>
            <Button onClick={confirmReject} disabled={actionLoading} variant="destructive">
              {actionLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              확인
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
