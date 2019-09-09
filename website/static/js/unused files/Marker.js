import React from "react";
import "./Marker.css"

export default class Marker extends React.PureComponent {
    constructor(props) {
        super(props);
        this.state = {
        }
    }

    static defaultProps = {
        coords: [37.6872, -97.3301],
        info: "error loading info",
        image: ""
    };

    render() {
        return <img src={`static/images/${this.props.image}.png`} className="marker"></img>;
    }
}