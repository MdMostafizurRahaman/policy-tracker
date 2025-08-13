/**
 * useVisitTracker - React Hook for Visit Tracking
 * Handles visit tracking and fetching visit statistics
 */
import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useVisitTracker = () => {
  const [visitStats, setVisitStats] = useState({
    total_visits: 0,
    unique_visitors: 0,
    today_visits: 0,
    user_type_breakdown: {
      viewer: 0,
      registered: 0,
      admin: 0
    },
    loading: true,
    error: null
  });

  // Ref to prevent duplicate API calls in development (React Strict Mode)
  const trackingInProgress = useRef(false);

  // Generate a browser fingerprint for better unique visitor identification
  const generateBrowserFingerprint = useCallback(() => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Browser fingerprint text', 2, 2);
    
    const fingerprint = {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      cookieEnabled: navigator.cookieEnabled,
      screenResolution: `${screen.width}x${screen.height}`,
      screenColorDepth: screen.colorDepth,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      canvasFingerprint: canvas.toDataURL(),
      hardwareConcurrency: navigator.hardwareConcurrency || 0,
      deviceMemory: navigator.deviceMemory || 0,
      webglVendor: (() => {
        try {
          const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
          return gl ? gl.getParameter(gl.VENDOR) : 'unknown';
        } catch (e) {
          return 'unknown';
        }
      })(),
      sessionId: sessionStorage.getItem('session_id') || Date.now().toString(),
      visitTimestamp: Date.now()
    };
    
    // Store session ID for consistency within same browser session
    if (!sessionStorage.getItem('session_id')) {
      sessionStorage.setItem('session_id', fingerprint.sessionId);
    }
    
    return fingerprint;
  }, []);

  // Track a visit
  const trackVisit = useCallback(async (userData = null, isNewRegistration = false) => {
    // Prevent duplicate calls in rapid succession (but allow new registrations)
    if (trackingInProgress.current && !isNewRegistration) {
      console.log('⏳ Visit tracking already in progress, skipping...');
      return { success: true, message: 'Already tracking' };
    }

    trackingInProgress.current = true;

    try {
      // Generate comprehensive browser fingerprint
      const browserFingerprint = generateBrowserFingerprint();
      
      const requestData = {
        user_data: userData,
        is_new_registration: isNewRegistration,
        browser_fingerprint: browserFingerprint,
        visit_context: {
          referrer: document.referrer,
          current_url: window.location.href,
          page_title: document.title,
          visit_type: isNewRegistration ? 'new_registration' : 'regular_visit'
        }
      };

      const response = await fetch(`${API_BASE_URL}/visits/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      const result = await response.json();
      
      if (result.success) {
        if (isNewRegistration) {
          console.log('🎉 New user registration tracked successfully');
        } else {
          console.log('✅ Visit tracked successfully');
        }
        
        // Refresh statistics after tracking
        fetchVisitSummary();
      } else {
        console.warn('⚠️ Visit tracking failed:', result);
      }
      
      return result;
    } catch (error) {
      console.error('❌ Error tracking visit:', error);
      return { success: false, error: error.message };
    } finally {
      // Reset tracking flag after a delay to allow for legitimate subsequent calls
      setTimeout(() => {
        trackingInProgress.current = false;
      }, 2000);
    }
  }, []);

  // Fetch visit summary for home page display
  const fetchVisitSummary = useCallback(async () => {
    try {
      setVisitStats(prev => ({ ...prev, loading: true }));
      
      const response = await fetch(`${API_BASE_URL}/visits/summary`);
      const result = await response.json();
      
      if (result.success) {
        setVisitStats(prev => ({
          ...prev,
          total_visits: result.total_visits,
          unique_visitors: result.unique_visitors,
          loading: false,
          error: null
        }));
      } else {
        setVisitStats(prev => ({
          ...prev,
          loading: false,
          error: result.error || 'Failed to fetch visit data'
        }));
      }
    } catch (error) {
      console.error('❌ Error fetching visit summary:', error);
      setVisitStats(prev => ({
        ...prev,
        loading: false,
        error: error.message
      }));
    }
  }, []);

  // Fetch detailed visit statistics
  const fetchDetailedStats = useCallback(async () => {
    try {
      setVisitStats(prev => ({ ...prev, loading: true }));
      
      const response = await fetch(`${API_BASE_URL}/visits/statistics`);
      const result = await response.json();
      
      if (result.success) {
        setVisitStats(prev => ({
          ...prev,
          ...result.statistics,
          loading: false,
          error: null
        }));
      } else {
        setVisitStats(prev => ({
          ...prev,
          loading: false,
          error: result.statistics?.error || 'Failed to fetch detailed statistics'
        }));
      }
    } catch (error) {
      console.error('❌ Error fetching detailed statistics:', error);
      setVisitStats(prev => ({
        ...prev,
        loading: false,
        error: error.message
      }));
    }
  }, []);

  // Initial load of visit summary - using detailed stats to get today_visits
  useEffect(() => {
    fetchDetailedStats();
  }, [fetchDetailedStats]);

  // Track new user registration
  const trackNewRegistration = useCallback(async (userData) => {
    return await trackVisit(userData, true);
  }, [trackVisit]);

  return {
    visitStats,
    trackVisit,
    trackNewRegistration,
    fetchVisitSummary,
    fetchDetailedStats,
    refreshStats: fetchDetailedStats  // Use detailed stats for refresh to get today_visits
  };
};

export default useVisitTracker;
