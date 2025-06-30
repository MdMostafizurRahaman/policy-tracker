'use client'
import PolicySubmissionForm from "../components/policy/PolicySubmissionForm"

export default function PolicySubmissionPage({ user, setView }) {
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
        <div className="bg-white/80 backdrop-blur-sm border border-white/20 rounded-3xl shadow-2xl px-8 py-12 max-w-lg w-full text-center">
          <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-8">
            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4">
            Authentication Required
          </h2>
          <p className="text-gray-600 mb-8 leading-relaxed">
            Please sign in or create an account to submit policy information to our global database.
          </p>
          <div className="space-y-4">
            <button
              className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white py-3 px-6 rounded-xl hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              onClick={() => setView("login")}
            >
              Sign In
            </button>
            <button
              className="w-full bg-white text-gray-700 py-3 px-6 rounded-xl border-2 border-gray-200 hover:border-indigo-300 hover:text-indigo-600 transition-all duration-300 font-semibold"
              onClick={() => setView("signup")}
            >
              Create Account
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100">
      <PolicySubmissionForm />
    </div>
  )
}
