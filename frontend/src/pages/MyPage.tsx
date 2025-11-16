import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { Save, Eye, EyeOff, Mail, Server, Lock } from 'lucide-react'

interface SMTPSettings {
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_password: string
  use_tls: boolean
  use_ssl: boolean
}

export const MyPage: React.FC = () => {
  const [smtpSettings, setSmtpSettings] = useState<SMTPSettings>({
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    use_tls: true,
    use_ssl: false,
  })

  const [showPassword, setShowPassword] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // localStorage에서 SMTP 설정 불러오기
  useEffect(() => {
    const savedSettings = localStorage.getItem('smtp_settings')
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings)
        setSmtpSettings(parsed)
        toast.success('저장된 SMTP 설정을 불러왔습니다')
      } catch (error) {
        console.error('SMTP 설정 로드 실패:', error)
      }
    }
  }, [])

  const handleSave = () => {
    // 필수 항목 검증
    if (!smtpSettings.smtp_host) {
      toast.error('SMTP 서버 주소를 입력하세요')
      return
    }

    if (!smtpSettings.smtp_user) {
      toast.error('SMTP 사용자 이메일을 입력하세요')
      return
    }

    if (!smtpSettings.smtp_password) {
      toast.error('SMTP 비밀번호를 입력하세요')
      return
    }

    setIsSaving(true)

    try {
      // localStorage에 저장
      localStorage.setItem('smtp_settings', JSON.stringify(smtpSettings))

      toast.success('SMTP 설정이 저장되었습니다', {
        description: '이제 이메일 전송 시 이 설정이 사용됩니다.',
        duration: 5000,
      })
    } catch (error) {
      console.error('SMTP 설정 저장 실패:', error)
      toast.error('SMTP 설정 저장에 실패했습니다')
    } finally {
      setIsSaving(false)
    }
  }

  const handleTest = async () => {
    if (!smtpSettings.smtp_host || !smtpSettings.smtp_user || !smtpSettings.smtp_password) {
      toast.error('모든 필수 항목을 입력하세요')
      return
    }

    toast.loading('SMTP 연결 테스트 중...', { id: 'smtp-test' })

    try {
      // 테스트 이메일 전송
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/smtp/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from_email: smtpSettings.smtp_user,
          to: smtpSettings.smtp_user, // 자기 자신에게 전송
          subject: 'SMTP 설정 테스트',
          body: '<h1>SMTP 연결 테스트</h1><p>이 이메일은 SMTP 설정이 정상적으로 작동하는지 확인하기 위한 테스트 메일입니다.</p>',
          smtp_config: smtpSettings, // 사용자 설정 전달
        }),
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || result.message || 'SMTP 테스트 실패')
      }

      toast.success('SMTP 연결 성공!', {
        id: 'smtp-test',
        description: '테스트 이메일이 전송되었습니다. 받은편지함을 확인하세요.',
        duration: 5000,
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류'
      toast.error('SMTP 연결 실패', {
        id: 'smtp-test',
        description: errorMessage,
        duration: 7000,
      })
    }
  }

  const handleLoadPreset = (preset: 'gmail' | 'naver' | 'mailplug') => {
    const presets: Record<string, Partial<SMTPSettings>> = {
      gmail: {
        smtp_host: 'smtp.gmail.com',
        smtp_port: 587,
        use_tls: true,
        use_ssl: false,
      },
      naver: {
        smtp_host: 'smtp.naver.com',
        smtp_port: 587,
        use_tls: true,
        use_ssl: false,
      },
      mailplug: {
        smtp_host: 'smtp.mailplug.co.kr',
        smtp_port: 465,
        use_tls: false,
        use_ssl: true,
      },
    }

    setSmtpSettings((prev) => ({
      ...prev,
      ...presets[preset],
    }))

    toast.success(`${preset.toUpperCase()} 프리셋이 적용되었습니다`, {
      description: '사용자 이메일과 비밀번호를 입력하세요.',
    })
  }

  return (
    <div className="container mx-auto max-w-4xl p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold">마이페이지</h2>
        <p className="text-muted-foreground">SMTP 서버 설정 및 개인 정보 관리</p>
      </div>

      <div className="space-y-6">
        {/* SMTP 설정 카드 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              SMTP 서버 설정
            </CardTitle>
            <CardDescription>
              이메일 전송에 사용할 SMTP 서버 정보를 입력하세요. 설정은 브라우저에 안전하게 저장됩니다.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* 프리셋 버튼 */}
            <div>
              <Label className="mb-2 block">빠른 설정 (프리셋)</Label>
              <div className="flex gap-2 flex-wrap">
                <Button variant="outline" size="sm" onClick={() => handleLoadPreset('gmail')}>
                  Gmail (587/TLS)
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleLoadPreset('naver')}>
                  Naver (587/TLS)
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleLoadPreset('mailplug')}>
                  Mailplug (465/SSL)
                </Button>
              </div>
            </div>

            {/* SMTP 호스트 */}
            <div className="grid gap-2">
              <Label htmlFor="smtp_host" className="flex items-center gap-2">
                <Server className="h-4 w-4" />
                SMTP 서버 주소
              </Label>
              <Input
                id="smtp_host"
                type="text"
                value={smtpSettings.smtp_host}
                onChange={(e) => setSmtpSettings({ ...smtpSettings, smtp_host: e.target.value })}
                placeholder="smtp.gmail.com"
              />
            </div>

            {/* SMTP 포트 */}
            <div className="grid gap-2">
              <Label htmlFor="smtp_port">SMTP 포트</Label>
              <Input
                id="smtp_port"
                type="number"
                value={smtpSettings.smtp_port}
                onChange={(e) =>
                  setSmtpSettings({ ...smtpSettings, smtp_port: parseInt(e.target.value) || 587 })
                }
                placeholder="587"
              />
              <p className="text-xs text-muted-foreground">
                일반적으로 587 (TLS) 또는 465 (SSL)를 사용합니다
              </p>
            </div>

            {/* 프로토콜 선택 */}
            <div className="grid gap-2">
              <Label>보안 프로토콜</Label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="protocol"
                    checked={smtpSettings.use_tls && !smtpSettings.use_ssl}
                    onChange={() =>
                      setSmtpSettings({ ...smtpSettings, use_tls: true, use_ssl: false })
                    }
                  />
                  <span className="text-sm">TLS (포트 587)</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="protocol"
                    checked={smtpSettings.use_ssl && !smtpSettings.use_tls}
                    onChange={() =>
                      setSmtpSettings({ ...smtpSettings, use_tls: false, use_ssl: true })
                    }
                  />
                  <span className="text-sm">SSL (포트 465)</span>
                </label>
              </div>
            </div>

            {/* SMTP 사용자 */}
            <div className="grid gap-2">
              <Label htmlFor="smtp_user" className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                이메일 주소
              </Label>
              <Input
                id="smtp_user"
                type="email"
                value={smtpSettings.smtp_user}
                onChange={(e) => setSmtpSettings({ ...smtpSettings, smtp_user: e.target.value })}
                placeholder="your@email.com"
              />
            </div>

            {/* SMTP 비밀번호 */}
            <div className="grid gap-2">
              <Label htmlFor="smtp_password" className="flex items-center gap-2">
                <Lock className="h-4 w-4" />
                비밀번호 또는 앱 비밀번호
              </Label>
              <div className="relative">
                <Input
                  id="smtp_password"
                  type={showPassword ? 'text' : 'password'}
                  value={smtpSettings.smtp_password}
                  onChange={(e) =>
                    setSmtpSettings({ ...smtpSettings, smtp_password: e.target.value })
                  }
                  placeholder="••••••••"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="text-xs text-muted-foreground">
                Gmail의 경우{' '}
                <a
                  href="https://myaccount.google.com/apppasswords"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary underline"
                >
                  앱 비밀번호
                </a>
                를 생성하여 사용하세요
              </p>
            </div>

            {/* 버튼 그룹 */}
            <div className="flex gap-2 pt-4">
              <Button onClick={handleSave} disabled={isSaving} className="flex-1">
                <Save className="mr-2 h-4 w-4" />
                {isSaving ? '저장 중...' : '설정 저장'}
              </Button>
              <Button variant="outline" onClick={handleTest} className="flex-1">
                <Mail className="mr-2 h-4 w-4" />
                연결 테스트
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 안내 카드 */}
        <Card>
          <CardHeader>
            <CardTitle>💡 SMTP 설정 안내</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Gmail 사용 시</h4>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                <li>2단계 인증 활성화 필요</li>
                <li>
                  <a
                    href="https://myaccount.google.com/apppasswords"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary underline"
                  >
                    앱 비밀번호 생성
                  </a>{' '}
                  후 사용
                </li>
                <li>포트: 587, 프로토콜: TLS</li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-2">Naver 메일 사용 시</h4>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                <li>환경설정 → POP3/IMAP 설정 → IMAP/SMTP 사용 ON</li>
                <li>포트: 587, 프로토콜: TLS</li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-2">보안 안내</h4>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                <li>설정은 브라우저 localStorage에 저장됩니다</li>
                <li>실제 전송 시에만 backend로 전달됩니다</li>
                <li>공용 PC에서는 사용 후 설정을 삭제하세요</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
