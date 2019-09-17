import React from "react";
import "./Filter.css"

export default class Filter extends React.Component {
    static defaultProps = {
        title: "untitled"
    };

    render = () => {
        let opacity = this.props.checkedFilters.includes(this.props.filterid) ? 1 : .25;

        return (
            <label {...this.props} style={{opacity: opacity}} className="Filter-label">
                <img {...this.props} className="Filter-img" src={`static/images/${this.props.type}.png`}></img>
                <input {...this.props} style={{display: "none"}} className="Filter-checkbox" type="checkbox" checked={this.props.checkedFilters.includes(this.props.filterid)} value={this.props.filterid} onChange={this.props.handleSingleCheck}/>
                <span {...this.props} className="Filter-title">{this.props.title}</span>
            </label>
        );
    }

}