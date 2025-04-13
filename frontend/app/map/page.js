import WorldMap from "./components/Worldmap"

export default function MapPage() {
  return (
    <main style={{ maxWidth: "1000px", margin: "0 auto", padding: "20px" }}>
      <h1>Global Policy Implementation Tracker</h1>
      <div style={{ 
        marginTop: "20px",
        border: "1px solid #DDD",
        borderRadius: "8px",
        overflow: "hidden"
      }}>
        <WorldMap />
      </div>
      
      <div style={{ marginTop: "20px", display: "flex", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center" }}>
          <div style={{
            width: "20px",
            height: "20px",
            background: "#FF0000",
            marginRight: "8px"
          }}></div>
          <span>0-3 Policies</span>
        </div>
        <div style={{ display: "flex", alignItems: "center" }}>
          <div style={{
            width: "20px",
            height: "20px",
            background: "#FFD700",
            marginRight: "8px"
          }}></div>
          <span>4-7 Policies</span>
        </div>
        <div style={{ display: "flex", alignItems: "center" }}>
          <div style={{
            width: "20px",
            height: "20px",
            background: "#00AA00",
            marginRight: "8px"
          }}></div>
          <span>8-10 Policies</span>
        </div>
      </div>
    </main>
  )
}