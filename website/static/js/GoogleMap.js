import {Map, InfoWindow, Marker, GoogleApiWrapper} from 'google-maps-react';
import React from "react";
import FilterContainer from './FilterContainer';

const Filters = require("./Filters.json");

const MarkerControl = React.createContext();

export class GoogleMap extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      markers: [],
      activeTags: Filters.map(filterObject => filterObject.type),
      ready: false
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
    //var startPicker = document.getElementById('datepicker-start');
    //var endPicker = document.getElementById('datepicker-end');
    
    //var dateString = moment(startPicker.getDate()).format('MM-DD-YYYY') + '+' + moment(endPicker.getDate()).format('MM-DD-YYYY');

    fetch('data/08-12-2019+08-22-2019')
      .then(response => response.json())
      .then(data => this.setState({markers: data, ready: true}));
  }

  createMarkers = (dataJSON) => {
    let markerArray = dataJSON.map((markerObject) => {
      return <Marker key={i} position={{lat: markerObject.lat, lng: markerObject.lng}} icon={{url: `static/images/${markerObject.identifier}.png`}} type={markerObject.identifier} />
    });
  }

  updateTags = (tag) => {
    if(this.state.activeTags.includes(tag)) {
      this.setState(prevState => ({
        activeTags: prevState.activeTags.filter(item => item != tag)
      }));
    } else {
      this.setState(prevState => ({
        activeTags: [...prevState.activeTags, tag]
      }));
    }
  }

  render() {
    let filterContainer = undefined;
    if(this.state.ready)
      filterContainer = <FilterContainer updatetags={this.updateTags}/>

    let markers = this.state.markers.map((markerObject, i) => {
      if(this.state.activeTags.includes(markerObject.identifier))
        return <Marker key={i} position={{lat: markerObject.lat, lng: markerObject.lng}} icon={{url: `static/images/${markerObject.identifier}.png`}} />
    })

    return (
      <Map google={this.props.google} initialCenter={this.props.center} zoom={this.props.zoom} onReady={this.getDataAndCreateMarkers}>
        {filterContainer}
        {markers}
      </Map>
    );
  }
}

export default GoogleApiWrapper({
  apiKey: "AIzaSyDUfEWFUwRP1EAtFrAw2pEVysDm8OYEcDQ"
})(GoogleMap)