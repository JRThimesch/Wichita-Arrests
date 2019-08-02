import React from "react";
import ReactDOM from "react-dom";

class ToggleButton extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      toggled: false,
      isHovered: false,
    };
    this.toggleActive = this.toggleActive.bind(this);
  }

  toggleActive = () => {
    this.setState({
      toggled: !this.state.toggled,
    });
  }

  render() {
    return (
      <div onClick={this.toggleActive}>
        {this.props.type}
        {this.state.toggled.toString()}
      </div>
    );
  }
}

class Filter extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      toggled: false,
      isHovered: false,
    };
    this.toggleActive = this.toggleActive.bind(this);
    this.toggleIsHovered = this.toggleIsHovered.bind(this);
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
    return(
      <div onMouseEnter={this.toggleIsHovered} onMouseLeave={this.toggleIsHovered}>
        <ToggleButton type="violence" />
        <ToggleButton type="drugs" />
        <ToggleButton type="property" />
        <ToggleButton type="vehicles" />
        <ToggleButton type="sex" />
        <ToggleButton type="warrants" />
        <ToggleButton type="other" />
      </div>
    );
  }
}

const rootElement = document.getElementById("root");
ReactDOM.render(<Filter />, rootElement);
