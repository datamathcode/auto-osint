import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'auto-osint - Agentic OSINT Research',
  description: 'Autonomous OSINT research agent with data journalism rigor',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
