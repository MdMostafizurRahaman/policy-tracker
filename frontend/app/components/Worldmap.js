'use client';
import useMapInteractions from "../hooks/useMapInteractions";
import MapView from "./MapView";

export default function Worldmap() {
  const { countries, geoFeatures, tooltipContent, hoveredCountry, handleHover, handleClick } = useMapInteractions();

  return (
    <MapView
      type="map"
      geoFeatures={geoFeatures}
      countries={countries}
      tooltipContent={tooltipContent}
      hoveredCountry={hoveredCountry}
      handleHover={handleHover}
      handleClick={handleClick}
    />
  );
}
