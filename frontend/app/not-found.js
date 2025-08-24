'use client'
import Link from 'next/link'
import { useEffect } from 'react'

export default function NotFound() {
  // Redirect to home with current path as view parameter for SPA routing
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const currentPath = window.location.pathname.replace(/^\/|\/$/g, '')
      if (currentPath && currentPath !== '404') {
        // Redirect to home with view parameter for SPA routing
        window.location.href = `/?view=${currentPath}`
      }
    }
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
          <h2 className="text-2xl font-semibold text-gray-700 mb-2">Page Not Found</h2>
          <p className="text-gray-600">
            Redirecting to home page...
          </p>
        </div>
        
        <div className="space-y-4">
          <Link 
            href="/"
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors duration-200"
          >
            Go Home
          </Link>
          <br />
          <Link 
            href="/chatbot"
            className="inline-block text-blue-600 hover:text-blue-800 transition-colors duration-200"
          >
            Visit Chatbot
          </Link>
        </div>
      </div>
    </div>
  )
}