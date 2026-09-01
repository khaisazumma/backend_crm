import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'sonner'

export const metadata: Metadata = { title: 'Venambak CRM', description: 'Kelola bisnis tambak dengan lebih mudah.' }
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="id" className="bg-background"><body>{children}<Toaster position="top-right" richColors /></body></html>
}
