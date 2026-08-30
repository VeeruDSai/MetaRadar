'use client'

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import type { UserMe, LoginRequest } from '@/types/api'
import { getMe, demoLogin as apiDemoLogin, login as apiLogin, logout as apiLogout } from '@/lib/api'

interface AuthContextType {
  user: UserMe | null
  role: string
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (credentials: LoginRequest) => Promise<void>
  demoLogin: (role: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const DEMO_ROLE_KEY = 'metaradar_demo_role'
const DEFAULT_ROLE = 'MEDICAL_AFFAIRS'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<UserMe | null>(null)
  const [storedRole, setStoredRole] = useState<string | null>(null)
  const [isMounted, setIsMounted] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const refreshUser = useCallback(async () => {
    try {
      setError(null)
      const currentUser = await getMe()
      setUser(currentUser)
      setStoredRole(currentUser.role)
      if (typeof window !== 'undefined') {
        localStorage.setItem(DEMO_ROLE_KEY, currentUser.role)
      }
    } catch {
      setUser(null)
    }
  }, [])

  const demoLogin = useCallback(async (targetRole: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const u = await apiDemoLogin(targetRole)
      setUser(u)
      setStoredRole(targetRole)
      if (typeof window !== 'undefined') {
        localStorage.setItem(DEMO_ROLE_KEY, targetRole)
      }
      if (pathname === '/login') {
        router.push('/dashboard')
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to authenticate demo persona')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [pathname, router])

  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true)
    setError(null)
    try {
      const u = await apiLogin(credentials)
      setUser(u)
      setStoredRole(u.role)
      if (typeof window !== 'undefined') {
        localStorage.setItem(DEMO_ROLE_KEY, u.role)
      }
      router.push('/dashboard')
    } catch (err: any) {
      setError(err?.message || 'Login failed')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [router])

  const logout = useCallback(async () => {
    setIsLoading(true)
    try {
      await apiLogout()
    } catch {
      // Ignore logout errors
    } finally {
      setUser(null)
      setStoredRole(null)
      try {
        localStorage.removeItem(DEMO_ROLE_KEY)
      } catch {}
      setIsLoading(false)
      router.push('/login')
    }
  }, [router])

  // Auto-bootstrap on initial mount
  useEffect(() => {
    let mounted = true
    setIsMounted(true)

    // Load persisted demo role safely after initial hydration
    try {
      const saved = localStorage.getItem(DEMO_ROLE_KEY)
      if (saved) {
        setStoredRole(saved)
      }
    } catch {}

    async function initAuth() {
      try {
        const u = await getMe()
        if (mounted) {
          setUser(u)
          setStoredRole(u.role)
          if (typeof window !== 'undefined') {
            localStorage.setItem(DEMO_ROLE_KEY, u.role)
          }
          if (pathname === '/login') {
            router.push('/dashboard')
          }
        }
      } catch {
        if (mounted) {
          setUser(null)
          if (pathname && pathname !== '/login' && !pathname.startsWith('/api')) {
            router.push('/login')
          }
        }
      } finally {
        if (mounted) {
          setIsLoading(false)
        }
      }
    }

    initAuth()
    return () => {
      mounted = false
    }
  }, [pathname, router])

  // Guaranteed identical on SSR and initial client hydration
  const role = user?.role || (isMounted ? storedRole : null) || DEFAULT_ROLE

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        demoLogin,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
