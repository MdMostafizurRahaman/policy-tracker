import './globals.css'
import AppLayout from '../src/components/layout/AppLayout.js'

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="antialiased">
        <AppLayout>
          {children}
        </AppLayout>
      </body>
    </html>
  )
}
