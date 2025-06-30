'use client'
import AdminPanel from "../components/admin/AdminDashboard"
import AdminLogin from "../components/admin/AdminLogin"

export default function AdminPage({ user, setUser, setView }) {
  if (!user) {
    return <AdminLogin setUser={setUser} setView={setView} />
  }
  
  if (!user.is_admin && !user.is_super_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-red-100">
        <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md mx-4 text-center border border-red-100">
          <div className="w-20 h-20 bg-gradient-to-br from-red-500 to-red-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.966-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Access Restricted</h2>
          <p className="text-gray-600 mb-6">Administrator privileges required to access this section.</p>
          <button 
            onClick={() => setView("admin-login")} 
            className="w-full bg-gradient-to-r from-red-500 to-red-600 text-white py-3 px-6 rounded-xl hover:from-red-600 hover:to-red-700 transition-all duration-300 font-semibold"
          >
            Admin Login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <AdminPanel />
    </div>
  )
}
