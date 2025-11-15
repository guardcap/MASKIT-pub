import React, { useState } from 'react'
import { AppLayout } from '@/components/AppLayout'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { Home, Settings, FileText, Shield, Users } from 'lucide-react'

type Page = 'login' | 'register' | 'main'

interface User {
  userId: string
  userName: string
  userEmail: string
  userTeam: string
  userRole: string
}

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('login')
  const [user, setUser] = useState<User | null>(null)
  const [currentView, setCurrentView] = useState('main')

  const handleLogin = (userData: any) => {
    setUser(userData)
    setCurrentPage('main')
  }

  const handleRegister = (userData: any) => {
    console.log('회원가입 데이터:', userData)
    // 여기서 실제 회원가입 API 호출
    alert('회원가입이 완료되었습니다!')
    setCurrentPage('login')
  }

  const handleLogout = () => {
    setUser(null)
    setCurrentPage('login')
    setCurrentView('main')
  }

  const sidebarMenu = [
    {
      id: 'main',
      label: '메인',
      icon: <Home className="h-4 w-4" />,
      onClick: () => setCurrentView('main'),
    },
    {
      id: 'policy',
      label: '정책 관리',
      icon: <Shield className="h-4 w-4" />,
      onClick: () => setCurrentView('policy'),
    },
    {
      id: 'users',
      label: '사용자 관리',
      icon: <Users className="h-4 w-4" />,
      onClick: () => setCurrentView('users'),
    },
    {
      id: 'logs',
      label: '로그 조회',
      icon: <FileText className="h-4 w-4" />,
      onClick: () => setCurrentView('logs'),
    },
    {
      id: 'settings',
      label: '설정',
      icon: <Settings className="h-4 w-4" />,
      onClick: () => setCurrentView('settings'),
    },
  ]

  // 로그인 페이지
  if (currentPage === 'login') {
    return (
      <LoginPage
        onLogin={handleLogin}
        onShowRegister={() => setCurrentPage('register')}
      />
    )
  }

  // 회원가입 페이지
  if (currentPage === 'register') {
    return (
      <RegisterPage
        onRegister={handleRegister}
        onShowLogin={() => setCurrentPage('login')}
      />
    )
  }

  // 메인 애플리케이션
  return (
    <AppLayout
      userName={user?.userName}
      userTeam={user?.userTeam}
      onLogout={handleLogout}
      sidebarMenu={sidebarMenu}
    >
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {currentView === 'main' && '메인'}
            {currentView === 'policy' && '정책 관리'}
            {currentView === 'users' && '사용자 관리'}
            {currentView === 'logs' && '로그 조회'}
            {currentView === 'settings' && '설정'}
          </h1>
          <p className="text-muted-foreground">
            {currentView === 'main' && '대시보드 개요'}
            {currentView === 'policy' && '이메일 마스킹 정책을 관리합니다'}
            {currentView === 'users' && '사용자 정보를 관리합니다'}
            {currentView === 'logs' && '시스템 로그를 조회합니다'}
            {currentView === 'settings' && '시스템 설정을 관리합니다'}
          </p>
        </div>

        {/* 여기에 각 페이지별 컨텐츠가 들어갑니다 */}
        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <p className="text-muted-foreground">
            이 영역에 실제 페이지 컨텐츠가 표시됩니다.
          </p>
        </div>
      </div>
    </AppLayout>
  )
}

export default App
