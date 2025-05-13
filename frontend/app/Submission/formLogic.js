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
export const PrinciplesOptions = [
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
    // Create a copy of the form data for submission
    const submissionData = {
      country: formData.country,
      policyInitiatives: formData.policyInitiatives.map(policy => {
        // Handle file data properly for serialization
        const policyData = { ...policy }
        
        // If there's a file, just keep basic metadata
        if (policyData.policyFile) {
          policyData.policyFile = {
            name: policyData.policyFile.name,
            size: policyData.policyFile.size,
            type: policyData.policyFile.type
          }
        }
        
        return policyData
      })
    }
    
    console.log("Submitting form data:", submissionData)
    
    // Send data to the backend
    const response = await fetch('/api/submit-form', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(submissionData)
    })
    
    const result = await response.json()
    
    if (!result.success) {
      throw new Error(result.message || 'Form submission failed')
    }
    
    console.log("Submission successful:", result)
    return true
    
  } catch (error) {
    console.error("Error submitting form:", error)
    alert(`Error submitting the form: ${error.message || 'Please try again.'}`)
    return false
  }
}

// File upload handler separate from main form submission
export const handleFileUpload = async (countryName, policyIndex, file) => {
  if (!file || !countryName) {
    return {
      success: false,
      message: 'Missing required data for file upload'
    }
  }
  
  try {
    // Check if we're in development mode
    const isDevelopment = process.env.NODE_ENV === 'development';
    
    // Skip the endpoint check in development mode if desired
    let endpointAvailable = true;
    
    if (!isDevelopment) {
      // Only perform the HEAD check in non-development environments
      try {
        const checkEndpoint = await fetch('/api/upload-policy-file', {
          method: 'HEAD',
          cache: 'no-cache'
        });
        
        endpointAvailable = checkEndpoint.ok;
        
        if (!endpointAvailable) {
          console.warn('File upload endpoint not available, will proceed with form submission without file upload');
        }
      } catch (endpointError) {
        console.warn('File upload endpoint check failed:', endpointError);
        endpointAvailable = false;
      }
    } else {
      console.log('Running in development mode - skipping endpoint availability check');
    }
    
    // If endpoint is not available or we're in development mode
    if (!endpointAvailable || isDevelopment) {
      return {
        success: true,
        filePath: null,
        localOnly: true,
        message: isDevelopment 
          ? 'File stored locally only (development mode)'
          : 'File stored locally only (endpoint not available)'
      };
    }
    
    // If we get here, the endpoint is available and we're not in development mode
    // Create FormData object for file upload
    const formData = new FormData()
    formData.append('country', countryName)
    formData.append('policy_index', policyIndex)
    formData.append('file', file)
    
    // Send file to backend
    const response = await fetch('/api/upload-policy-file', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `File upload failed with status: ${response.status}`)
    }
    
    const result = await response.json()
    return {
      success: true,
      filePath: result.file_path,
      message: 'File uploaded successfully'
    }
    
  } catch (error) {
    console.error('Error uploading file:', error)
    // Return success anyway so form submission can continue
    return {
      success: true,
      filePath: null,
      uploadFailed: true,
      message: `Will continue with form submission. File upload error: ${error.message}`
    }
  }
}
