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
      <body>
        {children}
        <footer className="mt-10 border-t p-6 text-xs text-gray-500">
          <strong>Responsible use:</strong> this tool automates open-source
          intelligence collection. Use it only for lawful, authorised
          investigations, respect platform terms of service, and never to
          profile private individuals or minors. Findings are machine-generated
          leads, not verified facts.
        </footer>
      </body>
    </html>
  )
}
