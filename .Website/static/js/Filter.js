import React from "react";
import "./Filter.css"

export default class Filter extends React.Component {
    static defaultProps = {
        title: "untitled"
    };

    render = () => {
        let opacity = this.props.isactivetag(this.props.tag) ? 1 : .25;
        let markerIcon = this.props.grouptype + 'Marker_2'
        return (
            <label style={{opacity: opacity}} className="Filter-label">
                <img style={this.props.style} className="Filter-img" src={`static/images/${markerIcon}.png`}></img>
                <input style={{display: "none"}} grouptype={this.props.grouptype} tag={this.props.tag} className="Filter-checkbox" type="checkbox" checked={this.props.checkedgroupids.includes(this.props.filterid)} value={this.props.filterid} onChange={this.props.handlesinglecheck}/>
                <span style={this.props.style} className="Filter-title">{this.props.tag} ({this.props.count})</span>
            </label>
        );
    }

}