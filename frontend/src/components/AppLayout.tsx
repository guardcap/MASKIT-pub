import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { LogOut, Menu } from 'lucide-react'

interface AppLayoutProps {
  children: React.ReactNode
  userName?: string
  userTeam?: string
  onLogout?: () => void
  sidebarMenu?: Array<{
    id: string
    label: string
    icon?: React.ReactNode
    onClick: () => void
  }>
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  userName = '사용자',
  userTeam = '팀',
  onLogout,
  sidebarMenu = [],
}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen flex-col">
      {/* 상단바 */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-16 items-center px-4">
          <div className="flex flex-1 items-center">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="mr-4 lg:hidden"
            >
              <Menu className="h-6 w-6" />
            </button>
            <div className="text-2xl font-bold text-primary">MASKIT</div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm font-medium">{userName}</div>
              <div className="text-xs text-muted-foreground">{userTeam}</div>
            </div>
            <Button variant="outline" size="sm" onClick={onLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              로그아웃
            </Button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* 사이드바 */}
        <aside
          className={`${
            isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
          } fixed inset-y-0 left-0 z-40 w-64 border-r bg-background pt-16 transition-transform duration-300 ease-in-out lg:static lg:translate-x-0`}
        >
          <div className="flex h-full flex-col">
            <div className="p-4">
              <h2 className="mb-4 text-lg font-semibold">메뉴</h2>
              <nav className="space-y-2">
                {sidebarMenu.map((item) => (
                  <button
                    key={item.id}
                    onClick={item.onClick}
                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
                  >
                    {item.icon}
                    {item.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>
        </aside>

        {/* 메인 컨텐츠 */}
        <main className="flex-1 overflow-y-auto bg-muted/40 p-6">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>

      {/* 사이드바 오버레이 (모바일) */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-background/80 backdrop-blur-sm lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
    </div>
  )
}
