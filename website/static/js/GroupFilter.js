import React from "react";
import DropdownButton from "./DropdownButton";
import "./GroupFilter.css"

export default class GroupFilter extends React.Component {
    render = () => {
        let opacity = this.props.istoggled ? 1 : .25;

        return (
            <div className="GroupFilter-container">
                <label style={{opacity: opacity}} className="GroupFilter-label">
                    <img style={this.props.style} className="GroupFilter-img" src={`static/images/${this.props.grouptype}.png`}></img>
                    <input style={{display: "none"}} grouptype={this.props.grouptype} className="GroupFilter-checkbox" type="checkbox" checked={this.props.istoggled} onChange={this.props.handlegroupcheck}/>
                    <span style={this.props.style} className="GroupFilter-title">{this.props.grouptype}</span>
                </label>
                <DropdownButton isdropped={this.props.isdropped} toggledropdown={this.props.toggledropdown} style={this.props.style}/>
            </div>
        );
    }

}