'use client'
import { useState } from "react"
import { 
  policyType, 
  targetGroupOptions, 
  PrinciplesOptions,
  getInitialFormData,
  updateHandlers,
  handleSubmission
} from "./formLogic"
import "./styles.css"

export default function PolicySubmissionForm() {
  const [formData, setFormData] = useState(getInitialFormData())
  const [submitted, setSubmitted] = useState(false)
  const [activeTab, setActiveTab] = useState("general")
  const [activePolicyIndex, setActivePolicyIndex] = useState(0)
  const [policyTabSelected, setPolicyTabSelected] = useState("basic") // 'basic', 'implementation', 'eval', 'participation', 'alignment'

  // Form reset handler
  const resetForm = () => {
    setSubmitted(true)
    alert("Submission successful! The country's AI policy data has been recorded.")
    
    // Reset form
    setFormData(getInitialFormData())
    setActiveTab("general")
    setActivePolicyIndex(0)
    setPolicyTabSelected("basic")
  }

  // Form submit handler
  const onSubmit = async (e) => {
    const success = await handleSubmission(e, formData, resetForm)
    if (success) {
      resetForm()
    }
  }

  // Main tab navigation
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

  // Policy detail tabs (shown when a policy is selected)
  const renderPolicyDetailTabs = () => (
    <div className="policy-detail-tabs">
      <div 
        className={`policy-tab ${policyTabSelected === "basic" ? "active" : ""}`}
        onClick={() => setPolicyTabSelected("basic")}
      >
        Basic Info
      </div>
      <div 
        className={`policy-tab ${policyTabSelected === "implementation" ? "active" : ""}`}
        onClick={() => setPolicyTabSelected("implementation")}
      >
        Implementation
      </div>
      <div 
        className={`policy-tab ${policyTabSelected === "eval" ? "active" : ""}`}
        onClick={() => setPolicyTabSelected("eval")}
      >
        Evaluation
      </div>
      <div 
        className={`policy-tab ${policyTabSelected === "participation" ? "active" : ""}`}
        onClick={() => setPolicyTabSelected("participation")}
      >
        Participation
      </div>
      <div 
        className={`policy-tab ${policyTabSelected === "alignment" ? "active" : ""}`}
        onClick={() => setPolicyTabSelected("alignment")}
      >
        Alignment
      </div>
    </div>
  )

  // Form sections
  const renderCountrySection = () => (
    <div className="form-section">
      <h3>Country Information</h3>
      <div>
        <label className="form-label">Country Name:</label>
        <input
          type="text"
          value={formData.country}
          onChange={(e) => updateHandlers.handleCountryChange(setFormData, e.target.value)}
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
              setActivePolicyIndex(prev => Math.max(0, prev - 1))
              setPolicyTabSelected("basic") // Reset to basic info tab when changing policies
            }}
          >
            Previous Policy
          </button>
          <button 
            type="button" 
            className="policy-nav-button"
            disabled={activePolicyIndex === 9}
            onClick={() => {
              setActivePolicyIndex(prev => Math.min(9, prev + 1))
              setPolicyTabSelected("basic") // Reset to basic info tab when changing policies
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
                setPolicyTabSelected("basic") // Reset to basic info tab when changing policies
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
            onChange={(e) => updateHandlers.handlePolicyChange(formData, setFormData, activePolicyIndex, "policyArea", e.target.value)}
            className="form-select"
          >
            <option value="">Select Policy type</option>
            {policyType.map((area, i) => (
              <option key={i} value={area}>{area}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="form-label">Policy Name:</label>
          <input
            type="text"
            value={currentPolicy.policyName}
            onChange={(e) => updateHandlers.handlePolicyChange(formData, setFormData, activePolicyIndex, "policyName", e.target.value)}
            className="form-input"
            placeholder="Enter policy name"
          />
        </div>
        
        <div>
          <label className="form-label">Policy ID:</label>
          <input
            type="text"
            value={currentPolicy.policyId}
            onChange={(e) => updateHandlers.handlePolicyChange(formData, setFormData, activePolicyIndex, "policyId", e.target.value)}
            className="form-input"
            placeholder="Enter policy ID"
          />
        </div>
        
        <div>
          <label className="form-label">Target Groups:</label>
          <div className="checkbox-group">
            {targetGroupOptions.map((group, i) => (
              <div key={i} className="checkbox-item">
                <input
                  type="checkbox"
                  id={`target-group-${activePolicyIndex}-${i}`}
                  checked={currentPolicy.targetGroups.includes(group)}
                  onChange={() => updateHandlers.handleTargetGroupToggle(formData, setFormData, activePolicyIndex, group)}
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
            onChange={(e) => updateHandlers.handlePolicyChange(formData, setFormData, activePolicyIndex, "policyDescription", e.target.value)}
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
              onChange={(e) => updateHandlers.handlePolicyChange(formData, setFormData, activePolicyIndex, "policyFile", e.target.files[0])}
              style={{ flex: 1 }}
            />
            {currentPolicy.policyFile && (
              <button 
                type="button" 
                onClick={() => updateHandlers.handleFileReset(formData, setFormData, activePolicyIndex)}
                className="btn-danger"
              >
                Clear
              </button>
            )}
          </div>
          {currentPolicy.policyFile && (
            <div className="file-name">
              Selected file: {currentPolicy.policyFile.name}
            </div>
          )}
        </div>
        
        <div>
          <label className="form-label">Policy Link:</label>
          <input
            type="url"
            value={currentPolicy.policyLink}
            onChange={(e) => updateHandlers.handlePolicyChange(formData, setFormData, activePolicyIndex, "policyLink", e.target.value)}
            className="form-input"
            placeholder="Enter policy URL"
          />
        </div>
      </div>
    )
  }

  const renderImplementationSection = () => {
    const currentPolicy = formData.policyInitiatives[activePolicyIndex]
    const implementation = currentPolicy.implementation
    
    return (
      <div className="form-section">
        <h3>Implementation & Funding</h3>
        
        <div>
          <label className="form-label">Yearly Budget:</label>
          <input
            type="number"
            value={implementation.yearlyBudget}
            onChange={(e) => updateHandlers.handleImplementationChange(formData, setFormData, activePolicyIndex, "yearlyBudget", e.target.value)}
            className="form-input"
            placeholder="Enter yearly budget amount"
          />
        </div>
        
        <div>
          <label className="form-label">Budget Currency:</label>
          <select
            value={implementation.budgetCurrency}
            onChange={(e) => updateHandlers.handleImplementationChange(formData, setFormData, activePolicyIndex, "budgetCurrency", e.target.value)}
            className="form-select"
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
          <label className="form-label">Private Sector Funding:</label>
          <div className="radio-group">
            <div className="checkbox-item">
              <input
                type="radio"
                id={`private-funding-yes-${activePolicyIndex}`}
                checked={implementation.privateSecFunding === true}
                onChange={() => updateHandlers.handleImplementationChange(formData, setFormData, activePolicyIndex, "privateSecFunding", true)}
              />
              <label htmlFor={`private-funding-yes-${activePolicyIndex}`}>Yes</label>
            </div>
            <div className="checkbox-item">
              <input
                type="radio"
                id={`private-funding-no-${activePolicyIndex}`}
                checked={implementation.privateSecFunding === false}
                onChange={() => updateHandlers.handleImplementationChange(formData, setFormData, activePolicyIndex, "privateSecFunding", false)}
              />
              <label htmlFor={`private-funding-no-${activePolicyIndex}`}>No</label>
            </div>
          </div>
        </div>
        
        <div>
          <label className="form-label">Deployment Year:</label>
          <input
            type="number"
            min="1990"
            max="2030"
            value={implementation.deploymentYear}
            onChange={(e) => updateHandlers.handleImplementationChange(formData, setFormData, activePolicyIndex, "deploymentYear", e.target.value)}
            className="form-input"
            placeholder="Enter year policy entered into force"
          />
        </div>
      </div>
    )
  }

  const renderEvaluationSection = () => {
    const currentPolicy = formData.policyInitiatives[activePolicyIndex]
    const evaluation = currentPolicy.evaluation
    
    return (
      <div className="form-section">
        <h3>Evaluation & Accountability</h3>
        
        <div>
          <label className="form-label">Is Evaluated:</label>
          <div className="radio-group">
            <div className="checkbox-item">
              <input
                type="radio"
                id={`is-evaluated-yes-${activePolicyIndex}`}
                checked={evaluation.isEvaluated === true}
                onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, activePolicyIndex, "isEvaluated", true)}
              />
              <label htmlFor={`is-evaluated-yes-${activePolicyIndex}`}>Yes</label>
            </div>
            <div className="checkbox-item">
              <input
                type="radio"
                id={`is-evaluated-no-${activePolicyIndex}`}
                checked={evaluation.isEvaluated === false}
                onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, activePolicyIndex, "isEvaluated", false)}
              />
              <label htmlFor={`is-evaluated-no-${activePolicyIndex}`}>No</label>
            </div>
          </div>
        </div>
        
        {evaluation.isEvaluated && (
          <div>
            <label className="form-label">Evaluation Type:</label>
            <div className="radio-group">
              <div className="checkbox-item">
                <input
                  type="radio"
                  id={`eval-type-internal-${activePolicyIndex}`}
                  checked={evaluation.evaluationType === "internal"}
                  onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, activePolicyIndex, "evaluationType", "internal")}
                />
                <label htmlFor={`eval-type-internal-${activePolicyIndex}`}>Internal</label>
              </div>
              <div className="checkbox-item">
                <input
                  type="radio"
                  id={`eval-type-external-${activePolicyIndex}`}
                  checked={evaluation.evaluationType === "external"}
                  onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, activePolicyIndex, "evaluationType", "external")}
                />
                <label htmlFor={`eval-type-external-${activePolicyIndex}`}>External</label>
              </div>
            </div>
          </div>
        )}
        
        <div>
          <label className="form-label">Risk Assessment Methodology:</label>
          <div className="radio-group">
            <div className="checkbox-item">
              <input
                type="radio"
                id={`risk-assessment-yes-${activePolicyIndex}`}
                checked={evaluation.riskAssessment === true}
                onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, activePolicyIndex, "riskAssessment", true)}
              />
              <label htmlFor={`risk-assessment-yes-${activePolicyIndex}`}>Yes</label>
            </div>
            <div className="checkbox-item">
              <input
                type="radio"
                id={`risk-assessment-no-${activePolicyIndex}`}
                checked={evaluation.riskAssessment === false}
                onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, activePolicyIndex, "riskAssessment", false)}
              />
              <label htmlFor={`risk-assessment-no-${activePolicyIndex}`}>No</label>
            </div>
          </div>
        </div>
        
        <div>
          <label className="form-label">Transparency Score (0-5): {evaluation.transparencyScore}</label>
          <input
            type="range"
            min="0"
            max="5"
            step="1"
            value={evaluation.transparencyScore}
            onChange={(e) => updateHandlers.handleEvaluationChange(formData, setFormData, activePolicyIndex, "transparencyScore", parseInt(e.target.value))}
            className="score-slider"
          />
        </div>
        
        <div>
          <label className="form-label">Explainability Score (0-5): {evaluation.explainabilityScore}</label>
          <input
            type="range"
            min="0"
            max="5"
            step="1"
            value={evaluation.explainabilityScore}
            onChange={(e) => updateHandlers.handleEvaluationChange(formData, setFormData, activePolicyIndex, "explainabilityScore", parseInt(e.target.value))}
            className="score-slider"
          />
        </div>
        
        <div>
          <label className="form-label">Accountability Score (0-5): {evaluation.accountabilityScore}</label>
          <input
            type="range"
            min="0"
            max="5"
            step="1"
            value={evaluation.accountabilityScore}
            onChange={(e) => updateHandlers.handleEvaluationChange(formData, setFormData, activePolicyIndex, "accountabilityScore", parseInt(e.target.value))}
            className="score-slider"
          />
        </div>
      </div>
    )
  }

  const renderParticipationSection = () => {
    const currentPolicy = formData.policyInitiatives[activePolicyIndex]
    const participation = currentPolicy.participation
    
    return (
      <div className="form-section">
        <h3>Public Participation</h3>
        
        <div>
          <label className="form-label">Has Consultation Process:</label>
          <div className="radio-group">
            <div className="checkbox-item">
              <input
                type="radio"
                id={`consultation-yes-${activePolicyIndex}`}
                checked={participation.hasConsultation === true}
                onChange={() => updateHandlers.handleParticipationChange(formData, setFormData, activePolicyIndex, "hasConsultation", true)}
              />
              <label htmlFor={`consultation-yes-${activePolicyIndex}`}>Yes</label>
            </div>
            <div className="checkbox-item">
              <input
                type="radio"
                id={`consultation-no-${activePolicyIndex}`}
                checked={participation.hasConsultation === false}
                onChange={() => updateHandlers.handleParticipationChange(formData, setFormData, activePolicyIndex, "hasConsultation", false)}
              />
              <label htmlFor={`consultation-no-${activePolicyIndex}`}>No</label>
            </div>
          </div>
        </div>
        
        {participation.hasConsultation && (
          <>
            <div>
              <label className="form-label">Consultation Start Date:</label>
              <input
                type="date"
                value={participation.consultationStartDate}
                onChange={(e) => updateHandlers.handleParticipationChange(formData, setFormData, activePolicyIndex, "consultationStartDate", e.target.value)}
                className="form-input"
              />
            </div>
            
            <div>
              <label className="form-label">Consultation End Date:</label>
              <input
                type="date"
                value={participation.consultationEndDate}
                onChange={(e) => updateHandlers.handleParticipationChange(formData, setFormData, activePolicyIndex, "consultationEndDate", e.target.value)}
                className="form-input"
              />
            </div>
            
            <div>
              <label className="form-label">Public Comments Availability:</label>
              <div className="radio-group">
                <div className="checkbox-item">
                  <input
                    type="radio"
                    id={`comments-public-${activePolicyIndex}`}
                    checked={participation.commentsPublic === true}
                    onChange={() => updateHandlers.handleParticipationChange(formData, setFormData, activePolicyIndex, "commentsPublic", true)}
                  />
                  <label htmlFor={`comments-public-${activePolicyIndex}`}>Yes</label>
                </div>
                <div className="checkbox-item">
                  <input
                    type="radio"
                    id={`comments-private-${activePolicyIndex}`}
                    checked={participation.commentsPublic === false}
                    onChange={() => updateHandlers.handleParticipationChange(formData, setFormData, activePolicyIndex, "commentsPublic", false)}
                  />
                  <label htmlFor={`comments-private-${activePolicyIndex}`}>No</label>
                </div>
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
            onChange={(e) => updateHandlers.handleParticipationChange(formData, setFormData, activePolicyIndex, "stakeholderScore", parseInt(e.target.value))}
            className="score-slider"
          />
        </div>
      </div>
    )
  }

  const renderAlignmentSection = () => {
    const currentPolicy = formData.policyInitiatives[activePolicyIndex]
    const alignment = currentPolicy.alignment
    
    return (
      <div className="form-section">
        <h3>Principles Alignment</h3>
        
        <div>
          <label className="form-label">Principles Coverage:</label>
          <div className="checkbox-group">
            {PrinciplesOptions.map((principle, i) => (
              <div key={i} className="checkbox-item">
                <input
                  type="checkbox"
                  id={`ai-principle-${activePolicyIndex}-${i}`}
                  checked={alignment.aiPrinciples.includes(principle)}
                  onChange={() => updateHandlers.handlePrincipleToggle(formData, setFormData, activePolicyIndex, principle)}
                />
                <label htmlFor={`ai-principle-${activePolicyIndex}-${i}`}>{principle}</label>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <label className="form-label">Human Rights Alignment:</label>
          <div className="radio-group">
            <div className="checkbox-item">
              <input
                // Continuing from where the code was cut off
                type="radio"
                id={`human-rights-yes-${activePolicyIndex}`}
                checked={alignment.humanRightsAlignment === true}
                onChange={() => updateHandlers.handleAlignmentChange(formData, setFormData, activePolicyIndex, "humanRightsAlignment", true)}
              />
              <label htmlFor={`human-rights-yes-${activePolicyIndex}`}>Yes</label>
            </div>
            <div className="checkbox-item">
              <input
                type="radio"
                id={`human-rights-no-${activePolicyIndex}`}
                checked={alignment.humanRightsAlignment === false}
                onChange={() => updateHandlers.handleAlignmentChange(formData, setFormData, activePolicyIndex, "humanRightsAlignment", false)}
              />
              <label htmlFor={`human-rights-no-${activePolicyIndex}`}>No</label>
            </div>
          </div>
        </div>
        
        <div>
          <label className="form-label">Environmental Considerations:</label>
          <div className="radio-group">
            <div className="checkbox-item">
              <input
                type="radio"
                id={`environmental-yes-${activePolicyIndex}`}
                checked={alignment.environmentalConsiderations === true}
                onChange={() => updateHandlers.handleAlignmentChange(formData, setFormData, activePolicyIndex, "environmentalConsiderations", true)}
              />
              <label htmlFor={`environmental-yes-${activePolicyIndex}`}>Yes</label>
            </div>
            <div className="checkbox-item">
              <input
                type="radio"
                id={`environmental-no-${activePolicyIndex}`}
                checked={alignment.environmentalConsiderations === false}
                onChange={() => updateHandlers.handleAlignmentChange(formData, setFormData, activePolicyIndex, "environmentalConsiderations", false)}
              />
              <label htmlFor={`environmental-no-${activePolicyIndex}`}>No</label>
            </div>
          </div>
        </div>
        
        <div>
          <label className="form-label">International Cooperation:</label>
          <div className="radio-group">
            <div className="checkbox-item">
              <input
                type="radio"
                id={`international-yes-${activePolicyIndex}`}
                checked={alignment.internationalCooperation === true}
                onChange={() => updateHandlers.handleAlignmentChange(formData, setFormData, activePolicyIndex, "internationalCooperation", true)}
              />
              <label htmlFor={`international-yes-${activePolicyIndex}`}>Yes</label>
            </div>
            <div className="checkbox-item">
              <input
                type="radio"
                id={`international-no-${activePolicyIndex}`}
                checked={alignment.internationalCooperation === false}
                onChange={() => updateHandlers.handleAlignmentChange(formData, setFormData, activePolicyIndex, "internationalCooperation", false)}
              />
              <label htmlFor={`international-no-${activePolicyIndex}`}>No</label>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Render the appropriate policy tab content
  const renderPolicyTabContent = () => {
    switch (policyTabSelected) {
      case "basic":
        return renderBasicPolicyInfo();
      case "implementation":
        return renderImplementationSection();
      case "eval":
        return renderEvaluationSection();
      case "participation":
        return renderParticipationSection();
      case "alignment":
        return renderAlignmentSection();
      default:
        return renderBasicPolicyInfo();
    }
  }

  return (
    <div className="form-container">
      <h2>AI Policy Database - Country Submission Form</h2>
      <p className="form-description">
        Submit information about AI policies and regulatory frameworks in your country.
        You can add up to 10 different policy initiatives.
      </p>
      
      {renderMainTabs()}
      
      <form onSubmit={onSubmit}>
        {activeTab === "general" ? (
          renderCountrySection()
        ) : (
          <div className="policy-section">
            {renderPolicyNavigation()}
            {renderPolicyDetailTabs()}
            {renderPolicyTabContent()}
          </div>
        )}
        
        <div className="form-buttons">
          <button type="submit" className="btn-primary">Submit Data</button>
          <button 
            type="button" 
            onClick={resetForm} 
            className="btn-secondary"
          >
            Reset Form
          </button>
        </div>
      </form>
    </div>
  )
}