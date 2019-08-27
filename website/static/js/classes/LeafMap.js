import React from 'react';
import L from 'leaflet';

export class LeafMap extends React.Component {
  constructor() {
    super()
    this.state = {
      initialLat: 37.6872,
      initialLng: -97.3301,
      initialZoom: 12.5,
      apiToken: 'pk.eyJ1Ijoia2Fuc2FzIiwiYSI6ImNqemN2dzJjMDAwM3gzaW80am81aGlyZmEifQ.oIqSPm9agdE1c87LkUzHwg'
    }
  }
  componentDidMount() {
    this.map = L.map('map', {
      center: [this.state.initialLat, this.state.initialLng],
      zoom: this.state.initialZoom,
      layers: [
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png?access_token={accessToken}', {
          attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
          accessToken: this.state.apiToken
        }),
      ]
    });
    L.control.layers().addTo(this.map);
  }

  render() {
    return (
      <div id="map"></div>

    );
  }
}
