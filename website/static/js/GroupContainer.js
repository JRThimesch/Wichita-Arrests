import React from "react";
import GroupFilter from "./GroupFilter";
import Filter from "./Filter";

const Filters = require("./Filters.json");

export default class GroupContainer extends React.Component {
    constructor(props) {
        super(props);
    }

    render = () => {
        return (
            <>
                <GroupFilter {...this.props}/>
                {Filters.map((filterObject, i) => {
                    if(filterObject.type === this.props.type)
                        return <Filter {...this.props} key={i} title={filterObject.title}  />
                })}
            </>
        );
    }

}