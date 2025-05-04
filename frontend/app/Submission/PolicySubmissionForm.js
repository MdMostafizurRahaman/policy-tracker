'use client'
import { useState } from "react"

export default function PolicySubmissionForm() {
  const [country, setCountry] = useState("")
  const [formData, setFormData] = useState({
    // General country info
    countryName: "",
    
    // Policy Coverage
    policyInitiatives: Array(10).fill(null).map(() => ({
      policyArea: "",
      policyId: "",
      targetGroups: [],
      policyFile: null,
      policyLink: "",
      policyName: "",
      policyDescription: "",
    })),
    
    // Implementation & Funding
    implementation: {
      yearlyBudget: "",
      budgetCurrency: "USD",
      privateSecFunding: false,
      deploymentYear: "",
    },
    
    // Evaluation & Accountability
    evaluation: {
      isEvaluated: false,
      evaluationType: "none", // "none", "internal", "external"
      riskAssessment: false,
      transparencyScore: 0, // 0-5 scale
      explainabilityScore: 0, // 0-5 scale
      accountabilityScore: 0, // 0-5 scale
    },
    
    // Public Participation
    participation: {
      hasConsultation: false,
      consultationStartDate: "",
      consultationEndDate: "",
      publicAccessUrl: "",
    },
    
    // Strategic Alignment
    alignment: {
      aiPrinciples: [],
      covidRelatedShifts: false,
      hasStrategicTargets: false,
      strategicTargetsDeadline: "",
    }
  })
  
  const [submitted, setSubmitted] = useState(false)
  const [activeTab, setActiveTab] = useState("general")
  const [activePolicyIndex, setActivePolicyIndex] = useState(0)
  
  const policyAreaOptions = [
    "AI Safety",
    "CyberSafety",
    "Digital Education",
    "Digital Inclusion",
    "Digital Leisure",
    "(Dis)Information",
    "Digital Work",
    "Mental Health",
    "Physical Health",
    "Social Media/Gaming Regulation",
  ]
  
  const targetGroupOptions = [
    "General Public",
    "Children",
    "Youth",
    "Elderly",
    "Businesses",
    "Public Sector",
    "Education Sector",
    "Healthcare Sector",
    "Vulnerable Groups",
    "Other"
  ]
  
  const aiPrinciplesOptions = [
    "Transparency",
    "Fairness",
    "Accountability",
    "Explainability",
    "Privacy",
    "Security",
    "Human Oversight",
    "Robustness",
    "Safety",
    "Inclusivity",
    "Sustainability"
  ]

  const handleGeneralChange = (e) => {
    setCountry(e.target.value)
    setFormData({...formData, countryName: e.target.value})
  }

  const handlePolicyChange = (index, field, value) => {
    const updatedPolicyInitiatives = [...formData.policyInitiatives]
    updatedPolicyInitiatives[index] = {
      ...updatedPolicyInitiatives[index],
      [field]: value
    }
    setFormData({
      ...formData,
      policyInitiatives: updatedPolicyInitiatives
    })
  }
  
  const handleImplementationChange = (field, value) => {
    setFormData({
      ...formData,
      implementation: {
        ...formData.implementation,
        [field]: value
      }
    })
  }
  
  const handleEvaluationChange = (field, value) => {
    setFormData({
      ...formData,
      evaluation: {
        ...formData.evaluation,
        [field]: value
      }
    })
  }
  
  const handleParticipationChange = (field, value) => {
    setFormData({
      ...formData,
      participation: {
        ...formData.participation,
        [field]: value
      }
    })
  }
  
  const handleAlignmentChange = (field, value) => {
    setFormData({
      ...formData,
      alignment: {
        ...formData.alignment,
        [field]: value
      }
    })
  }
  
  const handleTargetGroupToggle = (index, group) => {
    const currentGroups = [...formData.policyInitiatives[index].targetGroups]
    const newGroups = currentGroups.includes(group)
      ? currentGroups.filter(g => g !== group)
      : [...currentGroups, group]
    
    handlePolicyChange(index, "targetGroups", newGroups)
  }
  
  const handleAIPrincipleToggle = (principle) => {
    const currentPrinciples = [...formData.alignment.aiPrinciples]
    const newPrinciples = currentPrinciples.includes(principle)
      ? currentPrinciples.filter(p => p !== principle)
      : [...currentPrinciples, principle]
    
    handleAlignmentChange("aiPrinciples", newPrinciples)
  }

  const handleFileReset = (index) => {
    handlePolicyChange(index, "policyFile", null)
    // Reset the file input element
    const fileInput = document.getElementById(`file-input-${index}`)
    if (fileInput) fileInput.value = ""
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // We need to adapt our data structure to match the expected format of the original API
    // The original form was submitting country name and policy files/links
    const formDataToSubmit = new FormData()
    
    // Add country name
    formDataToSubmit.append("country", country)
    
    // For each policy that has content, add it to the form data in the format expected by the API
    formData.policyInitiatives.forEach((policy, index) => {
      // Only include policies that have some data
      if (policy.policyFile || policy.policyLink || policy.policyName) {
        if (policy.policyFile) {
          formDataToSubmit.append(`policy_${index + 1}_file`, policy.policyFile)
        }
        
        // If we have a link, add it as text
        if (policy.policyLink) {
          formDataToSubmit.append(`policy_${index + 1}_text`, policy.policyLink)
        } 
        // If no link but we have a name/description, use that
        else if (policy.policyName || policy.policyDescription) {
          const policyText = `${policy.policyName}${policy.policyDescription ? ': ' + policy.policyDescription : ''}`
          formDataToSubmit.append(`policy_${index + 1}_text`, policyText)
        }
      }
    })
    
    // Also add the structured SYNC data as a JSON string in a separate field
    // This way we maintain backward compatibility with the original API
    // while also sending our enhanced data
    formDataToSubmit.append("sync_framework_data", JSON.stringify({
      countryName: country,
      policyInitiatives: formData.policyInitiatives.map(p => ({
        ...p,
        policyFile: p.policyFile ? p.policyFile.name : null // Don't send the file object in JSON
      })),
      implementation: formData.implementation,
      evaluation: formData.evaluation,
      participation: formData.participation,
      alignment: formData.alignment
    }))
    
    try {
      const response = await fetch("http://localhost:8000/api/submit-policy", {
        method: "POST",
        body: formDataToSubmit,
      })
      
      if (!response.ok) {
        // Enhanced error handling
        const errorText = await response.text().catch(() => "Unknown error");
        console.error("Server response:", errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      setSubmitted(true)
      alert("Submission successful! The country's AI policy data has been recorded.")
      
      // Reset form
      setCountry("")
      setFormData({
        // Reset form data
        countryName: "",
        policyInitiatives: Array(10).fill(null).map(() => ({
          policyArea: "",
          policyId: "",
          targetGroups: [],
          policyFile: null,
          policyLink: "",
          policyName: "",
          policyDescription: "",
        })),
        implementation: {
          yearlyBudget: "",
          budgetCurrency: "USD",
          privateSecFunding: false,
          deploymentYear: "",
        },
        evaluation: {
          isEvaluated: false,
          evaluationType: "none",
          riskAssessment: false,
          transparencyScore: 0,
          explainabilityScore: 0,
          accountabilityScore: 0,
        },
        participation: {
          hasConsultation: false,
          consultationStartDate: "",
          consultationEndDate: "",
          publicAccessUrl: "",
        },
        alignment: {
          aiPrinciples: [],
          covidRelatedShifts: false,
          hasStrategicTargets: false,
          strategicTargetsDeadline: "",
        }
      })
      setActiveTab("general")
      setActivePolicyIndex(0)
    } catch (error) {
      console.error("Failed to submit:", error)
      alert(`Submission failed: ${error.message}. Please check console for details.`)
    }
  }

  // Styles
  const styles = {
    container: {
      maxWidth: "800px",
      margin: "0 auto",
      padding: "20px",
      border: "1px solid #ccc",
      borderRadius: "8px",
      background: "#f9f9f9"
    },
    header: {
      textAlign: "center",
      marginBottom: "20px",
      color: "#333"
    },
    tabContainer: {
      display: "flex",
      marginBottom: "20px",
      borderBottom: "1px solid #ddd"
    },
    tab: {
      padding: "10px 15px",
      cursor: "pointer",
      borderBottom: "2px solid transparent",
      transition: "all 0.3s"
    },
    activeTab: {
      borderBottom: "2px solid #007BFF",
      fontWeight: "bold"
    },
    formSection: {
      marginBottom: "20px"
    },
    label: {
      fontWeight: "bold",
      display: "block",
      marginBottom: "5px"
    },
    input: {
      width: "100%",
      padding: "8px",
      marginBottom: "10px",
      borderRadius: "4px",
      border: "1px solid #ccc"
    },
    select: {
      width: "100%",
      padding: "8px",
      marginBottom: "10px",
      borderRadius: "4px",
      border: "1px solid #ccc"
    },
    radioGroup: {
      display: "flex",
      gap: "15px",
      marginBottom: "10px"
    },
    checkboxGroup: {
      display: "flex",
      flexWrap: "wrap",
      gap: "10px",
      marginBottom: "15px"
    },
    checkbox: {
      display: "flex",
      alignItems: "center",
      gap: "5px",
      marginBottom: "5px"
    },
    button: {
      padding: "10px 20px",
      background: "#007BFF",
      color: "#FFF",
      border: "none",
      borderRadius: "4px",
      cursor: "pointer",
      fontSize: "16px",
      width: "100%"
    },
    secondaryButton: {
      padding: "8px 15px",
      background: "#6c757d",
      color: "#FFF",
      border: "none",
      borderRadius: "4px",
      cursor: "pointer",
      fontSize: "14px"
    },
    clearButton: {
      padding: "5px 10px",
      background: "#dc3545",
      color: "#fff",
      border: "none",
      borderRadius: "4px",
      cursor: "pointer"
    },
    policyNav: {
      display: "flex",
      justifyContent: "space-between",
      marginBottom: "15px"
    },
    policyNavButton: {
      padding: "5px 10px",
      background: "#007BFF",
      color: "#FFF",
      border: "none",
      borderRadius: "4px",
      cursor: "pointer"
    },
    policyIndicator: {
      display: "flex",
      justifyContent: "center",
      gap: "5px",
      marginBottom: "15px"
    },
    policyDot: {
      width: "10px",
      height: "10px",
      borderRadius: "50%",
      background: "#ccc"
    },
    activePolicyDot: {
      background: "#007BFF"
    },
    scoreSlider: {
      width: "100%",
      marginBottom: "10px"
    },
    sliderValue: {
      textAlign: "center",
      marginBottom: "15px"
    }
  }

  // Tab navigation
  const renderTabs = () => (
    <div style={styles.tabContainer}>
      <div 
        style={{...styles.tab, ...(activeTab === "general" ? styles.activeTab : {})}}
        onClick={() => setActiveTab("general")}
      >
        General
      </div>
      <div 
        style={{...styles.tab, ...(activeTab === "policy" ? styles.activeTab : {})}}
        onClick={() => setActiveTab("policy")}
      >
        Policy Coverage
      </div>
      <div 
        style={{...styles.tab, ...(activeTab === "implementation" ? styles.activeTab : {})}}
        onClick={() => setActiveTab("implementation")}
      >
        Implementation
      </div>
      <div 
        style={{...styles.tab, ...(activeTab === "evaluation" ? styles.activeTab : {})}}
        onClick={() => setActiveTab("evaluation")}
      >
        Evaluation
      </div>
      <div 
        style={{...styles.tab, ...(activeTab === "participation" ? styles.activeTab : {})}}
        onClick={() => setActiveTab("participation")}
      >
        Participation
      </div>
      <div 
        style={{...styles.tab, ...(activeTab === "alignment" ? styles.activeTab : {})}}
        onClick={() => setActiveTab("alignment")}
      >
        Alignment
      </div>
    </div>
  )

  // Form sections
  const renderGeneralSection = () => (
    <div style={styles.formSection}>
      <h3>Country Information</h3>
      <div>
        <label style={styles.label}>Country Name:</label>
        <input
          type="text"
          value={country}
          onChange={handleGeneralChange}
          required
          style={styles.input}
          placeholder="Enter country name"
        />
      </div>
    </div>
  )

  const renderPolicySection = () => {
    const currentPolicy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div style={styles.formSection}>
        <div style={styles.policyNav}>
          <button 
            type="button" 
            style={styles.policyNavButton}
            disabled={activePolicyIndex === 0}
            onClick={() => setActivePolicyIndex(prev => Math.max(0, prev - 1))}
          >
            Previous Policy
          </button>
          <button 
            type="button" 
            style={styles.policyNavButton}
            disabled={activePolicyIndex === 9}
            onClick={() => setActivePolicyIndex(prev => Math.min(9, prev + 1))}
          >
            Next Policy
          </button>
        </div>
        
        <div style={styles.policyIndicator}>
          {Array(10).fill(null).map((_, i) => (
            <div 
              key={i}
              style={{
                ...styles.policyDot,
                ...(i === activePolicyIndex ? styles.activePolicyDot : {})
              }}
              onClick={() => setActivePolicyIndex(i)}
            />
          ))}
        </div>
        
        <h3>Policy {activePolicyIndex + 1}</h3>
        
        <div>
          <label style={styles.label}>Policy Name:</label>
          <input
            type="text"
            value={currentPolicy.policyName || ""}
            onChange={(e) => handlePolicyChange(activePolicyIndex, "policyName", e.target.value)}
            style={styles.input}
            placeholder="Enter policy name"
          />
        </div>
        
        <div>
          <label style={styles.label}>Policy ID:</label>
          <input
            type="text"
            value={currentPolicy.policyId || ""}
            onChange={(e) => handlePolicyChange(activePolicyIndex, "policyId", e.target.value)}
            style={styles.input}
            placeholder="Enter policy ID"
          />
        </div>
        
        <div>
          <label style={styles.label}>Policy Area:</label>
          <select
            value={currentPolicy.policyArea || ""}
            onChange={(e) => handlePolicyChange(activePolicyIndex, "policyArea", e.target.value)}
            style={styles.select}
          >
            <option value="">Select Policy Area</option>
            {policyAreaOptions.map((area, i) => (
              <option key={i} value={area}>{area}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label style={styles.label}>Target Groups:</label>
          <div style={styles.checkboxGroup}>
            {targetGroupOptions.map((group, i) => (
              <div key={i} style={styles.checkbox}>
                <input
                  type="checkbox"
                  id={`target-group-${activePolicyIndex}-${i}`}
                  checked={currentPolicy.targetGroups?.includes(group) || false}
                  onChange={() => handleTargetGroupToggle(activePolicyIndex, group)}
                />
                <label htmlFor={`target-group-${activePolicyIndex}-${i}`}>{group}</label>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <label style={styles.label}>Policy Description:</label>
          <textarea
            value={currentPolicy.policyDescription || ""}
            onChange={(e) => handlePolicyChange(activePolicyIndex, "policyDescription", e.target.value)}
            style={{...styles.input, minHeight: "100px"}}
            placeholder="Enter policy description"
          />
        </div>
        
        <div>
          <label style={styles.label}>Policy File:</label>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <input
              id={`file-input-${activePolicyIndex}`}
              type="file"
              onChange={(e) => handlePolicyChange(activePolicyIndex, "policyFile", e.target.files[0])}
              style={{ flex: 1 }}
            />
            {currentPolicy.policyFile && (
              <button 
                type="button" 
                onClick={() => handleFileReset(activePolicyIndex)}
                style={styles.clearButton}
              >
                Clear
              </button>
            )}
          </div>
          {currentPolicy.policyFile && (
            <div style={{ marginTop: "5px", fontSize: "14px", color: "green" }}>
              Selected file: {currentPolicy.policyFile.name}
            </div>
          )}
        </div>
        
        <div>
          <label style={styles.label}>Policy Link:</label>
          <input
            type="url"
            value={currentPolicy.policyLink || ""}
            onChange={(e) => handlePolicyChange(activePolicyIndex, "policyLink", e.target.value)}
            style={styles.input}
            placeholder="Enter policy URL"
          />
        </div>
      </div>
    )
  }

  const renderImplementationSection = () => (
    <div style={styles.formSection}>
      <h3>Implementation & Funding</h3>
      
      <div>
        <label style={styles.label}>Yearly Budget:</label>
        <input
          type="number"
          value={formData.implementation.yearlyBudget}
          onChange={(e) => handleImplementationChange("yearlyBudget", e.target.value)}
          style={styles.input}
          placeholder="Enter yearly budget amount"
        />
      </div>
      
      <div>
        <label style={styles.label}>Budget Currency:</label>
        <select
          value={formData.implementation.budgetCurrency}
          onChange={(e) => handleImplementationChange("budgetCurrency", e.target.value)}
          style={styles.select}
        >
          <option value="USD">USD</option>
          <option value="EUR">EUR</option>
          <option value="GBP">GBP</option>
          <option value="JPY">JPY</option>
          <option value="CNY">CNY</option>
          <option value="Local">Local Currency</option>
        </select>
      </div>
      
      <div>
        <label style={styles.label}>Private Sector Funding:</label>
        <div style={styles.radioGroup}>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="private-funding-yes"
              checked={formData.implementation.privateSecFunding === true}
              onChange={() => handleImplementationChange("privateSecFunding", true)}
            />
            <label htmlFor="private-funding-yes">Yes</label>
          </div>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="private-funding-no"
              checked={formData.implementation.privateSecFunding === false}
              onChange={() => handleImplementationChange("privateSecFunding", false)}
            />
            <label htmlFor="private-funding-no">No</label>
          </div>
        </div>
      </div>
      
      <div>
        <label style={styles.label}>Deployment Year:</label>
        <input
          type="number"
          min="1990"
          max="2030"
          value={formData.implementation.deploymentYear}
          onChange={(e) => handleImplementationChange("deploymentYear", e.target.value)}
          style={styles.input}
          placeholder="Enter year policies entered into force"
        />
      </div>
    </div>
  )

  const renderEvaluationSection = () => (
    <div style={styles.formSection}>
      <h3>Evaluation & Accountability</h3>
      
      <div>
        <label style={styles.label}>Is Evaluated:</label>
        <div style={styles.radioGroup}>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="is-evaluated-yes"
              checked={formData.evaluation.isEvaluated === true}
              onChange={() => handleEvaluationChange("isEvaluated", true)}
            />
            <label htmlFor="is-evaluated-yes">Yes</label>
          </div>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="is-evaluated-no"
              checked={formData.evaluation.isEvaluated === false}
              onChange={() => handleEvaluationChange("isEvaluated", false)}
            />
            <label htmlFor="is-evaluated-no">No</label>
          </div>
        </div>
      </div>
      
      {formData.evaluation.isEvaluated && (
        <div>
          <label style={styles.label}>Evaluation Type:</label>
          <div style={styles.radioGroup}>
            <div style={styles.checkbox}>
              <input
                type="radio"
                id="eval-type-internal"
                checked={formData.evaluation.evaluationType === "internal"}
                onChange={() => handleEvaluationChange("evaluationType", "internal")}
              />
              <label htmlFor="eval-type-internal">Internal</label>
            </div>
            <div style={styles.checkbox}>
              <input
                type="radio"
                id="eval-type-external"
                checked={formData.evaluation.evaluationType === "external"}
                onChange={() => handleEvaluationChange("evaluationType", "external")}
              />
              <label htmlFor="eval-type-external">External</label>
            </div>
          </div>
        </div>
      )}
      
      <div>
        <label style={styles.label}>Risk Assessment Methodology:</label>
        <div style={styles.radioGroup}>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="risk-assessment-yes"
              checked={formData.evaluation.riskAssessment === true}
              onChange={() => handleEvaluationChange("riskAssessment", true)}
            />
            <label htmlFor="risk-assessment-yes">Yes</label>
          </div>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="risk-assessment-no"
              checked={formData.evaluation.riskAssessment === false}
              onChange={() => handleEvaluationChange("riskAssessment", false)}
            />
            <label htmlFor="risk-assessment-no">No</label>
          </div>
        </div>
      </div>
      
      <div>
        <label style={styles.label}>Transparency Score (0-5): {formData.evaluation.transparencyScore}</label>
        <input
          type="range"
          min="0"
          max="5"
          step="1"
          value={formData.evaluation.transparencyScore}
          onChange={(e) => handleEvaluationChange("transparencyScore", parseInt(e.target.value))}
          style={styles.scoreSlider}
        />
      </div>
      
      <div>
        <label style={styles.label}>Explainability Score (0-5): {formData.evaluation.explainabilityScore}</label>
        <input
          type="range"
          min="0"
          max="5"
          step="1"
          value={formData.evaluation.explainabilityScore}
          onChange={(e) => handleEvaluationChange("explainabilityScore", parseInt(e.target.value))}
          style={styles.scoreSlider}
        />
      </div>
      
      <div>
        <label style={styles.label}>Accountability Score (0-5): {formData.evaluation.accountabilityScore}</label>
        <input
          type="range"
          min="0"
          max="5"
          step="1"
          value={formData.evaluation.accountabilityScore}
          onChange={(e) => handleEvaluationChange("accountabilityScore", parseInt(e.target.value))}
          style={styles.scoreSlider}
        />
      </div>
    </div>
  )

  const renderParticipationSection = () => (
    <div style={styles.formSection}>
      <h3>Public Participation</h3>
      
      <div>
        <label style={styles.label}>Has Consultation Process:</label>
        <div style={styles.radioGroup}>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="consultation-yes"
              checked={formData.participation.hasConsultation === true}
              onChange={() => handleParticipationChange("hasConsultation", true)}
            />
            <label htmlFor="consultation-yes">Yes</label>
          </div>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="consultation-no"
              checked={formData.participation.hasConsultation === false}
              onChange={() => handleParticipationChange("hasConsultation", false)}
            />
            <label htmlFor="consultation-no">No</label>
          </div>
        </div>
      </div>
      
      {formData.participation.hasConsultation && (
        <>
          <div>
            <label style={styles.label}>Consultation Start Date:</label>
            <input
              type="date"
              value={formData.participation.consultationStartDate}
              onChange={(e) => handleParticipationChange("consultationStartDate", e.target.value)}
              style={styles.input}
            />
          </div>
          
          <div>
            <label style={styles.label}>Consultation End Date:</label>
            <input
              type="date"
              value={formData.participation.consultationEndDate}
              onChange={(e) => handleParticipationChange("consultationEndDate", e.target.value)}
              style={styles.input}
            />
          </div>
        </>
      )}
      
      <div>
        <label style={styles.label}>Public Access URL:</label>
        <input
          type="url"
          value={formData.participation.publicAccessUrl}
          onChange={(e) => handleParticipationChange("publicAccessUrl", e.target.value)}
          style={styles.input}
          placeholder="Enter URL for public access"
        />
      </div>
    </div>
  )

  const renderAlignmentSection = () => (
    <div style={styles.formSection}>
      <h3>Strategic Alignment</h3>
      
      <div>
        <label style={styles.label}>AI Principles Addressed:</label>
        <div style={styles.checkboxGroup}>
          {aiPrinciplesOptions.map((principle, i) => (
            <div key={i} style={styles.checkbox}>
              <input
                type="checkbox"
                id={`ai-principle-${i}`}
                checked={formData.alignment.aiPrinciples.includes(principle)}
                onChange={() => handleAIPrincipleToggle(principle)}
              />
              <label htmlFor={`ai-principle-${i}`}>{principle}</label>
            </div>
          ))}
        </div>
      </div>
      
      <div>
        <label style={styles.label}>COVID-19 Related Shifts:</label>
        <div style={styles.radioGroup}>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="covid-shifts-yes"
              checked={formData.alignment.covidRelatedShifts === true}
              onChange={() => handleAlignmentChange("covidRelatedShifts", true)}
            />
            <label htmlFor="covid-shifts-yes">Yes</label>
          </div>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="covid-shifts-no"
              checked={formData.alignment.covidRelatedShifts === false}
              onChange={() => handleAlignmentChange("covidRelatedShifts", false)}
            />
            <label htmlFor="covid-shifts-no">No</label>
          </div>
        </div>
      </div>
      <div>
        <label style={styles.label}>Has Strategic Targets:</label>
        <div style={styles.radioGroup}>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="strategic-targets-yes"
              checked={formData.alignment.hasStrategicTargets === true}
              onChange={() => handleAlignmentChange("hasStrategicTargets", true)}
            />
            <label htmlFor="strategic-targets-yes">Yes</label>
          </div>
          <div style={styles.checkbox}>
            <input
              type="radio"
              id="strategic-targets-no"
              checked={formData.alignment.hasStrategicTargets === false}
              onChange={() => handleAlignmentChange("hasStrategicTargets", false)}
            />
            <label htmlFor="strategic-targets-no">No</label>
          </div>
        </div>
      </div>
      
      {formData.alignment.hasStrategicTargets && (
        <div>
          <label style={styles.label}>Strategic Targets Deadline:</label>
          <input
            type="date"
            value={formData.alignment.strategicTargetsDeadline}
            onChange={(e) => handleAlignmentChange("strategicTargetsDeadline", e.target.value)}
            style={styles.input}
          />
        </div>
      )}
    </div>
  )

  // Render active tab content
  const renderActiveTabContent = () => {
    switch (activeTab) {
      case "general":
        return renderGeneralSection();
      case "policy":
        return renderPolicySection();
      case "implementation":
        return renderImplementationSection();
      case "evaluation":
        return renderEvaluationSection();
      case "participation":
        return renderParticipationSection();
      case "alignment":
        return renderAlignmentSection();
      default:
        return renderGeneralSection();
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2>Global AI Policies Submission Form</h2>
        <p>Submit AI policies and regulations from your country</p>
      </div>
      
      <form onSubmit={handleSubmit}>
        {renderTabs()}
        {renderActiveTabContent()}
        
        <div style={{ marginTop: "20px" }}>
          <button type="submit" style={styles.button}>
            Submit Policy Data
          </button>
        </div>
      </form>
      
      {submitted && (
        <div style={{ marginTop: "20px", padding: "10px", background: "#d4edda", color: "#155724", borderRadius: "4px" }}>
          Submission successful! The country's AI policy data has been recorded.
        </div>
      )}
    </div>
  )
}