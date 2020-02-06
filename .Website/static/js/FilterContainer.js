import React from "react";
import GroupContainer from "./GroupContainer";
import MapButton from './MapButton';
import "./FilterContainer.css";

export default class FilterContainer extends React.Component {
    constructor(props){
        super(props);
        this.wrapper = React.createRef();
        this.state = {
            active: false
        };
    }

    toggleFilters = () => {
        const wrapper = this.wrapper.current
        wrapper.classList.toggle('is-open')

        this.setState(prevState => ({
            active: !prevState.active
        }))
    }

    render() {

        let active = this.state.active ? 1 : 0;
        let displayHovered = active ? "flex" : "none";

        let groupContainers = this.props.getgroupinfo.group.map((group, i) => {
            let count = this.props.getgroupinfo.count[i]
            if(count > 0 && active)
                return <GroupContainer isactivetag={this.props.isactivetag} isactivegroup={this.props.isactivegroup} count={count} getcounts={this.props.getcounts} updatetags={this.props.updatetags} updategroups={this.props.updategroups} key={i} style={{display: displayHovered}} hovered={active} grouptype={group} />
        })

        return (
            <>
                <MapButton class="button-filters" handlecheck={this.toggleFilters}>
                    <img style={{width: '26px', height: '26px', margin: '7px'}} src="static/images/filters.png"/>
                </MapButton>
                <div ref={this.wrapper} className="FilterContainer" >
                    {groupContainers}
                </div>
            </>
        );
    }
}