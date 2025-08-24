'use client'
import React, { useState, useEffect, useCallback, useRef } from "react"
import { useRouter, usePathname } from "next/navigation"
import { MapDataProvider } from "../../context/MapDataContext.js"
import VisitCounter from "../common/VisitCounter.js"
import { useVisitTracker } from "../../hooks/useVisitTracker.js"

export default function AppLayout({ children }) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState(null)
  const [darkMode, setDarkMode] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const [scrollY, setScrollY] = useState(0)
  const [isClient, setIsClient] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)

  // Visit tracking hook
  const { trackVisit, trackNewRegistration, visitStats } = useVisitTracker()
  
  // Ref to track if visit has been recorded to prevent duplicates
  const visitTracked = useRef(false)

  // Initialize dark mode from localStorage or system preference
  useEffect(() => {
    setIsClient(true)
    
    const storedDarkMode = localStorage.getItem('darkMode')
    if (storedDarkMode !== null) {
      setDarkMode(JSON.parse(storedDarkMode))
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setDarkMode(prefersDark)
    }

    setTimeout(() => setIsLoaded(true), 100)
  }, [])

  // Mouse tracking for interactive backgrounds
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY })
    }

    const handleScroll = () => {
      setScrollY(window.scrollY)
    }

    if (isClient) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('scroll', handleScroll)
      
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('scroll', handleScroll)
      }
    }
  }, [isClient])

  useEffect(() => {
    if (isClient) {
      localStorage.setItem('darkMode', JSON.stringify(darkMode))
      if (darkMode) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    }
  }, [darkMode, isClient])

  // Listen for storage changes to sync user state
  useEffect(() => {
    const checkUserSession = () => {
      const storedUser = localStorage.getItem('userData')
      if (storedUser) {
        try {
          const userData = JSON.parse(storedUser)
          setUser(userData)
        } catch (error) {
          console.error('Error parsing stored user data:', error)
          localStorage.removeItem('userData')
          localStorage.removeItem('access_token')
        }
      } else {
        setUser(null)
      }
    }

    // Check on mount
    checkUserSession()

    // Listen for storage changes (cross-tab sync)
    const handleStorageChange = (e) => {
      if (e.key === 'userData' || e.key === 'access_token') {
        checkUserSession()
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  // Track visit when component mounts and when user changes
  useEffect(() => {
    if (isClient && !visitTracked.current) {
      console.log('🎯 Tracking visit for user:', user?.email || 'anonymous')
      trackVisit(user)
      visitTracked.current = true
    }
  }, [user, trackVisit, isClient])

  const handleLogout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('userData')
    setUser(null)
    router.push('/')
  }, [router])

  const navigationItems = [
    {
      key: "/",
      label: "🏠 Home",
      icon: "M3 12l9-9 9 9M4 10v10a2 2 0 002 2h4a2 2 0 002-2v-4h4v4a2 2 0 002 2h4a2 2 0 002-2V10",
      gradient: "from-gray-400 via-blue-300 to-indigo-400",
      bgGradient: "from-gray-50 via-blue-50 to-indigo-100",
      description: "Go to home page",
      emoji: "🏠",
      category: "home"
    },
    { 
      key: "/worldmap", 
      label: "🌍 Explore Map", 
      icon: "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z M3 7l9 6 9-6",
      gradient: "from-cyan-400 via-blue-500 to-indigo-600",
      bgGradient: "from-cyan-50 via-blue-50 to-indigo-100",
      description: "Interactive world map visualization",
      emoji: "🌍",
      category: "explore"
    },
    { 
      key: "/chatbot", 
      label: "🤖 Policy Bot", 
      icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
      gradient: "from-purple-400 via-pink-500 to-red-500",
      bgGradient: "from-purple-50 via-pink-50 to-red-100",
      description: "AI-powered policy research assistant",
      emoji: "🤖",
      category: "ai"
    },
    { 
      key: "/submission", 
      label: "📝 Submit Policy", 
      icon: "M12 4v16m8-8H4",
      gradient: "from-emerald-400 via-teal-500 to-green-600",
      bgGradient: "from-emerald-50 via-teal-50 to-green-100",
      description: "Contribute to global policy database",
      emoji: "📝",
      category: "contribute"
    },
    { 
      key: "/ranking", 
      label: "📊 Policy Rankings", 
      icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
      gradient: "from-yellow-400 via-orange-500 to-red-600",
      bgGradient: "from-yellow-50 via-orange-50 to-red-100",
      description: "Policy transparency & accountability rankings",
      emoji: "📊",
      category: "analytics"
    },
    { 
      key: "/admin", 
      label: "⚙️ Dashboard", 
      icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
      gradient: "from-orange-400 via-red-500 to-pink-600",
      bgGradient: "from-orange-50 via-red-50 to-pink-100",
      description: "Administrative control panel",
      emoji: "⚙️",
      category: "admin"
    }
  ]

  const currentNavItem = navigationItems.find(item => item.key === pathname)

  return (
    <MapDataProvider>
      <div className={`${darkMode ? 'dark' : ''} ${isLoaded ? 'opacity-100' : 'opacity-0'} transition-opacity duration-300`}>
        {/* Navigation Header - REMOVED */}
        {/* <header className="fixed top-0 left-0 right-0 z-50 bg-black/10 backdrop-blur-xl border-b border-white/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div 
                className="flex items-center cursor-pointer group"
                onClick={() => router.push('/')}
              >
                <div className="w-10 h-10 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-600 rounded-xl flex items-center justify-center mr-3 group-hover:scale-110 transition-transform duration-300">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="text-white font-bold text-lg">Policy Tracker</div>
              </div>

              <nav className="hidden md:flex items-center space-x-1">
                {navigationItems.map((item) => (
                  <button
                    key={item.key}
                    onClick={() => router.push(item.key)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                      pathname === item.key
                        ? 'bg-white/20 text-white shadow-lg'
                        : 'text-white/70 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    {item.emoji} {item.label.split(' ').slice(1).join(' ')}
                  </button>
                ))}
              </nav>

              <div className="flex items-center space-x-4">
                {user ? (
                  <div className="flex items-center space-x-4">
                    <div className="text-white/90 text-sm">
                      Welcome, {user.first_name || user.email}
                    </div>
                    <button
                      onClick={handleLogout}
                      className="px-4 py-2 bg-red-500/20 text-red-200 rounded-xl text-sm font-medium hover:bg-red-500/30 transition-all duration-300"
                    >
                      Logout
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => router.push('/login')}
                      className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium transition-all duration-300"
                    >
                      Login
                    </button>
                    <button
                      onClick={() => router.push('/signup')}
                      className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl text-sm font-medium hover:shadow-lg transition-all duration-300"
                    >
                      Sign Up
                    </button>
                  </div>
                )}

                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="md:hidden p-2 text-white/70 hover:text-white transition-colors duration-300"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          {mobileMenuOpen && (
            <div className="md:hidden bg-black/20 backdrop-blur-xl border-t border-white/10">
              <div className="px-4 py-4 space-y-2">
                {navigationItems.map((item) => (
                  <button
                    key={item.key}
                    onClick={() => {
                      router.push(item.key)
                      setMobileMenuOpen(false)
                    }}
                    className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-300 ${
                      pathname === item.key
                        ? 'bg-white/20 text-white'
                        : 'text-white/70 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </header> */}

        {/* Main Content */}
        <main>
          {React.cloneElement(children, { 
            user, 
            setUser, 
            visitStats,
            mousePosition,
            scrollY,
            isClient,
            isLoaded,
            darkMode,
            setDarkMode
          })}
        </main>

        {/* Visit Counter */}
        <VisitCounter />
      </div>
    </MapDataProvider>
  )
}
