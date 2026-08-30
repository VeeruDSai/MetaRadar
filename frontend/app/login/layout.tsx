import React from 'react'

export const metadata = {
  title: 'Sign In — MetaRadar Haemophilia Intelligence',
  description: 'Enterprise Haemophilia Decision Intelligence Radar — Novo Nordisk GBS Hackathon 2026',
}

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen bg-[#0b1220] text-slate-100">{children}</div>
}
