import React from "react";
import { render } from "react-dom";
import {
  BrowserRouter as Router,
  Switch,
  Route,
} from "react-router-dom";
import NavBar from "./NavBar"
import Maps from "./Maps";
import Stats from "./Stats";

export default function App() {
    return (
        <Router>
            <NavBar/>
            
            <Switch>
                <Route path="/maps">
                    <Maps/>
                </Route>
                <Route path="/stats">
                    <Stats/>
                </Route>
            </Switch>
        </Router>
    )
}

render(<App />, document.getElementById("root"));
