import React, { useState, useEffect } from 'react';
import { policyService } from '../../services/api';
import { countries, policyTypes } from '../../utils/constants';
import Button from '../ui/Button';
import Input from '../ui/Input';
import LoadingSpinner from '../ui/LoadingSpinner';

const PolicySubmissionForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    country: '',
    policyType: '',
    source: '',
    url: '',
    tags: '',
    keyPoints: '',
    file: null
  });
  const [policyAreas, setPolicyAreas] = useState([]);
  const [filteredCountries, setFilteredCountries] = useState([]);
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    // Load policy areas
    const loadPolicyAreas = async () => {
      try {
        const response = await policyService.get('/policy-areas');
        setPolicyAreas(response.policy_areas || []);
      } catch (err) {
        console.error('Failed to load policy areas:', err);
      }
    };
    loadPolicyAreas();
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

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setFormData(prev => ({ ...prev, file }));
  };

  const handleCountrySelect = (country) => {
    setFormData(prev => ({ ...prev, country }));
    setShowCountryDropdown(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.title || !formData.description || !formData.country || !formData.policyType) {
      setError('Please fill in all required fields');
      return;
    }

    if (!countries.includes(formData.country)) {
      setError('Please select a valid country from the list');
      return;
    }

    setLoading(true);
    try {
      let response;
      
      if (formData.file) {
        // Submit with file upload
        const formDataToSend = new FormData();
        formDataToSend.append('title', formData.title);
        formDataToSend.append('description', formData.description);
        formDataToSend.append('country', formData.country);
        formDataToSend.append('policyType', formData.policyType);
        if (formData.source) formDataToSend.append('source', formData.source);
        if (formData.url) formDataToSend.append('url', formData.url);
        if (formData.tags) formDataToSend.append('tags', formData.tags);
        if (formData.keyPoints) formDataToSend.append('keyPoints', formData.keyPoints);
        formDataToSend.append('file', formData.file);

        response = await fetch('/api/policies/submit-with-file', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: formDataToSend
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Submission failed');
        }

        response = await response.json();
      } else {
        // Submit without file
        response = await policyService.submitPolicy({
          title: formData.title,
          description: formData.description,
          country: formData.country,
          policyType: formData.policyType,
          source: formData.source || null,
          url: formData.url || null,
          tags: formData.tags ? formData.tags.split(',').map(tag => tag.trim()) : [],
          keyPoints: formData.keyPoints ? formData.keyPoints.split('\n').map(point => point.trim()).filter(point => point) : []
        });
      }

      setSuccess('Policy submitted successfully! It will be reviewed by our admin team.');
      
      // Reset form
      setFormData({
        title: '',
        description: '',
        country: '',
        policyType: '',
        source: '',
        url: '',
        tags: '',
        keyPoints: '',
        file: null
      });

      if (onSuccess) {
        setTimeout(() => onSuccess(), 2000);
      }

    } catch (err) {
      setError(err.message || 'Failed to submit policy. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden border border-blue-100">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 p-8 text-white text-center">
            <h1 className="text-3xl font-bold mb-2">Submit AI Policy</h1>
            <p className="text-blue-100">Help us track AI policies worldwide</p>
          </div>

          <div className="p-8">
            {/* Messages */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-400 text-red-700 rounded-lg">
                <span className="font-medium">{error}</span>
              </div>
            )}
            {success && (
              <div className="mb-6 p-4 bg-green-50 border-l-4 border-green-400 text-green-700 rounded-lg">
                <span className="font-medium">{success}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Input
                  label="Policy Title"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  placeholder="Enter policy title"
                  required
                />

                <div className="relative">
                  <Input
                    label="Country"
                    value={formData.country}
                    onChange={(e) => {
                      handleInputChange('country', e.target.value);
                      setShowCountryDropdown(true);
                    }}
                    onFocus={() => setShowCountryDropdown(true)}
                    placeholder="🌍 Type to search countries..."
                    required
                  />
                  {showCountryDropdown && filteredCountries.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-xl shadow-xl max-h-60 overflow-y-auto">
                      {filteredCountries.slice(0, 10).map((country) => (
                        <button
                          key={country}
                          type="button"
                          onClick={() => handleCountrySelect(country)}
                          className="w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors border-b border-gray-100 last:border-0"
                        >
                          {country}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Policy Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.policyType}
                    onChange={(e) => handleInputChange('policyType', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                    required
                  >
                    <option value="">Select policy type</option>
                    {policyTypes.map(type => (
                      <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
                    ))}
                  </select>
                </div>

                <Input
                  label="Source"
                  value={formData.source}
                  onChange={(e) => handleInputChange('source', e.target.value)}
                  placeholder="Government agency, organization, etc."
                />
              </div>

              <Input
                label="URL"
                type="url"
                value={formData.url}
                onChange={(e) => handleInputChange('url', e.target.value)}
                placeholder="https://example.com/policy-document"
              />

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Provide a detailed description of the policy..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  rows={4}
                  required
                />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Tags</label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={(e) => handleInputChange('tags', e.target.value)}
                    placeholder="AI safety, regulation, privacy (comma-separated)"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Supporting File</label>
                  <input
                    type="file"
                    onChange={handleFileChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                    accept=".pdf,.doc,.docx,.txt"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Key Points</label>
                <textarea
                  value={formData.keyPoints}
                  onChange={(e) => handleInputChange('keyPoints', e.target.value)}
                  placeholder="Enter key points, one per line..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 hover:bg-white"
                  rows={3}
                />
              </div>

              <div className="flex gap-4 pt-6">
                <Button
                  type="submit"
                  disabled={loading}
                  className="flex-1"
                >
                  {loading ? <LoadingSpinner /> : '📝 Submit Policy'}
                </Button>
                
                {onCancel && (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={onCancel}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                )}
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PolicySubmissionForm;
