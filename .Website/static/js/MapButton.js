import React from 'react';
import './MapButton.css';

export default class MapButton extends React.Component {
    constructor(props) {
        super(props);
    }

    static defaultProps = {
        class: "MapButton-label"
    }
    
    render = () => {
        return(
            <label className={this.props.class}>
                <input style={{display: "none"}} type="checkbox" checked={this.props.checked} onChange={this.props.handlecheck}/>
                {this.props.children}
            </label>
        );
    }
}