import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { Mail, Save, Server } from 'lucide-react'

interface SettingsPageProps {
  onBack?: () => void
}

interface EmailSettings {
  default_email: string
}

interface SMTPSettings {
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_password: string
  smtp_use_tls: boolean
}

export function SettingsPage({ onBack }: SettingsPageProps) {
  // 이메일 설정
  const [emailSettings, setEmailSettings] = useState<EmailSettings>({
    default_email: '',
  })

  // SMTP 설정
  const [smtpSettings, setSmtpSettings] = useState<SMTPSettings>({
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    smtp_use_tls: true,
  })

  const [showPassword, setShowPassword] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = () => {
    // 이메일 설정 로드
    const savedEmailSettings = localStorage.getItem('email_settings')
    if (savedEmailSettings) {
      try {
        setEmailSettings(JSON.parse(savedEmailSettings))
      } catch (error) {
        console.error('Failed to parse email settings:', error)
      }
    }

    // SMTP 설정 로드
    const savedSmtpSettings = localStorage.getItem('smtp_settings')
    if (savedSmtpSettings) {
      try {
        setSmtpSettings(JSON.parse(savedSmtpSettings))
      } catch (error) {
        console.error('Failed to parse SMTP settings:', error)
      }
    }
  }

  const handleSaveEmailSettings = () => {
    if (!emailSettings.default_email) {
      toast.error('이메일 주소를 입력해주세요.')
      return
    }

    // 이메일 형식 검증
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(emailSettings.default_email)) {
      toast.error('올바른 이메일 형식이 아닙니다.')
      return
    }

    localStorage.setItem('email_settings', JSON.stringify(emailSettings))
    toast.success('이메일 설정이 저장되었습니다.')
  }

  const handleSaveSMTPSettings = () => {
    if (!smtpSettings.smtp_host || !smtpSettings.smtp_user || !smtpSettings.smtp_password) {
      toast.error('모든 SMTP 설정을 입력해주세요.')
      return
    }

    localStorage.setItem('smtp_settings', JSON.stringify(smtpSettings))
    toast.success('SMTP 설정이 저장되었습니다.')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">설정</h1>
        <p className="text-muted-foreground">이메일 및 SMTP 설정을 관리합니다</p>
      </div>

      {/* 이메일 설정 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            이메일 설정
          </CardTitle>
          <CardDescription>
            메일 작성 시 자동으로 입력될 기본 발신 이메일 주소를 설정합니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="default_email">기본 발신 이메일</Label>
            <Input
              id="default_email"
              type="email"
              placeholder="your-email@company.com"
              value={emailSettings.default_email}
              onChange={(e) =>
                setEmailSettings({ ...emailSettings, default_email: e.target.value })
              }
            />
            <p className="text-sm text-muted-foreground">
              이 주소는 메일 작성 페이지의 '보내는 사람' 필드에 자동으로 입력됩니다.
            </p>
          </div>

          <Button onClick={handleSaveEmailSettings}>
            <Save className="mr-2 h-4 w-4" />
            이메일 설정 저장
          </Button>
        </CardContent>
      </Card>

      {/* SMTP 설정 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            SMTP 서버 설정
          </CardTitle>
          <CardDescription>
            이메일 전송을 위한 SMTP 서버 정보를 설정합니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="smtp_host">SMTP 서버 주소</Label>
              <Input
                id="smtp_host"
                placeholder="smtp.gmail.com"
                value={smtpSettings.smtp_host}
                onChange={(e) =>
                  setSmtpSettings({ ...smtpSettings, smtp_host: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="smtp_port">SMTP 포트</Label>
              <Input
                id="smtp_port"
                type="number"
                placeholder="587"
                value={smtpSettings.smtp_port}
                onChange={(e) =>
                  setSmtpSettings({ ...smtpSettings, smtp_port: parseInt(e.target.value) || 587 })
                }
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="smtp_user">SMTP 사용자명 (이메일)</Label>
            <Input
              id="smtp_user"
              type="email"
              placeholder="your-email@gmail.com"
              value={smtpSettings.smtp_user}
              onChange={(e) =>
                setSmtpSettings({ ...smtpSettings, smtp_user: e.target.value })
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="smtp_password">SMTP 비밀번호</Label>
            <div className="flex gap-2">
              <Input
                id="smtp_password"
                type={showPassword ? 'text' : 'password'}
                placeholder="앱 비밀번호"
                value={smtpSettings.smtp_password}
                onChange={(e) =>
                  setSmtpSettings({ ...smtpSettings, smtp_password: e.target.value })
                }
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? '숨기기' : '보기'}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Gmail을 사용하는 경우 앱 비밀번호를 생성하여 입력하세요.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="smtp_use_tls"
              checked={smtpSettings.smtp_use_tls}
              onChange={(e) =>
                setSmtpSettings({ ...smtpSettings, smtp_use_tls: e.target.checked })
              }
              className="h-4 w-4"
            />
            <Label htmlFor="smtp_use_tls" className="text-sm font-normal">
              TLS/STARTTLS 사용
            </Label>
          </div>

          <Button onClick={handleSaveSMTPSettings}>
            <Save className="mr-2 h-4 w-4" />
            SMTP 설정 저장
          </Button>

          {/* SMTP 설정 가이드 */}
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="pt-6 text-sm text-blue-900 space-y-2">
              <p className="font-semibold">📌 Gmail SMTP 설정 가이드</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>SMTP 서버: smtp.gmail.com</li>
                <li>포트: 587 (TLS)</li>
                <li>사용자명: Gmail 주소</li>
                <li>비밀번호: 앱 비밀번호 (2단계 인증 활성화 후 생성)</li>
              </ul>
              <p className="text-xs text-blue-700 mt-2">
                앱 비밀번호 생성: Google 계정 &gt; 보안 &gt; 2단계 인증 &gt; 앱 비밀번호
              </p>
            </CardContent>
          </Card>
        </CardContent>
      </Card>
    </div>
  )
}
