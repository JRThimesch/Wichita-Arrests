import React from "react";
import "./GraphButton.css"

export default class GraphButton extends React.Component {
    constructor(props) {
        super(props);
    }

    render = () => {
        return (
            <div onClick={(e) => this.props.handleclick(e)} type={this.props.type} className="GraphButton">
                {this.props.children}
            </div>
        )
    }
}