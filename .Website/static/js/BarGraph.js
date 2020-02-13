import React from "react";
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
            extendedData : {
                subtitles: null,
                sublabels: null,
                subnumbers: null,
                currentLabel: null
            },
            activeBar : null,
            currentCount : null,
            selectedIndex: [null, null]
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
        return ceiling != Number.NEGATIVE_INFINITY ? [
            0, 
            ceiling / 4, 
            ceiling / 2, 
            3 * ceiling / 4, 
            ceiling
        ] : [0, 0, 0, 0, 0]
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
        let barNumber = null
        if (parentIndex != this.state.activeBar || sublabel != this.state.activeSubBar) {
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
                    currentCount: currentCount,
                    selectedIndex: [parentIndex, sublabelIndex]
            }))).then(this.opacityOnSelect(parentIndex, sublabelIndex))
        } else {
            this.setState({activeBar: null, selectedIndex: [null, null]})
        }
    }

    closeInfo = () => {
        this.setState({activeBar: null, selectedIndex: [null, null]})
        this.opacityOnCloseInfo()
    }

    opacityHover = (e) => {
        let parentIndex = this.state.selectedIndex[0]
        let childIndex = this.state.selectedIndex[1]
        
        let hoveredIndex = e.currentTarget.parentNode.getAttribute('class').split(' ')[1]
        let subIndex = e.currentTarget.getAttribute('index')
        let bars = Array.from(document.getElementsByClassName('BarGraph-bar'))

        if (parentIndex != null) {
            bars.forEach(element => element.style.opacity = 1)
            let filteredBars = bars.filter((_, i) => i != hoveredIndex && i != parentIndex)
            filteredBars.forEach(element => element.style.opacity = .5)
            let hoveredBarChildren = Array.from(bars[hoveredIndex].childNodes)
            let filteredChildren = hoveredBarChildren.filter((_, i) => i != subIndex)
            filteredChildren.forEach(element => element.style.opacity = .5)
            bars[parentIndex].childNodes[childIndex].style.opacity = 1
            if (hoveredIndex == parentIndex) {
                bars[parentIndex].childNodes[subIndex].style.opacity = 1
            }
        } else {
            let filteredBars = bars.filter((_, i) => i != hoveredIndex)
            filteredBars.forEach(element => element.style.opacity = .5)
            let hoveredBarChildren = Array.from(bars[hoveredIndex].childNodes)
            let filteredChildren = hoveredBarChildren.filter((_, i) => i != subIndex)
            filteredChildren.forEach(element => element.style.opacity = .5)
        }
    }

    opacityReset = (e) => {
        let parentIndex = this.state.selectedIndex[0]
        let childIndex = this.state.selectedIndex[1]
        let bars = Array.from(document.getElementsByClassName('BarGraph-bar'))

        if (parentIndex != null) {
            bars.forEach(element => element.style.opacity = 1)
            let hoveredBarChildren = Array.from(e.currentTarget.parentNode.childNodes)
            hoveredBarChildren.forEach(child => child.style.opacity = 1)
            let filteredBars = bars.filter((_, i) => i != parentIndex)
            filteredBars.forEach(element => element.style.opacity = .5)
            let selectedBarChildren = Array.from(bars[parentIndex].childNodes)
            let filteredChildren = selectedBarChildren.filter((_, i) => i != childIndex)
            filteredChildren.forEach(element => element.style.opacity = .5)
        } else {
            bars.forEach(element => element.style.opacity = 1)
            let hoveredBarChildren = Array.from(e.currentTarget.parentNode.childNodes)
            hoveredBarChildren.forEach(child => child.style.opacity = 1)
        }
    }

    opacityOnSelect = (parentIndex, childIndex) => {
        let oldParentIndex = this.state.selectedIndex[0]
        let oldChildIndex = this.state.selectedIndex[0]

        if (oldParentIndex != null) {
            let bars = Array.from(document.getElementsByClassName('BarGraph-bar'))
            bars[oldParentIndex].style.opacity = .5
            let oldSelectedChildren = Array.from(bars[oldParentIndex].childNodes)
            oldSelectedChildren.forEach(element => element.style.opacity = 1)
            if (parentIndex == oldParentIndex) {
                let selectedChildren = Array.from(bars[parentIndex].childNodes)
                bars[parentIndex].style.opacity = 1
                let filteredChildren = selectedChildren.filter((_, i) => i != childIndex)
                filteredChildren.forEach(element => element.style.opacity = .5)
            }
        }
    } 

    opacityOnCloseInfo = () => {
        let bars = Array.from(document.getElementsByClassName('BarGraph-bar'))
        bars.forEach(element => element.style.opacity = 1)
        let selectedParent = this.state.selectedIndex[0]
        let selectedChild = this.state.selectedIndex[1]

        let selectedChildren = Array.from(bars[selectedParent].childNodes)
        let childrenToReset = selectedChildren.filter((_, i) => i !== selectedChild)
        childrenToReset.forEach(element => element.style.opacity = 1)
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
            return <div key={i} className="BarGraph-y-axis-label-container" style={labelStyle}>{this.props.removeReady ? buttons[i] : null}<span>{label}</span></div>
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
