'use client'
import { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import WorldMap from "./components/Worldmap.js"
import PolicySubmissionForm from "./Submission/PolicySubmissionForm.js"
import AdminPanel from "./admin/AdminDashboard.js"
import AuthSystem from "./AuthSystem.js"

const GlobeView = dynamic(() => import("./components/GlobeView.js"), { ssr: false })

export default function Page() {
  const [view, setView] = useState("home")
  const [darkMode, setDarkMode] = useState(false)
  const [animate, setAnimate] = useState(false)
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])
  
  useEffect(() => {
    setAnimate(true)
    const timeoutId = setTimeout(() => setAnimate(false), 600)
    return () => clearTimeout(timeoutId)
  }, [view])

  useEffect(() => {
    const userData = localStorage.getItem('userData');
    if (userData) setUser(JSON.parse(userData));
  }, []);

  const navigateBack = () => {
    setView("home")
  }
  
  const renderContent = () => {
    switch (view) {
      case "worldmap":
        return (
          <div className="w-full h-full bg-white dark:bg-slate-900 rounded-2xl shadow-xl overflow-auto">
            <WorldMap />
          </div>
        );
      case "login":
      case "signup":
      case "forgot":
        return (
          <AuthSystem setView={setView} setUser={setUser} initialView={view} />
        );
      case "submission":
        if (!user) {
          return (
            <div className="flex flex-col items-center justify-center min-h-[40vh]">
              <div className="bg-white/90 border border-blue-200 rounded-2xl shadow-lg px-8 py-10 max-w-md text-center">
                <svg className="mx-auto mb-4 w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <h2 className="text-2xl font-bold text-blue-700 mb-2">Sign in Required</h2>
                <p className="text-gray-600 mb-6">
                  Please <button
                    className="text-blue-600 hover:underline font-semibold"
                    onClick={() => setView("login")}
                  >login</button> or <button
                    className="text-purple-600 hover:underline font-semibold"
                    onClick={() => setView("signup")}
                  >sign up</button> to submit a policy.
                </p>
              </div>
            </div>
          );
        }
        return (
          <div className="w-full h-full bg-white dark:bg-slate-900 rounded-2xl p-4 shadow-xl overflow-auto">
            <PolicySubmissionForm />
          </div>
        );
      case "admin":
        // Only allow admin users
        if (!user || !user.is_admin) {
          return (
            <div className="text-center text-red-600 font-bold p-8">
              Admin access required.
            </div>
          );
        }
        return (
          <div className="w-full h-full bg-white dark:bg-slate-900 rounded-2xl p-4 shadow-xl overflow-auto">
            <AdminPanel />
          </div>
        );
      default:
        return (
          <div className={`w-full h-full max-w-7xl mx-auto ${animate ? 'animate-fade-in' : ''}`}>
            {/* Hero Section */}
            <div className="text-center mb-2">
              <h1 className="text-5xl md:text-7xl font-black mb-6 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent leading-tight">
                Global Policy Tracker
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
                Transform how you understand global policies with cutting-edge data visualization and intelligent analytics
              </p>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-4">
              <div className="group relative overflow-hidden bg-white dark:bg-white-500 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all transform hover:-translate-y-2 border border-slate-200 dark:border-white-700">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 group-hover:from-blue-500/10 group-hover:to-purple-500/10 transition-all"></div>
                <div className="relative">
                  <div className="inline-flex items-center justify-center w-16 h-16 mb-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl shadow-lg">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-bold text-slate-800 dark:text-black mb-4">Interactive World Maps</h3>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                    Explore global policy data through stunning interactive maps with real-time updates and detailed regional insights.
                  </p>
                </div>
              </div>

              <div className="group relative overflow-hidden bg-white dark:bg-white-500 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all transform hover:-translate-y-2 border border-slate-200 dark:border-white-700">
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-teal-500/5 group-hover:from-emerald-500/10 group-hover:to-teal-500/10 transition-all"></div>
                <div className="relative">
                  <div className="inline-flex items-center justify-center w-16 h-16 mb-6 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl shadow-lg">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-bold text-slate-800 dark:text-black mb-4">3D Globe Experience</h3>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                    Immerse yourself in a 3D globe visualization that brings policy data to life with smooth animations and interactions.
                  </p>
                </div>
              </div>

              <div className="group relative overflow-hidden bg-white dark:bg-shite-500 rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-all transform hover:-translate-y-2 border border-slate-200 dark:border-white-700">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-pink-500/5 group-hover:from-purple-500/10 group-hover:to-pink-500/10 transition-all"></div>
                <div className="relative">
                  <div className="inline-flex items-center justify-center w-16 h-16 mb-6 bg-gradient-to-r from-purple-500 to-pink-600 rounded-2xl shadow-lg">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-bold text-slate-800 dark:text-black mb-4">Smart Policy Database</h3>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                    Access comprehensive policy information with AI-powered search, categorization, and trend analysis capabilities.
                  </p>
                </div>
              </div>
            </div>

            {/* Enhanced CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-2 justify-center items-center">
              <button
                onClick={() => setView("worldmap")}
                className="group inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg hover:shadow-xl"
              >
                <svg className="w-5 h-5 group-hover:rotate-12 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
                Explore World Map
              </button>
              
              <button
                onClick={() => setView("submission")}
                className="group inline-flex items-center gap-3 px-8 py-4 bg-white dark:bg-slate-800 border-2 border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-semibold rounded-xl hover:border-blue-500 hover:text-blue-600 dark:hover:text-blue-400 transition-all transform hover:scale-105"
              >
                <svg className="w-5 h-5 group-hover:rotate-12 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Submit Policy
              </button>
              
              <button
                onClick={() => setView("admin")}
                className="group inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all transform hover:scale-105 shadow-lg hover:shadow-xl"
              >
                <svg className="w-5 h-5 group-hover:rotate-12 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Admin Panel
              </button>
            </div>
          </div>
        );
    }
  };
  
  return (
    <div className={`h-screen flex flex-col transition-all duration-500 ${darkMode ? 'dark bg-slate-900' : 'bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50'}`}>
      {/* Navigation */}
      <nav className="flex-shrink-0 sticky top-0 z-50 backdrop-blur-md bg-white/80 dark:bg-slate-900/80 border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div 
              className="flex items-center gap-3 cursor-pointer group"
              onClick={() => setView("home")}
            >
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-xl group-hover:scale-105 transition-all">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="text-xl font-bold text-slate-800 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                Global Policy Tracker
              </span>
            </div>

            <div className="flex items-center gap-2">
             ={[

                { key: "worldmap", label: "Map", icon: "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" },
                { key: "submission", label: "Submit", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
                { key: "admin", label: "Admin", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" }
              ].map((item) => (
                <button
                  key={item.key}
                  onClick={() => setView(item.key)}
                  className={`group px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                    view === item.key
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
                  </svg>
                  <span className="hidden sm:inline">{item.label}</span>
                </button>
              ))}
              
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-800 dark:hover:text-white transition-all"
                title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {darkMode ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {view !== "home" && (
          <button 
            onClick={navigateBack}
            className="group inline-flex items-center gap-2 mb-8 px-4 py-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-all hover:-translate-x-1"
          >
            <svg className="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Home
          </button>
        )}
        
        {renderContent()}
      </main>

      {/* Enhanced Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-1.5">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="font-semibold text-slate-800 dark:text-white">Global Policy Tracker</span>
            </div>
            
            <div className="flex gap-6 text-sm text-slate-600 dark:text-slate-400">
              {['About', 'Contact', 'API', 'Privacy'].map((item) => (
                <a 
                  key={item}
                  href="#" 
                  className="hover:text-slate-800 dark:hover:text-white transition-colors hover:underline"
                >
                  {item}
                </a>
              ))}
            </div>
          </div>
          
          <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700 text-center text-sm text-slate-500 dark:text-slate-400">
            © 2025 Global Policy Tracker. All rights reserved.
          </div>
        </div>
      </footer>

      <style jsx>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        .animate-fade-in {
          animation: fade-in 0.6s ease-out;
        }
      `}</style>
    </div>
  )
}