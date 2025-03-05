import React, { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import 'mapbox-gl/dist/mapbox-gl.css';
import "./App.css";

mapboxgl.accessToken = "pk.eyJ1IjoibWluZ2NhbiIsImEiOiJjbTJtMTBycHEwaHB2Mmlwd21udHhnN2wxIn0.oeKsHIH-fmTg7Sd5BCusig";

function App() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);

  useEffect(() => {
    mapRef.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/streets-v11",
      center: [-106.8175, 39.1911], // Default coordinates
      zoom: 7,
    });

    mapRef.current.on('load', () => {
      mapRef.current.addSource('custom-layer', {
        type: 'raster',
        tiles: ["https://ullr.snowmap.ai/tiles/snodas.depth/{z}/{x}/{y}"],  // TODO Implement your own tile server
        tileSize: 256,
      });

      mapRef.current.addLayer({
        id: 'custom-layer',
        type: 'raster',
        source: 'custom-layer',
        paint: {
          'raster-opacity': 0.5,
        },
      });
    });

    return () => mapRef.current.remove();
  }, []);

  return <div ref={mapContainer} className="map-container" />;
}

export default App;
