import React from "react";
import GraphButton from "./GraphButton";
import "./InfoBox.css"

const AnimatedGraphBars = props => {
    return <div className="AnimatedGraphBars-container" {...props}>
        <div className="AnimatedGraphBars" style={{ height: "18px" }} />
        <div className="AnimatedGraphBars" style={{ height: "25px" }}/>
        <div className="AnimatedGraphBars" style={{ height: "16px" }} />
        <div className="AnimatedGraphBars" style={{ height: "8px" }} />
        <div className="AnimatedGraphBars" style={{ height: "12px" }} />
    </div>
} 

export default class InfoBox extends React.PureComponent {
    constructor(props) {
        super(props)
    }

    handleClick = (e) => {
        let index = e.currentTarget.getAttribute("index")
        let active = this.props.data.actives[index]
        let data = {
            numbers: this.props.data.subnumbers[index],
            labels: this.props.data.sublabels[index],
            colors: this.props.data.subcolors[index],
        }
        this.props.getinfoboxdata(data, active)
    }

    isInt = (num) => {
        return parseInt(num) === num
    }

    render = () => {
        let data = this.props.data
        let subcontainers = data.subtitles ?
            data.subtitles.map((subtitle, i) => {
                return (
                    <div key={i} className="InfoBox-info-subcontainer">
                        <span className="InfoBox-subtitle"><u>{subtitle}</u></span>
                        {data.sublabels[i].map((sublabel, j) => {
                            let title = "Summary for: " + sublabel + " (" + data.subnumbers[i][j]+ ")"
                            return <div key={j} title={title} className="InfoBox-text-container">
                                <b style={{marginRight: '5px'}}>{j+1})</b> 
                                <span className="InfoBox-text">{sublabel}: </span>
                                <span style={{marginLeft: '5px'}}>({data.subnumbers[i][j]})</span>
                            </div>
                        })}
                        <AnimatedGraphBars key={i} index={i} onClick={this.handleClick}/>
                    </div>
                )
            }) : null
        
        let groupInfo = data.groupInfo ? 
            <span className="InfoBox-info-text">
                <img className="InfoBox-info-img" src="static/images/groupsIcon.png"/>
                {data.groupInfo}
            </span> : null

        let tagInfo = data.tagInfo ? 
            <span className="InfoBox-info-text">
                <img className="InfoBox-info-img" src="static/images/tagsIcon.png"/>
                {data.tagInfo}
            </span> : null

        let averageAge = data.averageAge ? 
            <span className="InfoBox-info-text">
                <img className="InfoBox-info-img" src="static/images/agesIcon.png"/>
                {data.averageAge}
            </span> : null

        let warningIcon = this.props.graphlevel > 0 ? 
            <>
            <hr className="InfoBox-line-large"/>
            <p style={{fontSize: '50px', fontWeight: 900, color: 'red'}}>!</p>
            </> : null

        let count = this.isInt(parseFloat(this.props.currentcount)) ? this.props.currentcount : parseFloat(this.props.currentcount).toFixed(2)

        return (
            <div style={this.props.style} className="InfoBox-main-container">
                <div className="InfoBox-title-container">
                    <span className="InfoBox-count">{count}</span>
                    <span className="InfoBox-title">Expanded Info for <b>{this.props.data.currentLabel}</b></span>
                    <span className="InfoBox-button-close" onClick={this.props.closeinfo}/>
                </div>
                <div className="InfoBox-info-top-container">
                        {groupInfo}
                        {tagInfo}
                        {averageAge}
                </div>
                <hr className="InfoBox-line-large"/>
                
                <div className="InfoBox-info-container">
                    {subcontainers}
                </div>
                {warningIcon}
            </div>
        )
    }
}