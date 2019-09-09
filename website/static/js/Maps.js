import React from "react";
import ReactDOM from "react-dom";
import GoogleMap from "./GoogleMap";

ReactDOM.render(
    <GoogleMap center={{lat: 37.6872, lng: -97.3301}} zoom={13} />, 
    document.getElementById('leaflet-map')
);