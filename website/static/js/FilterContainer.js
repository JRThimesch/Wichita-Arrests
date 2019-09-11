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
        let text, display;

        text = this.state.isHovered ? "" : "Filters";
        display = this.state.isHovered ? "flex" : "none";

        return (
            <div className="FilterContainer" onMouseEnter={this.mouseHovered} onMouseLeave={this.mouseNotHovered}>
                {text}
                {groupTypes.map((groupType, i) => {
                    return <GroupContainer key={i} style={{display: display}} type={groupType} groupid={i} />;
                })}
            </div>
        );
    }
}