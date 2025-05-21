'use client'
import { useState } from "react"
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

// API base URL - configurable for different environments
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

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
  }
})

// Handle file uploads
const uploadPolicyFile = async (countryName, policyIndex, file) => {
  if (!file || !countryName) {
    return { success: false, message: 'Missing required data for file upload' }
  }

  try {
    const formData = new FormData()
    formData.append('country', countryName)
    formData.append('policy_index', policyIndex)
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
      filePath: result.file_path,
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
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("general")
  const [activePolicyIndex, setActivePolicyIndex] = useState(0)
  const [policyTabSelected, setPolicyTabSelected] = useState("basic")
  const [formError, setFormError] = useState("")
  const [formSuccess, setFormSuccess] = useState("")

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
    setFormSuccess("Submission successful! The country's AI policy data has been recorded.")
    
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

      // Process file uploads first
      const fileUploadPromises = []
      const submissionData = {
        country: formData.country,
        policyInitiatives: JSON.parse(JSON.stringify(formData.policyInitiatives))
      }

      // Handle file uploads
      for (let index = 0; index < formData.policyInitiatives.length; index++) {
        const policy = formData.policyInitiatives[index]
        if (policy.policyFile && policy.policyFile instanceof File) {
          const uploadPromise = uploadPolicyFile(formData.country, index, policy.policyFile)
            .then(result => {
              if (result.success) {
                submissionData.policyInitiatives[index].policyFile = {
                  name: policy.policyFile.name, 
                  path: result.filePath || 'local-only',
                  size: policy.policyFile.size,
                  type: policy.policyFile.type
                }
              } else {
                throw new Error(result.message || "File upload failed")
              }
              return result
            })
          fileUploadPromises.push(uploadPromise)
        } else if (policy.policyFile === null) {
          // If no file, ensure the field is null in the submission
          submissionData.policyInitiatives[index].policyFile = null
        }
      }

      if (fileUploadPromises.length > 0) {
        await Promise.all(fileUploadPromises)
      }

      // Remove empty policies (those without a name)
      submissionData.policyInitiatives = submissionData.policyInitiatives
        .filter(policy => policy.policyName.trim() !== "");

      // Submit the form data
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
              className={`policy-dot ${i === activePolicyIndex ? "active" : ""}`}
              onClick={() => {
                setActivePolicyIndex(i)
                setPolicyTabSelected("basic")
              }}
            />
          ))}
        </div>
        
        <h3>Policy {activePolicyIndex + 1}</h3>
      </>
    )
  }

  const renderBasicPolicyInfo = () => {
    const currentPolicy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="form-section">
        <div>
          <label className="form-label">Policy type:</label>
          <select
            value={currentPolicy.policyArea}
            onChange={(e) => updatePolicy(activePolicyIndex, "policyArea", e.target.value)}
            className="form-select"
          >
            <option value="">Select Policy type</option>
            {POLICY_TYPES.map((area, i) => (
              <option key={i} value={area}>{area}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="form-label">Policy Name:</label>
          <input
            type="text"
            value={currentPolicy.policyName}
            onChange={(e) => updatePolicy(activePolicyIndex, "policyName", e.target.value)}
            className="form-input"
            placeholder="Enter policy name"
          />
        </div>
        
        <div>
          <label className="form-label">Policy ID:</label>
          <input
            type="text"
            value={currentPolicy.policyId}
            onChange={(e) => updatePolicy(activePolicyIndex, "policyId", e.target.value)}
            className="form-input"
            placeholder="Enter policy ID"
          />
        </div>
        
        <div>
          <label className="form-label">Target Groups:</label>
          <div className="checkbox-group">
            {TARGET_GROUPS.map((group, i) => (
              <div key={i} className="checkbox-item">
                <input
                  type="checkbox"
                  id={`target-group-${activePolicyIndex}-${i}`}
                  checked={currentPolicy.targetGroups.includes(group)}
                  onChange={() => toggleArrayItem(activePolicyIndex, null, "targetGroups", group)}
                />
                <label htmlFor={`target-group-${activePolicyIndex}-${i}`}>{group}</label>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <label className="form-label">Policy Description:</label>
          <textarea
            value={currentPolicy.policyDescription}
            onChange={(e) => updatePolicy(activePolicyIndex, "policyDescription", e.target.value)}
            className="form-textarea"
            placeholder="Enter policy description"
          />
        </div>
        
        <div>
          <label className="form-label">Policy File:</label>
          <div className="file-upload-container">
            <input
              id={`file-input-${activePolicyIndex}`}
              type="file"
              onChange={(e) => updatePolicy(activePolicyIndex, "policyFile", e.target.files[0])}
              style={{ flex: 1 }}
            />
            {currentPolicy.policyFile && (
              <button 
                type="button" 
                onClick={() => updatePolicy(activePolicyIndex, "policyFile", null)}
                className="btn-danger"
              >
                Clear
              </button>
            )}
          </div>
          {currentPolicy.policyFile && (
            <div className="file-name">
              Selected file: {typeof currentPolicy.policyFile === 'object' && 'name' in currentPolicy.policyFile ? 
                currentPolicy.policyFile.name : 'File selected'}
            </div>
          )}
        </div>
        
        <div>
          <label className="form-label">Policy Link:</label>
          <input
            type="url"
            value={currentPolicy.policyLink}
            onChange={(e) => updatePolicy(activePolicyIndex, "policyLink", e.target.value)}
            className="form-input"
            placeholder="Enter policy URL"
          />
        </div>
      </div>
    )
  }

  const renderImplementationSection = () => {
    const implementation = formData.policyInitiatives[activePolicyIndex].implementation
    
    return (
      <div className="form-section">
        <h3>Implementation & Funding</h3>
        
        <div>
          <label className="form-label">Yearly Budget:</label>
          <input
            type="number"
            value={implementation.yearlyBudget}
            onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "yearlyBudget", e.target.value)}
            className="form-input"
            placeholder="Enter yearly budget amount"
          />
        </div>
        
        <div>
          <label className="form-label">Budget Currency:</label>
          <select
            value={implementation.budgetCurrency}
            onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "budgetCurrency", e.target.value)}
            className="form-select"
          >
            {CURRENCIES.map(currency => (
              <option key={currency} value={currency}>{currency}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="form-label">Private Sector Funding:</label>
          <div className="radio-group">
            {[true, false].map(value => (
              <div key={`private-funding-${value}`} className="checkbox-item">
                <input
                  type="radio"
                  id={`private-funding-${value ? "yes" : "no"}-${activePolicyIndex}`}
                  checked={implementation.privateSecFunding === value}
                  onChange={() => updatePolicySection(activePolicyIndex, "implementation", "privateSecFunding", value)}
                />
                <label htmlFor={`private-funding-${value ? "yes" : "no"}-${activePolicyIndex}`}>
                  {value ? "Yes" : "No"}
                </label>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <label className="form-label">Deployment Year:</label>
          <input
            type="number"
            min="1990"
            max="2030"
            value={implementation.deploymentYear}
            onChange={(e) => updatePolicySection(activePolicyIndex, "implementation", "deploymentYear", parseInt(e.target.value))}
            className="form-input"
            placeholder="Enter year policy entered into force"
          />
        </div>
      </div>
    )
  }

  const renderEvaluationSection = () => {
    const evaluation = formData.policyInitiatives[activePolicyIndex].evaluation
    
    return (
      <div className="form-section">
        <h3>Evaluation & Accountability</h3>
        
        <div>
          <label className="form-label">Is Evaluated:</label>
          <div className="radio-group">
            {[true, false].map(value => (
              <div key={`is-evaluated-${value}`} className="checkbox-item">
                <input
                  type="radio"
                  id={`is-evaluated-${value ? "yes" : "no"}-${activePolicyIndex}`}
                  checked={evaluation.isEvaluated === value}
                  onChange={() => updatePolicySection(activePolicyIndex, "evaluation", "isEvaluated", value)}
                />
                <label htmlFor={`is-evaluated-${value ? "yes" : "no"}-${activePolicyIndex}`}>
                  {value ? "Yes" : "No"}
                </label>
              </div>
            ))}
          </div>
        </div>
        
        {evaluation.isEvaluated && (
          <div>
            <label className="form-label">Evaluation Type:</label>
            <div className="radio-group">
              {["internal", "external"].map(type => (
                <div key={`eval-type-${type}`} className="checkbox-item">
                  <input
                    type="radio"
                    id={`eval-type-${type}-${activePolicyIndex}`}
                    checked={evaluation.evaluationType === type}
                    onChange={() => updatePolicySection(activePolicyIndex, "evaluation", "evaluationType", type)}
                  />
                  <label htmlFor={`eval-type-${type}-${activePolicyIndex}`}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </label>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div>
          <label className="form-label">Risk Assessment Methodology:</label>
          <div className="radio-group">
            {[true, false].map(value => (
              <div key={`risk-assessment-${value}`} className="checkbox-item">
                <input
                  type="radio"
                  id={`risk-assessment-${value ? "yes" : "no"}-${activePolicyIndex}`}
                  checked={evaluation.riskAssessment === value}
                  onChange={() => updatePolicySection(activePolicyIndex, "evaluation", "riskAssessment", value)}
                />
                <label htmlFor={`risk-assessment-${value ? "yes" : "no"}-${activePolicyIndex}`}>
                  {value ? "Yes" : "No"}
                </label>
              </div>
            ))}
          </div>
        </div>
        
        {/* Score sliders */}
        {["transparency", "explainability", "accountability"].map(metric => (
          <div key={metric}>
            <label className="form-label">
              {metric.charAt(0).toUpperCase() + metric.slice(1)} Score (0-5): {evaluation[`${metric}Score`]}
            </label>
            <input
              type="range"
              min="0"
              max="5"
              step="1"
              value={evaluation[`${metric}Score`]}
              onChange={(e) => updatePolicySection(
                activePolicyIndex, 
                "evaluation", 
                `${metric}Score`, 
                parseInt(e.target.value)
              )}
              className="score-slider"
            />
          </div>
        ))}
      </div>
    )
  }

  const renderParticipationSection = () => {
    const participation = formData.policyInitiatives[activePolicyIndex].participation
    
    return (
      <div className="form-section">
        <h3>Public Participation</h3>
        
        <div>
          <label className="form-label">Has Consultation Process:</label>
          <div className="radio-group">
            {[true, false].map(value => (
              <div key={`consultation-${value}`} className="checkbox-item">
                <input
                  type="radio"
                  id={`consultation-${value ? "yes" : "no"}-${activePolicyIndex}`}
                  checked={participation.hasConsultation === value}
                  onChange={() => updatePolicySection(activePolicyIndex, "participation", "hasConsultation", value)}
                />
                <label htmlFor={`consultation-${value ? "yes" : "no"}-${activePolicyIndex}`}>
                  {value ? "Yes" : "No"}
                </label>
              </div>
            ))}
          </div>
        </div>
        
        {participation.hasConsultation && (
          <>
            <div>
              <label className="form-label">Consultation Start Date:</label>
              <input
                type="date"
                value={participation.consultationStartDate}
                onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "consultationStartDate", e.target.value)}
                className="form-input"
              />
            </div>
            
            <div>
              <label className="form-label">Consultation End Date:</label>
              <input
                type="date"
                value={participation.consultationEndDate}
                onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "consultationEndDate", e.target.value)}
                className="form-input"
              />
            </div>
            
            <div>
              <label className="form-label">Public Comments Availability:</label>
              <div className="radio-group">
                {[true, false].map(value => (
                  <div key={`comments-${value}`} className="checkbox-item">
                    <input
                      type="radio"
                      id={`comments-${value ? "public" : "private"}-${activePolicyIndex}`}
                      checked={participation.commentsPublic === value}
                      onChange={() => updatePolicySection(activePolicyIndex, "participation", "commentsPublic", value)}
                    />
                    <label htmlFor={`comments-${value ? "public" : "private"}-${activePolicyIndex}`}>
                      {value ? "Yes" : "No"}
                    </label>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
        
        <div>
          <label className="form-label">Stakeholder Engagement Score (0-5): {participation.stakeholderScore}</label>
          <input
            type="range"
            min="0"
            max="5"
            step="1"
            value={participation.stakeholderScore}
            onChange={(e) => updatePolicySection(activePolicyIndex, "participation", "stakeholderScore", parseInt(e.target.value))}
            className="score-slider"
          />
        </div>
      </div>
    )
  }

  const renderAlignmentSection = () => {
    const alignment = formData.policyInitiatives[activePolicyIndex].alignment
    
    return (
      <div className="form-section">
        <h3>Principles Alignment</h3>
        
        <div>
          <label className="form-label">Principles Coverage:</label>
          <div className="checkbox-group">
            {PRINCIPLES.map((principle, i) => (
              <div key={i} className="checkbox-item">
                <input
                  type="checkbox"
                  id={`ai-principle-${activePolicyIndex}-${i}`}
                  checked={alignment.aiPrinciples.includes(principle)}
                  onChange={() => toggleArrayItem(activePolicyIndex, "alignment", "aiPrinciples", principle)}
                />
                <label htmlFor={`ai-principle-${activePolicyIndex}-${i}`}>{principle}</label>
              </div>
            ))}
          </div>
        </div>
        
        {/* Boolean fields */}
        {[
          { id: "humanRightsAlignment", label: "Human Rights Alignment" },
          { id: "environmentalConsiderations", label: "Environmental Considerations" },
          { id: "internationalCooperation", label: "International Cooperation" }
        ].map(field => (
          <div key={field.id}>
            <label className="form-label">{field.label}:</label>
            <div className="radio-group">
              {[true, false].map(value => (
                <div key={`${field.id}-${value}`} className="checkbox-item">
                  <input
                    type="radio"
                    id={`${field.id}-${value ? "yes" : "no"}-${activePolicyIndex}`}
                    checked={alignment[field.id] === value}
                    onChange={() => updatePolicySection(activePolicyIndex, "alignment", field.id, value)}
                  />
                  <label htmlFor={`${field.id}-${value ? "yes" : "no"}-${activePolicyIndex}`}>
                    {value ? "Yes" : "No"}
                  </label>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderPolicyTabContent = () => {
    switch (policyTabSelected) {
      case "basic": return renderBasicPolicyInfo();
      case "implementation": return renderImplementationSection();
      case "eval": return renderEvaluationSection();
      case "participation": return renderParticipationSection();
      case "alignment": return renderAlignmentSection();
      default: return <p>Please select a valid tab.</p>;
    }
  }

  const renderFormButtons = () => (
    <div className="form-buttons">
      <button 
        type="submit" 
        className="btn-primary"
        disabled={loading}
      >
        {loading ? "Submitting..." : "Submit Data"}
      </button>
      <button 
        type="button" 
        onClick={resetForm} 
        className="btn-secondary"
        disabled={loading}
      >
        Reset Form
      </button>
    </div>
  )

  return (
    <div className="form-container">
      <h2>Policy Database - Country Submission Form</h2>
      <p className="form-description">
        Submit information about policy and regulatory frameworks in your country.
        You can add up to 10 different policy initiatives.
      </p>
      
      {renderMainTabs()}
      
      {formError && (
        <div className="error-message">
          {formError}
        </div>
      )}
      
      {formSuccess && (
        <div className="success-message">
          {formSuccess}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        {activeTab === "general" ? (
          renderCountrySection()
        ) : (
          <div className="policy-section">
            {renderPolicyNavigation()}
            {renderPolicyDetailTabs()}
            {renderPolicyTabContent()}
          </div>
        )}
        
        {renderFormButtons()}
      </form>
    </div>
  )
}