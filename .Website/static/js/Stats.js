import React from "react";
import BarGraph from "./BarGraph";
import GraphButton from "./GraphButton";
import './Stats.css'

const AnimatedBars = props => {
    return <div className="AnimatedBars-container">
        <div className="AnimatedBars" style={{ width: "12px" }} />
        <div className="AnimatedBars" style={{ width: "15px" }}/>
        <div className="AnimatedBars" style={{ width: "8px" }} />
    </div>
} 

export default class Stats extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            ascending: true,
            level: 0,
            activeData: {
                barsActive: 'groups',
                groupingActive: 'default',
                queryType: 'distinct'
            },
            data: { 
                numbers: Array.from(Array(5), () => 0),
                labels: [],
                colors: null,
                genderData: {
                    maleCounts: null,
                    femaleCounts: null
                },
                ageData : {
                    averages: null
                },
                timeData: {
                    dayCounts: null,
                    nightCounts: null,
                },
                dayData: {
                    sundayCounts: null,
                    mondayCounts: null,
                    tuesdayCounts: null,
                    wednesdayCounts: null,
                    thursdayCounts: null,
                    fridayCounts: null,
                    saturdayCounts: null
                }
            },
            key: 0,
            inactiveLabels: [],
            inactiveLabelsVisible: false
        }
    }

    createCustomGraph = () => {
        this.setState(prevState => ({
            data: { 
                numbers: Array.from(Array(5), () => 0),
                labels: [],
                colors: null,
                genderData: {
                    maleCounts: null,
                    femaleCounts: null
                },
                ageData : {
                    averages: null
                },
                timeData: {
                    dayCounts: null,
                    nightCounts: null,
                },
                dayData: {
                    sundayCounts: null,
                    mondayCounts: null,
                    tuesdayCounts: null,
                    wednesdayCounts: null,
                    thursdayCounts: null,
                    fridayCounts: null,
                    saturdayCounts: null
                },
            },
            inactiveLabels: [...prevState.data.labels, ...prevState.inactiveLabels]
        }))
    }

    getInfoBoxData = (passedData, active) => {
        this.setState(prevState => ({
            level: prevState.level + 1,
            activeData: {
                barsActive: active,
                groupingActive: 'default',
                queryType: prevState.activeData.queryType
            },
            data: passedData,
            key : Math.random() * 10000
        }))
    }

    groupGenders = (passedData, active) => {
        fetch("api/stats/grouping/genders", {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                labels: passedData.labels,
                dataActive: active,
                queryType: this.state.activeData.queryType
            })
        })
            .then(response => response.json())
            .then(data => this.setState(prevState => ({
                ready: true,
                data: {
                    ...prevState.data,
                    genderData: data,
                }
        })))
    }

    groupDays = (passedData, active) => {
        fetch("api/stats/grouping/days", {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                labels: passedData.labels,
                dataActive: active,
                queryType: this.state.activeData.queryType
            })
        })
            .then(response => response.json())
            .then(data => this.setState(prevState => ({
                ready: true,
                data: {
                    ...prevState.data,
                    dayData: data,
                }
        })))
    }

    groupAges = (passedData, active) => {
        fetch("api/stats/grouping/ages", {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                labels: passedData.labels,
                dataActive: active,
                queryType: this.state.activeData.queryType
            })
        })
            .then(response => response.json())
            .then(data => this.setState(prevState => ({
                ready: true,
                data: {
                    ...prevState.data,
                    ageData: data
                }
        })))
    }

    groupTimes = (passedData, active) => {
        fetch("api/stats/grouping/times", {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                labels: passedData.labels,
                dataActive: active,
                queryType: this.state.activeData.queryType
            })
        })
            .then(response => response.json())
            .then(data => this.setState(prevState => ({
                ready: true,
                data: {
                    ...prevState.data,
                    timeData: data
                }
        })))
    }

    groupData = (passedData, groupType, ) => {
        fetch(`api/stats/grouping/${type}`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                labels: passedData.labels,
                dataActive: groupType,
                queryType: this.state.activeData.queryType
            })
        })
            .then(response => response.json())
            .then(data => this.setState(prevState => ({
                data: {
                    ...prevState.data,
                    data
                }
        })))
    }

    toggleGrouping = (e) => {
        let grouping = e.currentTarget.getAttribute('type')
        if (this.state.activeData.groupingActive == grouping) {
            this.setState(prevState => ({
                activeData: {
                    groupingActive: 'default',
                    barsActive: prevState.activeData.barsActive,
                    queryType: prevState.activeData.queryType
                }
            }))
        }
        else {
            this.setState(prevState => ({
                activeData: {
                    groupingActive: grouping,
                    barsActive: prevState.activeData.barsActive,
                    queryType: prevState.activeData.queryType
                },
                key : Math.random() * 10000
            }))
        }
    }

    toggleQuery = (e) => {
        let queryType = e.currentTarget.getAttribute('type')
        if (this.state.activeData.queryType == queryType) {
            this.setState(prevState => ({
                activeData: {
                    groupingActive: prevState.activeData.groupingActive,
                    barsActive: prevState.activeData.barsActive,
                    queryType: prevState.activeData.queryType
                }
            }))
        }
        else {
            this.setState(prevState => ({
                activeData: {
                    groupingActive: prevState.activeData.groupingActive,
                    barsActive: prevState.activeData.barsActive,
                    queryType: queryType
                },
                key : Math.random() * 10000
            }))
            this.getData(null, queryType)
        }
    }

    getData = (e, queryType) => {
        let currentData = null
        if (e) {
            currentData = e.currentTarget.getAttribute('type')
        } else {
            currentData = this.state.activeData.barsActive
        }
        let currentQuery = null
        if (queryType) {
            currentQuery = queryType
        } else {
            currentQuery = this.state.activeData.queryType
        }
        fetch(`/api/stats/${currentData}/${currentQuery}`)
        .then(response => response.json())
        .then(data => {
            this.groupGenders(data, currentData)
            this.groupAges(data, currentData)
            this.groupTimes(data, currentData)
            this.groupDays(data, currentData)
            this.setState(prevState => ({
                data, 
                activeData: {
                    barsActive: currentData,
                    groupingActive: 'default',
                    queryType: prevState.activeData.queryType
                },
                key : Math.random() * 10000
            }))
        })
    }

    sortData = (e) => {
        let sortType = e.currentTarget.getAttribute('type')
        let ascending = this.state.ascending ? "ascending" : "descending"
        fetch(`/api/stats/sort/${sortType}-${ascending}`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                data: this.state.data,
                activeData: this.state.activeData
            })
        })
        .then(response => response.json())
        .then(data => this.setState(prevState => ({
                data: data,
                ascending: !prevState.ascending,
                key : Math.random() * 10000
        })))
    }

    removeBar = (key) => {
        this.setState(prevState => ({
            data: {
                numbers: prevState.data.numbers.filter((_, i) => i !== key),
                labels: prevState.data.labels.filter((_, i) => i !== key),
                colors: prevState.data.colors.filter((_, i) => i !== key),
                genderData: {
                    maleCounts: prevState.data.genderData.maleCounts.filter((_, i) => i !== key),
                    femaleCounts: prevState.data.genderData.femaleCounts.filter((_, i) => i !== key)
                },
                ageData: {
                    averages: prevState.data.ageData.averages.filter((_, i) => i !== key)
                },
                timeData: {
                    dayCounts: prevState.data.timeData.dayCounts.filter((_, i) => i !== key),
                    nightCounts: prevState.data.timeData.nightCounts.filter((_, i) => i !== key)
                },
                dayData: {
                    'sundayCounts': prevState.data.dayData.sundayCounts.filter((_, i) => i !== key),
                    'mondayCounts': prevState.data.dayData.mondayCounts.filter((_, i) => i !== key),
                    'tuesdayCounts': prevState.data.dayData.tuesdayCounts.filter((_, i) => i !== key),
                    'wednesdayCounts': prevState.data.dayData.wednesdayCounts.filter((_, i) => i !== key),
                    'thursdayCounts': prevState.data.dayData.thursdayCounts.filter((_, i) => i !== key),
                    'fridayCounts': prevState.data.dayData.fridayCounts.filter((_, i) => i !== key),
                    'saturdayCounts': prevState.data.dayData.saturdayCounts.filter((_, i) => i !== key)
                },
            },
            inactiveLabels: [...prevState.inactiveLabels, prevState.data.labels[key]]
        }))
    }

    toggleInactiveVisible = () => {
        this.setState(prevState => ({inactiveLabelsVisible: !prevState.inactiveLabelsVisible}))
    }

    closeInactiveLabels = (e) => {
        e.stopPropagation()
        this.setState({inactiveLabelsVisible: false})
    }


    addBar = (e) => {
        e.stopPropagation()
        let label = e.currentTarget.innerHTML
        fetch(`/api/stats/label`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                labels: [label],
                queryType: this.state.activeData.queryType,
                dataActive: this.state.activeData.barsActive
            })
        })
        .then(response => response.json())
        .then(data => this.setState(prevState => ({
            data: {
                numbers: [...prevState.data.numbers, ...data.numbers],
                labels: [...prevState.data.labels, label],
                colors: [...prevState.data.colors, ...data.colors],
                genderData: {
                    maleCounts: [...prevState.data.genderData.maleCounts, ...data.genderData.maleCounts],
                    femaleCounts: [...prevState.data.genderData.femaleCounts, ...data.genderData.femaleCounts]
                },
                ageData: {
                    averages: [...prevState.data.ageData.averages, ...data.ageData.averages]
                },
                timeData: {
                    dayCounts: [...prevState.data.timeData.dayCounts, ...data.timeData.dayCounts],
                    nightCounts: [...prevState.data.timeData.nightCounts, ...data.timeData.nightCounts]
                },
                dayData: {
                    sundayCounts: [...prevState.data.dayData.sundayCounts, ...data.dayData.sundayCounts],
                    mondayCounts: [...prevState.data.dayData.mondayCounts, ...data.dayData.mondayCounts],
                    tuesdayCounts: [...prevState.data.dayData.tuesdayCounts, ...data.dayData.tuesdayCounts],
                    wednesdayCounts: [...prevState.data.dayData.wednesdayCounts, ...data.dayData.wednesdayCounts],
                    thursdayCounts: [...prevState.data.dayData.thursdayCounts, ...data.dayData.thursdayCounts],
                    fridayCounts: [...prevState.data.dayData.fridayCounts, ...data.dayData.fridayCounts],
                    saturdayCounts: [...prevState.data.dayData.saturdayCounts, ...data.dayData.saturdayCounts]
                }
            },
            inactiveLabels: prevState.inactiveLabels.filter((item, _) => item != label)

        })))
        /*
        this.setState(prevState => ({
            data: {
                numbers: prevState.data.numbers,
                labels: [...prevState.data.labels, label],
                colors: prevState.data.colors,
                genderData: {
                    maleCounts: prevState.data.genderData.maleCounts,
                    femaleCounts: prevState.data.genderData.femaleCounts
                },
                ageData: {
                    averages: prevState.data.ageData.averages
                },
                timeData: {
                    dayCounts: prevState.data.timeData.dayCounts,
                    nightCounts: prevState.data.timeData.nightCounts
                },
                dayData: {
                    sundayCounts: prevState.data.dayData.sundayCounts,
                    mondayCounts: prevState.data.dayData.mondayCounts,
                    tuesdayCounts: prevState.data.dayData.tuesdayCounts,
                    wednesdayCounts: prevState.data.dayData.wednesdayCounts,
                    thursdayCounts: prevState.data.dayData.thursdayCounts,
                    fridayCounts: prevState.data.dayData.fridayCounts,
                    saturdayCounts: prevState.data.dayData.saturdayCounts
                }
            },
            inactiveLabels: prevState.inactiveLabels.filter((item, _) => item != label)

        }))*/
    }

    componentDidMount = () => {
        let currentData = 'groups'
        let queryType = this.state.activeData.queryType
        fetch(`/api/stats/${currentData}/${queryType}`)
        .then(response => response.json())
        .then(data => {
            this.groupGenders(data, currentData)
            this.groupAges(data, currentData)
            this.groupTimes(data, currentData)
            this.groupDays(data, currentData)
            this.setState(prevState => ({
                data, 
                activeData: {
                    barsActive: currentData,
                    groupingActive: 'default',
                    queryType: prevState.activeData.queryType
                },
                key : Math.random() * 10000
            }))
        })
    }

    render = () => {
        let sortReady = (this.state.data.genderData && this.state.data.ageData && this.state.data.timeData && this.state.data.dayData)
        let truncatedLabels = this.state.inactiveLabels.length !== 0  ? 
            this.state.inactiveLabels.sort().map(label =>{
                if (label.length > 16) {
                    return label.slice(0, 16) + "..."
                } else {
                    return label
                }
            }) : []
        let inactiveLabels = this.state.inactiveLabelsVisible ?
            <div className="Stats-add-container">
                <div style={{display:'flex', justifyContent:'flex-end'}}>
                    labels to add
                    <span className="Stats-add-button-close" onClick={this.closeInactiveLabels}/>
                </div>
                <div className="Stats-add-label-container">
                    {truncatedLabels.map((label, i) => {
                        return <span className="Stats-add-label" onClick={this.addBar} key={i}>{label}</span>
                    })}
                </div>
            </div> : null
            
        let addButton = this.state.inactiveLabels.length !== 0 ? <div
            className="Stats-add-button"
            onClick={this.toggleInactiveVisible}
            ><p style={{fontSize: '50px', fontWeight: 900}}>+</p>{inactiveLabels}</div> : null
        
        return (
            <>
                <div className="Stats-container">
                    <BarGraph
                        data={this.state.data}
                        key={this.state.key}
                        activedata={this.state.activeData}
                        removebar={this.removeBar}
                        hoverdata={this.getHoverData}
                        getinfoboxdata={this.getInfoBoxData}
                        graphlevel={this.state.level}
                    />
                    <div className="Stats-right-container">       
                        <div className="Stats-button-container">
                            <div className="Stats-button-container-group" style={{alignItems:'center', justifyContent:'center'}}>
                                <GraphButton
                                    handleclick={this.tutorial}
                                    ><p style={{fontSize: '50px'}}>?</p></GraphButton>
                            </div>
                            <hr className="Stats-button-container-line"/>
                            <div className="Stats-button-container-group">
                                <GraphButton
                                    handleclick={this.createCustomGraph}
                                    ><img src="static/images/customGraph.png"/></GraphButton>
                                {addButton}
                                {this.state.activeData.queryType != 'distinct' 
                                    ? <GraphButton
                                    handleclick={this.toggleQuery}
                                    type="distinct"
                                    ><img src="static/images/recordsIcon.png"/></GraphButton> : null }
                                {this.state.activeData.queryType != 'charges' 
                                    ? <GraphButton 
                                    handleclick={this.toggleQuery}
                                    type="charges"
                                    ><img src="static/images/chargesIcon.png"/></GraphButton> : null }
                            </div>
                            <hr className="Stats-button-container-line"/>
                            <div className="Stats-button-container-group">
                                <GraphButton
                                    handleclick={this.getData}
                                    type="arrests"
                                    ><img src="static/images/arrestsIcon.png"/></GraphButton>
                                <GraphButton 
                                    handleclick={this.getData}
                                    type="tags"
                                    ><img src="static/images/tagsIcon.png"/></GraphButton>
                                <GraphButton
                                    handleclick={this.getData}
                                    type="groups"
                                    ><img src="static/images/groupsIcon.png"/></GraphButton>
                                <GraphButton
                                    handleclick={this.getData}
                                    type="ages"
                                    ><img src="static/images/agesIcon.png"/></GraphButton>
                                <GraphButton
                                    handleclick={this.getData}
                                    type="genders"
                                    ><img src="static/images/gendersIcon.png"/></GraphButton>
                                <GraphButton
                                    handleclick={this.getData}
                                    type="dates"
                                    ><img src="static/images/datesIcon.png"/></GraphButton>
                                <GraphButton
                                    handleclick={this.getData}
                                    type="times"
                                    ><img src="static/images/timesIcon.png"/></GraphButton>
                                <GraphButton
                                    handleclick={this.getData}
                                    type="days"
                                    ><img src="static/images/daysIcon.png"/></GraphButton>
                                <GraphButton
                                    handleclick={this.getData}
                                    type="months"
                                    ><img src="static/images/monthsIcon.png"/></GraphButton>
                            </div>
                            <hr className="Stats-button-container-line"/>
                            <div className="Stats-button-container-group">
                                {this.state.activeData.barsActive != 'genders' &&
                                    this.state.data.genderData ? <GraphButton
                                    handleclick={this.toggleGrouping}
                                    type="genders"
                                    ><img src="static/images/gendersIcon.png"/>
                                    <AnimatedBars/>
                                    </GraphButton> : null }
                                {this.state.activeData.barsActive != 'ages' &&
                                    this.state.data.ageData ? <GraphButton
                                    handleclick={this.toggleGrouping}
                                    type="ages"
                                    ><img src="static/images/agesIcon.png"/>
                                    <AnimatedBars/>
                                    </GraphButton> : null }
                                {this.state.activeData.barsActive != 'times' &&
                                    this.state.data.timeData ? <GraphButton
                                    handleclick={this.toggleGrouping}
                                    type="times"
                                    ><img src="static/images/timesIcon.png"/>
                                    <AnimatedBars/>
                                    </GraphButton> : null }
                                {this.state.activeData.barsActive != 'dates' &&
                                    this.state.activeData.barsActive != 'days' &&
                                    this.state.data.dayData ? <GraphButton
                                    handleclick={this.toggleGrouping}
                                    type="days"
                                    ><img src="static/images/daysIcon.png"/>
                                    <AnimatedBars/>
                                    </GraphButton> : null }
                            </div>
                            <hr className="Stats-button-container-line"/>
                            <div className="Stats-button-container-group">
                                {sortReady ? <GraphButton
                                    handleclick={this.sortData}
                                    type="numeric"
                                    ><p>1</p><p>2</p><p>3</p></GraphButton> : null }
                                {sortReady ? <GraphButton 
                                    handleclick={this.sortData}
                                    type="alpha"
                                    ><p>A</p><p>B</p><p>C</p></GraphButton> : null }
                            </div>
                        </div>
                    </div>
                </div>
            </>
        )
    }
}