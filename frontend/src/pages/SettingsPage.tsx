import { useState, useEffect } from 'react' // [수정] 사용되지 않는 'React' 제거
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { Mail, Save, Server, Eye, EyeOff, CheckCircle } from 'lucide-react' // 아이콘 추가

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
  smtp_use_ssl: boolean
}

// API URL (LoginPage.tsx 참고)
// [수정] 'process.env'는 브라우저 런타임 오류를 일으키므로 Vite의 표준 방식인 'import.meta.env'로 수정합니다.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function SettingsPage({ onBack }: SettingsPageProps) { // [수정] { onBack } -> { } (또는 onBack을 사용)
  const [isLoading, setIsLoading] = useState(false)

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
    smtp_use_ssl: false,
  })

  // 포트 변경 시 SSL/TLS 자동 설정
  const handlePortChange = (port: number) => {
    if (port === 465) {
      // SSL 포트
      setSmtpSettings({
        ...smtpSettings,
        smtp_port: port,
        smtp_use_tls: false,
        smtp_use_ssl: true
      })
    } else if (port === 587 || port === 25) {
      // TLS/STARTTLS 포트
      setSmtpSettings({
        ...smtpSettings,
        smtp_port: port,
        smtp_use_tls: true,
        smtp_use_ssl: false
      })
    } else {
      // 기타 포트는 사용자 설정 유지
      setSmtpSettings({ ...smtpSettings, smtp_port: port })
    }
  }

  const [showPassword, setShowPassword] = useState(false)
  const [isTesting, setIsTesting] = useState(false)

  // API 호출을 위한 토큰 가져오기
  const getToken = () => localStorage.getItem('auth_token')

  useEffect(() => {
    loadSettings()
  }, [])

  // 1. 설정 로드 (localStorage -> API 호출로 변경)
  const loadSettings = async () => {
    setIsLoading(true)
    const token = getToken()
    if (!token) {
      toast.error('인증 정보가 없습니다. 다시 로그인해주세요.')
      setIsLoading(false)
      return
    }

    try {
      // /api/settings 엔드포인트가 있다고 가정합니다.
      const response = await fetch(`${API_BASE_URL}/api/settings/all`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('설정 정보를 불러오는데 실패했습니다.')
      }

      const data = await response.json()

      // email_settings와 smtp_settings가 data 객체 안에 있다고 가정
      if (data.email_settings) {
        setEmailSettings(data.email_settings)
      }
      if (data.smtp_settings) {
        setSmtpSettings(data.smtp_settings)
      }

    } catch (error) {
      console.error('설정 로드 오류:', error)
      toast.error(error instanceof Error ? error.message : '설정 로드 실패')
      
      // API 로드 실패 시 localStorage에서라도 시도 (선택 사항)
      // const savedEmailSettings = localStorage.getItem('email_settings')
      // ... (기존 로직)
      
    } finally {
      setIsLoading(false)
    }
  }

  // 2. 이메일 설정 저장 (localStorage -> API 호출로 변경)
  const handleSaveEmailSettings = async () => {
    if (!emailSettings.default_email) {
      toast.error('이메일 주소를 입력해주세요.')
      return
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(emailSettings.default_email)) {
      toast.error('올바른 이메일 형식이 아닙니다.')
      return
    }

    setIsLoading(true)
    const token = getToken()

    try {
      // /api/settings/email 엔드포인트가 있다고 가정합니다.
      const response = await fetch(`${API_BASE_URL}/api/settings/email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(emailSettings),
      })

      if (!response.ok) {
        throw new Error('이메일 설정 저장에 실패했습니다.')
      }

      toast.success('이메일 설정이 서버에 저장되었습니다.')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '저장 실패')
    } finally {
      setIsLoading(false)
    }

    // localStorage.setItem('email_settings', JSON.stringify(emailSettings)) // 이 줄 제거
  }

  // 3. SMTP 설정 저장 (localStorage -> API 호출로 변경)
  const handleSaveSMTPSettings = async () => {
    if (!smtpSettings.smtp_host || !smtpSettings.smtp_user || !smtpSettings.smtp_password) {
      toast.error('모든 SMTP 설정을 입력해주세요.')
      return
    }

    setIsLoading(true)
    const token = getToken()

    try {
      // /api/settings/smtp 엔드포인트가 있다고 가정합니다.
      const response = await fetch(`${API_BASE_URL}/api/settings/smtp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        // .py 파일과 키 이름을 맞추는 것이 좋습니다 (예: smtp_use_tls)
        body: JSON.stringify(smtpSettings),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'SMTP 설정 저장에 실패했습니다.')
      }
      
      toast.success('SMTP 설정이 서버에 저장되었습니다.')
    } catch (error) {
       toast.error(error instanceof Error ? error.message : '저장 실패')
    } finally {
      setIsLoading(false)
    }
    
    // localStorage.setItem('smtp_settings', JSON.stringify(smtpSettings)) // 이 줄 제거
  }

  // 4. SMTP 연결 테스트
  const handleTestSMTPConnection = async () => {
    if (!smtpSettings.smtp_host || !smtpSettings.smtp_user || !smtpSettings.smtp_password) {
      toast.error('모든 SMTP 설정을 입력해주세요.')
      return
    }

    setIsTesting(true)
    const token = getToken()

    try {
      // 현재 입력된 설정으로 테스트 (저장하지 않음)
      const response = await fetch(`${API_BASE_URL}/api/settings/smtp/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(smtpSettings),
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || 'SMTP 연결 테스트 실패')
      }

      toast.success('SMTP 연결 테스트 성공!', {
        description: `${result.details.host}:${result.details.port}에 성공적으로 연결되었습니다.`,
      })
    } catch (error) {
      toast.error('SMTP 연결 테스트 실패', {
        description: error instanceof Error ? error.message : '알 수 없는 오류',
      })
    } finally {
      setIsTesting(false)
    }
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
            메일 작성 시 자동으로 입력될 기본 발신 이메일 주소를 설정합니다. (서버에 저장됨)
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
              disabled={isLoading}
            />
            <p className="text-sm text-muted-foreground">
              이 주소는 메일 작성 페이지의 '보내는 사람' 필드에 자동으로 입력됩니다.
            </p>
          </div>

          <Button onClick={handleSaveEmailSettings} disabled={isLoading}>
            <Save className="mr-2 h-4 w-4" />
            {isLoading ? '저장 중...' : '이메일 설정 저장'}
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
            이메일 전송을 위한 SMTP 서버 정보를 설정합니다. (서버에 저장됨)
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
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="smtp_port">SMTP 포트</Label>
              <Input
                id="smtp_port"
                type="number"
                placeholder="587"
                value={smtpSettings.smtp_port}
                onChange={(e) => handlePortChange(parseInt(e.target.value) || 587)}
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                587: TLS/STARTTLS (권장) | 465: SSL | 25: Plain/TLS
              </p>
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
              disabled={isLoading}
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
                disabled={isLoading}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => setShowPassword(!showPassword)}
                disabled={isLoading}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Gmail을 사용하는 경우 앱 비밀번호를 생성하여 입력하세요.
            </p>
          </div>

          <div className="space-y-3 p-4 bg-muted/50 rounded-lg">
            <p className="text-sm font-medium">암호화 프로토콜 (포트에 따라 자동 설정됨)</p>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="smtp_use_tls"
                checked={smtpSettings.smtp_use_tls}
                onChange={(e) =>
                  setSmtpSettings({ ...smtpSettings, smtp_use_tls: e.target.checked, smtp_use_ssl: false })
                }
                className="h-4 w-4"
                disabled={isLoading}
              />
              <Label htmlFor="smtp_use_tls" className="text-sm font-normal">
                TLS/STARTTLS 사용 (포트 587, 25)
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="smtp_use_ssl"
                checked={smtpSettings.smtp_use_ssl}
                onChange={(e) =>
                  setSmtpSettings({ ...smtpSettings, smtp_use_ssl: e.target.checked, smtp_use_tls: false })
                }
                className="h-4 w-4"
                disabled={isLoading}
              />
              <Label htmlFor="smtp_use_ssl" className="text-sm font-normal">
                SSL 사용 (포트 465)
              </Label>
            </div>
          </div>

          <div className="flex gap-2">
            <Button onClick={handleTestSMTPConnection} disabled={isTesting || isLoading} variant="outline">
              <CheckCircle className="mr-2 h-4 w-4" />
              {isTesting ? '테스트 중...' : '연결 테스트'}
            </Button>
            <Button onClick={handleSaveSMTPSettings} disabled={isLoading || isTesting}>
              <Save className="mr-2 h-4 w-4" />
              {isLoading ? '저장 중...' : 'SMTP 설정 저장'}
            </Button>
          </div>

          {/* SMTP 설정 가이드 */}
          <Card className="border-blue-200 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-700">
            <CardContent className="pt-6 text-sm text-blue-900 dark:text-blue-200 space-y-2">
              <p className="font-semibold">📌 Gmail SMTP 설정 가이드</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>SMTP 서버: smtp.gmail.com</li>
                <li>포트: 587 (TLS) 또는 465 (SSL)</li>
                <li>사용자명: Gmail 주소</li>
                <li>비밀번호: 앱 비밀번호 (2단계 인증 활성화 후 생성)</li>
              </ul>
              <p className="text-xs text-blue-700 dark:text-blue-400 mt-2">
                앱 비밀번호 생성: Google 계정 &gt; 보안 &gt; 2단계 인증 &gt; 앱 비밀번호
              </p>
            </CardContent>
          </Card>
        </CardContent>
      </Card>
    </div>
  )
}