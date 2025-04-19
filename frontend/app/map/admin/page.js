'use client'
import { useState, useEffect } from "react"

export default function AdminPage() {
  const [pendingSubmissions, setPendingSubmissions] = useState([])

  useEffect(() => {
    fetchPendingSubmissions()
  }, [])

  const fetchPendingSubmissions = async () => {
    const response = await fetch("http://localhost:8000/api/pending-submissions")
    const data = await response.json()
    setPendingSubmissions(data)
  }

  const approveSubmission = async (country) => {
    const response = await fetch("http://localhost:8000/api/approve-submission", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ country }),
    });
  
    if (response.ok) {
      alert(`Submission for ${country} approved!`);
      fetchPendingSubmissions();
    } else {
      alert("Failed to approve submission.");
    }
  };

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "20px" }}>
      <h2 style={{ textAlign: "center", marginBottom: "20px" }}>Admin Panel</h2>
      {pendingSubmissions.length === 0 ? (
        <p style={{ textAlign: "center" }}>No pending submissions.</p>
      ) : (
        <ul>
          {pendingSubmissions.map((submission, index) => (
            <li key={index} style={{ marginBottom: "20px", border: "1px solid #ccc", padding: "10px", borderRadius: "5px" }}>
              <h3>{submission.country}</h3>
              <button
                onClick={() => approveSubmission(submission.country)}
                style={{
                  padding: "10px 20px",
                  background: "#28A745",
                  color: "#FFF",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                }}
              >
                Approve
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}