import React from "react";
import "./Filter.css"

const Checkbox = props => {
    <input type="checkbox" {...props}/>
}

export default class Filter extends React.Component {
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
            <label {...this.props} style={{opacity: opacity}} className="Filter-label">
                <img {...this.props} className="Filter-img" src={`static/images/${this.props.type}.png`}></img>
                <input {...this.props} style={{display: "none"}} className="Filter-checkbox" type="checkbox" checked={this.state.checked} onChange={this.handleCheck}/>
                <span {...this.props} className="Filter-title">{this.props.title}</span>
            </label>
        );
    }

}