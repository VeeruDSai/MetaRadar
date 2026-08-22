'use client'

import React, { createContext, useContext, useEffect, useState, useMemo } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  isDark: boolean
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('dark')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    try {
      const saved = localStorage.getItem('metaradar_theme') || localStorage.getItem('theme')
      if (saved === 'light' || saved === 'dark') {
        setThemeState(saved)
        document.documentElement.classList.toggle('dark', saved === 'dark')
      } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        const initial = prefersDark ? 'dark' : 'light'
        setThemeState(initial)
        document.documentElement.classList.toggle('dark', initial === 'dark')
      }
    } catch {
      // Fallback to dark if localStorage inaccessible
      document.documentElement.classList.add('dark')
    }
    setMounted(true)
  }, [])

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    try {
      localStorage.setItem('metaradar_theme', newTheme)
      localStorage.setItem('theme', newTheme)
      document.documentElement.classList.toggle('dark', newTheme === 'dark')
    } catch (e) {
      console.warn('Could not persist theme to localStorage:', e)
    }
  }

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  const value = useMemo(
    () => ({
      theme,
      isDark: theme === 'dark',
      setTheme,
      toggleTheme,
    }),
    [theme]
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    // Graceful fallback if called outside provider
    return {
      theme: 'dark' as Theme,
      isDark: true,
      setTheme: () => {},
      toggleTheme: () => {},
    }
  }
  return context
}
