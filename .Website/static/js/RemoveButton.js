import React from "react";
import "./RemoveButton.css"

export default class RemoveButton extends React.Component {
    constructor(props) {
        super(props);
    }

    handleClick = () => {
        this.props.removebar(this.props.value)        
    }

    render = () => {
        return (
            <div onClick={this.handleClick} className="RemoveButton">
                <div className="RemoveButton-dash"/>
            </div>
        )
    }
}