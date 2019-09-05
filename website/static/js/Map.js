import GoogleMap  from "google-map-react";
import React from "react";

export default class Map extends React.Component {
  static defaultProps = {
    center: [37.6872, -97.3301],
    zoom: 13
  };

  render() {
    return <GoogleMap center={this.props.center} zoom={this.props.zoom} 
      bootstrapURLKeys={{ key: "AIzaSyDUfEWFUwRP1EAtFrAw2pEVysDm8OYEcDQ" }}
    />;

  }
}
