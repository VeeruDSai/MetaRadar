import type { Metadata, Viewport } from 'next'
import './globals.css'
import { ThemeProvider } from '@/components/theme/ThemeProvider'

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
    <html lang="en" suppressHydrationWarning data-scroll-behavior="smooth">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var saved = localStorage.getItem('metaradar_theme') || localStorage.getItem('theme');
                  var isDark = saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
                  if (isDark) {
                    document.documentElement.classList.add('dark');
                  } else {
                    document.documentElement.classList.remove('dark');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="antialiased bg-background text-foreground min-h-screen">
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
