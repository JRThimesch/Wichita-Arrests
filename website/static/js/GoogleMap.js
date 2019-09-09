import {Map, InfoWindow, Marker, GoogleApiWrapper} from 'google-maps-react';
import React from "react";
import FilterContainer from './FilterContainer';

export class GoogleMap extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      markers: []
    }
  }

  static defaultProps = {
    center: {
      lat: 37.6872,
      lng: -97.3301
    },
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
    let markerArray = dataJSON.map((markerObject, i) => {
      return <Marker key={i} position={{lat: markerObject.lat, lng: markerObject.lng}} icon={{url: `static/images/${markerObject.identifier}.png`}} type={markerObject.identifier} />
    });

    this.setState({markers: {markerArray}});
    this.forceUpdate();
  }

  componentDidMount = () => {
    this.getDataAndCreateMarkers();
  }

  render() {
    return (
      <Map google={this.props.google} initialCenter={{lat: 37.6872, lng: -97.3301}} zoom={this.props.zoom}>
        <FilterContainer/>
        {this.state.markers.markerArray}
      </Map>
    );
  }
}

export default GoogleApiWrapper({
  apiKey: "AIzaSyDUfEWFUwRP1EAtFrAw2pEVysDm8OYEcDQ"
})(GoogleMap)