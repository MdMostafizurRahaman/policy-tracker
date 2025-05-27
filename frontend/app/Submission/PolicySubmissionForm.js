'use client'
import { useState, useEffect } from "react"
import './styles.css'

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
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

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
  const handleSubmit = async (e) => {
    e.preventDefault()
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
    <div className="tab-container">
      <div 
        className={`tab ${activeTab === "general" ? "active" : ""}`}
        onClick={() => setActiveTab("general")}
      >
        Country
      </div>
      <div 
        className={`tab ${activeTab === "policy" ? "active" : ""}`}
        onClick={() => setActiveTab("policy")}
      >
        Policy Details
      </div>
    </div>
  )

  const renderPolicyDetailTabs = () => (
    <div className="policy-detail-tabs">
      {["basic", "implementation", "eval", "participation", "alignment"].map(tab => (
        <div 
          key={tab}
          className={`policy-tab ${policyTabSelected === tab ? "active" : ""}`}
          onClick={() => setPolicyTabSelected(tab)}
        >
          {tab === "basic" ? "Basic Info" : 
           tab === "eval" ? "Evaluation" : 
           tab.charAt(0).toUpperCase() + tab.slice(1)}
        </div>
      ))}
    </div>
  )

  const renderCountrySection = () => (
    <div className="form-section">
      <h3>Country Information</h3>
      <div>
        <label className="form-label">Country Name:</label>
        <input
          type="text"
          value={formData.country}
          onChange={(e) => setFormData({...formData, country: e.target.value})}
          required
          className="form-input"
          placeholder="Enter country name"
        />
      </div>
      <div className="submission-info">
        <p><strong>Submission ID:</strong> {submissionId}</p>
        <p><em>This ID will be used to track your submission through the admin review process.</em></p>
      </div>
    </div>
  )

  const renderPolicyNavigation = () => {
    return (
      <>
        <div className="policy-nav">
          <button 
            type="button" 
            className="policy-nav-button"
            disabled={activePolicyIndex === 0}
            onClick={() => {
              setActivePolicyIndex(Math.max(0, activePolicyIndex - 1))
              setPolicyTabSelected("basic")
            }}
          >
            Previous Policy
          </button>
          <button 
            type="button" 
            className="policy-nav-button"
            disabled={activePolicyIndex === 9}
            onClick={() => {
              setActivePolicyIndex(Math.min(9, activePolicyIndex + 1))
              setPolicyTabSelected("basic")
            }}
          >
            Next Policy
          </button>
        </div>
        
        <div className="policy-indicator">
          {Array(10).fill(null).map((_, i) => (
            <div 
              key={i}
              className={`policy-dot ${i === activePolicyIndex ? "active" : ""} ${formData.policyInitiatives[i].policyName ? "filled" : ""}`}
              onClick={() => {
                setActivePolicyIndex(i)
                setPolicyTabSelected("basic")
              }}
              title={`Policy ${i + 1}${formData.policyInitiatives[i].policyName ? ': ' + formData.policyInitiatives[i].policyName : ''}`}
            />
          ))}
        </div>
      </>
    )
  }

  const renderBasicInfo = () => {
    const policy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="form-section">
        <h4>Policy {activePolicyIndex + 1} - Basic Information</h4>
        
        <div>
          <label className="form-label">Policy Name:</label>
          <input
            type="text"
            value={policy.policyName}
            onChange={(e) => updatePolicy(activePolicyIndex, "policyName", e.target.value)}
            className="form-input"
            placeholder="Enter policy name"
          />
        </div>

        <div>
          <label className="form-label">Policy ID:</label>
          <input
            type="text"
            value={policy.policyId}
            onChange={(e) => updatePolicy(activePolicyIndex, "policyId", e.target.value)}
            className="form-input"
            placeholder="Enter policy ID"
          />
        </div>

        <div>
          <label className="form-label">Policy Area:</label>
          <select
            value={policy.policyArea}
            onChange={(e) => updatePolicy(activePolicyIndex, "policyArea", e.target.value)}
            className="form-select"
          >
            <option value="">Select Policy Area</option>
            {POLICY_TYPES.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="form-label">Target Groups:</label>
          <div className="checkbox-group">
            {TARGET_GROUPS.map(group => (
              <label key={group} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={policy.targetGroups.includes(group)}
                  onChange={() => toggleArrayItem(activePolicyIndex, null, "targetGroups", group)}
                />
                {group}
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="form-label">Policy Description:</label>
          <textarea
            value={policy.policyDescription}
            onChange={(e) => updatePolicy(activePolicyIndex, "policyDescription", e.target.value)}
            className="form-textarea"
            rows="4"
            placeholder="Describe the policy..."
          />
        </div>

        <div>
          <label className="form-label">Policy Document:</label>
          <div className="file-upload-section">
            <input
              type="file"
              onChange={(e) => {
                const file = e.target.files[0]
                if (file) {
                  handleFileUpload(activePolicyIndex, file)
                }
              }}
              className="form-input"
              accept=".pdf,.doc,.docx,.txt"
              disabled={fileUploading[activePolicyIndex]}
            />
            {fileUploading[activePolicyIndex] && (
              <div className="upload-status">Uploading...</div>
            )}
            {policy.policyFile && (
              <div className="file-info">
                <span className="file-name">📄 {policy.policyFile.name}</span>
                <span className="file-size">({(policy.policyFile.size / 1024).toFixed(1)} KB)</span>
                <button 
                  type="button"
                  onClick={() => updatePolicy(activePolicyIndex, "policyFile", null)}
                  className="remove-file-btn"
                >
                  Remove
                </button>
              </div>
            )}
          </div>
        </div>

        <div>
          <label className="form-label">Policy Link (Optional):</label>
          <input
            type="url"
            value={policy.policyLink}
            onChange={(e) => updatePolicy(activePolicyIndex, "policyLink", e.target.value)}
            className="form-input"
            placeholder="https://..."
          />
        </div>
      </div>
    )
  }

  const renderImplementation = () => {
    const policy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="form-section">
        <h4>Policy {activePolicyIndex + 1} - Implementation</h4>
        
        <div className="form-row">
          <div>
            <label className="form-label">Yearly Budget:</label>
            <input
              type="number"
              value={policy.implementation.yearlyBudget}
              onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "yearlyBudget", e.target.value)}
              className="form-input"
              placeholder="Enter budget amount"
            />
          </div>
          <div>
            <label className="form-label">Currency:</label>
            <select
              value={policy.implementation.budgetCurrency}
              onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "budgetCurrency", e.target.value)}
              className="form-select"
            >
              {CURRENCIES.map(currency => (
                <option key={currency} value={currency}>{currency}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={policy.implementation.privateSecFunding}
              onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "privateSecFunding", e.target.checked)}
            />
            Private Sector Funding
          </label>
        </div>

        <div>
          <label className="form-label">Deployment Year:</label>
          <input
            type="number"
            value={policy.implementation.deploymentYear}
            onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "deploymentYear", parseInt(e.target.value) || new Date().getFullYear())}
            className="form-input"
            min="2020"
            max="2030"
          />
        </div>
      </div>
    )
  }

  const renderEvaluation = () => {
    const policy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="form-section">
        <h4>Policy {activePolicyIndex + 1} - Evaluation</h4>
        
        <div>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={policy.evaluation.isEvaluated}
              onChange={(e) => updatePolicySection(activePolicyIndex, "evaluation", "isEvaluated", e.target.checked)}
            />
            Policy has been evaluated
          </label>
        </div>

        {policy.evaluation.isEvaluated && (
          <>
            <div>
              <label className="form-label">Evaluation Type:</label>
              <select
                value={policy.evaluation.evaluationType}
                onChange={(e) => updatePolicySection(activePolicyIndex, "evaluation", "evaluationType", e.target.value)}
                className="form-select"
              >
                <option value="internal">Internal</option>
                <option value="external">External</option>
                <option value="mixed">Mixed</option>
              </select>
            </div>

            <div>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={policy.evaluation.riskAssessment}
                  onChange={(e) => updatePolicySection(activePolicyIndex, "evaluation", "riskAssessment", e.target.checked)}
                />
                Risk Assessment Conducted
              </label>
            </div>

            <div className="score-section">
              <div>
                <label className="form-label">Transparency Score (0-10):</label>
                <input
                  type="range"
                  min="0"
                  max="10"
                  value={policy.evaluation.transparencyScore}
                  onChange={(e) => updatePolicySection(activePolicyIndex, "evaluation", "transparencyScore", parseInt(e.target.value))}
                  className="form-range"
                />
                <span className="score-value">{policy.evaluation.transparencyScore}</span>
              </div>

              <div>
                <label className="form-label">Explainability Score (0-10):</label>
                <input
                  type="range"
                  min="0"
                  max="10"
                  value={policy.evaluation.explainabilityScore}
                  onChange={(e) => updatePolicySection(activePolicyIndex, "evaluation", "explainabilityScore", parseInt(e.target.value))}
                  className="form-range"
                />
                <span className="score-value">{policy.evaluation.explainabilityScore}</span>
              </div>

              <div>
                <label className="form-label">Accountability Score (0-10):</label>
                <input
                  type="range"
                  min="0"
                  max="10"
                  value={policy.evaluation.accountabilityScore}
                  onChange={(e) => updatePolicySection(activePolicyIndex, "evaluation", "accountabilityScore", parseInt(e.target.value))}
                  className="form-range"
                />
                <span className="score-value">{policy.evaluation.accountabilityScore}</span>
              </div>
            </div>
          </>
        )}
      </div>
    )
  }

  const renderParticipation = () => {
    const policy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="form-section">
        <h4>Policy {activePolicyIndex + 1} - Public Participation</h4>
        
        <div>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={policy.participation.hasConsultation}
              onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "hasConsultation", e.target.checked)}
            />
            Public Consultation Conducted
          </label>
        </div>

        {policy.participation.hasConsultation && (
          <>
            <div className="form-row">
              <div>
                <label className="form-label">Consultation Start Date:</label>
                <input
                  type="date"
                  value={policy.participation.consultationStartDate}
                  onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "consultationStartDate", e.target.value)}
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Consultation End Date:</label>
                <input
                  type="date"
                  value={policy.participation.consultationEndDate}
                  onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "consultationEndDate", e.target.value)}
                  className="form-input"
                />
              </div>
            </div>

            <div>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={policy.participation.commentsPublic}
                  onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "commentsPublic", e.target.checked)}
                />
                Comments Made Public
              </label>
            </div>

            <div>
              <label className="form-label">Stakeholder Engagement Score (0-10):</label>
              <input
                type="range"
                min="0"
                max="10"
                value={policy.participation.stakeholderScore}
                onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "stakeholderScore", parseInt(e.target.value))}
                className="form-range"
              />
              <span className="score-value">{policy.participation.stakeholderScore}</span>
            </div>
          </>
        )}
      </div>
    )
  }

  const renderAlignment = () => {
    const policy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="form-section">
        <h4>Policy {activePolicyIndex + 1} - Alignment</h4>
        
        <div>
          <label className="form-label">AI Principles Alignment:</label>
          <div className="checkbox-group">
            {PRINCIPLES.map(principle => (
              <label key={principle} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={policy.alignment.aiPrinciples.includes(principle)}
                  onChange={() => toggleArrayItem(activePolicyIndex, "alignment", "aiPrinciples", principle)}
                />
                {principle}
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={policy.alignment.humanRightsAlignment}
              onChange={(e) => updatePolicySection(activePolicyIndex, "alignment", "humanRightsAlignment", e.target.checked)}
            />
            Human Rights Alignment
          </label>
        </div>

        <div>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={policy.alignment.environmentalConsiderations}
              onChange={(e) => updatePolicySection(activePolicyIndex, "alignment", "environmentalConsiderations", e.target.checked)}
            />
            Environmental Considerations
          </label>
        </div>

        <div>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={policy.alignment.internationalCooperation}
              onChange={(e) => updatePolicySection(activePolicyIndex, "alignment", "internationalCooperation", e.target.checked)}
            />
            International Cooperation
          </label>
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
    <div className="policy-form-container">
      <div className="form-header">
        <h1>Policy Submission Form</h1>
        <p>Submit policy information for admin review before final database storage.</p>
      </div>

      {formError && (
        <div className="alert alert-error">
          {formError}
        </div>
      )}

      {formSuccess && (
        <div className="alert alert-success">
          {formSuccess}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {renderMainTabs()}

        {activeTab === "general" && renderCountrySection()}

        {activeTab === "policy" && (
          <div className="policy-section">
            {renderPolicyNavigation()}
            {renderPolicyDetailTabs()}
            {renderPolicyContent()}
          </div>
        )}

        <div className="form-actions">
          <button 
            type="submit" 
            disabled={loading}
            className="submit-btn"
          >
            {loading ? "Submitting..." : "Submit for Review"}
          </button>
        </div>
      </form>
    </div>
  )
}