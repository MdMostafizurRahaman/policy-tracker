'use client'
import { useState } from "react"

export default function PolicySubmissionForm() {
  const [country, setCountry] = useState("")
  const [policies, setPolicies] = useState(Array(10).fill({ file: null, text: "" }))

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

  const handlePolicyChange = (index, field, value) => {
    const updatedPolicies = [...policies]
    updatedPolicies[index][field] = value
    setPolicies(updatedPolicies)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const formData = new FormData()
    formData.append("country", country)
    policies.forEach((policy, index) => {
      if (policy.file) {
        formData.append(`policy_${index + 1}_file`, policy.file)
      } else if (policy.text) {
        formData.append(`policy_${index + 1}_text`, policy.text)
      }
    })

    try {
        const response = await fetch("http://localhost:8000/api/submit-policy", {
          method: "POST",
          body: formData,
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        alert("Submission sent for approval!");
      } catch (error) {
        console.error("Failed to fetch:", error);
        alert("Failed to submit. Please try again.");
      }
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: "600px", margin: "0 auto", padding: "20px", border: "1px solid #ccc", borderRadius: "8px", background: "#f9f9f9", color: "#333" }}>
      <h2 style={{ textAlign: "center", marginBottom: "20px", color: "#333" }}>Upload Policy for a Country</h2>
      <div style={{ marginBottom: "10px", color: "#333" }}>
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
        <div key={index} style={{ marginBottom: "20px" }}>
          <label style={{ fontWeight: "bold" }}>{policyName}:</label>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "5px" }}>
            <input
              type="file"
              onChange={(e) => handlePolicyChange(index, "file", e.target.files[0])}
              style={{ padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
            <input
              type="text"
              placeholder="Or enter a link"
              value={policies[index].text}
              onChange={(e) => handlePolicyChange(index, "text", e.target.value)}
              style={{ padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
            />
          </div>
        </div>
      ))}
      <button type="submit" style={{ padding: "10px 20px", background: "#007BFF", color: "#FFF", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "16px" }}>
        Submit
      </button>
    </form>
  )
}