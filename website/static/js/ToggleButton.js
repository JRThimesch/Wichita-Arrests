import React from "react";
import ReactDOM from "react-dom";
import "./styles.css";

class ToggleButton extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      toggled: false,
      isHovered: false,
    };
  }

  toggleActive = () => {
    this.setState({
      toggled: !this.state.toggled,
    });
  }

  toggleIsHovered = () => {
    this.setState({
      isHovered: !this.state.isHovered,
    });
  }

  render() {
    return (
      <div class="button" onClick={this.toggleActive} onMouseEnter={this.toggleIsHovered} onMouseLeave={this.toggleIsHovered}>
        {this.state.isHovered.toString()}
        {this.state.toggled.toString()}
      </div>
    );
  }
}

class Filter extends React.Component {
  render() {
    return(
      <ToggleButton/>
    );
  }
}

const rootElement = document.getElementById("root");
ReactDOM.render(<Filter />, rootElement);
