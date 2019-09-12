import React from "react";
import Filter from "./Filter";
import GroupContainer from "./GroupContainer";
import "./FilterContainer.css";

const Filters = require("./Filters.json");

var groupTypes = new Set();

Filters.forEach(filterObject => {
    groupTypes.add(filterObject.type)
});

groupTypes = Array.from(groupTypes);

export default class FilterContainer extends React.Component {
    constructor(props){
        super(props);
        this.state = {
            isHovered: false
        };
    }

    mouseHovered = () => {
        this.setState({isHovered: true});
    }

    mouseNotHovered = () => {
        this.setState({isHovered: false});
    }
    
    render() {
        let displayNotHovered, displayHovered;

        displayNotHovered = this.state.isHovered ? "none" : "flex";
        displayHovered = this.state.isHovered ? "flex" : "none";

        return (
            <div className="FilterContainer" onMouseEnter={this.mouseHovered} onMouseLeave={this.mouseNotHovered}>
                <img className="FilterContainer-img" src="static/images/filters.png" style={{display: displayNotHovered}}/>
                {groupTypes.map((groupType, i) => {
                    return <GroupContainer key={i} style={{display: displayHovered}} type={groupType} groupid={i} />
                })}
            </div>
        );
    }
}