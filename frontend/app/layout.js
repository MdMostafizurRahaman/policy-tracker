import './globals.css'

export const metadata = {
  title: 'Global Policy Tracker',
  description: 'Discover, analyze, and understand global policy frameworks through our comprehensive interactive platform',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
