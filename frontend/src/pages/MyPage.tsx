import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  Field,
  FieldGroup,
  FieldLabel,
  FieldDescription,
  FieldError,
  FieldSet,
  FieldLegend,
} from '@/components/ui/field'
import { toast } from 'sonner'
import {
  User,
  Mail,
  Phone,
  Building,
  Save,
  Server,
  Eye,
  EyeOff,
  CheckCircle,
  Upload,
  Lock,
  Camera
} from 'lucide-react'

interface MyPageProps {
  onBack?: () => void
}

interface UserProfile {
  email: string
  nickname: string
  phone_number?: string
  extension_number?: string
  team_name?: string
  profile_image?: string
}

interface SMTPSettings {
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_password: string
  smtp_use_tls: boolean
  smtp_use_ssl: boolean
}

interface PasswordChange {
  current_password: string
  new_password: string
  confirm_password: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function MyPage({ onBack }: MyPageProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [userProfile, setUserProfile] = useState<UserProfile>({
    email: '',
    nickname: '',
    phone_number: '',
    extension_number: '',
    team_name: '',
    profile_image: '',
  })

  const [smtpSettings, setSmtpSettings] = useState<SMTPSettings>({
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    smtp_use_tls: true,
    smtp_use_ssl: false,
  })

  const [passwordChange, setPasswordChange] = useState<PasswordChange>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })

  const [showPassword, setShowPassword] = useState({
    current: false,
    new: false,
    confirm: false,
    smtp: false,
  })

  const [isTesting, setIsTesting] = useState(false)
  const [profileImageFile, setProfileImageFile] = useState<File | null>(null)
  const [profileImagePreview, setProfileImagePreview] = useState<string>('')

  const getToken = () => localStorage.getItem('auth_token')

  useEffect(() => {
    loadUserProfile()
    loadSMTPSettings()
  }, [])

  const loadUserProfile = async () => {
    setIsLoading(true)
    const token = getToken()
    if (!token) {
      toast.error('인증 정보가 없습니다. 다시 로그인해주세요.')
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/users/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('프로필 정보를 불러오는데 실패했습니다.')
      }

      const data = await response.json()
      setUserProfile({
        email: data.email || '',
        nickname: data.nickname || '',
        phone_number: data.phone_number || '',
        extension_number: data.extension_number || '',
        team_name: data.team_name || '',
        profile_image: data.profile_image || '',
      })

      if (data.profile_image) {
        setProfileImagePreview(data.profile_image)
      }
    } catch (error) {
      console.error('프로필 로드 오류:', error)
      toast.error(error instanceof Error ? error.message : '프로필 로드 실패')
    } finally {
      setIsLoading(false)
    }
  }

  const loadSMTPSettings = async () => {
    const token = getToken()
    if (!token) return

    try {
      const response = await fetch(`${API_BASE_URL}/api/settings/all`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error('SMTP 설정을 불러오는데 실패했습니다.')
      }

      const data = await response.json()
      if (data.smtp_settings) {
        setSmtpSettings(data.smtp_settings)
      }
    } catch (error) {
      console.error('SMTP 설정 로드 오류:', error)
    }
  }

  const handleProfileImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('이미지 크기는 5MB 이하여야 합니다.')
        return
      }

      if (!file.type.startsWith('image/')) {
        toast.error('이미지 파일만 업로드 가능합니다.')
        return
      }

      setProfileImageFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setProfileImagePreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleSaveProfile = async () => {
    if (!userProfile.nickname) {
      toast.error('닉네임을 입력해주세요.')
      return
    }

    setIsLoading(true)
    const token = getToken()

    try {
      const formData = new FormData()
      formData.append('nickname', userProfile.nickname)
      if (userProfile.phone_number) formData.append('phone_number', userProfile.phone_number)
      if (userProfile.extension_number) formData.append('extension_number', userProfile.extension_number)
      if (profileImageFile) formData.append('profile_image', profileImageFile)

      const response = await fetch(`${API_BASE_URL}/api/users/me`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      })

      if (!response.ok) {
        throw new Error('프로필 저장에 실패했습니다.')
      }

      // localStorage의 user 정보도 업데이트
      const userData = JSON.parse(localStorage.getItem('user') || '{}')
      userData.nickname = userProfile.nickname
      localStorage.setItem('user', JSON.stringify(userData))

      toast.success('프로필이 저장되었습니다.')
      setProfileImageFile(null)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '저장 실패')
    } finally {
      setIsLoading(false)
    }
  }

  const handleChangePassword = async () => {
    if (!passwordChange.current_password || !passwordChange.new_password || !passwordChange.confirm_password) {
      toast.error('모든 비밀번호 필드를 입력해주세요.')
      return
    }

    if (passwordChange.new_password !== passwordChange.confirm_password) {
      toast.error('새 비밀번호가 일치하지 않습니다.')
      return
    }

    if (passwordChange.new_password.length < 8) {
      toast.error('새 비밀번호는 8자 이상이어야 합니다.')
      return
    }

    setIsLoading(true)
    const token = getToken()

    try {
      const response = await fetch(`${API_BASE_URL}/api/users/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: passwordChange.current_password,
          new_password: passwordChange.new_password,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || '비밀번호 변경에 실패했습니다.')
      }

      toast.success('비밀번호가 변경되었습니다.')
      setPasswordChange({
        current_password: '',
        new_password: '',
        confirm_password: '',
      })
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '비밀번호 변경 실패')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePortChange = (port: number) => {
    if (port === 465) {
      setSmtpSettings({
        ...smtpSettings,
        smtp_port: port,
        smtp_use_tls: false,
        smtp_use_ssl: true
      })
    } else if (port === 587 || port === 25) {
      setSmtpSettings({
        ...smtpSettings,
        smtp_port: port,
        smtp_use_tls: true,
        smtp_use_ssl: false
      })
    } else {
      setSmtpSettings({ ...smtpSettings, smtp_port: port })
    }
  }

  const handleSaveSMTPSettings = async () => {
    if (!smtpSettings.smtp_host || !smtpSettings.smtp_user || !smtpSettings.smtp_password) {
      toast.error('모든 SMTP 설정을 입력해주세요.')
      return
    }

    setIsLoading(true)
    const token = getToken()

    try {
      const response = await fetch(`${API_BASE_URL}/api/settings/smtp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(smtpSettings),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'SMTP 설정 저장에 실패했습니다.')
      }

      toast.success('SMTP 설정이 저장되었습니다.')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '저장 실패')
    } finally {
      setIsLoading(false)
    }
  }

  const handleTestSMTPConnection = async () => {
    if (!smtpSettings.smtp_host || !smtpSettings.smtp_user || !smtpSettings.smtp_password) {
      toast.error('모든 SMTP 설정을 입력해주세요.')
      return
    }

    setIsTesting(true)
    const token = getToken()

    try {
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

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">마이페이지</h1>
        <p className="text-muted-foreground">프로필 및 계정 설정을 관리합니다</p>
      </div>

      {/* 프로필 설정 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            프로필 설정
          </CardTitle>
          <CardDescription>
            프로필 사진, 닉네임 및 연락처 정보를 관리합니다
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 프로필 이미지 */}
          <Field>
            <div className="flex items-center gap-6">
              <Avatar className="h-24 w-24">
                <AvatarImage src={profileImagePreview} alt={userProfile.nickname} />
                <AvatarFallback className="text-2xl">
                  {getInitials(userProfile.nickname || userProfile.email)}
                </AvatarFallback>
              </Avatar>
              <div className="space-y-2">
                <FieldLabel htmlFor="profile-image" className="cursor-pointer">
                  <div className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-accent transition-colors">
                    <Camera className="h-4 w-4" />
                    <span className="text-sm">사진 변경</span>
                  </div>
                </FieldLabel>
                <Input
                  id="profile-image"
                  type="file"
                  accept="image/*"
                  onChange={handleProfileImageChange}
                  className="hidden"
                />
                <FieldDescription>
                  JPG, PNG 파일 (최대 5MB)
                </FieldDescription>
              </div>
            </div>
          </Field>

          <Separator />

          {/* 기본 정보 */}
          <FieldGroup className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field>
              <FieldLabel htmlFor="email">이메일</FieldLabel>
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  value={userProfile.email}
                  disabled
                  className="bg-muted"
                />
              </div>
              <FieldDescription>변경할 수 없습니다</FieldDescription>
            </Field>

            <Field>
              <FieldLabel htmlFor="nickname">닉네임 *</FieldLabel>
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="nickname"
                  placeholder="홍길동"
                  value={userProfile.nickname}
                  onChange={(e) =>
                    setUserProfile({ ...userProfile, nickname: e.target.value })
                  }
                  disabled={isLoading}
                />
              </div>
            </Field>

            <Field>
              <FieldLabel htmlFor="phone">전화번호</FieldLabel>
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="phone"
                  placeholder="010-1234-5678"
                  value={userProfile.phone_number}
                  onChange={(e) =>
                    setUserProfile({ ...userProfile, phone_number: e.target.value })
                  }
                  disabled={isLoading}
                />
              </div>
            </Field>

            <Field>
              <FieldLabel htmlFor="extension">사내 내선번호</FieldLabel>
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="extension"
                  placeholder="1234"
                  value={userProfile.extension_number}
                  onChange={(e) =>
                    setUserProfile({ ...userProfile, extension_number: e.target.value })
                  }
                  disabled={isLoading}
                />
              </div>
            </Field>

            <Field className="md:col-span-2">
              <FieldLabel htmlFor="team">소속 팀</FieldLabel>
              <div className="flex items-center gap-2">
                <Building className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="team"
                  value={userProfile.team_name}
                  disabled
                  className="bg-muted"
                />
              </div>
              <FieldDescription>변경할 수 없습니다</FieldDescription>
            </Field>
          </FieldGroup>

          <Button onClick={handleSaveProfile} disabled={isLoading}>
            <Save className="mr-2 h-4 w-4" />
            {isLoading ? '저장 중...' : '프로필 저장'}
          </Button>
        </CardContent>
      </Card>

      {/* 비밀번호 변경 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-5 w-5" />
            비밀번호 변경
          </CardTitle>
          <CardDescription>
            계정의 비밀번호를 변경합니다
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="current_password">현재 비밀번호</FieldLabel>
              <div className="flex gap-2">
                <Input
                  id="current_password"
                  type={showPassword.current ? 'text' : 'password'}
                  placeholder="현재 비밀번호를 입력하세요"
                  value={passwordChange.current_password}
                  onChange={(e) =>
                    setPasswordChange({ ...passwordChange, current_password: e.target.value })
                  }
                  disabled={isLoading}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setShowPassword({ ...showPassword, current: !showPassword.current })}
                  disabled={isLoading}
                >
                  {showPassword.current ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </Field>

            <Field>
              <FieldLabel htmlFor="new_password">새 비밀번호</FieldLabel>
              <div className="flex gap-2">
                <Input
                  id="new_password"
                  type={showPassword.new ? 'text' : 'password'}
                  placeholder="새 비밀번호를 입력하세요 (8자 이상)"
                  value={passwordChange.new_password}
                  onChange={(e) =>
                    setPasswordChange({ ...passwordChange, new_password: e.target.value })
                  }
                  disabled={isLoading}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setShowPassword({ ...showPassword, new: !showPassword.new })}
                  disabled={isLoading}
                >
                  {showPassword.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              <FieldDescription>비밀번호는 8자 이상이어야 합니다</FieldDescription>
            </Field>

            <Field>
              <FieldLabel htmlFor="confirm_password">새 비밀번호 확인</FieldLabel>
              <div className="flex gap-2">
                <Input
                  id="confirm_password"
                  type={showPassword.confirm ? 'text' : 'password'}
                  placeholder="새 비밀번호를 다시 입력하세요"
                  value={passwordChange.confirm_password}
                  onChange={(e) =>
                    setPasswordChange({ ...passwordChange, confirm_password: e.target.value })
                  }
                  disabled={isLoading}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setShowPassword({ ...showPassword, confirm: !showPassword.confirm })}
                  disabled={isLoading}
                >
                  {showPassword.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
            </Field>

            <Button onClick={handleChangePassword} disabled={isLoading}>
              <Lock className="mr-2 h-4 w-4" />
              {isLoading ? '변경 중...' : '비밀번호 변경'}
            </Button>
          </FieldGroup>
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
            이메일 전송을 위한 SMTP 서버 정보를 설정합니다
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FieldGroup>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field>
                <FieldLabel htmlFor="smtp_host">SMTP 서버 주소</FieldLabel>
                <Input
                  id="smtp_host"
                  placeholder="smtp.gmail.com"
                  value={smtpSettings.smtp_host}
                  onChange={(e) =>
                    setSmtpSettings({ ...smtpSettings, smtp_host: e.target.value })
                  }
                  disabled={isLoading}
                />
              </Field>

              <Field>
                <FieldLabel htmlFor="smtp_port">SMTP 포트</FieldLabel>
                <Input
                  id="smtp_port"
                  type="number"
                  placeholder="587"
                  value={smtpSettings.smtp_port}
                  onChange={(e) => handlePortChange(parseInt(e.target.value) || 587)}
                  disabled={isLoading}
                />
                <FieldDescription>
                  587: TLS/STARTTLS (권장) | 465: SSL | 25: Plain/TLS
                </FieldDescription>
              </Field>
            </div>

            <Field>
              <FieldLabel htmlFor="smtp_user">SMTP 사용자명 (이메일)</FieldLabel>
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
            </Field>

            <Field>
              <FieldLabel htmlFor="smtp_password">SMTP 비밀번호</FieldLabel>
              <div className="flex gap-2">
                <Input
                  id="smtp_password"
                  type={showPassword.smtp ? 'text' : 'password'}
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
                  onClick={() => setShowPassword({ ...showPassword, smtp: !showPassword.smtp })}
                  disabled={isLoading}
                >
                  {showPassword.smtp ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              <FieldDescription>
                Gmail을 사용하는 경우 앱 비밀번호를 생성하여 입력하세요.
              </FieldDescription>
            </Field>

            <Field>
              <div className="space-y-3 p-4 bg-muted/50 rounded-lg">
                <FieldLabel>암호화 프로토콜</FieldLabel>
                <FieldDescription>포트에 따라 자동 설정됩니다</FieldDescription>
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
                  <FieldLabel htmlFor="smtp_use_tls" className="text-sm font-normal">
                    TLS/STARTTLS 사용 (포트 587, 25)
                  </FieldLabel>
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
                  <FieldLabel htmlFor="smtp_use_ssl" className="text-sm font-normal">
                    SSL 사용 (포트 465)
                  </FieldLabel>
                </div>
              </div>
            </Field>

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
          </FieldGroup>
        </CardContent>
      </Card>
    </div>
  )
}
