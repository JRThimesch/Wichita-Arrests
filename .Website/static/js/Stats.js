import React from "react";
import BarGraph from "./BarGraph";
import './Stats.css'
import GraphButton from "./GraphButton";

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
            activeData: {
                barsActive: 'groups',
                groupingActive: 'default',
                queryType: 'distinct'
            },
            data: { 
                numbers: Array.from(Array(150), () => 0),
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
                }
            },
            key: 0
        }
    }

    createCustomGraph = () => {
        this.setState({data: { 
            numbers: Array.from(Array(150), () => 0),
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
            }
        }})
    }

    getInfoBoxData = (passedData, active) => {
        this.setState(prevState => ({
            activeData: {
                barsActive: active,
                groupingActive: 'default',
                queryType: prevState.activeData.queryType
            },
            data: passedData
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
                colors: prevState.data.colors.filter((_, i) => i !== key)
            },
            genderData: {
                maleCounts: prevState.genderData.maleCounts.filter((_, i) => i !== key),
                femaleCounts: prevState.genderData.femaleCounts.filter((_, i) => i !== key)
            }
        }))
    }

    addBar = () => {
        this.setState(prevState => ({
            data: {
                numbers: [...prevState.data.numbers, Math.round(Math.random() * 900)],
                labels: [...prevState.data.labels, 'new test label'],
                colors: [...prevState.data.colors, '#123123']
            }
        }))
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
        let num = Math.random() * 100000
        return (
            <>
                <div className="Stats-container">
                    <BarGraph
                        data={this.state.data}
                        key={this.state.key}
                        activedata={this.state.activeData}
                        addbar={this.addBar}
                        removebar={this.removeBar}
                        hoverdata={this.getHoverData}
                        getinfoboxdata={this.getInfoBoxData}
                    />
                    <div className="Stats-right-container">
                        <div className="Stats-button-container">
                            <div className="Stats-button-container-group">
                                <GraphButton
                                handleclick={this.createCustomGraph}
                                ><img src="static/images/customGraph.png"/></GraphButton>
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