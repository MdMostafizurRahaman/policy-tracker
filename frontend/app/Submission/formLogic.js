export const policyAreaOptions = [
  "AI Strategy", 
  "Governance", 
  "Regulation", 
  "Ethics", 
  "R&D Investment", 
  "Education", 
  "Labor Market", 
  "Economic Development",
  "Security",
  "Health",
  "Environment"
]

export const targetGroupOptions = [
  "Government", 
  "Private Sector", 
  "Academia", 
  "Civil Society", 
  "General Public"
]

export const aiPrinciplesOptions = [
  "Transparency", 
  "Accountability", 
  "Safety", 
  "Non-discrimination", 
  "Privacy", 
  "Human Oversight", 
  "Technical Robustness", 
  "Social Benefit"
]

// Initialize form data with default values for all fields
export const getInitialFormData = () => ({
  policyInitiatives: Array(10).fill(null).map(() => ({
    policyName: "",
    policyId: "",
    policyArea: "",
    targetGroups: [],
    policyDescription: "",
    policyFile: null,
    policyLink: ""
  })),
  implementation: {
    yearlyBudget: "",
    budgetCurrency: "USD",
    privateSecFunding: false,
    deploymentYear: ""
  },
  evaluation: {
    isEvaluated: false,
    evaluationType: "internal", // Default value to avoid undefined
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
    humanRightsAligned: false,
    ethicsScore: 0,
    internationalCooperation: false,
    comments: ""
  }
})

// Update handlers
export const updateHandlers = {
  // General section handlers
  handleGeneralChange: (setCountry, setFormData, value) => {
    setCountry(value)
  },
  
  // Policy section handlers
  handlePolicyChange: (formData, setFormData, policyIndex, field, value) => {
    const updatedPolicies = [...formData.policyInitiatives]
    updatedPolicies[policyIndex] = {
      ...updatedPolicies[policyIndex],
      [field]: value
    }
    
    setFormData({
      ...formData,
      policyInitiatives: updatedPolicies
    })
  },
  
  handleTargetGroupToggle: (formData, setFormData, policyIndex, groupName) => {
    const currentGroups = formData.policyInitiatives[policyIndex].targetGroups || []
    let updatedGroups
    
    if (currentGroups.includes(groupName)) {
      updatedGroups = currentGroups.filter(group => group !== groupName)
    } else {
      updatedGroups = [...currentGroups, groupName]
    }
    
    const updatedPolicies = [...formData.policyInitiatives]
    updatedPolicies[policyIndex] = {
      ...updatedPolicies[policyIndex],
      targetGroups: updatedGroups
    }
    
    setFormData({
      ...formData,
      policyInitiatives: updatedPolicies
    })
  },
  
  handleFileReset: (formData, setFormData, policyIndex) => {
    const updatedPolicies = [...formData.policyInitiatives]
    updatedPolicies[policyIndex] = {
      ...updatedPolicies[policyIndex],
      policyFile: null
    }
    
    setFormData({
      ...formData,
      policyInitiatives: updatedPolicies
    })
  },
  
  // Implementation section handlers
  handleImplementationChange: (formData, setFormData, field, value) => {
    setFormData({
      ...formData,
      implementation: {
        ...formData.implementation,
        [field]: value
      }
    })
  },
  
  // Evaluation section handlers
  handleEvaluationChange: (formData, setFormData, field, value) => {
    setFormData({
      ...formData,
      evaluation: {
        ...formData.evaluation,
        [field]: value
      }
    })
  },
  
  // Participation section handlers
  handleParticipationChange: (formData, setFormData, field, value) => {
    setFormData({
      ...formData,
      participation: {
        ...formData.participation,
        [field]: value
      }
    })
  },
  
  // Alignment section handlers
  handleAlignmentChange: (formData, setFormData, field, value) => {
    setFormData({
      ...formData,
      alignment: {
        ...formData.alignment,
        [field]: value
      }
    })
  },
  
  handlePrincipleToggle: (formData, setFormData, principleName) => {
    const currentPrinciples = formData.alignment.aiPrinciples || []
    let updatedPrinciples
    
    if (currentPrinciples.includes(principleName)) {
      updatedPrinciples = currentPrinciples.filter(principle => principle !== principleName)
    } else {
      updatedPrinciples = [...currentPrinciples, principleName]
    }
    
    setFormData({
      ...formData,
      alignment: {
        ...formData.alignment,
        aiPrinciples: updatedPrinciples
      }
    })
  }
}

// Form submission handler
export const handleSubmission = async (e, country, formData, resetForm) => {
  e.preventDefault()
  
  // Validation
  if (!country.trim()) {
    alert("Please enter a country name")
    return false
  }
  
  // Here you would typically send the data to your backend
  console.log("Submitting form with data:", { country, ...formData })
  
  // For demonstration purposes, we'll simulate a successful submission
  return true
}