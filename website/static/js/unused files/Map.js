import GoogleMap  from "google-map-react";
import React from "react";
import Marker from "./Marker"

export default class Map extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      markers: []
    }
  }

  static defaultProps = {
    center: [37.6872, -97.3301],
    zoom: 13
  };

  getDataAndCreateMarkers = () => {
    var _this = this;
    var xhr = new XMLHttpRequest();
    //var startPicker = document.getElementById('datepicker-start');
    //var endPicker = document.getElementById('datepicker-end');
    
    //var dateString = moment(startPicker.getDate()).format('MM-DD-YYYY') + '+' + moment(endPicker.getDate()).format('MM-DD-YYYY');
    var dataLink = 'data/08-12-2019+08-22-2019';
    xhr.open('GET', dataLink, true);

    xhr.onload = function() {
      if(this.status >= 200 && this.status < 400) {
        var responseJSON = JSON.parse(this.response);
        _this.createMarkers(responseJSON);
      }
    }
    xhr.send();
  }

  createMarkers = (dataJSON) => {
    let markerArray = dataJSON.map((markerObject) => {
      return <Marker lat = {markerObject.lat} lng = {markerObject.lng} image = {markerObject.identifier}/>
    });

    this.setState({markers: {markerArray}});
    this.forceUpdate();
  }

  componentDidMount = () => {
    this.getDataAndCreateMarkers();
  }

  render() {
    return (
    <GoogleMap center={this.props.center} zoom={this.props.zoom} bootstrapURLKeys={{ key: "AIzaSyDUfEWFUwRP1EAtFrAw2pEVysDm8OYEcDQ" }} key = "yes">
      {this.state.markers.markerArray}
    </GoogleMap>
    );
  }
}
