import React from "react";
import AddButton from './AddButton'
import RemoveButton from './RemoveButton'
import InfoBox from "./InfoBox";
import "./BarGraph.css"

const genderLabels = ['MALE', 'FEMALE']
const dayLabels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
    'Thursday', 'Friday', 'Saturday']
const timeLabels = ['DAY', 'NIGHT']


export default class BarGraph extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            'extendedData' : {
                'subtitles': null,
                'sublabels': null,
                'subnumbers': null,
                'currentLabel': null
            },
            'activeBar' : null,
            'currentCount' : null,

        }
    }

    getMax = (numbers) => { 
        return Math.max(...numbers) 
    }

    getCeiling = (numbers) => { 
        let max = this.getMax(numbers)
        
        let defaultIncrements = [5, 10, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
        let selectedIncrement = 500
        for (const increment of defaultIncrements) {
            if(increment/max > .1) {
                selectedIncrement = increment
                break
            }
          }

        return Math.ceil(max / selectedIncrement) * selectedIncrement 
    }

    getIncrements = (numbers) => {
        let ceiling = this.getCeiling(numbers)
        return [
            0, 
            ceiling / 4, 
            ceiling / 2, 
            3 * ceiling / 4, 
            ceiling
        ]
    }

    getWidths = (numbers) => {
        let ceiling = this.getCeiling(numbers)
        let widths = numbers.map(number => {
            let width = number/ceiling * 100
            if(isNaN(width))
                return 0
            if(number == 0)
                return '0%'
            return width + '%'
        })

        return widths
    }

    getHoverData = (e) => {
        let parentIndex = e.currentTarget.parentNode.getAttribute('class').split(' ')[1]
        let sublabelIndex = e.currentTarget.getAttribute('index')
        let currentCount = e.currentTarget.getAttribute('count')
        let sublabel = e.currentTarget.getAttribute('label')
        //let label = e.currentTarget.innerHTML
        let barNumber = null
        if (parentIndex != this.state.activeBar || sublabelIndex != this.state.activeSubBar) {
            barNumber = parentIndex
            fetch(`api/stats/hover`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    label: this.props.data.labels[parentIndex],
                    sublabel: sublabel,
                    activeData: this.props.activedata
                })
            })
                .then(response => response.json())
                .then(extendedData => this.setState(prevState => ({
                    extendedData,
                    activeBar: barNumber,
                    activeSubBar: sublabel,
                    currentCount: currentCount
            })))
        } else {
            this.setState({activeBar: null})
        }
    }

    closeInfo = () => {
        this.setState({activeBar: null})
    }

    opacityHover = (e) => {
        let hoveredIndex = e.currentTarget.parentNode.getAttribute('class').split(' ')[1]
        let range = [...Array(this.props.data.numbers.length).keys()]
        let subIndex = e.currentTarget.getAttribute('index')
        let children = null
        range.forEach(i => {
            if (i != hoveredIndex) {
                document.getElementsByClassName(i)[0].style.opacity = .5
            } else {
                children = Array.from(document.getElementsByClassName(i)[0].childNodes)
                children.forEach((child, k) => {
                    if (subIndex !== child.getAttribute('index')) {
                        child.style.opacity = .5
                    } else {
                        child.style.opacity = 1
                    }
                })
            }
        })
    }

    opacityReset = (e) => {
        let bars = Array.from(document.getElementsByClassName('BarGraph-bar'))
        bars.forEach(element => element.style.opacity = 1)
        let hoveredBarChildren = Array.from(e.currentTarget.parentNode.childNodes)
        hoveredBarChildren.forEach(child => child.style.opacity = 1)
    }

    render = () => {
        let numbers = this.props.data.numbers
        let widths = this.getWidths(numbers)
        let labelHeight = 15
        let className = null
        let substyle = null
        let counts = numbers
        let sublabels = null
        
        let lines = this.getIncrements(numbers).map((increment, i) => {
            return <div key={i}><span>{increment}</span></div>
        })

        if (this.props.activedata.groupingActive == 'genders') { 
            let genderData = this.props.data.genderData
            let genderNumbers = [...genderData.maleCounts, ...genderData.femaleCounts]
            labelHeight = 15 * 2;
            widths = this.getWidths(genderNumbers)
            lines = this.getIncrements(genderNumbers).map((increment, i) => {
                return <div key={i}><span>{increment}</span></div>
            })
            counts = [...this.props.data.genderData.maleCounts, ...this.props.data.genderData.femaleCounts]
            sublabels = genderLabels
        } else if (this.props.activedata.groupingActive == 'ages') { 
            let averages = this.props.data.ageData.averages
            widths = this.getWidths(averages)
            lines = this.getIncrements(averages).map((increment, i) => {
                return <div key={i}><span>{increment}</span></div>
            })
            counts = averages
            sublabels = ["AGES"]
        } else if (this.props.activedata.groupingActive == 'times') { 
            let timeData = this.props.data.timeData
            let timeNumbers = [...timeData.dayCounts, ...timeData.nightCounts]
            labelHeight = 15 * 2;
            widths = this.getWidths(timeNumbers)
            lines = this.getIncrements(timeNumbers).map((increment, i) => {
                return <div key={i}><span>{increment}</span></div>
            })
            counts = timeNumbers
            sublabels = timeLabels
        }  else if (this.props.activedata.groupingActive == 'days') { 
            let dayData = this.props.data.dayData
            let dayNumbers = [...dayData.sundayCounts, ...dayData.mondayCounts, 
                ...dayData.tuesdayCounts, ...dayData.wednesdayCounts, ...dayData.thursdayCounts,
                ...dayData.fridayCounts, ...dayData.saturdayCounts]
            labelHeight = 15 * 7;
            widths = this.getWidths(dayNumbers)
            lines = this.getIncrements(dayNumbers).map((increment, i) => {
                return <div key={i}><span>{increment}</span></div>
            })
            counts = dayNumbers
            sublabels = dayLabels
        }

        let buttons = this.props.data.labels.map((number, i) => {
            return <RemoveButton key={i} value={i} removebar={this.props.removebar}/>
        })

        let labelStyle = {
            minHeight: `${labelHeight}px`
        }

        let labels = this.props.data.labels.map((label, i) => {
            return <span key={i} style={labelStyle}>{this.props.removeReady ? buttons[i] : null}{label}</span>
        })

        let colors = this.props.data.colors
        if(this.props.activedata.groupingActive == 'genders') {
            colors = ['#80d8f2', '#eb88d4']
        } else if(this.props.activedata.groupingActive == 'ages') {
            colors = ['#123123']
        } else if(this.props.activedata.groupingActive == 'times') {
            colors = ["#37c4b0", "#00044A"]
        } else if(this.props.activedata.groupingActive == 'days') {
            colors = ["#FF5500", "#FF6D00", "#FF8500", "#FF9D00", "#FFBC22", "#FFDB44", "#FFFA66"]
        }
  
        let bars = colors ? numbers.map((number, i) => {
            className = 'BarGraph-bar ' + i;
            if (this.props.activedata.groupingActive == 'default') {
                substyle = {
                    width: widths[i],
                    backgroundColor: colors[i]
                }

                return (
                    <div key={i} className={className}>
                        <div className="BarGraph-bar-subbar" index={0} onMouseLeave={this.opacityReset} onMouseOver={this.opacityHover} count={counts[i]} onClick={this.getHoverData} style={substyle}/>
                    </div>
                ) 

            } else {
                let substyles = colors.map((color, j) => {
                    return {
                        width: widths[i + j * widths.length / colors.length],
                        backgroundColor: color
                    }
                })

                return (
                    <div key={i} className={className}>
                        {substyles.map((substyle, k) => {
                            return <div className="BarGraph-bar-subbar" key={k} label={sublabels[k]} count={counts[i + k * counts.length / substyles.length]} index={k} onMouseLeave={this.opacityReset} onMouseOver={this.opacityHover} onClick={this.getHoverData} style={substyle}/>
                        })}
                    </div>
                ) 
            } 
        }) : null

        //console.log(this.props.activedata.barsActive)
        //console.log(this.props.data.numbers, this.props.data.labels, this.props.data.colors)
        return (
            <div className="BarGraph-main-container">
                {this.state.activeBar ? <InfoBox graphlevel={this.props.graphlevel} closeinfo={this.closeInfo} getinfoboxdata={this.props.getinfoboxdata} currentcount={this.state.currentCount} data={this.state.extendedData}/> : null}
                <div className="BarGraph-title-container">
                    <span className="BarGraph-title-main">Number of Arrests</span>
                    <span className="BarGraph-title-subtext">(by {this.props.activedata.barsActive})</span>
                    {this.props.activedata.groupingActive != "default" ? <span className="BarGraph-title-subtext">(grouped by {this.props.activedata.groupingActive})</span>
                    : null}
                </div>

                <div className="BarGraph-background">
                    <div className="BarGraph-background-color"/>
                    <div className="BarGraph-x-axis">{lines}</div>
                </div>

                <div className="BarGraph-scroll-wrapper">
                    <div className="BarGraph-y-axis">
                        {labels}
                        
                    </div>
                    <div className="BarGraph-bar-container">
                        {bars}
                    </div>
                </div>
            </div>
        )
    }
}
