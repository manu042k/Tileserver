// import React, { useRef, useEffect, useState } from 'react';
// import mapboxgl from 'mapbox-gl';
// import 'mapbox-gl/dist/mapbox-gl.css';
// import './App.css';

// // Set your mapbox token here
// mapboxgl.accessToken = 'pk.eyJ1IjoibWluZ2NhbiIsImEiOiJjbTJtMTBycHEwaHB2Mmlwd21udHhnN2wxIn0.oeKsHIH-fmTg7Sd5BCusig';

// function App() {
//   const mapContainer = useRef(null);
//   const map = useRef(null);
//   const [lng, setLng] = useState(-100);
//   const [lat, setLat] = useState(40);
//   const [zoom, setZoom] = useState(3);

//   useEffect(() => {
//     if (map.current) return; // initialize map only once
    
//     map.current = new mapboxgl.Map({
//       container: mapContainer.current,
//       style: {
//         version: 8,
//         sources: {
//           'base-map': {
//             type: 'raster',
//             tiles: [
//               'https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg'
//             ],
//             tileSize: 256,
//             attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'
//           },
//           'snow-depth': {
//             type: 'raster',
//             tiles: [
//               'http://localhost:8000/tiles/{z}/{x}/{y}.png'
//             ],
//             tileSize: 256,
//             attribution: 'Snow depth data rendered locally'
//           }
//         },
//         layers: [
//           {
//             id: 'base-layer',
//             type: 'raster',
//             source: 'base-map',
//             minzoom: 0,
//             maxzoom: 22
//           },
//           {
//             id: 'snow-layer',
//             type: 'raster',
//             source: 'snow-depth',
//             minzoom: 0,
//             maxzoom: 22,
//             paint: {
//               'raster-opacity': 0.7
//             }
//           }
//         ]
//       },
//       center: [lng, lat],
//       zoom: zoom
//     });

//     map.current.on('move', () => {
//       setLng(map.current.getCenter().lng.toFixed(4));
//       setLat(map.current.getCenter().lat.toFixed(4));
//       setZoom(map.current.getZoom().toFixed(2));
//     });
//   });

//   return (
//     <div>
//       <div className="sidebar">
//         Longitude: {lng} | Latitude: {lat} | Zoom: {zoom}
//       </div>
//       <div ref={mapContainer} className="map-container" />
//     </div>
//   );
// }

// export default App;
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
        tiles: ["http://localhost:8000/tiles/{z}/{x}/{y}.png"],  // TODO Implement your own tile server
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
