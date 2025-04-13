export default function Tooltip({ content }) {
    return (
      <div style={{
        position: "absolute",
        bottom: 20,
        left: 20,
        padding: "12px",
        background: "white",
        borderRadius: "4px",
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        borderLeft: `4px solid ${content.color}`
      }}>
        <h3 style={{ margin: 0 }}>{content.name}</h3>
        <p>Total Policies: {content.total}/10</p>
      </div>
    )
  }