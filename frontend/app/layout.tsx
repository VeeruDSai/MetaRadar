import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/theme/ThemeProvider'
import { AuthProvider } from '@/context/AuthContext'
import { ScrollReveal } from '@/components/common/ScrollReveal'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
  weight: ['300', '400', '500', '600', '700', '800', '900'],
})

export const metadata: Metadata = {
  title: 'MetaRadar — Decision intelligence',
  description: 'A real-time decision intelligence workspace for the haemophilia landscape.',
  icons: {
    icon: '/icon.svg',
    shortcut: '/icon.svg',
    apple: '/icon.svg',
  },
}

export const viewport: Viewport = {
  colorScheme: 'light dark',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#eef2f6' },
    { media: '(prefers-color-scheme: dark)', color: '#0b1220' },
  ],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning data-scroll-behavior="smooth" className={inter.variable}>
      <body className={`${inter.className} antialiased bg-background text-foreground min-h-screen font-sans`}>
        <ThemeProvider>
          <AuthProvider>
            <ScrollReveal />
            {children}
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
