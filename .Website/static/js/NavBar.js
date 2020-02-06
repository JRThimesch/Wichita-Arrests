import React from "react";
import {
    BrowserRouter as Router,
    Link
    } from "react-router-dom";
import "./NavBar.css"

export default class NavBar extends React.Component {
    constructor(props) {
        super(props);
        this.wrapper = React.createRef();
    }
    toggleMenu = () => {
        const wrapper = this.wrapper.current;
        wrapper.classList.toggle('is-open')
    }

    render() {
        return (
            <nav className="NavBar-container">
                <div className="NavBar-inner-container">
                    <Link to="/maps">
                        <img className="NavBar-logo-large" src="static/images/Logo-Large.png"/>
                    </Link>
                    <div className="NavBar-link-container">
                        <a className="NavBar-link-upper" href="#">How It Was Made</a>
                        <div className="NavBar-link-container-main">
                            <Link to="/maps" className="NavBar-link">
                                Maps
                            </Link>
                            <Link to="/stats" className="NavBar-link">
                                Statistics
                            </Link>
                            <a className="NavBar-link" href="#">FAQ</a>
                        </div>
                    </div>
                </div>
                <img onClick={this.toggleMenu} className="NavBar-mobile-menu-button" src="static/images/expandMenu.png"/>
                <div ref={this.wrapper} className="NavBar-mobile-menu-container">
                    <a className="NavBar-mobile-link" href="http://127.0.0.1:5000/maps">Maps</a>
                    <a className="NavBar-mobile-link" href="#">Statistics</a>
                    <a className="NavBar-mobile-link" href="#">FAQ</a>
                </div>
            </nav>
        )
    }
}