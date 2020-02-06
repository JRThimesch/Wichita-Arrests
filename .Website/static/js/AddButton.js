import React from "react";
import "./AddButton.css"

export default class RemoveButton extends React.Component {
    constructor(props) {
        super(props);
    }

    handleClick = () => {
        this.props.addbar()        
    }

    render = () => {
        return (
            <div onClick={this.handleClick} className="AddButton"></div>
        )
    }
}