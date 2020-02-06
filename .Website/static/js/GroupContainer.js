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
            isToggled: true,
            objects: Filters.filter((filterObject, i) => {
                if(filterObject.identifier === this.props.grouptype) {
                    filterObject.id = i;
                    filterObject.count = this.props.getcounts[i]
                    return filterObject;
                }
            }),
            checkedGroupIDs: Filters.map((filterObject, i) => {
                if(filterObject.identifier === this.props.grouptype)
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

        this.props.updategroups(event.target.getAttribute("grouptype"));

        if(checked) {
            for(const filter of objects) {
                IDs.push(filter.id);
            }
        }

        this.setState({
            checkedGroupIDs: IDs,
            isToggled: checked
        });

    }

    handleSingleCheck = (event) => {
        const { value, checked } = event.target;

        this.props.updatetags(event.target.getAttribute("tag"));

        if (checked) {
            this.setState(prevState => ({
                checkedGroupIDs: [...prevState.checkedGroupIDs, value * 1]
            }));
        } else {
            this.setState(prevState => ({
                checkedGroupIDs: prevState.checkedGroupIDs.filter(item => item != value)
            }));
        }
    }

    render = () => {
        let isDropped = this.state.isDropped ? 1 : 0;
        let display = this.state.isDropped && this.props.hovered ? "flex" : "none";

        let isToggled = this.state.isToggled ? 1 : 0;

        let advancedFilters = this.state.objects.map(filterObject => {
            if(filterObject.count > 0)
                return <Filter {...this.props} count={filterObject.count} style={{display: display}} tag={filterObject.tag} key={filterObject.id} filterid={filterObject.id} checkedgroupids={this.state.checkedGroupIDs} handlesinglecheck={this.handleSingleCheck} />
        })

        return (
            <div className="GroupContainer">
                <GroupFilter {...this.props} istoggled={isToggled} grouptype={this.props.grouptype} handlegroupcheck={this.handleGroupCheck} isdropped={isDropped} toggledropdown={this.toggleDropdown}/>
                {advancedFilters}
            </div>
        );
    }
}