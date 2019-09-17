import React from "react";
import GroupFilter from "./GroupFilter";
import Filter from "./Filter";
import "./GroupContainer.css";

const Filters = require("./Filters.json");

export default class GroupContainer extends React.Component {
    constructor(props) {
        super(props);
        this.handleGroupCheck = this.handleGroupCheck.bind(this);
        this.handleSingleCheck = this.handleSingleCheck.bind(this);
        this.state = {
            isDropped: false,
            isToggled: true,
            objects: Filters.filter((filterObject, i) => {
                if(filterObject.type === this.props.type) {
                    filterObject.id = i;
                    return filterObject;
                }
            }),
            checkedFilters: Filters.map((filterObject, i) => {
                if(filterObject.type === this.props.type)
                    return i;
            })
        };
    }

    toggleDropdown = () => {
        this.setState(prevState => ({
            isDropped: !prevState.isDropped
        }));
    }

    handleGroupCheck = (event) => {
        const { checked } = event.target;
        const { objects } = this.state;
        const IDs = [];

        if(checked) {
            for(const filter of objects) {
                IDs.push(filter.id);
            }
        }

        this.setState({
            checkedFilters: IDs,
            isToggled: checked
        });

    }

    handleSingleCheck = (event) => {
        const { value, checked } = event.target;

        if (checked) {
            this.setState(prevState => ({
                checkedFilters: [...prevState.checkedFilters, value * 1]
            }));
        } else {
            this.setState(prevState => ({
                checkedFilters: prevState.checkedFilters.filter(item => item != value)
            }));
        }
    }

    render = () => {
        console.log(this.state.checkedFilters)
        let isDropped = this.state.isDropped ? 1 : 0;
        let display = this.state.isDropped && this.props.hovered ? "flex" : "none";

        let isToggled = this.state.isToggled ? 1 : 0;

        let advancedFilters = this.state.objects.map((filterObject, i) => {
            return <Filter {...this.props} style={{display: display}} title={filterObject.title} key={filterObject.id} filterid={filterObject.id} checkedFilters={this.state.checkedFilters} handleSingleCheck={this.handleSingleCheck} />
        })

        return (
            <div className="GroupContainer">
                <GroupFilter {...this.props} istoggled={isToggled} handlegroupcheck={this.handleGroupCheck} isdropped={isDropped} toggledropdown={this.toggleDropdown}/>
                {advancedFilters}
            </div>
        );
    }
}