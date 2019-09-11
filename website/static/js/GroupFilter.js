import React from "react";
import "./GroupFilter.css"

export default class GroupFilter extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            checked: true
        }
    }

    static defaultProps = {
        type: null,
        title: "untitled",
        inputid: -1
    };

    handleCheck = event => {
        this.setState({checked: event.target.checked})
    }

    render = () => {
        let opacity = this.state.checked ? 1 : .25;

        return (
            <label {...this.props} style={{opacity: opacity}} className="GroupFilter-label">
                <img {...this.props} className="GroupFilter-img" src={`static/images/${this.props.type}.png`}></img>
                <input {...this.props} style={{display: "none"}} className="GroupFilter-checkbox" type="checkbox" checked={this.state.checked} onChange={this.handleCheck}/>
                <span {...this.props} className="GroupFilter-title">{this.props.type}</span>
            </label>
        );
    }

}