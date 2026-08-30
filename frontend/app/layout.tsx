import type { Metadata, Viewport } from 'next'
import { Plus_Jakarta_Sans } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/theme/ThemeProvider'
import { AuthProvider } from '@/context/AuthContext'
import { ScrollReveal } from '@/components/common/ScrollReveal'

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
  weight: ['300', '400', '500', '600', '700', '800'],
})

export const metadata: Metadata = {
  title: 'MetaRadar — Decision Intelligence',
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
    <html lang="en" suppressHydrationWarning data-scroll-behavior="smooth" className={plusJakarta.variable}>
      <body className={`${plusJakarta.className} antialiased bg-background text-foreground min-h-screen font-sans tracking-tight`}>
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
