import React from "react";
import DropdownButton from "./DropdownButton";
import "./GroupFilter.css"

export default class GroupFilter extends React.Component {
    render = () => {
        let opacity = this.props.istoggled ? 1 : .25;

        return (
            <div className="GroupFilter-container">
                <label style={{opacity: opacity}} type={this.props.type} groupid={this.props.groupid} className="GroupFilter-label">
                    <img style={this.props.style} type={this.props.type} groupid={this.props.groupid} className="GroupFilter-img" src={`static/images/${this.props.type}.png`}></img>
                    <input style={{display: "none"}} type={this.props.type} groupid={this.props.groupid} className="GroupFilter-checkbox" type="checkbox" checked={this.props.istoggled} onChange={this.props.handlegroupcheck}/>
                    <span style={this.props.style} type={this.props.type} groupid={this.props.groupid} className="GroupFilter-title">{this.props.type}</span>
                </label>
                <DropdownButton isdropped={this.props.isdropped} toggledropdown={this.props.toggledropdown} style={this.props.style}/>
            </div>
        );
    }

}