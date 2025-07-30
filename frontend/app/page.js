'use client'
import React, { useState, useEffect, useCallback, useRef } from "react"
import dynamic from "next/dynamic"
import { MapDataProvider } from "../src/context/MapDataContext.js"
import WorldMap from "../src/components/layout/Worldmap.js"
import IntegratedWorldMap from "../src/components/layout/IntegratedWorldMap.js"
import PolicySubmissionForm from "../src/components/policy/PolicySubmissionForm.js"
import AdminPanel from "../src/components/admin/AdminDashboard.js"
import AuthSystem from "../src/components/auth/AuthSystem.js"
import AdminLogin from "../src/components/admin/AdminLogin.js"
import PolicyChatAssistant from "../src/components/chatbot/PolicyChatAssistant.js"
import VisitCounter from "../src/components/common/VisitCounter.js"
import { useVisitTracker } from "../src/hooks/useVisitTracker.js"

const GlobeView = dynamic(() => import("../src/components/layout/GlobeView.js"), { ssr: false })

export default function Page() {
  const [view, setView] = useState("home")
  const [darkMode, setDarkMode] = useState(false)
  const [animate, setAnimate] = useState(false)
  const [user, setUser] = useState(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const [scrollY, setScrollY] = useState(0)

  // Visit tracking hook
  const { trackVisit, visitStats } = useVisitTracker()
  
  // Ref to track if visit has been recorded to prevent duplicates
  const visitTracked = useRef(false)

  // Initialize dark mode from localStorage or system preference
  useEffect(() => {
    const savedDarkMode = localStorage.getItem('darkMode')
    if (savedDarkMode !== null) {
      setDarkMode(JSON.parse(savedDarkMode))
    } else {
      setDarkMode(window.matchMedia('(prefers-color-scheme: dark)').matches)
    }
  }, [])

  // Mouse tracking for interactive backgrounds
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({ x: e.clientX, y: e.clientY })
    }
    const handleScroll = () => setScrollY(window.scrollY)
    
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('scroll', handleScroll)
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('scroll', handleScroll)
    }
  }, [])

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    // Save preference to localStorage
    localStorage.setItem('darkMode', JSON.stringify(darkMode))
  }, [darkMode])
  
  useEffect(() => {
    setAnimate(true)
    const timeoutId = setTimeout(() => setAnimate(false), 1200)
    return () => clearTimeout(timeoutId)
  }, [view])

  useEffect(() => {
    try {
      const userData = localStorage.getItem('userData')
      if (userData && userData !== 'undefined' && userData !== 'null') {
        const parsedUser = JSON.parse(userData)
        if (parsedUser && typeof parsedUser === 'object') {
          setUser(parsedUser)
        }
      }
    } catch (error) {
      console.error('Error parsing user data from localStorage:', error)
      localStorage.removeItem('userData')
      localStorage.removeItem('access_token')
    }
  }, [])

  // Track visit when component mounts and when user changes
  useEffect(() => {
    // Only track visit once per session to prevent duplicates
    if (!visitTracked.current) {
      trackVisit(user)
      visitTracked.current = true
    }
  }, [user, trackVisit])

  const navigateBack = useCallback(() => {
    setView("home")
    setMobileMenuOpen(false)
  }, [])
  
  const handleLogout = useCallback(() => {
    setUser(null)
    localStorage.removeItem('userData')
    localStorage.removeItem('access_token')
    setView('home')
  }, [])

  const navigationItems = [
    { 
      key: "worldmap", 
      label: "🌍 Explore Map", 
      icon: "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z M3 7l9 6 9-6",
      gradient: "from-cyan-400 via-blue-500 to-indigo-600",
      bgGradient: "from-cyan-50 via-blue-50 to-indigo-100",
      description: "Interactive world map visualization",
      emoji: "🌍",
      category: "explore"
    },
    { 
      key: "chatbot", 
      label: "🤖 Policy Bot", 
      icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
      gradient: "from-purple-400 via-pink-500 to-red-500",
      bgGradient: "from-purple-50 via-pink-50 to-red-100",
      description: "AI-powered policy research assistant",
      emoji: "🤖",
      category: "ai"
    },
    { 
      key: "submission", 
      label: "📝 Submit Policy", 
      icon: "M12 4v16m8-8H4",
      gradient: "from-emerald-400 via-teal-500 to-green-600",
      bgGradient: "from-emerald-50 via-teal-50 to-green-100",
      description: "Contribute to global policy database",
      emoji: "📝",
      category: "contribute"
    },
    { 
      key: "admin", 
      label: "⚙️ Dashboard", 
      icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
      gradient: "from-orange-400 via-red-500 to-pink-600",
      bgGradient: "from-orange-50 via-red-50 to-pink-100",
      description: "Administrative control panel",
      emoji: "⚙️",
      category: "admin"
    }
  ]

  const renderContent = () => {
    switch (view) {
      case "admin-login":
        return <AdminLogin setUser={setUser} setView={setView} />
      
      case "admin":
        if (!user) {
          return <AdminLogin setUser={setUser} setView={setView} />
        }
        if (!user.is_admin && !user.is_super_admin && user.role !== 'super_admin' && user.role !== 'admin') {
          return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 via-rose-50 to-pink-100 relative overflow-hidden">
              <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
              <div className="floating-shapes">
                <div className="shape shape-1"></div>
                <div className="shape shape-2"></div>
                <div className="shape shape-3"></div>
              </div>
              <div className="glass-card max-w-md mx-4 text-center transform hover:scale-105 transition-all duration-500">
                <div className="w-24 h-24 bg-gradient-to-br from-red-400 via-rose-500 to-pink-600 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-2xl">
                  <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.966-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-red-600 via-rose-600 to-pink-600 bg-clip-text text-transparent mb-4">
                  Access Restricted
                </h2>
                <p className="text-gray-600 mb-8 leading-relaxed">
                  Administrator privileges required to access this section.
                </p>
                <button 
                  onClick={() => setView("admin-login")} 
                  className="premium-button bg-gradient-to-r from-red-500 via-rose-500 to-pink-600 text-white"
                >
                  <span>Admin Login</span>
                  <div className="button-shine"></div>
                </button>
              </div>
            </div>
          )
        }
        return (
          <div className="min-h-screen bg-gradient-mesh from-slate-50 via-blue-50 to-indigo-100">
            <AdminPanel />
          </div>
        )
      
      case "worldmap":
        return (
          <div className="min-h-screen bg-gradient-mesh from-blue-50 via-cyan-50 to-indigo-100">
            <IntegratedWorldMap />
          </div>
        )
      
      case "login":
      case "signup":
      case "forgot":
        return (
          <div className="min-h-screen bg-gradient-mesh from-indigo-50 via-purple-50 to-pink-100">
            <AuthSystem 
              key={view} 
              setView={setView} 
              setUser={setUser} 
              initialView={view} 
            />
          </div>
        )
      
      case "submission":
        if (!user) {
          return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-mesh from-blue-50 via-indigo-50 to-purple-100 px-4 relative overflow-hidden">
              <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
              <div className="floating-shapes">
                <div className="shape shape-1"></div>
                <div className="shape shape-2"></div>
                <div className="shape shape-3"></div>
              </div>
              <div className="glass-card max-w-lg w-full text-center transform hover:scale-105 transition-all duration-500">
                <div className="w-28 h-28 bg-gradient-to-br from-blue-400 via-indigo-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-8 shadow-2xl">
                  <svg className="w-14 h-14 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent mb-6">
                  Authentication Required
                </h2>
                <p className="text-gray-600 mb-10 leading-relaxed text-lg">
                  Please sign in or create an account to submit policy information to our global database.
                </p>
                <div className="space-y-4">
                  <button
                    className="premium-button bg-gradient-to-r from-blue-500 via-indigo-600 to-purple-600 text-white w-full"
                    onClick={() => setView("login")}
                  >
                    <span>Sign In</span>
                    <div className="button-shine"></div>
                  </button>
                  <button
                    className="premium-button-outline w-full"
                    onClick={() => setView("signup")}
                  >
                    <span>Create Account</span>
                  </button>
                </div>
              </div>
            </div>
          )
        }
        return (
          <div className="min-h-screen bg-gradient-mesh from-emerald-50 via-teal-50 to-cyan-100">
            <PolicySubmissionForm />
          </div>
        )
      
      case "chatbot":
        return (
          <div className="min-h-screen bg-gradient-mesh from-purple-50 via-pink-50 to-rose-100 dark:from-purple-900 dark:via-pink-900 dark:to-rose-900">
            <PolicyChatAssistant />
          </div>
        )
      
      default:
        return (
          <div className={`min-h-screen ${animate ? 'animate-page-enter' : ''} relative overflow-hidden`}>
            {/* Dynamic Background */}
            <div className="fixed inset-0 bg-gradient-mesh from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900"></div>
            <div className="floating-orbs">
              <div className="orb orb-1" style={{
                transform: `translate(${mousePosition.x * 0.01}px, ${mousePosition.y * 0.01}px)`
              }}></div>
              <div className="orb orb-2" style={{
                transform: `translate(${mousePosition.x * 0.015}px, ${mousePosition.y * 0.015}px)`
              }}></div>
              <div className="orb orb-3" style={{
                transform: `translate(${mousePosition.x * 0.008}px, ${mousePosition.y * 0.008}px)`
              }}></div>
            </div>

            {/* Hero Section */}
            <section className="relative py-32 px-4 overflow-hidden" style={{
              transform: `translateY(${scrollY * 0.1}px)`
            }}>
              <div className="relative max-w-7xl mx-auto text-center">
                <h1 className="text-4xl md:text-8xl font-black mb-12 leading-tight">
                  <span className="hero-text bg-gradient-to-r from-white to-yellow-300 bg-clip-text text-transparent">
                    Global Policy Tracker
                  </span>
                </h1>
                
                <p className="text-2xl md:text-3xl text-gray-600 dark:text-gray-300 max-w-5xl mx-auto leading-relaxed mb-16 font-light">
                  <b>Discover, analyze, and understand global policy frameworks through our </b>
                  <span className="font-semibold bg-gradient-to-r from-yellow-300 to-yellow-600 bg-clip-text text-transparent"> AI-powered platform </span>
                  <b>with real-time visualization technology.</b>
                </p>

                {/* Enhanced CTA Buttons */}
                <div className="flex flex-col sm:flex-row gap-8 justify-center items-center mb-20">
                  <button
                    onClick={() => setView("worldmap")}
                    className="hero-button-primary group"
                  >
                    <span className="relative z-10 flex items-center gap-4">
                      <span className="text-2xl">🌍</span>
                      <span className="font-bold text-xl">Explore World Map</span>
                      <svg className="w-6 h-6 group-hover:translate-x-2 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                      </svg>
                    </span>
                    <div className="button-glow"></div>
                  </button>
                  
                  <button
                    onClick={() => setView("chatbot")}
                    className="hero-button-secondary group"
                  >
                    <span className="flex items-center gap-4">
                      <span className="text-2xl">🤖</span>
                      <span className="font-bold text-xl text-white">Policy Bot</span>
                    </span>
                  </button>
                </div>

                {/* Enhanced Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 max-w-6xl mx-auto">
                  {[
                    { 
                      number: visitStats.loading ? "..." : `${visitStats.total_visits.toLocaleString()}+`, 
                      label: "Website Visits", 
                      icon: "M15 12a3 3 0 11-6 0 3 3 0 016 0zM2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z", 
                      gradient: "from-blue-500 to-cyan-600",
                      dynamic: true 
                    },
                    { number: "195+", label: "Countries Analyzed", icon: "M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z", gradient: "from-emerald-500 to-teal-600" },
                    { number: "50K+", label: "Policy Documents", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z", gradient: "from-purple-500 to-pink-600" },
                    { number: "24/7", label: "Real-time Updates", icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z", gradient: "from-orange-500 to-red-600" }
                  ].map((stat, index) => (
                    <div key={index} className="stat-card group" style={{ animationDelay: `${index * 0.2}s` }}>
                      <div className={`w-16 h-16 bg-gradient-to-br ${stat.gradient} rounded-2xl flex items-center justify-center mb-6 mx-auto shadow-2xl group-hover:scale-110 transition-all duration-500`}>
                        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={stat.icon} />
                        </svg>
                      </div>
                      <div className="text-4xl font-black bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent mb-3">
                        {stat.number}
                      </div>
                      <div className="text-gray-600 dark:text-gray-400 font-semibold">{stat.label}</div>
                      {stat.dynamic && (
                        <div className="text-xs text-white-500 dark:text-gray-400 mt-2">
                          {visitStats.unique_visitors > 0 && `${visitStats.unique_visitors} unique visitors`}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Enhanced Features Section */}
            <section className="py-32 px-4 relative">
              <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/50 to-transparent dark:via-gray-900/50"></div>
              <div className="relative max-w-7xl mx-auto">
                <div className="text-center mb-20">
                  <h2 className="text-5xl md:text-7xl font-black bg-gradient-to-r from-gray-900 via-blue-600 to-purple-600 dark:from-white dark:via-blue-400 dark:to-purple-400 bg-clip-text text-transparent mb-8">
                    Revolutionary Features
                  </h2>
                  <p className="text-2xl text-gray-600 dark:text-gray-300 max-w-4xl mx-auto font-light">
                    Cutting-edge technology meets intuitive design for unparalleled policy analysis
                  </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                  {[
                    {
                      title: "AI-Powered Visualization",
                      description: "Experience policy data through stunning interactive 3D maps, real-time analytics, and machine learning insights that reveal hidden patterns in global governance.",
                      icon: "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z M3 7l9 6 9-6",
                      gradient: "from-blue-400 via-cyan-500 to-teal-600",
                      bgGradient: "from-blue-50 via-cyan-50 to-teal-100"
                    },
                    {
                      title: "Neural Policy Analysis",
                      description: "Advanced deep learning algorithms analyze policy effectiveness, predict outcomes, and provide actionable recommendations for governments worldwide.",
                      icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
                      gradient: "from-purple-400 via-pink-500 to-rose-600",
                      bgGradient: "from-purple-50 via-pink-50 to-rose-100"
                    },
                    {
                      title: "Global Intelligence Network",
                      description: "Connect with a vast network of policy experts, real-time government data feeds, and collaborative tools for comprehensive policy research.",
                      icon: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4",
                      gradient: "from-emerald-400 via-green-500 to-lime-600",
                      bgGradient: "from-emerald-50 via-green-50 to-lime-100"
                    }
                  ].map((feature, index) => (
                    <div key={index} className="feature-card group" style={{ animationDelay: `${index * 0.3}s` }}>
                      <div className="feature-card-inner">
                        <div className={`w-20 h-20 bg-gradient-to-br ${feature.gradient} rounded-3xl flex items-center justify-center mb-8 shadow-2xl group-hover:scale-110 group-hover:rotate-6 transition-all duration-700`}>
                          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={feature.icon} />
                          </svg>
                        </div>
                        <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">{feature.title}</h3>
                        <p className="text-gray-600 dark:text-gray-300 leading-relaxed text-lg">{feature.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Enhanced Navigation Cards */}
            <section className="py-32 px-4 relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-50/50 via-purple-50/50 to-pink-50/50 dark:from-blue-900/20 dark:via-purple-900/20 dark:to-pink-900/20"></div>
              <div className="relative max-w-7xl mx-auto">
                <div className="text-center mb-20">
                  <h2 className="text-5xl md:text-7xl font-black bg-gradient-to-r from-gray-900 via-indigo-600 to-purple-600 dark:from-white dark:via-indigo-400 dark:to-purple-400 bg-clip-text text-transparent mb-8">
                    Choose Your Journey
                  </h2>
                  <p className="text-2xl text-gray-600 dark:text-gray-300 max-w-4xl mx-auto font-light">
                    Multiple pathways to explore the world of global policy Tracker
                  </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 max-w-6xl mx-auto">
                  {navigationItems.map((item, index) => (
                    <div
                      key={item.key}
                      onClick={() => setView(item.key)}
                      className="navigation-card group"
                      style={{ animationDelay: `${index * 0.2}s` }}
                    >
                      <div className="navigation-card-inner">
                        <div className="flex items-start gap-6">
                          <div className={`w-24 h-24 bg-gradient-to-br ${item.gradient} rounded-3xl flex items-center justify-center shadow-2xl group-hover:scale-110 group-hover:rotate-12 transition-all duration-700 flex-shrink-0`}>
                            <span className="text-4xl">{item.emoji}</span>
                          </div>
                          <div className="flex-1">
                            <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">{item.label.replace(item.emoji + ' ', '')}</h3>
                            <p className="text-gray-600 dark:text-gray-300 leading-relaxed text-lg mb-6">{item.description}</p>
                            <div className="flex items-center gap-3">
                              <span className={`inline-flex items-center gap-2 text-lg font-bold bg-gradient-to-r ${item.gradient} bg-clip-text text-transparent group-hover:scale-105 transition-transform duration-300`}>
                                Launch Platform
                                <svg className="w-5 h-5 group-hover:translate-x-2 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                                </svg>
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>
        )
    }
  }
  
  return (
    <MapDataProvider>
      <div className={`min-h-screen transition-all duration-700 ${darkMode ? 'dark' : ''}`}>
        {/* Enhanced Sidebar */}
        <div className={`fixed inset-y-0 left-0 z-50 w-96 bg-white/80 dark:bg-gray-900/80 backdrop-blur-2xl border-r border-white/20 dark:border-gray-700/20 shadow-2xl transform transition-transform duration-500 ease-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} overflow-y-auto scrollbar-custom`}>
          <div className="flex flex-col min-h-full">
            {/* Enhanced Sidebar Header */}
            <div className="flex items-center justify-between p-8 border-b border-white/20 dark:border-gray-700/20">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 rounded-2xl flex items-center justify-center shadow-xl">
                  <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-xl font-black bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                    Policy Tracker
                  </h1>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Global Platform</p>
                </div>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-3 rounded-xl text-gray-500 dark:text-gray-400 hover:bg-gray-100/50 dark:hover:bg-gray-800/50 transition-all duration-300 hover:scale-110"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Enhanced Navigation Items */}
            <div className="flex-1 px-6 py-8 space-y-3">
              <div className="mb-8">
                <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4 px-2">Navigation</h3>
                {navigationItems.map((item) => (
                  <button
                    key={item.key}
                    onClick={() => {
                      setView(item.key)
                      setSidebarOpen(false)
                    }}
                    className={`sidebar-nav-item group ${
                      view === item.key
                        ? `active bg-gradient-to-r ${item.gradient} text-white shadow-xl`
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100/50 dark:hover:bg-gray-800/50'
                    }`}
                  >
                    <span className="text-2xl">{item.emoji}</span>
                    <div className="flex-1 text-left">
                      <span className="block font-bold text-lg">{item.label.replace(item.emoji + ' ', '')}</span>
                      <span className="text-sm opacity-75">{item.description}</span>
                    </div>
                    <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                ))}
              </div>

              {/* Enhanced User Section */}
              {user && (
                <div className="border-t border-white/20 dark:border-gray-700/20 pt-6">
                  <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4 px-2">Account</h3>
                  <div className="user-card p-4 bg-gradient-to-r from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl border border-blue-200/30 dark:border-blue-700/30">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-14 bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                        <span className="text-white text-lg font-bold">
                          {user.firstName?.[0]?.toUpperCase() || 'U'}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-lg font-bold text-gray-900 dark:text-white truncate">
                          {user.firstName} {user.lastName}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                          {user.email || 'User'}
                        </p>
                        {(user.is_admin || user.is_super_admin || user.role === 'admin' || user.role === 'super_admin') && (
                          <span className="inline-block px-2 py-1 bg-gradient-to-r from-orange-400 to-red-500 text-white text-xs font-bold rounded-lg mt-1">
                            ADMIN
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="logout-button w-full mt-4 flex items-center gap-3 px-4 py-3 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-all duration-300"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    <span className="font-semibold">Logout</span>
                  </button>
                </div>
              )}

              {/* Enhanced Auth Buttons */}
              {!user && (
                <div className="border-t border-white/20 dark:border-gray-700/20 pt-6 space-y-3">
                  <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4 px-2">Account</h3>
                  <button
                    onClick={() => {
                      setView("login")
                      setSidebarOpen(false)
                    }}
                    className="auth-button bg-gradient-to-r from-blue-500 to-indigo-600 text-white"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    <span className="font-bold">Sign In</span>
                  </button>
                  <button
                    onClick={() => {
                      setView("signup")
                      setSidebarOpen(false)
                    }}
                    className="auth-button bg-gradient-to-r from-emerald-500 to-teal-600 text-white"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                    </svg>
                    <span className="font-bold">Sign Up</span>
                  </button>
                </div>
              )}
            </div>

            {/* Enhanced Sidebar Footer */}
            <div className="p-6 border-t border-white/20 dark:border-gray-700/20">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="theme-toggle w-full flex items-center gap-4 px-4 py-3 text-gray-600 dark:text-gray-300 hover:bg-gray-100/50 dark:hover:bg-gray-800/50 rounded-xl transition-all duration-300"
              >
                <div className="w-10 h-10 bg-gradient-to-r from-yellow-400 to-orange-500 dark:from-blue-500 dark:to-indigo-600 rounded-xl flex items-center justify-center">
                  {darkMode ? (
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                  )}
                </div>
                <span className="font-semibold">{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Enhanced Overlay */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden transition-all duration-300" 
            onClick={() => setSidebarOpen(false)}
          ></div>
        )}

        {/* Enhanced Top Bar */}
        <div className="bg-white/70 dark:bg-gray-900/70 backdrop-blur-2xl border-b border-white/20 dark:border-gray-700/20 shadow-xl sticky top-0 z-30">
          <div className="flex items-center justify-between px-6 py-4">
            {/* Left - Enhanced Menu Button */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="menu-button p-3 rounded-2xl text-gray-600 dark:text-gray-300 hover:bg-gray-100/50 dark:hover:bg-gray-800/50 transition-all duration-300"
              >
                <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>

            {/* Center - Enhanced Logo */}
            <div className="flex-1 flex justify-center">
              <div 
                className="flex items-center gap-4 cursor-pointer group"
                onClick={() => setView("home")}
              >
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 rounded-2xl flex items-center justify-center shadow-xl group-hover:scale-110 group-hover:rotate-12 transition-all duration-500">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h1 className="text-3xl md:text-3xl font-black bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Global Policy Tracker Platform
                </h1>
              </div>
            </div>

            {/* Right - Enhanced User Info */}
            <div className="flex items-center gap-4">
              {user && (
                <div className="hidden md:flex items-center gap-3 bg-gradient-to-r from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl px-4 py-2 border border-blue-200/30 dark:border-blue-700/30">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                    <span className="text-white text-sm font-bold">
                      {user.firstName?.[0]?.toUpperCase() || 'U'}
                    </span>
                  </div>
                  <span className="text-sm font-bold text-gray-700 dark:text-gray-300">
                    {user.firstName}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <main className="relative">
          {renderContent()}
        </main>

        {/* Enhanced Footer */}
        <footer className="bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white relative overflow-hidden">
          {/* Animated Background */}
          <div className="absolute inset-0">
            <div className="absolute inset-0 bg-grid-pattern opacity-10"></div>
            <div className="floating-orbs">
              <div className="orb orb-footer-1"></div>
              <div className="orb orb-footer-2"></div>
              <div className="orb orb-footer-3"></div>
            </div>
          </div>

          <div className="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-20">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
              {/* Enhanced Company Info */}
              <div className="lg:col-span-2">
                <div className="flex items-center gap-5 mb-8">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-400 via-indigo-500 to-purple-600 rounded-3xl flex items-center justify-center shadow-2xl">
                    <svg className="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-3xl font-black bg-gradient-to-r from-white via-indigo-400 to-purple-400 bg-clip-text text-transparent">
                      Global Policy Tracker
                    </h3>
                    <p className="text-blue-200 text-lg">Empowering Global Understanding</p>
                  </div>
                </div>
                <p className="text-gray-300 leading-relaxed mb-8 max-w-lg text-lg">
                  The world's most advanced platform for exploring, analyzing, and understanding 
                  global policy frameworks through cutting-edge AI visualization and real-time intelligence.
                </p>
                <div className="flex space-x-4">
                  {[
                    { name: 'Twitter', color: 'from-blue-400 to-blue-600' },
                    { name: 'LinkedIn', color: 'from-blue-600 to-blue-800' },
                    { name: 'GitHub', color: 'from-gray-600 to-gray-800' },
                    { name: 'Discord', color: 'from-indigo-500 to-purple-600' }
                  ].map((social, index) => (
                    <a key={social.name} href="#" className={`w-12 h-12 bg-gradient-to-r ${social.color} hover:scale-110 rounded-2xl flex items-center justify-center transition-all duration-300 hover:shadow-2xl`}>
                      <span className="sr-only">{social.name}</span>
                      <div className="w-6 h-6 bg-white/90 rounded-lg"></div>
                    </a>
                  ))}
                </div>
              </div>

              {/* Enhanced Quick Links */}
              <div>
                <h4 className="text-xl font-black mb-8 text-blue-100">Quick Access</h4>
                <ul className="space-y-4">
                  {[
                    { label: 'World Map Explorer', action: () => setView('worldmap'), icon: '🌍' },
                    { label: 'AI Policy Assistant', action: () => setView('chatbot'), icon: '🤖' },
                    { label: 'Submit Policy Data', action: () => setView('submission'), icon: '📝' },
                    { label: 'Admin Dashboard', action: () => setView('admin'), icon: '⚙️' },
                    { label: 'API Documentation', action: () => {}, icon: '📚' }
                  ].map((link, index) => (
                    <li key={index}>
                      <button
                        onClick={link.action}
                        className="footer-link text-gray-300 hover:text-white transition-all duration-300 flex items-center gap-3 group"
                      >
                        <span className="text-lg">{link.icon}</span>
                        <span className="font-semibold">{link.label}</span>
                        <svg className="w-4 h-4 group-hover:translate-x-2 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Enhanced Contact */}
              <div>
                <h4 className="text-xl font-black mb-8 text-blue-100">Get In Touch</h4>
                <div className="space-y-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-2xl flex items-center justify-center shadow-lg">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-gray-300 font-semibold">bsse1320@iit.du.ac.bd</p>
                      <p className="text-gray-400 text-sm">Primary Contact</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center shadow-lg">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-gray-300 font-semibold">Dhaka, Bangladesh</p>
                      <p className="text-gray-400 text-sm">Global Headquarters</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Enhanced Bottom Bar */}
            <div className="border-t border-white/20 mt-16 pt-10 flex flex-col lg:flex-row justify-between items-center gap-6">
              <div className="text-gray-400 text-lg font-medium">
                © 2025 Global Policy Tracker Platform. All rights reserved.
              </div>
              
              {/* Visit Counter */}
              <div className="flex items-center gap-4 ">
                <VisitCounter showDetailed={false} />
              </div>
              
              <div className="flex items-center gap-8 text-sm">
                {['Privacy Policy', 'Terms of Service', 'API Documentation', 'Security'].map((item, index) => (
                  <a key={index} href="#" className="text-gray-400 hover:text-white transition-colors font-semibold hover:underline">
                    {item}
                  </a>
                ))}
              </div>
            </div>
          </div>
        </footer>
      </div>
    </MapDataProvider>
  )
}