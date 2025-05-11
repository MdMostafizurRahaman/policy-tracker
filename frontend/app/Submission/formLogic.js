// Policy Area Options
export const policyType = [
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

// Target Group Options
export const targetGroupOptions = [
  "Government", 
  "Industry", 
  "Academia", 
  "Small Businesses", 
  "General Public", 
  "Specific Sector"
]

// AI Principles Options
export const aiPrinciplesOptions = [
  "Fairness", 
  "Accountability", 
  "Transparency", 
  "Explainability", 
  "Safety", 
  "Human Control",
  "Privacy", 
  "Security", 
  "Non-discrimination", 
  "Trust", 
  "Sustainability"
]

// Initial form data structure
export const getInitialFormData = () => ({
  country: "",
  policyInitiatives: Array(10).fill().map(() => ({
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
  }))
})

// Form update handlers
export const updateHandlers = {
  // Country section handlers
  handleCountryChange: (setFormData, value) => {
    setFormData(prev => ({
      ...prev,
      country: value
    }))
  },
  
  // Policy handlers
  handlePolicyChange: (formData, setFormData, index, field, value) => {
    const newPolicyInitiatives = [...formData.policyInitiatives]
    newPolicyInitiatives[index] = {
      ...newPolicyInitiatives[index],
      [field]: value
    }
    
    setFormData(prev => ({
      ...prev,
      policyInitiatives: newPolicyInitiatives
    }))
  },
  
  handleTargetGroupToggle: (formData, setFormData, index, group) => {
    const currentGroups = formData.policyInitiatives[index].targetGroups
    let updatedGroups
    
    if (currentGroups.includes(group)) {
      updatedGroups = currentGroups.filter(g => g !== group)
    } else {
      updatedGroups = [...currentGroups, group]
    }
    
    const newPolicyInitiatives = [...formData.policyInitiatives]
    newPolicyInitiatives[index] = {
      ...newPolicyInitiatives[index],
      targetGroups: updatedGroups
    }
    
    setFormData(prev => ({
      ...prev,
      policyInitiatives: newPolicyInitiatives
    }))
  },
  
  handleFileReset: (formData, setFormData, index) => {
    const newPolicyInitiatives = [...formData.policyInitiatives]
    newPolicyInitiatives[index] = {
      ...newPolicyInitiatives[index],
      policyFile: null
    }
    
    setFormData(prev => ({
      ...prev,
      policyInitiatives: newPolicyInitiatives
    }))
  },
  
  // Implementation section handlers
  handleImplementationChange: (formData, setFormData, index, field, value) => {
    const newPolicyInitiatives = [...formData.policyInitiatives]
    newPolicyInitiatives[index] = {
      ...newPolicyInitiatives[index],
      implementation: {
        ...newPolicyInitiatives[index].implementation,
        [field]: value
      }
    }
    
    setFormData(prev => ({
      ...prev,
      policyInitiatives: newPolicyInitiatives
    }))
  },
  
  // Evaluation section handlers
  handleEvaluationChange: (formData, setFormData, index, field, value) => {
    const newPolicyInitiatives = [...formData.policyInitiatives]
    newPolicyInitiatives[index] = {
      ...newPolicyInitiatives[index],
      evaluation: {
        ...newPolicyInitiatives[index].evaluation,
        [field]: value
      }
    }
    
    setFormData(prev => ({
      ...prev,
      policyInitiatives: newPolicyInitiatives
    }))
  },
  
  // Participation section handlers
  handleParticipationChange: (formData, setFormData, index, field, value) => {
    const newPolicyInitiatives = [...formData.policyInitiatives]
    newPolicyInitiatives[index] = {
      ...newPolicyInitiatives[index],
      participation: {
        ...newPolicyInitiatives[index].participation,
        [field]: value
      }
    }
    
    setFormData(prev => ({
      ...prev,
      policyInitiatives: newPolicyInitiatives
    }))
  },
  
  // Alignment section handlers
  handleAlignmentChange: (formData, setFormData, index, field, value) => {
    const newPolicyInitiatives = [...formData.policyInitiatives]
    newPolicyInitiatives[index] = {
      ...newPolicyInitiatives[index],
      alignment: {
        ...newPolicyInitiatives[index].alignment,
        [field]: value
      }
    }
    
    setFormData(prev => ({
      ...prev,
      policyInitiatives: newPolicyInitiatives
    }))
  },
  
  handlePrincipleToggle: (formData, setFormData, index, principle) => {
    const currentPrinciples = formData.policyInitiatives[index].alignment.aiPrinciples
    let updatedPrinciples
    
    if (currentPrinciples.includes(principle)) {
      updatedPrinciples = currentPrinciples.filter(p => p !== principle)
    } else {
      updatedPrinciples = [...currentPrinciples, principle]
    }
    
    const newPolicyInitiatives = [...formData.policyInitiatives]
    newPolicyInitiatives[index] = {
      ...newPolicyInitiatives[index],
      alignment: {
        ...newPolicyInitiatives[index].alignment,
        aiPrinciples: updatedPrinciples
      }
    }
    
    setFormData(prev => ({
      ...prev,
      policyInitiatives: newPolicyInitiatives
    }))
  }
}

// Form submission handler
export const handleSubmission = async (e, formData, resetForm) => {
  e.preventDefault()
  
  // Basic validation
  if (!formData.country.trim()) {
    alert("Please enter a country name")
    return false
  }
  
  // Check if at least the first policy has a name
  if (!formData.policyInitiatives[0].policyName.trim()) {
    alert("Please enter a name for at least the first policy")
    return false
  }
  
  try {
    // Here you would typically send the data to your backend
    console.log("Submitting form data:", formData)
    
    // Simulating API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    return true
  } catch (error) {
    console.error("Error submitting form:", error)
    alert("Error submitting the form. Please try again.")
    return false
  }
}