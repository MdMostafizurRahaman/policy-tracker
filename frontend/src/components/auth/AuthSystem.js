import React, { useState, useEffect } from 'react';
import { countries } from '../../utils/constants';
import { authService } from '../../services/api';
import LoadingSpinner from '../ui/LoadingSpinner';

const AuthSystem = ({ setView, setUser, initialView = 'login' }) => {
  const [currentView, setCurrentView] = useState(initialView);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    country: '',
    otp: '',
    newPassword: ''
  });
  const [filteredCountries, setFilteredCountries] = useState([]);
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [user, setUserState] = useState(null);
  const [otpTimer, setOtpTimer] = useState(0);
  const [canResendOtp, setCanResendOtp] = useState(true);

  // Country autocomplete
  useEffect(() => {
    if (formData.country) {
      const filtered = countries.filter(country =>
        country.toLowerCase().includes(formData.country.toLowerCase())
      );
      setFilteredCountries(filtered);
    } else {
      setFilteredCountries([]);
    }
  }, [formData.country]);

  // Check if user is logged in
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('userData');
    if (token && userData) {
      try {
        setUserState(JSON.parse(userData));
      } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('userData');
      }
    }
  }, []);

  // OTP Timer effect
  useEffect(() => {
    let interval = null;
    if (otpTimer > 0) {
      interval = setInterval(() => {
        setOtpTimer(timer => timer - 1);
      }, 1000);
    } else if (otpTimer === 0) {
      setCanResendOtp(true);
    }
    return () => clearInterval(interval);
  }, [otpTimer]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
  };

  const handleCountrySelect = (country) => {
    setFormData(prev => ({ ...prev, country }));
    setShowCountryDropdown(false);
  };

  const validateEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const validatePassword = (password) => {
    return password.length >= 8;
  };

  const handleSignup = async () => {
    if (!formData.firstName || !formData.lastName || !formData.email || !formData.password || !formData.country) {
      setError('Please fill in all required fields');
      return;
    }

    if (!validateEmail(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    if (!validatePassword(formData.password)) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!countries.includes(formData.country)) {
      setError('Please select a valid country from the list');
      return;
    }

    setLoading(true);
    try {
      const response = await authService.register({
        firstName: formData.firstName,
        lastName: formData.lastName,
        email: formData.email,
        password: formData.password,
        confirmPassword: formData.confirmPassword,
        country: formData.country
      });
      
      if (response.email_sent) {
        setSuccess('Account created successfully! 🎉 Please check your email for verification code.');
      } else {
        setSuccess(`Account created! 🎉 Email failed to send. Your verification code is: ${response.otp_for_dev || 'Check server logs'}`);
      }
      
      setCurrentView('otp');
      setOtpTimer(120);
      setCanResendOtp(false);
      
    } catch (err) {
      setError(err.message || 'Failed to create account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!formData.email || !formData.password) {
      setError('Please enter both email and password');
      return;
    }

    setLoading(true);
    try {
      const response = await authService.login({
        email: formData.email,
        password: formData.password
      });

      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('userData', JSON.stringify(response.user));
      setUser(response.user);
      setSuccess('Login successful! 🎉 Welcome back!');
      if (setView) {
        setTimeout(() => setView("home"), 1500);
      }
    } catch (err) {
      if (err.message.includes('verify')) {
        setError('Please verify your email first. Check your inbox for verification code.');
        setCurrentView('otp');
      } else {
        setError('Invalid credentials. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!formData.otp || formData.otp.length !== 6) {
      setError('Please enter a valid 6-digit verification code');
      return;
    }

    setLoading(true);
    try {
      await authService.verifyEmail({
        email: formData.email,
        otp: formData.otp
      });
      
      setSuccess('Email verified successfully! 🎉 You can now log in.');
      setCurrentView('login');
      setOtpTimer(0);
    } catch (err) {
      setError(err.message || 'Invalid verification code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('userData');
    setUserState(null);
    setFormData({
      email: '',
      password: '',
      confirmPassword: '',
      firstName: '',
      lastName: '',
      country: '',
      otp: '',
      newPassword: ''
    });
    setSuccess('Logged out successfully! 👋');
  };

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // If user is logged in, show profile
  if (user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-md border border-blue-100 transform hover:scale-105 transition-all duration-300">
          <div className="text-center mb-6">
            <div className="w-24 h-24 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg animate-pulse">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
              Welcome Back! 🎉
            </h2>
            <p className="text-gray-700 text-lg font-semibold">{user.firstName} {user.lastName}</p>
            <p className="text-sm text-gray-500 mb-3">{user.email}</p>
          </div>
          
          <div className="space-y-4">
            <button
              onClick={() => setView && setView("submission")}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-4 rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center gap-2"
            >
              Submit AI Policies
            </button>
            
            <button
              onClick={() => setView && setView("worldmap")}
              className="w-full bg-gradient-to-r from-green-500 to-teal-600 text-white font-semibold py-4 rounded-xl hover:from-green-600 hover:to-teal-700 transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center gap-2"
            >
              Explore World Map
            </button>
            
            {user.is_admin && (
              <button
                onClick={() => setView && setView("admin")}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white font-semibold py-4 rounded-xl hover:from-purple-600 hover:to-pink-700 transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center gap-2"
              >
                Admin Dashboard
              </button>
            )}
            
            <button
              onClick={handleLogout}
              className="w-full bg-gradient-to-r from-gray-400 to-gray-500 text-white font-semibold py-4 rounded-xl hover:from-gray-500 hover:to-gray-600 transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center gap-2"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl overflow-hidden w-full max-w-md border border-blue-100 transform hover:scale-105 transition-all duration-300">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 p-8 text-white text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-white/10 backdrop-blur-sm"></div>
          <div className="relative z-10">
            <h1 className="text-2xl font-bold mb-2">AI Policy Tracker</h1>
            <p className="text-blue-100">
              {currentView === 'login' && '🔐 Welcome back!'}
              {currentView === 'signup' && '🚀 Join our community'}
              {currentView === 'forgot' && '🔄 Reset your password'}
              {currentView === 'otp' && '📧 Verify your email'}
              {currentView === 'reset' && '🔑 Set new password'}
            </p>
          </div>
        </div>

        <div className="p-8">
          {/* Messages */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-400 text-red-700 rounded-lg shadow-sm">
              <span className="font-medium">{error}</span>
            </div>
          )}
          {success && (
            <div className="mb-6 p-4 bg-green-50 border-l-4 border-green-400 text-green-700 rounded-lg shadow-sm">
              <span className="font-medium">{success}</span>
            </div>
          )}

          {/* Login Form */}
          {currentView === 'login' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  placeholder="Enter your email"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  placeholder="Enter your password"
                />
              </div>

              <button
                onClick={handleLogin}
                disabled={loading}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-4 rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 shadow-lg"
              >
                {loading ? <LoadingSpinner /> : '🔐 Sign In'}
              </button>

              <div className="text-center">
                <span className="text-gray-600">Don't have an account? </span>
                <button
                  onClick={() => setCurrentView('signup')}
                  className="text-blue-600 hover:text-blue-800 font-semibold transition-colors"
                >
                  Sign up 🎯
                </button>
              </div>
            </div>
          )}

          {/* Signup Form */}
          {currentView === 'signup' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">First Name</label>
                  <input
                    type="text"
                    value={formData.firstName}
                    onChange={(e) => handleInputChange('firstName', e.target.value)}
                    className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                    placeholder="First name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Last Name</label>
                  <input
                    type="text"
                    value={formData.lastName}
                    onChange={(e) => handleInputChange('lastName', e.target.value)}
                    className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                    placeholder="Last name"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  placeholder="Enter your email"
                />
              </div>
              
              <div className="relative">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Country</label>
                <input
                  type="text"
                  value={formData.country}
                  onChange={(e) => {
                    handleInputChange('country', e.target.value);
                    setShowCountryDropdown(true);
                  }}
                  onFocus={() => setShowCountryDropdown(true)}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  placeholder="🌍 Type to search countries..."
                />
                {showCountryDropdown && filteredCountries.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-xl shadow-xl max-h-60 overflow-y-auto">
                    {filteredCountries.slice(0, 10).map((country) => (
                      <button
                        key={country}
                        onClick={() => handleCountrySelect(country)}
                        className="text-black w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors border-b border-gray-100 last:border-0 font-medium"
                      >
                        {country}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  placeholder="Create a strong password"
                />
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Confirm Password</label>
                <input
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  placeholder="Confirm your password"
                />
              </div>
              
              <button
                onClick={handleSignup}
                disabled={loading}
                className="w-full bg-gradient-to-r from-green-500 to-teal-600 text-white font-semibold py-4 rounded-xl hover:from-green-600 hover:to-teal-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 shadow-lg"
              >
                {loading ? <LoadingSpinner /> : '🚀 Create Account'}
              </button>

              <div className="text-center">
                <span className="text-gray-600">Already have an account? </span>
                <button
                  onClick={() => setCurrentView('login')}
                  className="text-blue-600 hover:text-blue-800 font-semibold transition-colors"
                >
                  Sign in 🔐
                </button>
              </div>
            </div>
          )}

          {/* OTP Verification Form */}
          {currentView === 'otp' && (
            <div className="space-y-6">
              <div className="text-center text-gray-600 mb-6">
                <p className="font-semibold">We've sent a 6-digit code to</p>
                <p className="text-blue-600 font-bold">{formData.email}</p>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Verification Code</label>
                <input
                  type="text"
                  value={formData.otp}
                  onChange={(e) => handleInputChange('otp', e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="w-full px-4 py-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-center text-2xl tracking-widest font-mono bg-gray-50 hover:bg-white"
                  placeholder="000000"
                  maxLength={6}
                />
              </div>
              
              {otpTimer > 0 && (
                <div className="text-center text-sm text-gray-500">
                  Code expires in: <span className="font-mono font-bold text-red-600">{formatTimer(otpTimer)}</span>
                </div>
              )}
              
              <button
                onClick={handleVerifyOTP}
                disabled={loading}
                className="w-full bg-gradient-to-r from-green-500 to-teal-600 text-white font-semibold py-4 rounded-xl hover:from-green-600 hover:to-teal-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 shadow-lg"
              >
                {loading ? <LoadingSpinner /> : '✅ Verify Email'}
              </button>
              
              <div className="text-center">
                <button
                  onClick={() => setCurrentView('login')}
                  className="text-gray-600 hover:text-gray-800 font-medium transition-colors"
                >
                  ← Back to login
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthSystem;
