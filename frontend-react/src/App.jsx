import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { apiFetch } from './api/client'
import LoginPage from './auth/LoginPage'
import Sidebar from './components/layout/Sidebar'
import Browse from './pages/Browse/Browse'
import Analytics from './pages/Analytics/Analytics'
import ReviewQueue from './pages/ReviewQueue/ReviewQueue'
import Statements from './pages/Statements/Statements'
import Rules from './pages/Rules/Rules'
import styles from './App.module.css'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

function AppShell() {
  const { token, isAuthed } = useAuth()

  const { data: pendingData } = useQuery({
    queryKey: ['pending-count', token],
    queryFn: () => apiFetch('GET', '/api/transactions/pending', { token, params: { limit: 1 } }),
    enabled: isAuthed,
    refetchInterval: 60_000,
  })

  const pendingCount = pendingData?.total ?? 0

  if (!isAuthed) return <LoginPage />

  return (
    <div className={styles.shell}>
      <Sidebar pendingCount={pendingCount} />
      <div className={styles.main}>
        <Routes>
          <Route path="/" element={<Navigate to="/browse" replace />} />
          <Route path="/browse" element={<Browse />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/review" element={<ReviewQueue />} />
          <Route path="/statements" element={<Statements />} />
          <Route path="/rules" element={<Rules />} />
        </Routes>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppShell />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
