'use client'
import { useState } from "react"
import { 
  policyAreaOptions, 
  targetGroupOptions, 
  aiPrinciplesOptions,
  getInitialFormData,
  updateHandlers,
  handleSubmission
} from "./formLogic"
import "./styles.css"

export default function PolicySubmissionForm() {
  const [country, setCountry] = useState("")
  const [formData, setFormData] = useState(getInitialFormData())
  const [submitted, setSubmitted] = useState(false)
  const [activeTab, setActiveTab] = useState("general")
  const [activePolicyIndex, setActivePolicyIndex] = useState(0)

  // Form reset handler
  const resetForm = () => {
    setSubmitted(true)
    alert("Submission successful! The country's AI policy data has been recorded.")
    
    // Reset form
    setCountry("")
    setFormData(getInitialFormData())
    setActiveTab("general")
    setActivePolicyIndex(0)
  }

  // Form submit handler
  const onSubmit = async (e) => {
    const success = await handleSubmission(e, country, formData, resetForm)
    if (success) {
      resetForm()
    }
  }

  // Tab navigation
  const renderTabs = () => (
    <div className="tab-container">
      <div 
        className={`tab ${activeTab === "general" ? "active" : ""}`}
        onClick={() => setActiveTab("general")}
      >
        General
      </div>
      <div 
        className={`tab ${activeTab === "policy" ? "active" : ""}`}
        onClick={() => setActiveTab("policy")}
      >
        Policy Coverage
      </div>
      <div 
        className={`tab ${activeTab === "implementation" ? "active" : ""}`}
        onClick={() => setActiveTab("implementation")}
      >
        Implementation
      </div>
      <div 
        className={`tab ${activeTab === "evaluation" ? "active" : ""}`}
        onClick={() => setActiveTab("evaluation")}
      >
        Evaluation
      </div>
      <div 
        className={`tab ${activeTab === "participation" ? "active" : ""}`}
        onClick={() => setActiveTab("participation")}
      >
        Participation
      </div>
      <div 
        className={`tab ${activeTab === "alignment" ? "active" : ""}`}
        onClick={() => setActiveTab("alignment")}
      >
        Alignment
      </div>
    </div>
  )

  // Form sections
  const renderGeneralSection = () => (
    <div className="form-section">
      <h3>Country Information</h3>
      <div>
        <label className="form-label">Country Name:</label>
        <input
          type="text"
          value={country}
          onChange={(e) => updateHandlers.handleGeneralChange(setCountry, setFormData, e.target.value)}
          required
          className="form-input"
          placeholder="Enter country name"
        />
      </div>
    </div>
  )

  const renderPolicySection = () => {
    const currentPolicy = formData.policyInitiatives[activePolicyIndex]
    
    return (
      <div className="form-section">
        <div className="policy-nav">
          <button 
            type="button" 
            className="policy-nav-button"
            disabled={activePolicyIndex === 0}
            onClick={() => setActivePolicyIndex(prev => Math.max(0, prev - 1))}
          >
            Previous Policy
          </button>
          <button 
            type="button" 
            className="policy-nav-button"
            disabled={activePolicyIndex === 9}
            onClick={() => setActivePolicyIndex(prev => Math.min(9, prev + 1))}
          >
            Next Policy
          </button>
        </div>
        
        <div className="policy-indicator">
          {Array(10).fill(null).map((_, i) => (
            <div 
              key={i}
              className={`policy-dot ${i === activePolicyIndex ? "active" : ""}`}
              onClick={() => setActivePolicyIndex(i)}
            />
          ))}
        </div>
        
        <h3>Policy {activePolicyIndex + 1}</h3>
        
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
          <label className="form-label">Policy Area:</label>
          <select
            value={currentPolicy.policyArea}
            onChange={(e) => updateHandlers.handlePolicyChange(formData, setFormData, activePolicyIndex, "policyArea", e.target.value)}
            className="form-select"
          >
            <option value="">Select Policy Area</option>
            {policyAreaOptions.map((area, i) => (
              <option key={i} value={area}>{area}</option>
            ))}
          </select>
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

  const renderImplementationSection = () => (
    <div className="form-section">
      <h3>Implementation & Funding</h3>
      
      <div>
        <label className="form-label">Yearly Budget:</label>
        <input
          type="number"
          value={formData.implementation.yearlyBudget}
          onChange={(e) => updateHandlers.handleImplementationChange(formData, setFormData, "yearlyBudget", e.target.value)}
          className="form-input"
          placeholder="Enter yearly budget amount"
        />
      </div>
      
      <div>
        <label className="form-label">Budget Currency:</label>
        <select
          value={formData.implementation.budgetCurrency}
          onChange={(e) => updateHandlers.handleImplementationChange(formData, setFormData, "budgetCurrency", e.target.value)}
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
              id="private-funding-yes"
              checked={formData.implementation.privateSecFunding === true}
              onChange={() => updateHandlers.handleImplementationChange(formData, setFormData, "privateSecFunding", true)}
            />
            <label htmlFor="private-funding-yes">Yes</label>
          </div>
          <div className="checkbox-item">
            <input
              type="radio"
              id="private-funding-no"
              checked={formData.implementation.privateSecFunding === false}
              onChange={() => updateHandlers.handleImplementationChange(formData, setFormData, "privateSecFunding", false)}
            />
            <label htmlFor="private-funding-no">No</label>
          </div>
        </div>
      </div>
      
      <div>
        <label className="form-label">Deployment Year:</label>
        <input
          type="number"
          min="1990"
          max="2030"
          value={formData.implementation.deploymentYear}
          onChange={(e) => updateHandlers.handleImplementationChange(formData, setFormData, "deploymentYear", e.target.value)}
          className="form-input"
          placeholder="Enter year policies entered into force"
        />
      </div>
    </div>
  )

  const renderEvaluationSection = () => (
    <div className="form-section">
      <h3>Evaluation & Accountability</h3>
      
      <div>
        <label className="form-label">Is Evaluated:</label>
        <div className="radio-group">
          <div className="checkbox-item">
            <input
              type="radio"
              id="is-evaluated-yes"
              checked={formData.evaluation.isEvaluated === true}
              onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, "isEvaluated", true)}
            />
            <label htmlFor="is-evaluated-yes">Yes</label>
          </div>
          <div className="checkbox-item">
            <input
              type="radio"
              id="is-evaluated-no"
              checked={formData.evaluation.isEvaluated === false}
              onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, "isEvaluated", false)}
            />
            <label htmlFor="is-evaluated-no">No</label>
          </div>
        </div>
      </div>
      
      {formData.evaluation.isEvaluated && (
        <div>
          <label className="form-label">Evaluation Type:</label>
          <div className="radio-group">
            <div className="checkbox-item">
              <input
                type="radio"
                id="eval-type-internal"
                checked={formData.evaluation.evaluationType === "internal"}
                onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, "evaluationType", "internal")}
              />
              <label htmlFor="eval-type-internal">Internal</label>
            </div>
            <div className="checkbox-item">
              <input
                type="radio"
                id="eval-type-external"
                checked={formData.evaluation.evaluationType === "external"}
                onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, "evaluationType", "external")}
              />
              <label htmlFor="eval-type-external">External</label>
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
              id="risk-assessment-yes"
              checked={formData.evaluation.riskAssessment === true}
              onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, "riskAssessment", true)}
            />
            <label htmlFor="risk-assessment-yes">Yes</label>
          </div>
          <div className="checkbox-item">
            <input
              type="radio"
              id="risk-assessment-no"
              checked={formData.evaluation.riskAssessment === false}
              onChange={() => updateHandlers.handleEvaluationChange(formData, setFormData, "riskAssessment", false)}
            />
            <label htmlFor="risk-assessment-no">No</label>
          </div>
        </div>
      </div>
      
      <div>
        <label className="form-label">Transparency Score (0-5): {formData.evaluation.transparencyScore}</label>
        <input
          type="range"
          min="0"
          max="5"
          step="1"
          value={formData.evaluation.transparencyScore}
          onChange={(e) => updateHandlers.handleEvaluationChange(formData, setFormData, "transparencyScore", parseInt(e.target.value))}
          className="score-slider"
        />
      </div>
      
      <div>
        <label className="form-label">Explainability Score (0-5): {formData.evaluation.explainabilityScore}</label>
        <input
          type="range"
          min="0"
          max="5"
          step="1"
          value={formData.evaluation.explainabilityScore}
          onChange={(e) => updateHandlers.handleEvaluationChange(formData, setFormData, "explainabilityScore", parseInt(e.target.value))}
          className="score-slider"
        />
      </div>
      
      <div>
        <label className="form-label">Accountability Score (0-5): {formData.evaluation.accountabilityScore}</label>
        <input
          type="range"
          min="0"
          max="5"
          step="1"
          value={formData.evaluation.accountabilityScore}
          onChange={(e) => updateHandlers.handleEvaluationChange(formData, setFormData, "accountabilityScore", parseInt(e.target.value))}
          className="score-slider"
        />
      </div>
    </div>
  )

  const renderParticipationSection = () => (
    <div className="form-section">
      <h3>Public Participation</h3>
      
      <div>
        <label className="form-label">Has Consultation Process:</label>
        <div className="radio-group">
          <div className="checkbox-item">
            <input
              type="radio"
              id="consultation-yes"
              checked={formData.participation.hasConsultation === true}
              onChange={() => updateHandlers.handleParticipationChange(formData, setFormData, "hasConsultation", true)}
            />
            <label htmlFor="consultation-yes">Yes</label>
          </div>
          <div className="checkbox-item">
            <input
              type="radio"
              id="consultation-no"
              checked={formData.participation.hasConsultation === false}
              onChange={() => updateHandlers.handleParticipationChange(formData, setFormData, "hasConsultation", false)}
            />
            <label htmlFor="consultation-no">No</label>
          </div>
        </div>
      </div>
      
      {formData.participation.hasConsultation && (
        <>
          <div>
            <label className="form-label">Consultation Start Date:</label>
            <input
              type="date"
              value={formData.participation.consultationStartDate}
              onChange={(e) => updateHandlers.handleParticipationChange(formData, setFormData, "consultationStartDate", e.target.value)}
              className="form-input"
            />
          </div>
          
          <div>
            <label className="form-label">Consultation End Date:</label>
            <input
              type="date"
              value={formData.participation.consultationEndDate}
              onChange={(e) => updateHandlers.handleParticipationChange(formData, setFormData, "consultationEndDate", e.target.value)}
              className="form-input"
            />
          </div>
          
          <div>
            <label className="form-label">Public Comments Availability:</label>
            <div className="radio-group">
              <div className="checkbox-item">
                <input
                  type="radio"
                  id="comments-public"
                  checked={formData.participation.commentsPublic === true}
                  onChange={() => updateHandlers.handleParticipationChange(formData, setFormData, "commentsPublic", true)}
                />
                <label htmlFor="comments-public">Yes</label>
              </div>
              <div className="checkbox-item">
                <input
                  type="radio"
                  id="comments-private"
                  checked={formData.participation.commentsPublic === false}
                  onChange={() => updateHandlers.handleParticipationChange(formData, setFormData, "commentsPublic", false)}
                />
                <label htmlFor="comments-private">No</label>
              </div>
            </div>
          </div>
        </>
      )}
      
      <div>
        <label className="form-label">Stakeholder Engagement Score (0-5): {formData.participation.stakeholderScore}</label>
        <input
          type="range"
          min="0"
          max="5"
          step="1"
          value={formData.participation.stakeholderScore}
          onChange={(e) => updateHandlers.handleParticipationChange(formData, setFormData, "stakeholderScore", parseInt(e.target.value))}
          className="score-slider"
        />
      </div>
    </div>
  )

  const renderAlignmentSection = () => (
    <div className="form-section">
      <h3>AI Principles Alignment</h3>
      
      <div>
        <label className="form-label">AI Principles Coverage:</label>
        <div className="checkbox-group">
          {aiPrinciplesOptions.map((principle, i) => (
            <div key={i} className="checkbox-item">
              <input
                type="checkbox"
                id={`ai-principle-${i}`}
                checked={formData.alignment.aiPrinciples.includes(principle)}
                onChange={() => updateHandlers.handlePrincipleToggle(formData, setFormData, principle)}
              />
              <label htmlFor={`ai-principle-${i}`}>{principle}</label>
            </div>
          ))}
        </div>
      </div>
      
      <div>
        <label className="form-label">Human Rights Alignment:</label>
        <div className="radio-group">
          <div className="checkbox-item">
            <input
              type="radio"
              id="human-rights-yes"
              checked={formData.alignment.humanRightsAligned === true}
              onChange={() => updateHandlers.handleAlignmentChange(formData, setFormData, "humanRightsAligned", true)}
            />
            <label htmlFor="human-rights-yes">Yes</label>
          </div>
          <div className="checkbox-item">
            <input
              type="radio"
              id="human-rights-no"
              checked={formData.alignment.humanRightsAligned === false}
              onChange={() => updateHandlers.handleAlignmentChange(formData, setFormData, "humanRightsAligned", false)}
            />
            <label htmlFor="human-rights-no">No</label>
          </div>
        </div>
      </div>
      
      <div>
        <label className="form-label">Ethics Alignment Score (0-5): {formData.alignment.ethicsScore}</label>
        <input
          type="range"
          min="0"
          max="5"
          step="1"
          value={formData.alignment.ethicsScore}
          onChange={(e) => updateHandlers.handleAlignmentChange(formData, setFormData, "ethicsScore", parseInt(e.target.value))}
          className="score-slider"
        />
      </div>
      
      <div>
        <label className="form-label">International Cooperation:</label>
        <div className="radio-group">
          <div className="checkbox-item">
            <input
              type="radio"
              id="intl-coop-yes"
              checked={formData.alignment.internationalCooperation === true}
              onChange={() => updateHandlers.handleAlignmentChange(formData, setFormData, "internationalCooperation", true)}
            />
            <label htmlFor="intl-coop-yes">Yes</label>
          </div>
          <div className="checkbox-item">
            <input
              type="radio"
              id="intl-coop-no"
              checked={formData.alignment.internationalCooperation === false}
              onChange={() => updateHandlers.handleAlignmentChange(formData, setFormData, "internationalCooperation", false)}
            />
            <label htmlFor="intl-coop-no">No</label>
          </div>
        </div>
      </div>
      
      <div>
        <label className="form-label">Comments:</label>
        <textarea
          value={formData.alignment.comments}
          onChange={(e) => updateHandlers.handleAlignmentChange(formData, setFormData, "comments", e.target.value)}
          className="form-textarea"
          placeholder="Additional comments on alignment with AI principles"
        />
      </div>
    </div>
  )

  // Main render function
  return (
    <div className="policy-form-container">
      <h2>AI Policy Submission Form</h2>
      
      {renderTabs()}
      
      <form onSubmit={onSubmit}>
        {activeTab === "general" && renderGeneralSection()}
        {activeTab === "policy" && renderPolicySection()}
        {activeTab === "implementation" && renderImplementationSection()}
        {activeTab === "evaluation" && renderEvaluationSection()}
        {activeTab === "participation" && renderParticipationSection()}
        {activeTab === "alignment" && renderAlignmentSection()}
        
        <div className="form-navigation">
          {activeTab !== "general" && (
            <button 
              type="button" 
              onClick={() => {
                const tabs = ["general", "policy", "implementation", "evaluation", "participation", "alignment"]
                const currentIndex = tabs.indexOf(activeTab)
                setActiveTab(tabs[currentIndex - 1])
              }}
              className="nav-button"
            >
              Previous
            </button>
          )}
          
          {activeTab !== "alignment" ? (
            <button 
              type="button" 
              onClick={() => {
                const tabs = ["general", "policy", "implementation", "evaluation", "participation", "alignment"]
                const currentIndex = tabs.indexOf(activeTab)
                setActiveTab(tabs[currentIndex + 1])
              }}
              className="nav-button"
            >
              Next
            </button>
          ) : (
            <button type="submit" className="submit-button">
              Submit
            </button>
          )}
        </div>
      </form>
    </div>
  )
}