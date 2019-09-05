import React from "react";
import ReactDOM from "react-dom";
import Map from "./Map";

ReactDOM.render(
    <Map center={[37.6872, -97.3301]} zoom={13} />, 
    document.getElementById('leaflet-map')
);