/**
 * VisitCounter Component
 * Displays website visit statistics with attractive styling
 */
import React from 'react';
import { useVisitTracker } from '../../hooks/useVisitTracker';

const VisitCounter = ({ className = "", showDetailed = false }) => {
  const { visitStats } = useVisitTracker();

  if (visitStats.loading) {
    return (
      <div className={`visit-counter ${className}`}>
        <div className="flex items-center gap-2 text-gray-500">
          <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
          <span className="text-sm">Loading visit data...</span>
        </div>
      </div>
    );
  }

  if (visitStats.error) {
    return (
      <div className={`visit-counter ${className}`}>
        <div className="text-gray-400 text-sm">
          <span>👁️ Visitor data unavailable</span>
        </div>
      </div>
    );
  }

  if (showDetailed) {
    return (
      <div className={`visit-counter-detailed ${className}`}>
        <div className="bg-gradient-to-r from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-4 border border-blue-200/30 dark:border-blue-700/30">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <div>
              <h4 className="font-bold text-gray-900 dark:text-white">Website Analytics</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">Real-time visitor tracking</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {visitStats.total_visits.toLocaleString()}
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">Total Visits</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                {visitStats.unique_visitors.toLocaleString()}
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">Unique Visitors</div>
            </div>
          </div>

          {visitStats.user_type_breakdown && (
            <div className="mt-3 pt-3 border-t border-blue-200/50 dark:border-blue-700/50">
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
                <span>👥 Viewers: {visitStats.user_type_breakdown.viewer || 0}</span>
                <span>👤 Users: {visitStats.user_type_breakdown.registered || 0}</span>
                <span>⚙️ Admins: {visitStats.user_type_breakdown.admin || 0}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Simple display for home page stats
  return (
    <div className={`visit-counter-simple ${className}`}>
      <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
        <span className="text-sm font-medium">
          {visitStats.total_visits.toLocaleString()} Total Visits
        </span>
        <span className="text-xs text-gray-500">
          ({visitStats.unique_visitors.toLocaleString()} unique)
        </span>
      </div>
    </div>
  );
};

export default VisitCounter;
