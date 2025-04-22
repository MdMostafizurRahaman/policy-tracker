'use client';
import { useEffect, useRef } from "react";
import useMapInteractions from "../hooks/useMapInteractions";
import MapView from "./MapView";

export default function GlobeView() {
  const {
    countries,
    geoFeatures,
    tooltipContent,
    hoveredCountry,
    setHoveredCountry, // Ensure this is destructured
    setTooltipContent, // Ensure this is destructured
  } = useMapInteractions();
  const globeRef = useRef(null);

  // Enable auto-rotation on mount
  useEffect(() => {
    if (globeRef.current) {
      globeRef.current.controls().autoRotate = true;
      globeRef.current.controls().autoRotateSpeed = 1.5; // Adjust speed as needed
    }
  }, []);

  // Handle hover interaction
  const handlePolygonHover = (feat) => {
    if (feat) {
      const countryName = feat.properties.name;
      const countryData = countries?.[countryName];
      setHoveredCountry(countryName);
      setTooltipContent({
        name: countryName,
        total: countryData?.total_policies || 0,
      });
      if (globeRef.current) {
        globeRef.current.controls().autoRotate = false; // Stop rotation on hover
      }
    } else {
      setHoveredCountry(null);
      setTooltipContent(null);
      if (globeRef.current) {
        globeRef.current.controls().autoRotate = true; // Resume rotation when hover ends
      }
    }
  };

  // Handle click interaction
  const handlePolygonClick = (feat) => {
    const countryName = feat.properties.name;
    alert(`You clicked on ${countryName}`);
    if (globeRef.current) {
      globeRef.current.controls().autoRotate = false; // Stop rotation on click
    }
  };

  return (
    <MapView
      type="globe"
      geoFeatures={geoFeatures}
      countries={countries}
      tooltipContent={tooltipContent}
      hoveredCountry={hoveredCountry}
      handleHover={handlePolygonHover}
      handleClick={handlePolygonClick}
      globeRef={globeRef} // Pass the ref to MapView
    />
  );
}