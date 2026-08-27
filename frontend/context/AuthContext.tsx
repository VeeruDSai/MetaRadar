'use client'

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
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
  const [user, setUser] = useState<UserMe | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const refreshUser = useCallback(async () => {
    try {
      setError(null)
      const currentUser = await getMe()
      setUser(currentUser)
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
      if (typeof window !== 'undefined') {
        localStorage.setItem(DEMO_ROLE_KEY, targetRole)
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to authenticate demo persona')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true)
    setError(null)
    try {
      const u = await apiLogin(credentials)
      setUser(u)
      if (typeof window !== 'undefined') {
        localStorage.setItem(DEMO_ROLE_KEY, u.role)
      }
    } catch (err: any) {
      setError(err?.message || 'Login failed')
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    setIsLoading(true)
    try {
      await apiLogout()
    } catch {
      // Ignore logout errors
    } finally {
      setUser(null)
      setIsLoading(false)
    }
  }, [])

  // Auto-bootstrap on initial mount
  useEffect(() => {
    let mounted = true

    async function initAuth() {
      try {
        const u = await getMe()
        if (mounted) {
          setUser(u)
          if (typeof window !== 'undefined') {
            localStorage.setItem(DEMO_ROLE_KEY, u.role)
          }
        }
      } catch {
        // Fallback: auto-bootstrap demo login if demo role stored
        const savedRole = (typeof window !== 'undefined' && localStorage.getItem(DEMO_ROLE_KEY)) || DEFAULT_ROLE
        try {
          const demoUser = await apiDemoLogin(savedRole)
          if (mounted) {
            setUser(demoUser)
          }
        } catch {
          if (mounted) {
            setUser(null)
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
  }, [])

  const role = user?.role || (typeof window !== 'undefined' ? localStorage.getItem(DEMO_ROLE_KEY) : null) || DEFAULT_ROLE

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
