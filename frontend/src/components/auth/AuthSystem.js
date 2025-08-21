import React, { useState, useEffect } from 'react';
import { countries } from '../../utils/constants';
import { apiService } from '../../services/api';

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
  const [googleLoading, setGoogleLoading] = useState(false);
  const [otpTimer, setOtpTimer] = useState(0);
  const [canResendOtp, setCanResendOtp] = useState(true);

  // Load Google Sign-In script with better error handling
  useEffect(() => {
    // TEMPORARILY DISABLED - Google OAuth configuration issue
    return;
    
    // Use the correct Client ID from your Google Console
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID
    
    const loadGoogleScript = () => {
      if (window.google) {
        initializeGoogleSignIn();
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = initializeGoogleSignIn;
      script.onerror = () => {
        console.warn('Google Sign-In script failed to load');
      };
      document.head.appendChild(script);
    };

    const initializeGoogleSignIn = () => {
      try {
        if (window.google && window.google.accounts) {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: handleGoogleResponse,
            auto_select: false,
            cancel_on_tap_outside: true,
          });
          
          console.log('Google Sign-In initialized successfully');
        }
      } catch (error) {
        console.warn('Google Sign-In initialization failed:', error);
      }
    };

    loadGoogleScript();
  }, []);

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
        const parsedUser = JSON.parse(userData);
        setUserState(parsedUser);
        // Also update parent component state if setUser is provided
        if (setUser) {
          setUser(parsedUser);
        }
      } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('userData');
      }
    }
  }, [setUser]);

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

  // Clear OTP when switching views to prevent auto-fill issues
  useEffect(() => {
    if (currentView === 'reset') {
      setFormData(prev => ({ ...prev, otp: '', newPassword: '', confirmPassword: '' }));
      // Also clear any browser storage that might interfere
      sessionStorage.removeItem('otp');
      sessionStorage.removeItem('resetCode');
      localStorage.removeItem('otp');
      localStorage.removeItem('resetCode');
    } else if (currentView === 'otp') {
      setFormData(prev => ({ ...prev, otp: '' }));
      // Clear any browser storage that might interfere
      sessionStorage.removeItem('otp');
      sessionStorage.removeItem('verificationCode');
      localStorage.removeItem('otp');
      localStorage.removeItem('verificationCode');
    }
  }, [currentView]);

  // Helper function to reset form data
  const resetFormData = () => {
    setFormData({
      email: formData.email, // Keep email for continuity
      password: '',
      confirmPassword: '',
      firstName: '',
      lastName: '',
      country: '',
      otp: '',
      newPassword: ''
    });
    setError('');
    setSuccess('');
  };

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

  // Enhanced Google Sign-In Handler with fallback (DISABLED)
  const handleGoogleResponse = async (response) => {
    setError('Google Sign-In is temporarily disabled. Please use email/password login.');
    return;
    
    setGoogleLoading(true);
    setError('');
    try {
      const data = await apiService.auth.googleAuth(response.credential);

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('userData', JSON.stringify(data.user));
      setUser(data.user);
      setSuccess('Google sign-in successful! 🎉');
      if (setView) {
        setTimeout(() => setView('home'), 1500);
      }
    } catch (err) {
      setError('Google sign-in unavailable. Please use email/password login.');
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    // TEMPORARILY DISABLED
    setError('🚫 Google Sign-In is temporarily disabled due to configuration issues. Please use email/password login below.');
    return;
    
    setError('');
    
    // Use the same Client ID
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID
    
    try {
      if (window.google && window.google.accounts) {
        setGoogleLoading(true);
        window.google.accounts.id.prompt((notification) => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            // If prompt doesn't show, try the direct button approach
            setError('Please try the Google button below or use email/password login.');
            setGoogleLoading(false);
          }
        });
      } else {
        setError('Google Sign-In is loading. Please try again in a moment.');
      }
    } catch (error) {
      console.error('Google Sign-In error:', error);
      setError('Google Sign-In temporarily unavailable. Please use email/password login.');
      setGoogleLoading(false);
    }
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
      const data = await apiService.auth.register({
        firstName: formData.firstName,
        lastName: formData.lastName,
        email: formData.email,
        password: formData.password,
        confirmPassword: formData.confirmPassword,
        country: formData.country
      });

      // Show different messages based on email status
      if (data.email_sent) {
        setSuccess('Account created successfully! 🎉 Please check your email for verification code.');
      } else if (data.otp_for_dev) {
        setSuccess(`Account created! 🎉 Email failed to send. Your verification code is: ${data.otp_for_dev}`);
      } else {
        setSuccess('Account created! 🎉 Email failed to send. Your verification code is unavailable. Please contact support.');
      }

      setCurrentView('otp');
      setOtpTimer(120); // 2 minutes
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
      const data = await apiService.auth.login({ 
        email: formData.email, 
        password: formData.password 
      });

      // Store auth data
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('userData', JSON.stringify(data.user));
      
      // Update local state
      setUserState(data.user);
      
      // Update parent component state
      if (setUser) {
        setUser(data.user);
      }
      
      setSuccess('Login successful! 🎉 Welcome back!');
      
      // Navigate to home after showing success message
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

  const handleForgotPassword = async () => {
    if (!formData.email) {
      setError('Please enter your email address');
      return;
    }

    if (!validateEmail(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    try {
      const data = await apiService.auth.forgotPassword({ email: formData.email });
      
      // Show success message with OTP if email failed
      if (data.email_sent) {
        setSuccess('Password reset code sent to your email! 📧');
      } else if (data.otp_for_dev) {
        setSuccess(`Password reset code sent! 📧 Your code is: ${data.otp_for_dev}`);
      } else {
        setSuccess('Password reset code sent to your email! 📧');
      }
      
      resetFormData(); // Clear form data to prevent auto-fill
      setCurrentView('reset');
      setOtpTimer(600); // 10 minutes for password reset
      setCanResendOtp(false);
    } catch (err) {
      setError(err.message || 'Failed to send reset code. Please try again.');
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
      const data = await apiService.auth.verifyEmail({
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

  const handleResendOtp = async () => {
    if (!canResendOtp) return;
    
    setLoading(true);
    try {
      let data;
      if (currentView === 'reset') {
        data = await apiService.auth.forgotPassword({ email: formData.email });
      } else {
        data = await apiService.auth.resendOtp({ email: formData.email });
      }
      
      // Show success message with OTP if email failed
      if (data.email_sent) {
        setSuccess('New verification code sent! 📧');
      } else if (data.otp_for_dev) {
        setSuccess(`New verification code sent! 📧 Your code is: ${data.otp_for_dev}`);
      } else {
        setSuccess('New verification code sent! 📧');
      }
      
      setOtpTimer(120);
      setCanResendOtp(false);
    } catch (err) {
      setError('Failed to resend code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!formData.otp || !formData.newPassword || !formData.confirmPassword) {
      setError('Please fill in all fields');
      return;
    }

    if (!validatePassword(formData.newPassword)) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (formData.newPassword !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const data = await apiService.auth.resetPassword({
        email: formData.email,
        otp: formData.otp,
        newPassword: formData.newPassword,
        confirmPassword: formData.confirmPassword
      });
      
      setSuccess('Password reset successfully! 🎉 You can now log in.');
      setCurrentView('login');
      setOtpTimer(0);
    } catch (err) {
      setError(err.message || 'Failed to reset password. Please try again.');
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
            <div className="flex justify-center gap-2 flex-wrap">
              {user.google_auth && (
                <span className="inline-block px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold">
                  🔗 Google Account
                </span>
              )}
              {user.is_admin && (
                <span className="inline-block px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-semibold">
                  👑 Admin
                </span>
              )}
              <span className="inline-block px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                ✅ Verified
              </span>
            </div>
          </div>
          
          <div className="space-y-4">
            <button
              onClick={() => setView && setView("submission")}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-4 rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Submit AI Policies
            </button>
            
            <button
              onClick={() => setView && setView("worldmap")}
              className="w-full bg-gradient-to-r from-green-500 to-teal-600 text-white font-semibold py-4 rounded-xl hover:from-green-600 hover:to-teal-700 transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Explore World Map
            </button>
            
            {user.is_admin && (
              <button
                onClick={() => setView && setView("admin")}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white font-semibold py-4 rounded-xl hover:from-purple-600 hover:to-pink-700 transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Admin Dashboard
              </button>
            )}
            
            <button
              onClick={handleLogout}
              className="w-full bg-gradient-to-r from-gray-400 to-gray-500 text-white font-semibold py-4 rounded-xl hover:from-gray-500 hover:to-gray-600 transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
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
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
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
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span className="font-medium">{error}</span>
              </div>
            </div>
          )}
          {success && (
            <div className="mb-6 p-4 bg-green-50 border-l-4 border-green-400 text-green-700 rounded-lg shadow-sm">
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="font-medium">{success}</span>
              </div>
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
              
              <div className="flex justify-end">
                <button
                  onClick={() => setCurrentView('forgot')}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
                >
                  Forgot password? 🤔
                </button>
              </div>

              <button
                onClick={handleLogin}
                disabled={loading}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-4 rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 shadow-lg"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Signing in...
                  </div>
                ) : (
                  '🔐 Sign In'
                )}
              </button>

              {/* Google Sign-In Section - TEMPORARILY DISABLED */}
              {false && (
                <>
                  <div className="relative my-8">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-4 bg-white text-gray-500 font-medium">or continue with</span>
                    </div>
                  </div>

                  {/* Google Sign-In Button */}
                  <button
                    onClick={handleGoogleSignIn}
                    disabled={true}
                    className="w-full bg-gray-200 border-2 border-gray-300 text-gray-500 font-semibold py-4 rounded-xl cursor-not-allowed flex items-center justify-center gap-3 opacity-50"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="#9CA3AF" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#9CA3AF" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#9CA3AF" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path fill="#9CA3AF" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Google Sign-In (Temporarily Disabled)
                  </button>
                </>
              )}



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
                        className="text-black not-last-of-type:w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors border-b border-gray-100 last:border-0 font-medium"
                      >
                        🏃‍♂️ {country}
                      </button>
                    ))}
                  </div>
                )}
                {formData.country && !countries.includes(formData.country) && filteredCountries.length === 0 && (
                  <p className="text-sm text-red-600 mt-2 flex items-center">
                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Country not found. Please select from the list.
                  </p>
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
                <p className="text-xs text-gray-500 mt-2 flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  Must be at least 8 characters long
                </p>
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
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Creating account...
                  </div>
                ) : (
                  '🚀 Create Account'
                )}
              </button>

              {/* Google Sign-Up Section - DISABLED */}
              {false && (
                <>
                  <div className="relative my-8">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-4 bg-white text-gray-500 font-medium">or sign up with</span>
                    </div>
                  </div>

                  {/* Google Sign-Up Button */}
                  <button
                    onClick={handleGoogleSignIn}
                    disabled={true}
                    className="w-full bg-gray-200 border-2 border-gray-300 text-gray-500 font-semibold py-4 rounded-xl cursor-not-allowed flex items-center justify-center gap-3 opacity-50"
                  >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="#9CA3AF" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    </svg>
                    Google Sign-Up (Temporarily Disabled)
                  </button>
                </>
              )}



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

          {/* Forgot Password Form */}
          {currentView === 'forgot' && (
            <div className="space-y-6">
              <div className="text-center mb-6">
                <p className="text-gray-600">Enter your email address and we'll send you a reset code.</p>
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
              <button
                onClick={handleForgotPassword}
                disabled={loading}
                className="w-full bg-gradient-to-r from-orange-500 to-red-600 text-white font-semibold py-4 rounded-xl hover:from-orange-600 hover:to-red-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 shadow-lg"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Sending...
                  </div>
                ) : (
                  '📧 Send Reset Code'
                )}
              </button>
              <div className="text-center">
                <button
                  onClick={() => setCurrentView('login')}
                  className="text-blue-600 hover:text-blue-800 font-semibold transition-colors"
                >
                  ← Back to login
                </button>
              </div>
            </div>
          )}

          {/* OTP Verification Form */}
          {currentView === 'otp' && (
            <div className="space-y-6">
              <div className="text-center text-gray-600 mb-6">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="font-semibold">We've sent a 6-digit code to</p>
                <p className="text-blue-600 font-bold">{formData.email}</p>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Verification Code</label>
                <input
                  type="text"
                  name="email-verification-otp"
                  value={formData.otp}
                  onChange={(e) => handleInputChange('otp', e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="w-full px-4 py-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-center text-2xl tracking-widest font-mono bg-gray-50 hover:bg-white"
                  placeholder="000000"
                  maxLength={6}
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck="false"
                  data-form-type="other"
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
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Verifying...
                  </div>
                ) : (
                  '✅ Verify Email'
                )}
              </button>
              
              <div className="text-center space-y-2">
                <button 
                  onClick={handleResendOtp}
                  disabled={!canResendOtp || loading}
                  className="text-blue-600 hover:text-blue-800 font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {canResendOtp ? '🔄 Resend code' : `Resend in ${formatTimer(otpTimer)}`}
                </button>
                <br />
                <button
                  onClick={() => setCurrentView('login')}
                  className="text-gray-600 hover:text-gray-800 font-medium transition-colors"
                >
                  ← Back to login
                </button>
              </div>
            </div>
          )}

          {/* Reset Password Form */}
          {currentView === 'reset' && (
            <div className="space-y-6">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <p className="text-gray-600">Enter the code from your email and set a new password.</p>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Reset Code</label>
                <input
                  type="text"
                  name="password-reset-otp"
                  value={formData.otp}
                  onChange={(e) => handleInputChange('otp', e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white font-mono text-center"
                  placeholder="Enter 6-digit code"
                  maxLength={6}
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck="false"
                  data-form-type="other"
                />
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">New Password</label>
                <input
                  type="password"
                  value={formData.newPassword}
                  onChange={(e) => handleInputChange('newPassword', e.target.value)}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  placeholder="Enter new password"
                />
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Confirm New Password</label>
                <input
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  placeholder="Confirm new password"
                />
              </div>
              
              {otpTimer > 0 && (
                <div className="text-center text-sm text-gray-500">
                  Code expires in: <span className="font-mono font-bold text-red-600">{formatTimer(otpTimer)}</span>
                </div>
              )}
              
              <button
                onClick={handleResetPassword}
                disabled={loading}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white font-semibold py-4 rounded-xl hover:from-purple-600 hover:to-pink-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 shadow-lg"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Resetting...
                  </div>
                ) : (
                  '🔑 Reset Password'
                )}
              </button>
              
              <div className="text-center space-y-2">
                <button 
                  onClick={handleResendOtp}
                  disabled={!canResendOtp || loading}
                  className="text-blue-600 hover:text-blue-800 font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {canResendOtp ? '🔄 Resend code' : `Resend in ${formatTimer(otpTimer)}`}
                </button>
                <br />
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