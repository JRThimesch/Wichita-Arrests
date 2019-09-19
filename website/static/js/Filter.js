import React from "react";
import "./Filter.css"

export default class Filter extends React.Component {
    static defaultProps = {
        title: "untitled"
    };

    render = () => {
        let opacity = this.props.checkedfilters.includes(this.props.filterid) ? 1 : .25;

        return (
            <label style={{opacity: opacity}} className="Filter-label">
                <img style={this.props.style} className="Filter-img" src={`static/images/${this.props.grouptype}.png`}></img>
                <input style={{display: "none"}} grouptype={this.props.grouptype} tag={this.props.tag} className="Filter-checkbox" type="checkbox" checked={this.props.checkedfilters.includes(this.props.filterid)} value={this.props.filterid} onChange={this.props.handlesinglecheck}/>
                <span style={this.props.style} className="Filter-title">{this.props.tag}</span>
            </label>
        );
    }

}