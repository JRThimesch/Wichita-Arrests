import React from "react";
import GoogleMap from "./GoogleMap";
import './Maps.css'

export default class Maps extends React.Component {
    render = () => {
        return <GoogleMap center={{lat: 37.6872, lng: -97.3301}} zoom={13}/>
    }
}