export default function Tooltip({ content }) {
  return (
    <div style={{
      position: "absolute",
      top: "10px",
      left: "10px",
      background: "#fff",   // White background
      color: "#000",        // Black text
      padding: "5px 10px",
      borderRadius: "4px",
      pointerEvents: "none",
      boxShadow: "0 2px 8px rgba(0,0,0,0.08)" // Optional: subtle shadow for visibility
    }}>
      <strong>{content.name}</strong>
      <div>Total Policies: {content.total}</div>
    </div>
  )
}