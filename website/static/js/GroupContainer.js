import React from "react";
import GroupFilter from "./GroupFilter";
import Filter from "./Filter";
import "./GroupContainer.css";

const Filters = require("./Filters.json");

export default class GroupContainer extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            isDropped: false,
            isToggled: true
        };
    }

    toggleDropdown = () => {
        this.setState(prevState => ({
            isDropped: !prevState.isDropped
        }));
    }

    toggleFilters = () => {
        this.setState(prevState => ({
            isToggled: !prevState.isToggled
        }));
    }

    render = () => {
        let isDropped = this.state.isDropped;
        let isToggled = this.state.isToggled;

        let advancedFilters = Filters.map((filterObject, i) => {
            if(filterObject.type === this.props.type)
                if(isDropped)
                    return <Filter {...this.props} istoggled={isToggled.toString()} key={i} title={filterObject.title}  />
                else
                    return <Filter {...this.props} istoggled={isToggled.toString()} style={{display: 'none'}} key={i} title={filterObject.title}  />
        })

        return (
            <div className="GroupContainer">
                <GroupFilter {...this.props} istoggled={isToggled.toString()} ischecked={this.state.isDropped} togglefilters={this.toggleFilters} toggledropdown={this.toggleDropdown}/>
                {advancedFilters}
            </div>
        );
    }
}