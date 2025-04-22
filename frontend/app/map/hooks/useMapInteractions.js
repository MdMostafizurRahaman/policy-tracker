import { useState, useEffect } from "react";

export default function useMapInteractions() {
  const [countries, setCountries] = useState(null);
  const [geoFeatures, setGeoFeatures] = useState([]);
  const [tooltipContent, setTooltipContent] = useState(null);
  const [hoveredCountry, setHoveredCountry] = useState(null);

  // Fetch country data
  useEffect(() => {
    fetch("http://localhost:8000/api/countries")
      .then((res) => res.json())
      .then(setCountries);
  }, []);

  // Fetch geographical features
  useEffect(() => {
    fetch("/countries-110m.json")
      .then((res) => res.json())
      .then((data) => {
        import("topojson-client").then((topojson) => {
          const features = topojson.feature(data, data.objects.countries).features;
          setGeoFeatures(features);
        });
      });
  }, []);

  const handleHover = (feat) => {
    if (feat) {
      const countryName = feat.properties.name;
      const countryData = countries?.[countryName];
      setHoveredCountry(countryName);
      setTooltipContent({
        name: countryName,
        total: countryData?.total_policies || 0,
      });
    } else {
      setHoveredCountry(null);
      setTooltipContent(null);
    }
  };

  const handleClick = (feat) => {
    const countryName = feat.properties.name;
    alert(`You clicked on ${countryName}`);
  };

  return {
    countries,
    geoFeatures,
    tooltipContent,
    hoveredCountry,
    setHoveredCountry, // Ensure this is exported
    setTooltipContent, // Ensure this is exported
    handleHover,
    handleClick,
  };
}