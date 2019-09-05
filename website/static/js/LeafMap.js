import React from "react";
import L from "leaflet";

require("pikaday");
require("./leaflet.groupedlayercontrol.js");
require("./styles.css");

export default class LeafMap extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      latitude: 37.6872,
      longitude: -97.3301,
      zoom: 12.5,

      types: {
        VIOLENCE: 'violence',
        DRUGS: 'drug',
        PROPERTY: 'property',
        VEHICLE: 'vehicle',
        SEX: 'sex',
        OTHER: 'other',
        WARRANTS: 'warrant'
      },

      violenceGeneralArr: [],
      drugGeneralArr: [],
      propertyGeneralArr: [],
      vehicleGeneralArr: [],
      sexGeneralArr: [],
      otherGeneralArr: [],
      warrantGeneralArr: [],
    };

  }

  getDataAndCreateMap = () => {
    var _this = this;
      var xhr = new XMLHttpRequest();
      //var startPicker = document.getElementById('datepicker-start');
      //var endPicker = document.getElementById('datepicker-end');
      
      //var dateString = moment(startPicker.getDate()).format('MM-DD-YYYY') + '+' + moment(endPicker.getDate()).format('MM-DD-YYYY');
      var dataLink = 'data/08-02-2019+08-22-2019';
      xhr.open('GET', dataLink, true);

      xhr.onload = function() {
        if(this.status == 200) {
          var responseJSON = JSON.parse(this.response);
          _this.addMarkers(responseJSON);
          _this.createMap();
        }
      }
      xhr.send();      
  }

  addMarkers = (dataJSON) => {
    var violenceGeneralMarkers = [],
    drugGeneralMarkers = [],
    propertyGeneralMarkers = [],
    vehicleGeneralMarkers = [],
    sexGeneralMarkers = [],
    otherGeneralMarkers = [],
    warrantGeneralMarkers = [];

    dataJSON.forEach(element => {
      if (element.identifier === this.state.types.VIOLENCE) {
        violenceGeneralMarkers.push(
          L.marker([element.lat, element.lng]).bindPopup("1")
        );
      } else if (element.identifier === this.state.types.DRUGS) {
        drugGeneralMarkers.push(
          L.marker([element.lat, element.lng]).bindPopup("2")
        );
      } else if (element.identifier === this.state.types.PROPERTY) {
        propertyGeneralMarkers.push(
          L.marker([element.lat, element.lng]).bindPopup("3")
        );
      } else if (element.identifier === this.state.types.VEHICLE) {
        vehicleGeneralMarkers.push(
          L.marker([element.lat, element.lng]).bindPopup("4")
        );
      } else if (element.identifier === this.state.types.SEX) {
        sexGeneralMarkers.push(
          L.marker([element.lat, element.lng]).bindPopup("5")
        );
      } else if (element.identifier === this.state.types.OTHER) {
        otherGeneralMarkers.push(
          L.marker([element.lat, element.lng]).bindPopup("6")
        );
      } else if (element.identifier === this.state.types.WARRANTS) {
        warrantGeneralMarkers.push(
          L.marker([element.lat, element.lng]).bindPopup("7")
        );
      }
    });

    this.setState({violenceGeneralArr: violenceGeneralMarkers});
    this.setState({drugGeneralArr: drugGeneralMarkers});
    this.setState({propertyGeneralArr: propertyGeneralMarkers});
    this.setState({vehicleGeneralArr: vehicleGeneralMarkers});
    this.setState({sexGeneralArr: sexGeneralMarkers});
    this.setState({otherGeneralArr: otherGeneralMarkers});
    this.setState({warrantGeneralArr: warrantGeneralMarkers});

    
  }

  createMap = () => {
    console.log(this.state.drugGeneralArr);
    this.violenceGeneral = L.layerGroup(this.state.violenceGeneralArr);
    this.propertyGeneral = L.layerGroup(this.state.propertyGeneralArr);
    this.drugGeneral = L.layerGroup(this.state.drugGeneralArr);
    this.vehicleGeneral = L.layerGroup(this.state.vehicleGeneralArr);
    this.sexGeneral = L.layerGroup(this.state.sexGeneralArr);
    this.otherGeneral = L.layerGroup(this.state.otherGeneralArr);
    this.warrantGeneral = L.layerGroup(this.state.warrantGeneralArr);

    this.map = L.map("map", {
      center: [37.6402, -97.3301],
      zoom: 11,
      layers: [
        this.violenceGeneral,
        this.propertyGeneral,
        this.drugGeneral,
        this.vehicleGeneral,
        this.sexGeneral,
        this.otherGeneral,
        this.warrantGeneral,
        L.tileLayer("http://{s}.tile.osm.org/{z}/{x}/{y}.png", {
          attribution:
            '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        })
      ]
    });

    this.groupedOverlays = {
      Violence: {
        General: this.violenceGeneral
      },
      Drugs: {
        General: this.drugGeneral
      },
      Property: {
        General: this.propertyGeneral
      },
      Vehicle: {
        General: this.vehicleGeneral
      },
      Sex: {
        General: this.sexGeneral
      },
      Other: {
        General: this.otherGeneral
      },
      Warrants: {
        General: this.warrantGeneral
      }
    };

    this.options = {
      groupCheckboxes: true
    };

    L.control
      .groupedLayers(null, this.groupedOverlays, this.options)
      .addTo(this.map);

    }

  componentDidMount() {    
    this.getDataAndCreateMap();
  }
  render() {
    return <div id="map"/>;
  }
}

