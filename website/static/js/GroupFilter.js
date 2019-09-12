import React from "react";
import "./GroupFilter.css"
import DropdownButton from "./DropdownButton";

export default class GroupFilter extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            checked: true
        }
    }

    static defaultProps = {
        type: null
    };

    handleCheck = event => {
        this.setState({checked: event.target.checked})
    }

    componentDidUpdate = (prevProps) => {
        if(this.props.istoggled !== prevProps.istoggled) {
            this.setState(prevState => ({
                checked: !prevState.checked
            }));
        }
    }

    render = () => {
        let opacity = this.state.checked ? 1 : .25;

        return (
            <div className="GroupFilter-container">
                <label {...this.props} style={{opacity: opacity}} className="GroupFilter-label">
                    <img {...this.props} className="GroupFilter-img" src={`static/images/${this.props.type}.png`}></img>
                    <input {...this.props} style={{display: "none"}} className="GroupFilter-checkbox" type="checkbox" checked={this.state.checked} onChange={this.props.togglefilters}/>
                    <span {...this.props} className="GroupFilter-title">{this.props.type}</span>
                </label>
                <DropdownButton ischecked={this.props.ischecked} toggledropdown={this.props.toggledropdown} style={this.props.style}/>
            </div>
        );
    }

}