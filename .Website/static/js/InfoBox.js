import React from "react";
import GraphButton from "./GraphButton";
import "./InfoBox.css"

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

    render = () => {
        let data = this.props.data
        let subcontainers = data.subtitles ?
            data.subtitles.map((subtitle, i) => {
                return (
                    <div className="InfoBox-info-subcontainer">
                        <span className="InfoBox-subtitle"><u>{subtitle}</u></span>
                        {data.sublabels[i].map((sublabel, j) => {
                            return <span className="InfoBox-text"><b>{j+1})</b> {sublabel}: ({data.subnumbers[i][j]})</span>
                        })}
                        <img key={i} index={i} onClick={this.handleClick} className="InfoBox-info-img" src="static/images/createGraphIcon.png"/>
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
            <GraphButton
                handleclick={this.warning}
                ><p style={{fontSize: '50px', fontWeight: 900, color: 'red'}}>!</p></GraphButton>
            </> : null

        return (
            <div style={this.props.style} className="InfoBox-main-container">
                <div className="InfoBox-title-container">
                    <span className="InfoBox-count">{this.props.currentcount}</span>
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