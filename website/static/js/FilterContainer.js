import React from "react";
import Filter from "./Filter";
import "./FilterContainer.css";

const Filters = require("./Filters.json");
var filterArray = Filters.map((filterObject, i) => {
    //let groupID = groupTypes.indexOf(filterObject.type);
    return <Filter key={i} inputid={i} type={filterObject.type} title={filterObject.title} />
});

//var groupTypes = new Set();

//Filters.forEach(filterObject => {
//    groupTypes.add(filterObject.type)
//});

//groupTypes = Array.from(groupTypes);

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
                {Filters.map((filterObject, i) => {
                    //let groupID = groupTypes.indexOf(filterObject.type);
                    return <Filter key={i} inputid={i} type={filterObject.type} title={filterObject.title} style={{display: display}} />
                })}
            </div>
        );
    }
}