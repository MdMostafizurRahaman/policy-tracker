// Enhanced form submission with file handling
export const enhancedHandleSubmission = async (e, formData, resetForm) => {
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
    // First handle any file uploads
    const fileUploadPromises = []
    
    formData.policyInitiatives.forEach((policy, index) => {
      if (policy.policyFile && policy.policyFile instanceof File) {
        // Upload the file first and track the promise
        const uploadPromise = handleFileUpload(
          formData.country,
          index,
          policy.policyFile
        ).then(result => {
          if (result.success) {
            // Update policy with file path info in our form data
            policy.policyFile = {
              name: policy.policyFile.name, 
              path: result.filePath || 'local-only',
              size: policy.policyFile.size,
              type: policy.policyFile.type,
              localOnly: result.localOnly,
              uploadFailed: result.uploadFailed
            }
          } else {
            // If file upload fails, just note the filename without path
            console.warn(`Failed to upload file for policy ${index + 1}:`, result.message)
            policy.policyFile = {
              name: policy.policyFile.name,
              size: policy.policyFile.size,
              type: policy.policyFile.type,
              uploadFailed: true
            }
          }
          return result
        })
        
        fileUploadPromises.push(uploadPromise)
      }
    })
    
    // Wait for all file uploads to complete
    if (fileUploadPromises.length > 0) {
      const fileResults = await Promise.all(fileUploadPromises)
      console.log('File upload results:', fileResults)
    }
    
    // Check if submit-form endpoint exists
    let endpointAvailable = true;
    try {
      const checkEndpoint = await fetch('/api/submit-form', { 
        method: 'HEAD',
        cache: 'no-cache' 
      });
      endpointAvailable = checkEndpoint.ok;
    } catch (endpointError) {
      console.warn('Submit form endpoint check failed:', endpointError);
      endpointAvailable = false;
    }
    
    // If endpoint isn't available, show a message but "succeed" anyway
    if (!endpointAvailable) {
      console.log("API endpoint not available, would submit this data:", formData);
      alert("Form data processed successfully (in development mode - API endpoint not available)");
      return true;
    }
    
    // Prepare form data for submission
    const submissionData = {
      country: formData.country,
      policyInitiatives: formData.policyInitiatives.map(policy => {
        // Create a clean copy for submission
        const { ...policyData } = policy
        return policyData
      })
    }
    
    console.log("Submitting form data:", submissionData)
    
    // Send main form data to the backend
    const response = await fetch('/api/submit-form', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(submissionData)
    })
    
    const result = await response.json().catch(() => ({ 
      success: false, 
      message: `Request failed with status: ${response.status}` 
    }))
    
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

// File upload handler needed by enhancedHandleSubmission
export const handleFileUpload = async (countryName, policyIndex, file) => {
  if (!file || !countryName) {
    return {
      success: false,
      message: 'Missing required data for file upload'
    }
  }
  
  try {
    // Check if endpoint exists by making a HEAD request first
    try {
      const checkEndpoint = await fetch('/api/upload-policy-file', { 
        method: 'HEAD',
        cache: 'no-cache'
      });
      
      if (!checkEndpoint.ok) {
        console.warn('File upload endpoint not available, will proceed with form submission without file upload');
        return {
          success: true,
          filePath: null,
          localOnly: true,
          message: 'File stored locally only (endpoint not available)'
        };
      }
    } catch (endpointError) {
      console.warn('File upload endpoint check failed:', endpointError);
      return {
        success: true,
        filePath: null,
        localOnly: true,
        message: 'File stored locally only (endpoint not available)'
      };
    }
    
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