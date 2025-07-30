/**
 * useVisitTracker - React Hook for Visit Tracking
 * Handles visit tracking and fetching visit statistics
 */
import { useState, useEffect, useCallback } from 'react';

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

  // Track a visit
  const trackVisit = useCallback(async (userData = null) => {
    try {
      const response = await fetch(`${API_BASE_URL}/visits/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_data: userData })
      });

      const result = await response.json();
      
      if (result.success) {
        console.log('✅ Visit tracked successfully');
        
        // Refresh statistics after tracking
        fetchVisitSummary();
      } else {
        console.warn('⚠️ Visit tracking failed:', result);
      }
      
      return result;
    } catch (error) {
      console.error('❌ Error tracking visit:', error);
      return { success: false, error: error.message };
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

  // Initial load of visit summary
  useEffect(() => {
    fetchVisitSummary();
  }, [fetchVisitSummary]);

  return {
    visitStats,
    trackVisit,
    fetchVisitSummary,
    fetchDetailedStats,
    refreshStats: fetchVisitSummary
  };
};

export default useVisitTracker;
