import React from 'react';
import './DropdownButton.css';

const Checkbox = props => (
    <input type="checkbox" {...props} style={{display: "none"}} />
)

export default class DropdownButton extends React.Component {
    render = () => {
        let button = this.props.isdropped ? 'up-button' : 'down-button';

        return (
            <label style={this.props.style}>
                <Checkbox checked={this.props.isdropped} onChange={this.props.toggledropdown}/>
                <img className="DropdownButton-img" src={`static/images/${button}.png`}></img>
            </label>
        );
    }
}