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

        displayNotHovered = this.state.isHovered ? "" : <img className="FilterContainer-img" src="static/images/filters.png" style={{display: displayNotHovered}}/>;
        displayHovered = this.state.isHovered ? "flex" : "none";

        return (
            <div className="FilterContainer" onMouseEnter={this.mouseHovered} onMouseLeave={this.mouseNotHovered}>
                {displayNotHovered}
                {groupTypes.map((groupType, i) => {
                    return <GroupContainer key={i} style={{display: displayHovered}} hovered={this.state.isHovered} type={groupType} groupid={i} />
                })}
            </div>
        );
    }
}