'use client'
import { useState, useEffect } from "react"

// Policy configuration data
const POLICY_TYPES = [
  "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
  "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
  "Physical Health", "Social Media/Gaming Regulation"
]

const TARGET_GROUPS = [
  "Government", "Industry", "Academia", "Small Businesses", 
  "General Public", "Specific Sector"
]

const PRINCIPLES = [
  "Fairness", "Accountability", "Transparency", "Explainability", 
  "Safety", "Human Control", "Privacy", "Security", 
  "Non-discrimination", "Trust", "Sustainability"
]

const CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CNY", "Local"]

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Generate unique submission ID
const generateSubmissionId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Initial empty policy template 
const createEmptyPolicy = () => ({
  policyName: "",
  policyId: "",
  policyArea: "",
  targetGroups: [],
  policyDescription: "",
  policyFile: null,
  policyLink: "",
  implementation: {
    yearlyBudget: "",
    budgetCurrency: "USD",
    privateSecFunding: false,
    deploymentYear: new Date().getFullYear()
  },
  evaluation: {
    isEvaluated: false,
    evaluationType: "internal",
    riskAssessment: false,
    transparencyScore: 0,
    explainabilityScore: 0,
    accountabilityScore: 0
  },
  participation: {
    hasConsultation: false,
    consultationStartDate: "",
    consultationEndDate: "",
    commentsPublic: false,
    stakeholderScore: 0
  },
  alignment: {
    aiPrinciples: [],
    humanRightsAlignment: false,
    environmentalConsiderations: false,
    internationalCooperation: false
  },
  status: "pending",
  admin_notes: ""
})

// Handle individual file uploads
const uploadPolicyFile = async (countryName, policyIndex, submissionId, file) => {
  if (!file || !countryName || !submissionId) {
    return { success: false, message: 'Missing required data for file upload' }
  }

  try {
    const formData = new FormData()
    formData.append('country', countryName)
    formData.append('policy_index', policyIndex)
    formData.append('submission_id', submissionId)
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/upload-policy-file`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Upload failed with status: ${response.status}`)
    }

    const result = await response.json()
    return {
      success: true,
      fileData: {
        name: result.filename,
        file_id: result.file_id,
        size: result.size,
        type: result.content_type,
        upload_date: new Date().toISOString(),
        content: result.content // File content extracted by backend
      },
      message: 'File uploaded successfully'
    }
  } catch (error) {
    console.error('Error uploading file:', error)
    return {
      success: false,
      error: error.message,
      message: `Upload error: ${error.message}`
    }
  }
}

export default function PolicySubmissionForm() {
  const [formData, setFormData] = useState({
    country: "",
    policyInitiatives: Array(10).fill().map(() => createEmptyPolicy())
  })
  const [submissionId] = useState(generateSubmissionId())
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("general")
  const [activePolicyIndex, setActivePolicyIndex] = useState(0)
  const [policyTabSelected, setPolicyTabSelected] = useState("basic")
  const [formError, setFormError] = useState("")
  const [formSuccess, setFormSuccess] = useState("")
  const [fileUploading, setFileUploading] = useState({})

  // Generic update helpers
  const updatePolicy = (index, field, value) => {
    const updatedPolicies = [...formData.policyInitiatives]
    updatedPolicies[index] = {
      ...updatedPolicies[index],
      [field]: value
    }
    setFormData({...formData, policyInitiatives: updatedPolicies})
  }

  const updatePolicySection = (index, section, field, value) => {
    const updatedPolicies = [...formData.policyInitiatives]
    updatedPolicies[index] = {
      ...updatedPolicies[index],
      [section]: {
        ...updatedPolicies[index][section],
        [field]: value
      }
    }
    setFormData({...formData, policyInitiatives: updatedPolicies})
  }

  const toggleArrayItem = (index, section, field, item) => {
    const currentItems = section ? 
      formData.policyInitiatives[index][section][field] : 
      formData.policyInitiatives[index][field]
    
    const updatedItems = currentItems.includes(item) ?
      currentItems.filter(i => i !== item) :
      [...currentItems, item]
    
    if (section) {
      updatePolicySection(index, section, field, updatedItems)
    } else {
      updatePolicy(index, field, updatedItems)
    }
  }

  // File upload handler
  const handleFileUpload = async (policyIndex, file) => {
    if (!file) return;

    setFileUploading(prev => ({ ...prev, [policyIndex]: true }));

    try {
      const result = await uploadPolicyFile(formData.country, policyIndex, submissionId, file);
      
      if (result.success) {
        updatePolicy(policyIndex, "policyFile", result.fileData);
        setFormError("");
      } else {
        setFormError(result.message);
        updatePolicy(policyIndex, "policyFile", null);
      }
    } catch (error) {
      setFormError(`File upload error: ${error.message}`);
      updatePolicy(policyIndex, "policyFile", null);
    } finally {
      setFileUploading(prev => ({ ...prev, [policyIndex]: false }));
    }
  };

  // Form reset handler
  const resetForm = () => {
    setFormData({
      country: "",
      policyInitiatives: Array(10).fill().map(() => createEmptyPolicy())
    })
    setActiveTab("general")
    setActivePolicyIndex(0)
    setPolicyTabSelected("basic")
    setFormError("")
    setFormSuccess("Submission successful! Your data has been submitted for admin review.")
    
    // Clear success message after 5 seconds
    setTimeout(() => {
      setFormSuccess("")
    }, 5000)
  }

  // Form validation
  const validateForm = () => {
    if (!formData.country.trim()) {
      setFormError("Please enter a country name")
      return false
    }

    if (!formData.policyInitiatives[0].policyName.trim()) {
      setFormError("Please enter a name for at least the first policy")
      setActiveTab("policy")
      setActivePolicyIndex(0)
      setPolicyTabSelected("basic")
      return false
    }
    
    setFormError("")
    return true
  }

  // Form submission handler
  const handleSubmit = async () => {
    setLoading(true)
    setFormError("")
    setFormSuccess("")

    try {
      // Validate form data
      if (!validateForm()) {
        setLoading(false)
        return
      }

      // Prepare submission data
      const submissionData = {
        submission_id: submissionId,
        country: formData.country,
        policyInitiatives: formData.policyInitiatives
          .filter(policy => policy.policyName.trim() !== "")
          .map((policy, index) => ({
            ...policy,
            policy_index: index,
            // Ensure file data is properly formatted with content
            policyFile: policy.policyFile && typeof policy.policyFile === 'object' && 'file_id' in policy.policyFile 
              ? policy.policyFile 
              : null
          })),
        submission_status: "pending",
        submitted_at: new Date().toISOString()
      }

      // Submit the form data to temp database
      const response = await fetch(`${API_BASE_URL}/submit-form`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(submissionData)
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status: ${response.status}`)
      }

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.message || 'Form submission failed')
      }

      // Success!
      resetForm()
    } catch (error) {
      console.error("Error submitting form:", error)
      setFormError(`Error: ${error.message || 'Please try again.'}`)
    } finally {
      setLoading(false)
    }
  }

  // UI COMPONENTS
  const renderMainTabs = () => (
    <div className="flex border-b border-slate-200 dark:border-slate-700 mb-8">
      <button 
        type="button"
        className={`px-6 py-3 font-semibold border-b-2 transition-all ${
          activeTab === "general" 
            ? "border-blue-500 text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400" 
            : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
        }`}
        onClick={() => setActiveTab("general")}
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Country Information
        </div>
      </button>
      <button 
        type="button"
        className={`px-6 py-3 font-semibold border-b-2 transition-all ${
          activeTab === "policy" 
            ? "border-blue-500 text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400" 
            : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
        }`}
        onClick={() => setActiveTab("policy")}
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Policy Details
        </div>
      </button>
    </div>
  )

  const renderPolicyDetailTabs = () => (
    <div className="flex gap-2 mb-6 flex-wrap">
      {[
        { key: "basic", label: "Basic Info", icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
        { key: "implementation", label: "Implementation", icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" },
        { key: "eval", label: "Evaluation", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
        { key: "participation", label: "Participation", icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" },
        { key: "alignment", label: "Alignment", icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" }
      ].map(tab => (
        <button 
          key={tab.key}
          type="button"
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            policyTabSelected === tab.key
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
          }`}
          onClick={() => setPolicyTabSelected(tab.key)}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
          </svg>
          {tab.label}
        </button>
      ))}
    </div>
  )

  const renderCountrySection = () => (
    <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg border border-slate-200 dark:border-slate-700">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-2xl font-bold text-slate-800 dark:text-white">Country Information</h3>
      </div>
      
      <div className="space-y-6">
        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
            Country Name *
          </label>
          <input
            type="text"
            value={formData.country}
            onChange={(e) => setFormData({...formData, country: e.target.value})}
            required
            className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400"
            placeholder="Enter country name"
          />
      </div>
    </div>
  )

  const renderPolicyNavigation = () => (
    <div className="mb-8">
      <div className="flex justify-between items-center mb-6">
        <button 
          type="button" 
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={activePolicyIndex === 0}
          onClick={() => {
            setActivePolicyIndex(Math.max(0, activePolicyIndex - 1))
            setPolicyTabSelected("basic")
          }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Previous Policy
        </button>
        
        <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
          Policy {activePolicyIndex + 1} of 10
        </span>
        
        <button 
          type="button" 
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={activePolicyIndex === 9}
          onClick={() => {
            setActivePolicyIndex(Math.min(9, activePolicyIndex + 1))
            setPolicyTabSelected("basic")
          }}
        >
          Next Policy
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
      
      <div className="flex justify-center gap-2 flex-wrap">
        {Array(10).fill(null).map((_, i) => (
          <button 
            key={i}
            type="button"
            className={`w-10 h-10 rounded-full text-sm font-medium transition-all ${
              i === activePolicyIndex 
                ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg scale-110" 
                : formData.policyInitiatives[i].policyName 
                  ? "bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-800" 
                  : "bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-600"
            }`}
            onClick={() => {
              setActivePolicyIndex(i)
              setPolicyTabSelected("basic")
            }}
            title={`Policy ${i + 1}${formData.policyInitiatives[i].policyName ? ': ' + formData.policyInitiatives[i].policyName : ''}`}
          >
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  )

  const renderBasicInfo = () => {
    const policy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg border border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold">
            {activePolicyIndex + 1}
          </div>
          <h4 className="text-xl font-bold text-slate-800 dark:text-white">
            Policy {activePolicyIndex + 1} - Basic Information
          </h4>
        </div>
        
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Policy Name *
              </label>
              <input
                type="text"
                value={policy.policyName}
                onChange={(e) => updatePolicy(activePolicyIndex, "policyName", e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                placeholder="Enter policy name"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Policy ID
              </label>
              <input
                type="text"
                value={policy.policyId}
                onChange={(e) => updatePolicy(activePolicyIndex, "policyId", e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                placeholder="Enter policy ID"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Policy Area
            </label>
            <select
              value={policy.policyArea}
              onChange={(e) => updatePolicy(activePolicyIndex, "policyArea", e.target.value)}
              className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
            >
              <option value="">Select Policy Area</option>
              {POLICY_TYPES.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
              Target Groups
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {TARGET_GROUPS.map(group => (
                <label key={group} className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer transition-all">
                  <input
                    type="checkbox"
                    checked={policy.targetGroups.includes(group)}
                    onChange={() => toggleArrayItem(activePolicyIndex, null, "targetGroups", group)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{group}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Policy Description
            </label>
            <textarea
              value={policy.policyDescription}
              onChange={(e) => updatePolicy(activePolicyIndex, "policyDescription", e.target.value)}
              className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white resize-none"
              rows="4"
              placeholder="Describe the policy in detail..."
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Policy Document
            </label>
            <div className="space-y-3">
              <input
                type="file"
                onChange={(e) => {
                  const file = e.target.files[0]
                  if (file) {
                    handleFileUpload(activePolicyIndex, file)
                  }
                }}
                className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                accept=".pdf,.doc,.docx,.txt"
                disabled={fileUploading[activePolicyIndex]}
              />
              
              {fileUploading[activePolicyIndex] && (
                <div className="flex items-center gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300 rounded-lg">
                  <div className="animate-spin w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full"></div>
                  <span className="text-sm font-medium">Uploading...</span>
                </div>
              )}
              
              {policy.policyFile && (
                <div className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-100 dark:bg-green-800 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-green-800 dark:text-green-200">{policy.policyFile.name}</p>
                      <p className="text-sm text-green-600 dark:text-green-400">
                        {(policy.policyFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <button 
                    type="button"
                    onClick={() => updatePolicy(activePolicyIndex, "policyFile", null)}
                    className="px-3 py-1 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-200 dark:hover:bg-red-800 transition-all text-sm font-medium"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Policy Link (Optional)
            </label>
            <input
              type="url"
              value={policy.policyLink}
              onChange={(e) => updatePolicy(activePolicyIndex, "policyLink", e.target.value)}
              className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              placeholder="https://..."
            />
          </div>
        </div>
      </div>
    )
  }

  const renderImplementation = () => {
    const policy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg border border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
          </div>
          <h4 className="text-xl font-bold text-slate-800 dark:text-white">
            Policy {activePolicyIndex + 1} - Implementation
          </h4>
        </div>
        
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Yearly Budget
              </label>
              <input
                type="number"
                value={policy.implementation.yearlyBudget}
                onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "yearlyBudget", e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                placeholder="Enter budget amount"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Currency
              </label>
              <select
                value={policy.implementation.budgetCurrency}
                onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "budgetCurrency", e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              >
                {CURRENCIES.map(currency => (
                  <option key={currency} value={currency}>{currency}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={policy.implementation.privateSecFunding}
                onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "privateSecFunding", e.target.checked)}
                className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
              />
              <span className="font-medium text-emerald-800 dark:text-emerald-200">Private Sector Funding</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Deployment Year
            </label>
            <input
              type="number"
              value={policy.implementation.deploymentYear}
              onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "deploymentYear", parseInt(e.target.value) || new Date().getFullYear())}
              className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              min="2020"
              max="2030"
            />
          </div>
        </div>
      </div>
    )
  }

  const renderEvaluation = () => {
    const policy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg border border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h4 className="text-xl font-bold text-slate-800 dark:text-white">
            Policy {activePolicyIndex + 1} - Evaluation
          </h4>
        </div>
        
        <div className="space-y-6">
          <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={policy.evaluation.isEvaluated}
                onChange={(e) => updatePolicySection(activePolicyIndex, "evaluation", "isEvaluated", e.target.checked)}
                className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
              />
              <span className="font-medium text-purple-800 dark:text-purple-200">Policy has been evaluated</span>
            </label>
          </div>

          {policy.evaluation.isEvaluated && (
            <div className="space-y-6 border-t border-slate-200 dark:border-slate-700 pt-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                  Evaluation Type
                </label>
                <select
                  value={policy.evaluation.evaluationType}
                  onChange={(e) => updatePolicySection(activePolicyIndex, "evaluation", "evaluationType", e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                >
                  <option value="internal">Internal</option>
                  <option value="external">External</option>
                  <option value="mixed">Mixed</option>
                </select>
              </div>

              <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policy.evaluation.riskAssessment}
                    onChange={(e) => updatePolicySection(activePolicyIndex, "evaluation", "riskAssessment", e.target.checked)}
                    className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
                  />
                  <span className="font-medium text-orange-800 dark:text-orange-200">Risk Assessment Conducted</span>
                </label>
              </div>

              <div className="space-y-6">
                <h5 className="text-lg font-semibold text-slate-800 dark:text-white">Evaluation Scores</h5>
                
                {[
                  { key: 'transparencyScore', label: 'Transparency Score', color: 'blue' },
                  { key: 'explainabilityScore', label: 'Explainability Score', color: 'indigo' },
                  { key: 'accountabilityScore', label: 'Accountability Score', color: 'purple' }
                ].map(({ key, label, color }) => (
                  <div key={key} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                        {label} (0-10)
                      </label>
                      <span className={`px-3 py-1 bg-${color}-100 dark:bg-${color}-900 text-${color}-700 dark:text-${color}-300 rounded-lg font-bold`}>
                        {policy.evaluation[key]}
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="10"
                      value={policy.evaluation[key]}
                      onChange={(e) => updatePolicySection(activePolicyIndex, "evaluation", key, parseInt(e.target.value))}
                      className={`w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer slider-${color}`}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderParticipation = () => {
    const policy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg border border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-r from-teal-500 to-cyan-600 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h4 className="text-xl font-bold text-slate-800 dark:text-white">
            Policy {activePolicyIndex + 1} - Public Participation
          </h4>
        </div>
        
        <div className="space-y-6">
          <div className="p-4 bg-teal-50 dark:bg-teal-900/20 rounded-lg border border-teal-200 dark:border-teal-800">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={policy.participation.hasConsultation}
                onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "hasConsultation", e.target.checked)}
                className="w-5 h-5 text-teal-600 rounded focus:ring-teal-500"
              />
              <span className="font-medium text-teal-800 dark:text-teal-200">Public Consultation Conducted</span>
            </label>
          </div>

          {policy.participation.hasConsultation && (
            <div className="space-y-6 border-t border-slate-200 dark:border-slate-700 pt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Consultation Start Date
                  </label>
                  <input
                    type="date"
                    value={policy.participation.consultationStartDate}
                    onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "consultationStartDate", e.target.value)}
                    className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Consultation End Date
                  </label>
                  <input
                    type="date"
                    value={policy.participation.consultationEndDate}
                    onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "consultationEndDate", e.target.value)}
                    className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg border border-cyan-200 dark:border-cyan-800">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policy.participation.commentsPublic}
                    onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "commentsPublic", e.target.checked)}
                    className="w-5 h-5 text-cyan-600 rounded focus:ring-cyan-500"
                  />
                  <span className="font-medium text-cyan-800 dark:text-cyan-200">Comments Made Public</span>
                </label>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                    Stakeholder Engagement Score (0-10)
                  </label>
                  <span className="px-3 py-1 bg-teal-100 dark:bg-teal-900 text-teal-700 dark:text-teal-300 rounded-lg font-bold">
                    {policy.participation.stakeholderScore}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="10"
                  value={policy.participation.stakeholderScore}
                  onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "stakeholderScore", parseInt(e.target.value))}
                  className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderAlignment = () => {
    const policy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg border border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h4 className="text-xl font-bold text-slate-800 dark:text-white">
            Policy {activePolicyIndex + 1} - Alignment & Principles
          </h4>
        </div>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
              AI Principles Alignment
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {PRINCIPLES.map(principle => (
                <label key={principle} className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer transition-all">
                  <input
                    type="checkbox"
                    checked={policy.alignment.aiPrinciples.includes(principle)}
                    onChange={() => toggleArrayItem(activePolicyIndex, "alignment", "aiPrinciples", principle)}
                    className="w-4 h-4 text-green-600 rounded focus:ring-green-500"
                  />
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{principle}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <h5 className="text-lg font-semibold text-slate-800 dark:text-white">Additional Considerations</h5>
            
            <div className="space-y-3">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policy.alignment.humanRightsAlignment}
                    onChange={(e) => updatePolicySection(activePolicyIndex, "alignment", "humanRightsAlignment", e.target.checked)}
                    className="w-5 h-5 text-green-600 rounded focus:ring-green-500"
                  />
                  <span className="font-medium text-green-800 dark:text-green-200">Human Rights Alignment</span>
                </label>
              </div>

              <div className="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policy.alignment.environmentalConsiderations}
                    onChange={(e) => updatePolicySection(activePolicyIndex, "alignment", "environmentalConsiderations", e.target.checked)}
                    className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
                  />
                  <span className="font-medium text-emerald-800 dark:text-emerald-200">Environmental Considerations</span>
                </label>
              </div>

              <div className="p-4 bg-teal-50 dark:bg-teal-900/20 rounded-lg border border-teal-200 dark:border-teal-800">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={policy.alignment.internationalCooperation}
                    onChange={(e) => updatePolicySection(activePolicyIndex, "alignment", "internationalCooperation", e.target.checked)}
                    className="w-5 h-5 text-teal-600 rounded focus:ring-teal-500"
                  />
                  <span className="font-medium text-teal-800 dark:text-teal-200">International Cooperation</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderPolicyContent = () => {
    switch(policyTabSelected) {
      case "basic":
        return renderBasicInfo()
      case "implementation":
        return renderImplementation()
      case "eval":
        return renderEvaluation()
      case "participation":
        return renderParticipation()
      case "alignment":
        return renderAlignment()
      default:
        return renderBasicInfo()
    }
  }

  // Main render
  return (
    <div className="min-h-screen max-w-6xl mx-auto p-6 space-y-8">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">
          Policy Submission Form
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
          Submit comprehensive policy information for admin review before final database storage.
        </p>
      </div>

      {formError && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-6 py-4 rounded-xl">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-medium">{formError}</span>
          </div>
        </div>
      )}

      {formSuccess && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 px-6 py-4 rounded-xl">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-medium">{formSuccess}</span>
          </div>
        </div>
      )}

      <div className="space-y-8">
        {renderMainTabs()}

        {activeTab === "general" && renderCountrySection()}

        {activeTab === "policy" && (
          <div className="space-y-8">
            {renderPolicyNavigation()}
            {renderPolicyDetailTabs()}
            {renderPolicyContent()}
          </div>
        )}

        <div className="flex justify-center pt-8 border-t border-slate-200 dark:border-slate-700">
          <button 
            onClick={handleSubmit}
            disabled={loading}
            className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white font-bold rounded-xl hover:from-blue-700 hover:via-purple-700 hover:to-pink-700 transition-all transform hover:scale-105 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? (
              <>
                <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                Submitting...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                Submit for Review
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}