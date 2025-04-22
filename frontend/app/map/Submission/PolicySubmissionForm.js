'use client'
import { useState } from "react"

export default function PolicySubmissionForm() {
  const [country, setCountry] = useState("")
  const [policies, setPolicies] = useState(Array(10).fill(null).map(() => ({ file: null, text: "" })))
  const [submitted, setSubmitted] = useState(false)
  
  const policyNames = [
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

  // Fixed the handlePolicyChange function to only update the specific policy
  const handlePolicyChange = (index, field, value) => {
    const updatedPolicies = [...policies]
    updatedPolicies[index] = {
      ...updatedPolicies[index],
      [field]: value
    }
    setPolicies(updatedPolicies)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const formData = new FormData()
    formData.append("country", country)
    
    policies.forEach((policy, index) => {
      if (policy.file) {
        formData.append(`policy_${index + 1}_file`, policy.file)
      }
      if (policy.text) {
        formData.append(`policy_${index + 1}_text`, policy.text)
      }
    })
    
    try {
      const response = await fetch("http://localhost:8000/api/submit-policy", {
        method: "POST",
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      setSubmitted(true)
      alert("Submission sent for approval!")
      // Reset form after successful submission
      setCountry("")
      setPolicies(Array(10).fill(null).map(() => ({ file: null, text: "" })))
    } catch (error) {
      console.error("Failed to submit:", error)
      alert("Failed to submit. Please try again.")
    }
  }

  // File input reset handler
  const handleFileReset = (index) => {
    handlePolicyChange(index, "file", null)
    // Need to reset the file input element
    const fileInput = document.getElementById(`file-input-${index}`)
    if (fileInput) fileInput.value = ""
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: "600px", margin: "0 auto", padding: "20px", border: "1px solid #ccc", borderRadius: "8px", background: "#f9f9f9", color: "#333" }}>
      <h2 style={{ textAlign: "center", marginBottom: "20px", color: "#333" }}>Upload Policy for a Country</h2>
      
      <div style={{ marginBottom: "20px", color: "#333" }}>
        <label style={{ fontWeight: "bold" }}>Country Name:</label>
        <input
          type="text"
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          required
          style={{ width: "100%", padding: "8px", marginTop: "5px", borderRadius: "4px", border: "1px solid #ccc" }}
        />
      </div>
      
      {policyNames.map((policyName, index) => (
        <div key={index} style={{ marginBottom: "20px", padding: "15px", border: "1px solid #eee", borderRadius: "5px" }}>
          <label style={{ fontWeight: "bold", display: "block", marginBottom: "10px" }}>{policyName}:</label>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <input
                id={`file-input-${index}`}
                type="file"
                onChange={(e) => handlePolicyChange(index, "file", e.target.files[0])}
                style={{ flex: 1, padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
              />
              {policies[index].file && (
                <button 
                  type="button" 
                  onClick={() => handleFileReset(index)}
                  style={{ padding: "5px 10px", background: "#dc3545", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}
                >
                  Clear
                </button>
              )}
            </div>
            
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <input
                type="text"
                placeholder="Or enter a link"
                value={policies[index].text || ""}
                onChange={(e) => handlePolicyChange(index, "text", e.target.value)}
                style={{ flex: 1, padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
              />
              {policies[index].text && (
                <button 
                  type="button" 
                  onClick={() => handlePolicyChange(index, "text", "")}
                  style={{ padding: "5px 10px", background: "#dc3545", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}
                >
                  Clear
                </button>
              )}
            </div>
          </div>
          
          {policies[index].file && (
            <div style={{ marginTop: "5px", fontSize: "14px", color: "green" }}>
              Selected file: {policies[index].file.name}
            </div>
          )}
        </div>
      ))}
      
      <button 
        type="submit" 
        style={{ 
          padding: "10px 20px", 
          background: "#007BFF", 
          color: "#FFF", 
          border: "none", 
          borderRadius: "4px", 
          cursor: "pointer", 
          fontSize: "16px",
          width: "100%" 
        }}
      >
        Submit
      </button>
    </form>
  )
}