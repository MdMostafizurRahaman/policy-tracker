'use client';
import dynamic from "next/dynamic";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";

// Dynamically import react-globe.gl to avoid SSR issues
const Globe = dynamic(() => import("react-globe.gl"), { ssr: false });

export default function MapView({ type, geoFeatures, countries, tooltipContent, hoveredCountry, handleHover, handleClick, globeRef }) {
  if (type === "globe") {
    return (
      <div style={{ position: "relative", height: "100vh", width: "100%" }}>
        <Globe
          ref={globeRef} // Attach the ref to the Globe component
          globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
          backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
          polygonsData={geoFeatures}
          polygonCapColor={(feat) => {
            const name = feat.properties.name;
            if (hoveredCountry === name) return "#FFD700"; // Highlight color on hover
            const countryData = countries?.[name];
            return countryData ? countryData.color : "rgba(200, 200, 200, 0.6)";
          }}
          polygonSideColor={() => "rgba(100, 100, 100, 0.2)"}
          polygonStrokeColor={() => "#111"}
          polygonLabel={({ properties: p }) => `
            <b>${p.name}</b><br />
            ${countries?.[p.name]?.total_policies ?? "N/A"} policies
          `}
          onPolygonHover={handleHover}
          onPolygonClick={handleClick}
          polygonsTransitionDuration={300}
        />
        {tooltipContent && (
          <div style={{
            position: "absolute",
            top: "10px",
            left: "10px",
            background: "rgba(0, 0, 0, 0.7)",
            color: "#FFF",
            padding: "5px 10px",
            borderRadius: "4px",
            pointerEvents: "none",
          }}>
            <strong>{tooltipContent.name}</strong>
            <div>Total Policies: {tooltipContent.total}</div>
          </div>
        )}
      </div>
    );
  }

  // Render flat map
  return (
    <div style={{ position: "relative" }}>
      <ComposableMap projection="geoMercator" style={{ width: "100%", height: "500px" }}>
        <Geographies geography="/countries-110m.json">
          {({ geographies }) =>
            geographies.map((geo) => {
              const countryName = geo.properties.name;
              const countryData = countries?.[countryName];
              const isHighlighted = hoveredCountry === countryName;
              const fillColor = countryData ? countryData.color : "#EEE";

              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={isHighlighted ? "#FFD700" : fillColor}
                  stroke="#FFF"
                  strokeWidth={0.5}
                  onMouseEnter={() => handleHover(geo)}
                  onMouseLeave={() => handleHover(null)}
                  onClick={() => handleClick(geo)}
                  style={{
                    default: { outline: "none" },
                    hover: { outline: "none" },
                    pressed: { outline: "none" },
                  }}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>
      {tooltipContent && (
        <div style={{
          position: "absolute",
          top: "10px",
          left: "10px",
          background: "rgba(0, 0, 0, 0.7)",
          color: "#FFF",
          padding: "5px 10px",
          borderRadius: "4px",
          pointerEvents: "none",
        }}>
          <strong>{tooltipContent.name}</strong>
          <div>Total Policies: {tooltipContent.total}</div>
        </div>
      )}
    </div>
  );
}