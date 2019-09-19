import React from "react";
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
        let filterImage = <img className="FilterContainer-img" src="static/images/filters.png" style={{display: displayNotHovered}}/>;

        let isHovered = this.state.isHovered ? 1 : 0;
        let displayNotHovered = this.state.isHovered ? "" : filterImage;
        let displayHovered = this.state.isHovered ? "flex" : "none";

        return (
            <div className="FilterContainer" onMouseEnter={this.mouseHovered} onMouseLeave={this.mouseNotHovered}>
                {displayNotHovered}
                {groupTypes.map((groupType, i) => {
                    return <GroupContainer updatetags={this.props.updatetags} key={i} style={{display: displayHovered}} hovered={isHovered} grouptype={groupType} />
                })}
            </div>
        );
    }
}