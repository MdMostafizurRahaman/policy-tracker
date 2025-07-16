import React, { useState, useEffect } from 'react';
import { countries, policyAreas as POLICY_AREAS } from '../../utils/constants';
import { apiService } from '../../services/api';

const TARGET_GROUPS = [
  "Government", "Industry", "Academia", "Small Businesses", 
  "General Public", "Specific Sector", "Researchers", "Students",
  "Healthcare Providers", "Financial Institutions", "NGOs", "International Organizations"
];

const PRINCIPLES = [
  "Fairness", "Accountability", "Transparency", "Explainability", 
  "Safety", "Human Control", "Privacy", "Security", 
  "Non-discrimination", "Trust", "Sustainability", "Innovation",
  "Human Rights", "Democracy", "Rule of Law", "Ethics"
];

const CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CNY", "INR", "CAD", "AUD", "CHF", "SEK", "Others"];

// AI Analysis Service for document extraction
const analyzeDocumentWithAI = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    // This would call your backend AI analysis endpoint
    // Don't set Content-Type header - let browser set it automatically with boundary
    const response = await apiService.post('/ai-analysis/analyze-policy-document', formData);
    
    return response; // Return the full response, not just response.data
  } catch (error) {
    // Enhance error handling for JSON parsing issues
    if (error.message.includes('Expecting value') || error.message.includes('Invalid JSON')) {
      throw new Error('AI analysis returned invalid data format. Please try again or contact support.');
    }
    throw error; // Re-throw other errors
  }
};

// AI Analysis Service for uploaded files (by file_id)
const analyzeUploadedFileWithAI = async (fileId) => {
  try {
    // Call the backend AI analysis endpoint for uploaded files
    const response = await apiService.analyzeUploadedFile(fileId);
    
    return response;
  } catch (error) {
    // Enhance error handling for JSON parsing issues
    if (error.message.includes('Expecting value') || error.message.includes('Invalid JSON')) {
      throw new Error('AI analysis returned invalid data format. Please try again or contact support.');
    }
    throw error; // Re-throw other errors
  }
};

// Create empty policy template
const createEmptyPolicy = () => ({
  policyName: "",
  policyId: "",
  policyDescription: "",
  targetGroups: [],
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
});

// User card display
const UserSubmissionCard = ({ user }) => (
  <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 mb-8">
    <div className="flex items-center gap-3">
      <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      </div>
      <div>
        <p className="text-sm font-medium text-gray-600">Submitting as</p>
        <p className="text-lg font-bold text-gray-900">{user.firstName} {user.lastName}</p>
        <p className="text-sm text-gray-500">{user.email}</p>
      </div>
    </div>
  </div>
);

const PolicySubmissionForm = () => {
  // All hooks at the top!
  const [user, setUser] = useState(null);
  const [policyAreasState, setPolicyAreasState] = useState(() => {
    const areas = {};
    POLICY_AREAS.forEach(area => {
      areas[area.id] = [];
    });
    return areas;
  });
  const [formData, setFormData] = useState({
    country: "",
  });
  const [filteredCountries, setFilteredCountries] = useState([]);
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);
  const [selectedPolicyArea, setSelectedPolicyArea] = useState(null);
  const [selectedPolicyIndex, setSelectedPolicyIndex] = useState(null);
  const [activeTab, setActiveTab] = useState("basic");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [fileUploading, setFileUploading] = useState({});
  const [showAutoFillModal, setShowAutoFillModal] = useState(false);
  const [autoFillLoading, setAutoFillLoading] = useState(false);
  const [autoFillFile, setAutoFillFile] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('userData');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        if (!parsedUser.id && parsedUser._id) {
          parsedUser.id = parsedUser._id;
        }
        setUser(parsedUser);
      } catch (error) {
        console.error('Error parsing user data:', error);
        window.location.href = '/login';
      }
    } else {
      window.location.href = '/login';
    }
  }, []);

  // Country autocomplete
  useEffect(() => {
    if (formData.country) {
      const filtered = countries.filter(country =>
        country.toLowerCase().includes(formData.country.toLowerCase())
      );
      setFilteredCountries(filtered);
    } else {
      setFilteredCountries([]);
    }
  }, [formData.country]);

  const handleCountrySelect = (country) => {
    setFormData(prev => ({ ...prev, country }));
    setShowCountryDropdown(false);
  };

  const addPolicyToArea = (areaId) => {
    if (policyAreasState[areaId].length >= 10) {
      setError(`Maximum 10 policies allowed per policy area`);
      return;
    }

    const newPolicy = createEmptyPolicy();
    setPolicyAreasState(prev => ({
      ...prev,
      [areaId]: [...prev[areaId], newPolicy]
    }));

    setSelectedPolicyArea(areaId);
    setSelectedPolicyIndex(policyAreasState[areaId].length);
    setActiveTab("basic");
  };

  const removePolicyFromArea = (areaId, policyIndex) => {
    if (window.confirm('Are you sure you want to remove this policy?')) {
      setPolicyAreasState(prev => ({
        ...prev,
        [areaId]: prev[areaId].filter((_, index) => index !== policyIndex)
      }));

      if (selectedPolicyArea === areaId && selectedPolicyIndex === policyIndex) {
        setSelectedPolicyArea(null);
        setSelectedPolicyIndex(null);
      }
    }
  };

  const updatePolicy = (areaId, policyIndex, field, value) => {
    setPolicyAreasState(prev => ({
      ...prev,
      [areaId]: prev[areaId].map((policy, index) => 
        index === policyIndex ? { ...policy, [field]: value } : policy
      )
    }));
  };

  const updatePolicySection = (areaId, policyIndex, section, field, value) => {
    setPolicyAreasState(prev => ({
      ...prev,
      [areaId]: prev[areaId].map((policy, index) => 
        index === policyIndex ? {
          ...policy,
          [section]: { ...policy[section], [field]: value }
        } : policy
      )
    }));
  };

  const toggleArrayItem = (areaId, policyIndex, section, field, item) => {
    const policy = policyAreasState[areaId][policyIndex];
    const currentItems = section ? policy[section][field] : policy[field];
    
    const updatedItems = currentItems.includes(item) ?
      currentItems.filter(i => i !== item) :
      [...currentItems, item];
    
    if (section) {
      updatePolicySection(areaId, policyIndex, section, field, updatedItems);
    } else {
      updatePolicy(areaId, policyIndex, field, updatedItems);
    }
  };

  const handleFileUpload = async (areaId, policyIndex, file) => {
    if (!file) return;

    const uploadKey = `${areaId}-${policyIndex}`;
    setFileUploading(prev => ({ ...prev, [uploadKey]: true }));

    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', file);
      formData.append('policy_area', areaId);
      formData.append('country', formData.country || 'Unknown');
      formData.append('description', `Policy document for ${areaId}`);

      // Upload to AWS S3 via backend
      const response = await apiService.post('/policy/upload-policy-file', formData);

      if (response.success) {
        const fileData = {
          name: file.name,
          file_id: response.file_data.file_id,
          s3_key: response.file_data.s3_key || null,
          file_url: response.file_data.file_url,
          cdn_url: response.file_data.cdn_url || null,
          local_path: response.file_data.local_path || null,
          size: response.file_data.size,
          type: file.type,
          upload_date: response.file_data.upload_date,
          storage_type: response.file_data.storage_type || 's3'
        };

        updatePolicy(areaId, policyIndex, "policyFile", fileData);
        setError("");
        
        // Show appropriate success message based on storage type
        if (response.file_data.storage_type === 'local') {
          setSuccess("File uploaded successfully to local storage (cloud storage temporarily unavailable).");
        } else {
          setSuccess("File uploaded successfully to cloud storage.");
        }
      } else {
        throw new Error(response.message || 'Upload failed');
      }
    } catch (error) {
      console.error('File upload error:', error);
      
      let errorMessage = 'File upload failed. ';
      
      // Provide specific error messages based on the error type
      if (error.message.includes('AccessDenied') || error.message.includes('s3:PutObject')) {
        errorMessage = 'File uploaded to local storage (cloud storage temporarily unavailable). Your file has been saved successfully.';
        setError(""); // Don't show this as an error since it's just a fallback
        
        // Show a success message instead
        setTimeout(() => {
          setSuccess('File uploaded successfully to local storage. Cloud storage will be restored soon.');
        }, 100);
        
        return; // Don't treat this as an error
      } else if (error.message.includes('401') || error.message.includes('Token expired')) {
        errorMessage += 'Your session has expired. Please login again.';
      } else if (error.message.includes('413') || error.message.includes('too large')) {
        errorMessage += 'File is too large. Please use a file smaller than 10MB.';
      } else if (error.message.includes('400') || error.message.includes('not allowed')) {
        errorMessage += 'File type not supported. Please use PDF, DOC, DOCX, TXT, CSV, XLS, or XLSX files.';
      } else if (error.message.includes('Network') || error.message.includes('fetch')) {
        errorMessage += 'Network connection problem. Please check your internet and try again.';
      } else {
        errorMessage += error.message || 'Please try again or contact support.';
      }
      
      setError(errorMessage);
    } finally {
      setFileUploading(prev => ({ ...prev, [uploadKey]: false }));
    }
  };

  const handleAutoFillFromDocument = async (file) => {
    if (!file) return;

    setAutoFillLoading(true);
    setError("");

    try {
      // Determine appropriate policy area (will be refined after AI analysis)
      const suggestedArea = "AI and Technology"; // default
      
      // Upload file and get AI analysis in one call using the improved endpoint
      const uploadFormData = new FormData();
      uploadFormData.append('file', file);
      uploadFormData.append('policy_area', suggestedArea);
      uploadFormData.append('country', formData.country || 'Unknown');
      uploadFormData.append('description', `Policy document uploaded for analysis`);

      // Upload and analyze in one call (no double upload!)
      const response = await apiService.post('/policy/upload-policy-file', uploadFormData, {
        timeout: 60000 // 60 seconds for file upload and AI analysis
      });

      if (!response.success) {
        throw new Error(response.message || 'File upload and analysis failed');
      }

      // Extract AI analysis results
      const extractedData = response.ai_analysis || {};
      
      // Debug: Log the response to see what we're getting
      console.log("AI Analysis Response:", { success: true, data: extractedData });
      console.log("extractedData.data:", extractedData);
      
      // Check if we have useful extracted data
      let finalSuggestedArea = suggestedArea;
      if (extractedData && Object.keys(extractedData).length > 0) {
        finalSuggestedArea = determinePolicyArea(extractedData);
      }

      // Create new policy with extracted data and file info
      const newPolicy = {
        ...createEmptyPolicy(),
        ...(extractedData || {}), // Use extracted data if available
        policyFile: {
          name: file.name,
          file_id: response.file_data.file_id,
          s3_key: response.file_data.s3_key || null,
          file_url: response.file_data.file_url,
          cdn_url: response.file_data.cdn_url || null,
          size: response.file_data.size,
          type: file.type,
          upload_date: response.file_data.upload_date,
          storage_type: response.file_data.storage_type || 's3'
        }
      };

      // Add to the appropriate policy area
      setPolicyAreasState(prev => {
        // Ensure the policy area exists and is an array
        const currentAreaPolicies = prev[finalSuggestedArea] || [];
        return {
          ...prev,
          [finalSuggestedArea]: [...currentAreaPolicies, newPolicy]
        };
      });

      // Select the newly created policy for editing
      setSelectedPolicyArea(finalSuggestedArea);
      const currentAreaLength = (policyAreasState[finalSuggestedArea] || []).length;
      setSelectedPolicyIndex(currentAreaLength);
      setActiveTab("basic");
      
      setShowAutoFillModal(false);
      setAutoFillFile(null);
      
      if (extractedData && Object.keys(extractedData).length > 0) {
        setSuccess("Policy successfully auto-filled from document! You can now review and modify the extracted information.");
      } else {
        setSuccess("File uploaded successfully! AI analysis was not available, please fill in the details manually.");
      }

    } catch (error) {
      console.error("Auto-fill error:", error);
      let errorMessage = "Auto-fill failed: " + error.message;
      
      if (error.message.includes("503") || error.message.includes("Service Unavailable")) {
        errorMessage = "AI analysis service is not configured. Please contact your administrator to set up the GROQ_API_KEY.";
      } else if (error.message.includes("404") || error.message.includes("Not Found")) {
        errorMessage = "AI analysis endpoint not found. Please ensure the backend server is running with the latest updates.";
      } else if (error.message.includes("Invalid JSON") || error.message.includes("Expecting value") || error.message.includes("invalid data format")) {
        errorMessage = "AI analysis returned invalid data format. The document may not be suitable for automatic extraction. Please try uploading a different document or fill the form manually.";
      } else if (error.message.includes("Token expired") || error.message.includes("Invalid token")) {
        errorMessage = "Your session has expired. Please login again to continue.";
      } else if (error.message.includes("413") || error.message.includes("too large")) {
        errorMessage = "The document file is too large. Please try with a smaller file (under 10MB).";
      } else if (error.message.includes("400") || error.message.includes("Bad Request")) {
        errorMessage = "The document format is not supported or contains no readable text. Please try with a PDF, Word document, or text file.";
      }
      
      setError(errorMessage);
    } finally {
      setAutoFillLoading(false);
    }
  };

  const handleAutoFillFromUploadedFile = async (fileData) => {
    if (!fileData || !fileData.file_id) {
      setError("No file selected for analysis");
      return;
    }

    setAutoFillLoading(true);
    setError("");

    try {
      // Analyze uploaded file with AI using file_id
      const extractedData = await analyzeUploadedFileWithAI(fileData.file_id);
      
      // Debug: Log the response to see what we're getting
      console.log("AI Analysis Response:", extractedData);
      console.log("extractedData.data:", extractedData.data);
      
      // Check if the response contains the extracted data
      if (!extractedData || !extractedData.data) {
        console.error("Invalid response structure:", extractedData);
        throw new Error("No data extracted from document");
      }
      
      // Determine appropriate policy area based on extracted data
      const suggestedArea = determinePolicyArea(extractedData.data);
      
      // Create new policy with extracted data
      const newPolicy = {
        ...createEmptyPolicy(),
        ...extractedData.data,
        policyFile: fileData // Use the existing file data
      };

      // Add to the appropriate policy area
      setPolicyAreasState(prev => {
        // Ensure the policy area exists and is an array
        const currentAreaPolicies = prev[suggestedArea] || [];
        return {
          ...prev,
          [suggestedArea]: [...currentAreaPolicies, newPolicy]
        };
      });

      // Select the newly created policy for editing
      setSelectedPolicyArea(suggestedArea);
      const currentAreaLength = (policyAreasState[suggestedArea] || []).length;
      setSelectedPolicyIndex(currentAreaLength);
      setActiveTab("basic");
      
      setShowAutoFillModal(false);
      setAutoFillFile(null);
      setSuccess("Policy successfully auto-filled from uploaded document! You can now review and modify the extracted information.");

    } catch (error) {
      console.error("Auto-fill error:", error);
      let errorMessage = "Auto-fill failed: " + error.message;
      
      if (error.message.includes("503") || error.message.includes("Service Unavailable")) {
        errorMessage = "AI analysis service is not configured. Please contact your administrator to set up the GROQ_API_KEY.";
      } else if (error.message.includes("404") || error.message.includes("Not Found")) {
        errorMessage = "AI analysis endpoint not found or file not found. Please ensure the backend server is running with the latest updates.";
      } else if (error.message.includes("Invalid JSON") || error.message.includes("Expecting value") || error.message.includes("invalid data format")) {
        errorMessage = "AI analysis returned invalid data format. The document may not be suitable for automatic extraction. Please try uploading a different document or fill the form manually.";
      } else if (error.message.includes("Token expired") || error.message.includes("Invalid token")) {
        errorMessage = "Your session has expired. Please login again to continue.";
      } else if (error.message.includes("413") || error.message.includes("too large")) {
        errorMessage = "The document file is too large. Please try with a smaller file (under 10MB).";
      } else if (error.message.includes("400") || error.message.includes("Bad Request")) {
        errorMessage = "The document format is not supported or contains no readable text. Please try with a PDF, Word document, or text file.";
      }
      
      setError(errorMessage);
    } finally {
      setAutoFillLoading(false);
    }
  };

  const determinePolicyArea = (extractedData) => {
    // Simple logic to determine policy area based on content
    // You can enhance this with more sophisticated classification
    const description = extractedData.policyDescription?.toLowerCase() || "";
    const name = extractedData.policyName?.toLowerCase() || "";
    const content = `${name} ${description}`;

    // Check for keywords to classify into policy areas (using actual IDs from constants)
    if (content.includes("healthcare") || content.includes("medical") || content.includes("health")) return "physical-health";
    if (content.includes("education") || content.includes("learning")) return "digital-education";
    if (content.includes("work") || content.includes("employment") || content.includes("job")) return "digital-work";
    if (content.includes("mental") || content.includes("wellness")) return "mental-health";
    if (content.includes("cyber") || content.includes("security")) return "cyber-safety";
    if (content.includes("inclusion") || content.includes("accessibility") || content.includes("digital divide")) return "digital-inclusion";
    if (content.includes("leisure") || content.includes("gaming") || content.includes("entertainment")) return "digital-leisure";
    if (content.includes("social media") || content.includes("gaming")) return "social-media-gaming";
    if (content.includes("disinformation") || content.includes("misinformation") || content.includes("fake news")) return "disinformation";
    if (content.includes("ai") || content.includes("artificial intelligence") || content.includes("machine learning")) return "ai-safety";
    
    // Default to ai-safety if no specific area is detected (since most policies will be AI-related)
    return "ai-safety";
  };

  const validateForm = () => {
    if (!formData.country.trim()) {
      setError("Please select a country");
      return false;
    }

    if (!countries.includes(formData.country)) {
      setError("Please select a valid country from the list");
      return false;
    }

    const totalPolicies = Object.values(policyAreasState).reduce((total, policies) => total + policies.length, 0);
    if (totalPolicies === 0) {
      setError("Please add at least one policy");
      return false;
    }

    const hasNamedPolicy = Object.values(policyAreasState).some(policies => 
      policies.some(policy => policy.policyName.trim())
    );

    if (!hasNamedPolicy) {
      setError("At least one policy must have a name");
      return false;
    }

    setError("");
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const userId = String(user.user_id || user.id || user._id);
      
      const submissionData = {
        user_id: userId,
        user_email: user.email,
        user_name: `${user.firstName} ${user.lastName}`,
        country: formData.country,
        policyAreas: Object.entries(policyAreasState).map(([area_id, policies]) => ({
          area_id,
          area_name: POLICY_AREAS.find(a => a.id === area_id)?.name || area_id,
          policies: policies.map(policy => ({
            ...policy,
            policyName: policy.policyName || "",
            policyId: policy.policyId || "",
            policyDescription: policy.policyDescription || "",
            targetGroups: policy.targetGroups || [],
            policyFile: policy.policyFile || null,
            policyLink: policy.policyLink || "",
            implementation: policy.implementation || {},
            evaluation: policy.evaluation || {},
            participation: policy.participation || {},
            alignment: policy.alignment || {},
            status: policy.status || "pending",
            admin_notes: policy.admin_notes || ""
          }))
        })),
        submission_status: "pending"
      };

      await apiService.post('/policy/submit-enhanced-form', submissionData);
      
      setSuccess("Policies submitted successfully! Your submission is now pending admin review.");

      // Reset form
      setPolicyAreasState(() => {
        const areas = {};
        POLICY_AREAS.forEach(area => {
          areas[area.id] = [];
        });
        return areas;
      });
      setFormData({ country: "" });
      setSelectedPolicyArea(null);
      setSelectedPolicyIndex(null);

    } catch (error) {
      setError(`Submission failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentPolicy = () => {
    if (!selectedPolicyArea || selectedPolicyIndex === null) return null;
    return policyAreasState[selectedPolicyArea][selectedPolicyIndex];
  };

  const getTotalPolicies = () => {
    return Object.values(policyAreasState).reduce((total, policies) => total + policies.length, 0);
  };

  const renderPolicyAreaCard = (area) => {
    const policies = policyAreasState[area.id] || [];
    const hasMaxPolicies = policies.length >= 10;

    return (
      <div key={area.id} className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300">
        <div className={`p-6 bg-gradient-to-r ${area.color} text-white`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                <span className="text-2xl">{area.icon}</span>
              </div>
              <div>
                <h3 className="text-xl font-bold">{area.name}</h3>
                <p className="text-sm opacity-90">{area.description}</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{policies.length}</div>
              <div className="text-sm opacity-90">policies</div>
            </div>
          </div>
        </div>

        <div className="p-6">
          {policies.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p>No policies added yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {policies.map((policy, index) => (
                <div
                  key={index}
                  className={`p-4 border-2 rounded-xl cursor-pointer transition-all ${
                    selectedPolicyArea === area.id && selectedPolicyIndex === index
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                  onClick={() => {
                    setSelectedPolicyArea(area.id);
                    setSelectedPolicyIndex(index);
                    setActiveTab("basic");
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">
                        {policy.policyName || `Policy ${index + 1}`}
                      </h4>
                      <p className="text-sm text-gray-600 truncate">
                        {policy.policyDescription || "No description"}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>Budget: {policy.implementation.yearlyBudget || 'Not set'}</span>
                        <span>Year: {policy.implementation.deploymentYear}</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removePolicyFromArea(area.id, index);
                      }}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-all"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <button
            onClick={() => addPolicyToArea(area.id)}
            disabled={hasMaxPolicies}
            className={`w-full mt-4 py-3 rounded-xl font-semibold transition-all ${
              hasMaxPolicies
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : `bg-gradient-to-r ${area.color} text-white hover:opacity-90`
            }`}
          >
            {hasMaxPolicies ? 'Maximum policies reached' : '+ Add Policy'}
          </button>
        </div>
      </div>
    );
  };

  const renderPolicyEditor = () => {
    const currentPolicy = getCurrentPolicy();
    if (!currentPolicy) {
      return (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 text-center">
          <svg className="w-24 h-24 mx-auto mb-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">Select a Policy to Edit</h3>
          <p className="text-gray-500">Choose a policy from the areas above to start editing its details.</p>
        </div>
      );
    }

    const selectedArea = POLICY_AREAS.find(area => area.id === selectedPolicyArea);

    return (
      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
        <div className={`p-6 bg-gradient-to-r ${selectedArea.color} text-white`}>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={selectedArea.icon} />
              </svg>
            </div>
            <div>
              <h3 className="text-xl font-bold">{selectedArea.name}</h3>
              <p className="text-sm opacity-90">Policy {selectedPolicyIndex + 1} of {policyAreasState[selectedPolicyArea].length}</p>
            </div>
          </div>
        </div>

        {/* Policy Editor Tabs */}
        <div className="border-b border-gray-200">
          <div className="flex space-x-1 p-4">
            {[
              { key: "basic", label: "Basic Info", icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
              { key: "implementation", label: "Implementation", icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" },
              { key: "evaluation", label: "Evaluation", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
              { key: "participation", label: "Participation", icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" },
              { key: "alignment", label: "Alignment", icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.key
                    ? `bg-gradient-to-r ${selectedArea.color} text-white shadow-lg`
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
                </svg>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Policy Editor Content */}
        <div className="p-6">
          {activeTab === "basic" && renderBasicInfo()}
          {activeTab === "implementation" && renderImplementation()}
          {activeTab === "evaluation" && renderEvaluation()}
          {activeTab === "participation" && renderParticipation()}
          {activeTab === "alignment" && renderAlignment()}
        </div>
      </div>
    );
  };

  const renderBasicInfo = () => {
    const currentPolicy = getCurrentPolicy();
    const uploadKey = `${selectedPolicyArea}-${selectedPolicyIndex}`;

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Policy Name *
            </label>
            <input
              type="text"
              value={currentPolicy.policyName}
              onChange={(e) => updatePolicy(selectedPolicyArea, selectedPolicyIndex, "policyName", e.target.value)}
              className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="Enter policy name"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Policy ID
            </label>
            <input
              type="text"
              value={currentPolicy.policyId}
              onChange={(e) => updatePolicy(selectedPolicyArea, selectedPolicyIndex, "policyId", e.target.value)}
              className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="Policy Name - Nolicy number"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Target Groups
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {TARGET_GROUPS.map(group => (
              <label key={group} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={currentPolicy.targetGroups.includes(group)}
                  onChange={() => toggleArrayItem(selectedPolicyArea, selectedPolicyIndex, null, "targetGroups", group)}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">{group}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Policy Description
          </label>
          <textarea
            value={currentPolicy.policyDescription}
            onChange={(e) => updatePolicy(selectedPolicyArea, selectedPolicyIndex, "policyDescription", e.target.value)}
            className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
            rows="4"
            placeholder="Describe the policy in detail..."
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Policy Document
          </label>
          <div className="space-y-3">
            <input
              type="file"
              onChange={(e) => {
                const file = e.target.files[0];
                if (file) {
                  handleFileUpload(selectedPolicyArea, selectedPolicyIndex, file);
                }
              }}
              className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              accept=".pdf,.doc,.docx,.txt"
              disabled={fileUploading[uploadKey]}
            />
            
            <div className="flex gap-3">
              <button
                onClick={() => {
                  const fileInput = document.createElement('input');
                  fileInput.type = 'file';
                  fileInput.accept = '.pdf,.doc,.docx,.txt';
                  fileInput.onchange = (e) => {
                    const file = e.target.files[0];
                    if (file) {
                      handleFileUpload(selectedPolicyArea, selectedPolicyIndex, file);
                    }
                  };
                  fileInput.click();
                }}
                className="flex-1 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-all font-medium flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                </svg>
                Manual Upload
              </button>
              <button
                onClick={() => {
                  const fileInput = document.createElement('input');
                  fileInput.type = 'file';
                  fileInput.accept = '.pdf,.doc,.docx,.txt';
                  fileInput.onchange = (e) => {
                    const file = e.target.files[0];
                    if (file) {
                      setAutoFillFile(file);
                      setShowAutoFillModal(true);
                    }
                  };
                  fileInput.click();
                }}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-lg hover:from-purple-600 hover:to-blue-600 transition-all font-medium flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                AI Auto-Fill
              </button>
            </div>
            
            {fileUploading[uploadKey] && (
              <div className="flex items-center gap-2 p-3 bg-yellow-50 text-yellow-700 rounded-lg">
                <div className="animate-spin w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full"></div>
                <span className="text-sm font-medium">Uploading...</span>
              </div>
            )}
            
            {currentPolicy.policyFile && (
              <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-green-800">{currentPolicy.policyFile.name}</p>
                    <p className="text-sm text-green-600">
                      {(currentPolicy.policyFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => handleAutoFillFromUploadedFile(currentPolicy.policyFile)}
                    disabled={autoFillLoading}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-all text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {autoFillLoading ? 'Analyzing...' : 'Auto Fill'}
                  </button>
                  <button 
                    onClick={() => updatePolicy(selectedPolicyArea, selectedPolicyIndex, "policyFile", null)}
                    className="px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-all text-sm font-medium"
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Policy Link (Optional)
          </label>
          <input
            type="url"
            value={currentPolicy.policyLink}
            onChange={(e) => updatePolicy(selectedPolicyArea, selectedPolicyIndex, "policyLink", e.target.value)}
            className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            placeholder="https://..."
          />
        </div>
      </div>
    );
  };

  const renderImplementation = () => {
    const currentPolicy = getCurrentPolicy();
    
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Yearly Budget
            </label>
            <input
              type="number"
              value={currentPolicy.implementation.yearlyBudget}
              onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "implementation", "yearlyBudget", e.target.value)}
              className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
              placeholder="Enter budget amount"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Currency
            </label>
            <select
              value={currentPolicy.implementation.budgetCurrency}
              onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "implementation", "budgetCurrency", e.target.value)}
              className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
            >
              {CURRENCIES.map(currency => (
                <option key={currency} value={currency}>{currency}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={currentPolicy.implementation.privateSecFunding}
              onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "implementation", "privateSecFunding", e.target.checked)}
              className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
            />
            <span className="font-medium text-emerald-800">Private Sector Funding</span>
          </label>
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Deployment Year
          </label>
          <input
            type="number"
            value={currentPolicy.implementation.deploymentYear}
            onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "implementation", "deploymentYear", parseInt(e.target.value) || new Date().getFullYear())}
            className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
            min="1900"
            max="2025"
          />
        </div>
      </div>
    );
  };

  const renderEvaluation = () => {
    const currentPolicy = getCurrentPolicy();
    
    return (
      <div className="space-y-6">
        <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={currentPolicy.evaluation.isEvaluated}
              onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "evaluation", "isEvaluated", e.target.checked)}
              className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
            />
            <span className="font-medium text-purple-800">Policy has been evaluated</span>
          </label>
        </div>

        {currentPolicy.evaluation.isEvaluated && (
          <div className="space-y-6 border-t border-gray-200 pt-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Evaluation Type
              </label>
              <select
                value={currentPolicy.evaluation.evaluationType}
                onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "evaluation", "evaluationType", e.target.value)}
                className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
              >
                <option value="internal">Internal</option>
                <option value="external">External</option>
                <option value="mixed">Mixed</option>
              </select>
            </div>

            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentPolicy.evaluation.riskAssessment}
                  onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "evaluation", "riskAssessment", e.target.checked)}
                  className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
                />
                <span className="font-medium text-orange-800">Risk Assessment Conducted</span>
              </label>
            </div>

            <div className="space-y-6">
              <h5 className="text-lg font-semibold text-gray-800">Evaluation Scores</h5>
              
              {[
                { key: 'transparencyScore', label: 'Transparency Score', color: 'blue' },
                { key: 'explainabilityScore', label: 'Explainability Score', color: 'red' },
                { key: 'accountabilityScore', label: 'Accountability Score', color: 'green' }
              ].map(({ key, label, color }) => (
                <div key={key} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <label className="text-sm font-semibold text-gray-700">
                      {label} (0-10)
                    </label>
                    <span className={`px-3 py-1 bg-${color}-100 text-${color}-900 rounded-lg font-bold`}>
                      {currentPolicy.evaluation[key]}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="10"
                    value={currentPolicy.evaluation[key]}
                    onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "evaluation", key, parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderParticipation = () => {
    const currentPolicy = getCurrentPolicy();
    
    return (
      <div className="space-y-6">
        <div className="p-4 bg-teal-50 rounded-lg border border-teal-200">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={currentPolicy.participation.hasConsultation}
              onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "participation", "hasConsultation", e.target.checked)}
              className="w-5 h-5 text-teal-600 rounded focus:ring-teal-500"
            />
            <span className="font-medium text-teal-800">Public Consultation Conducted</span>
          </label>
        </div>

        {currentPolicy.participation.hasConsultation && (
          <div className="space-y-6 border-t border-gray-200 pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Consultation Start Date
                </label>
                <input
                  type="date"
                  value={currentPolicy.participation.consultationStartDate}
                  onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "participation", "consultationStartDate", e.target.value)}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Consultation End Date
                </label>
                <input
                  type="date"
                  value={currentPolicy.participation.consultationEndDate}
                  onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "participation", "consultationEndDate", e.target.value)}
                  className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <div className="p-4 bg-cyan-50 rounded-lg border border-cyan-200">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentPolicy.participation.commentsPublic}
                  onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "participation", "commentsPublic", e.target.checked)}
                  className="w-5 h-5 text-cyan-600 rounded focus:ring-cyan-500"
                />
                <span className="font-medium text-cyan-800">Comments Made Public</span>
              </label>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-sm font-semibold text-gray-700">
                  Stakeholder Engagement Score (0-10)
                </label>
                <span className="px-3 py-1 bg-teal-100 text-teal-700 rounded-lg font-bold">
                  {currentPolicy.participation.stakeholderScore}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="10"
                value={currentPolicy.participation.stakeholderScore}
                onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "participation", "stakeholderScore", parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderAlignment = () => {
    const currentPolicy = getCurrentPolicy();
    
    return (
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            AI Principles Alignment
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {PRINCIPLES.map(principle => (
              <label key={principle} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-all">
                <input
                  type="checkbox"
                  checked={currentPolicy.alignment.aiPrinciples.includes(principle)}
                  onChange={() => toggleArrayItem(selectedPolicyArea, selectedPolicyIndex, "alignment", "aiPrinciples", principle)}
                  className="w-4 h-4 text-green-600 rounded focus:ring-green-500"
                />
                <span className="text-sm font-medium text-gray-700">{principle}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <h5 className="text-lg font-semibold text-gray-800">Additional Considerations</h5>
          
          <div className="space-y-3">
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentPolicy.alignment.humanRightsAlignment}
                  onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "alignment", "humanRightsAlignment", e.target.checked)}
                  className="w-5 h-5 text-green-600 rounded focus:ring-green-500"
                />
                <span className="font-medium text-green-800">Human Rights Alignment</span>
              </label>
            </div>

            <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentPolicy.alignment.environmentalConsiderations}
                  onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "alignment", "environmentalConsiderations", e.target.checked)}
                  className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
                />
                <span className="font-medium text-emerald-800">Environmental Considerations</span>
              </label>
            </div>

            <div className="p-4 bg-teal-50 rounded-lg border border-teal-200">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentPolicy.alignment.internationalCooperation}
                  onChange={(e) => updatePolicySection(selectedPolicyArea, selectedPolicyIndex, "alignment", "internationalCooperation", e.target.checked)}
                  className="w-5 h-5 text-teal-600 rounded focus:ring-teal-500"
                />
                <span className="font-medium text-teal-800">International Cooperation</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Move this check **after all hooks**
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Loading user data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">
            Policy Submission
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Submit comprehensive policy information across multiple areas for admin review and database storage.
          </p>
        </div>

        {/* User Info Card */}
        <UserSubmissionCard user={user} />

        {/* Auto-Fill Quick Action */}
        <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 rounded-2xl shadow-xl border border-gray-200 p-6 mb-8 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h3 className="text-2xl font-bold mb-2">AI-Powered Auto-Fill</h3>
                <p className="text-lg opacity-90">Upload a policy document and let AI extract all the information automatically</p>
                <p className="text-sm opacity-75 mt-1">Supports PDF, DOC, DOCX, and TXT files</p>
              </div>
            </div>
            <button
              onClick={() => setShowAutoFillModal(true)}
              className="px-8 py-4 bg-white text-purple-600 font-bold rounded-xl hover:bg-gray-50 transition-all transform hover:scale-105 shadow-lg flex items-center gap-3"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
              </svg>
              Auto-Fill from Document
            </button>
          </div>
        </div>

        {/* User Info and Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Total Policies</p>
                <p className="text-2xl font-bold text-gray-900">{getTotalPolicies()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-r from-yellow-500 to-orange-600 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Areas Covered</p>
                <p className="text-2xl font-bold text-gray-900">{Object.values(policyAreasState).filter(policies => policies.length > 0).length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 012 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Max per Area</p>
                <p className="text-2xl font-bold text-gray-900">10</p>
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-medium">{error}</span>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 text-green-700 rounded-xl">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-medium">{success}</span>
            </div>
          </div>
        )}

        {/* Country Selection */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-800">Country Selection</h3>
          </div>

          <div className="relative">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Country *
            </label>
            <input
              type="text"
              value={formData.country}
              onChange={(e) => {
                setFormData(prev => ({ ...prev, country: e.target.value }));
                setShowCountryDropdown(true);
              }}
              onFocus={() => setShowCountryDropdown(true)}
              className="text-black w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="Type to search countries..."
            />
            
            {showCountryDropdown && filteredCountries.length > 0 && (
              <div className="text-black absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-xl shadow-xl max-h-60 overflow-y-auto">
                {filteredCountries.slice(0, 10).map((country) => (
                  <button
                    key={country}
                    onClick={() => handleCountrySelect(country)}
                    className="w-full text-left px-4 py-3 hover:bg-blue-500 transition-colors border-b border-gray-100 last:border-0"
                  >
                    <div className="flex items-center gap-3">
                      <div className=" w-6 h-6 bg-blue-400 rounded-full flex items-center justify-center">
                        <svg className="w-3 h-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      {country}
                    </div>
                  </button>
                ))}
              </div>
            )}
            
            {formData.country && !countries.includes(formData.country) && filteredCountries.length === 0 && (
              <p className="text-sm text-red-600 mt-1 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Country not found. Please select from the list.
              </p>
            )}
          </div>
        </div>

        {/* Policy Areas Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
          {POLICY_AREAS.map(area => renderPolicyAreaCard(area))}
        </div>

        {/* Policy Editor */}
        {renderPolicyEditor()}

        {/* Auto-Fill Modal */}
        {showAutoFillModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-3xl font-bold text-gray-800">AI Auto-Fill from Document</h2>
                  <button
                    onClick={() => {
                      setShowAutoFillModal(false);
                      setAutoFillFile(null);
                    }}
                    className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-all"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="space-y-6">
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center flex-shrink-0">
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-blue-800 mb-2">How AI Auto-Fill Works</h3>
                        <ul className="text-sm text-blue-700 space-y-1">
                          <li>• Upload your policy document (PDF, DOC, DOCX, TXT)</li>
                          <li>• AI analyzes the content and extracts structured information</li>
                          <li>• All form fields are automatically populated</li>
                          <li>• Review and modify the extracted data as needed</li>
                          <li>• Submit your complete policy information</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-200">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-amber-500 rounded-lg flex items-center justify-center">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-amber-800">Note</p>
                        <p className="text-xs text-amber-700">AI extraction is best-effort. Always review and verify the extracted information before submission.</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      Select Policy Document
                    </label>
                    <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition-all">
                      <input
                        type="file"
                        id="autoFillFile"
                        onChange={(e) => setAutoFillFile(e.target.files[0])}
                        className="hidden"
                        accept=".pdf,.doc,.docx,.txt"
                      />
                      <label htmlFor="autoFillFile" className="cursor-pointer">
                        <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                          <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                          </svg>
                        </div>
                        <p className="text-lg font-medium text-gray-700 mb-2">
                          Click to upload or drag and drop
                        </p>
                        <p className="text-sm text-gray-500">
                          PDF, DOC, DOCX, TXT files up to 10MB
                        </p>
                      </label>
                    </div>

                    {autoFillFile && (
                      <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-xl">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                          <div>
                            <p className="font-medium text-green-800">{autoFillFile.name}</p>
                            <p className="text-sm text-green-600">
                              {(autoFillFile.size / 1024).toFixed(1)} KB - Ready for analysis
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex gap-4 pt-4">
                    <button
                      onClick={() => {
                        setShowAutoFillModal(false);
                        setAutoFillFile(null);
                      }}
                      className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-all font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleAutoFillFromDocument(autoFillFile)}
                      disabled={!autoFillFile || autoFillLoading}
                      className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
                    >
                      {autoFillLoading ? (
                        <>
                          <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                          Analyzing Document...
                        </>
                      ) : (
                        <>
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          Start AI Analysis
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-center pt-8">
          <button 
            onClick={handleSubmit}
            disabled={loading || getTotalPolicies() === 0}
            className="inline-flex items-center gap-3 px-12 py-4 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white font-bold rounded-2xl hover:from-blue-700 hover:via-purple-700 hover:to-pink-700 transition-all transform hover:scale-105 shadow-xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none text-lg"
          >
            {loading ? (
              <>
                <div className="animate-spin w-6 h-6 border-2 border-white border-t-transparent rounded-full"></div>
                Submitting...
              </>
            ) : (
              <>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                Submit {getTotalPolicies()} Policies for Review
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PolicySubmissionForm;