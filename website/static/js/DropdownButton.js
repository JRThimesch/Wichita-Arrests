import React from 'react';
import './DropdownButton.css';

const Checkbox = props => (
    <input type="checkbox" {...props} style={{display: "none"}} />
)


export default class DropdownButton extends React.Component {
    constructor(props){
        super(props);
        this.state = {
            checked: true
        };
    }
    
    handleCheck = event => {
        this.setState({checked: event.target.checked})
    }

    render = () => {
        let button = this.state.checked ? 'down-button' : 'up-button';

        return (
            <label style={this.props.style}>
                <Checkbox checked={this.props.ischecked} onChange={this.props.toggledropdown}/>
                <img className="DropdownButton-img" src={`static/images/${button}.png`}></img>
            </label>
        );
    }
}