'use client'
import AuthSystem from "../components/auth/AuthSystem"

export default function AuthPage({ setView, setUser, initialView }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100">
      <AuthSystem 
        setView={setView} 
        setUser={setUser} 
        initialView={initialView} 
      />
    </div>
  )
}
