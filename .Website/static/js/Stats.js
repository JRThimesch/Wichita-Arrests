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

const LoadingContainer = props => {
    return (
        <GraphButton>
            {props.children}
            <div className="LoadingContainerFilter-before-load">
                <div className="LoadingCircleFilter"><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div></div>
            </div>
        </GraphButton>
    )
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
                    numbers: null
                },
                ageData : {
                    numbers: null
                },
                timeData: {
                    numbers: null
                },
                dayData: {
                    numbers: null
                },
            },
            key: 0,
            inactiveLabels: [],
            inactiveLabelsVisible: false
        }
    }

    deleteGraph = () => {
        if (this.state.inactiveLabelsVisible) {
            this.setState(prevState => ({
                data: { 
                    numbers: [],
                    labels: [],
                    colors: [],
                    genderData: {
                        numbers: []
                    },
                    ageData : {
                        numbers: []
                    },
                    timeData: {
                        numbers: []
                    },
                    dayData: {
                        numbers: []
                    },
                },
                inactiveLabels: [...prevState.data.labels, ...prevState.inactiveLabels],
                inactiveLabelsVisible: false,
                level: 0
            }))
        } else {
            this.setState(prevState => ({
                data: { 
                    numbers: [],
                    labels: [],
                    colors: [],
                    genderData: {
                        numbers: []
                    },
                    ageData : {
                        numbers: []
                    },
                    timeData: {
                        numbers: []
                    },
                    dayData: {
                        numbers: []
                    },
                },
                inactiveLabels: [...prevState.data.labels, ...prevState.inactiveLabels],
                level: 0
            }))
        }
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
        this.groupData(passedData, active, "genders")
        this.groupData(passedData, active, "ages")
        this.groupData(passedData, active, "times")
        this.groupData(passedData, active, "days")
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
                    dayData: data
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

    groupData = (passedData, groupType, type) => {
        fetch(`api/stats/grouping/${type}`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                labels: passedData.labels,
                dataActive: groupType,
                queryType: this.state.activeData.queryType,
                groupingType: type
            })
        })
            .then(response => response.json())
            .then(data => this.setState(prevState => ({
                data: {
                    ...prevState.data,
                    ...data
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
            this.groupData(data, currentData, "genders")
            this.groupData(data, currentData, "ages")
            this.groupData(data, currentData, "times")
            this.groupData(data, currentData, "days")
            this.setState(prevState => ({
                data, 
                activeData: {
                    barsActive: currentData,
                    groupingActive: 'default',
                    queryType: prevState.activeData.queryType
                },
                key : Math.random() * 10000,
                level: 0,
                inactiveLabels: []
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
        let uniqueLabels = [...new Set(this.state.inactiveLabels)]

        this.setState(prevState => ({
            data: {
                numbers: prevState.data.numbers.filter((_, i) => i !== key),
                labels: prevState.data.labels.filter((_, i) => i !== key),
                colors: prevState.data.colors.filter((_, i) => i !== key),
                genderData: {
                    numbers: prevState.data.genderData.numbers.filter((_, i) => i !== key),
                },
                ageData: {
                    numbers: prevState.data.ageData.numbers.filter((_, i) => i !== key)
                },
                timeData: {
                    numbers: prevState.data.timeData.numbers.filter((_, i) => i !== key),
                },
                dayData: {
                    numbers: prevState.data.dayData.numbers.filter((_, i) => i !== key),
                },
            },
            inactiveLabels: [...prevState.inactiveLabels, prevState.data.labels[key]],
            level: 0
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
        let label = e.currentTarget.getAttribute('title')
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
                    numbers: [...prevState.data.genderData.numbers, ...data.genderData.numbers],
                },
                ageData: {
                    numbers: [...prevState.data.ageData.numbers, ...data.ageData.numbers]
                },
                timeData: {
                    numbers: [...prevState.data.timeData.numbers, ...data.timeData.numbers],
                },
                dayData: {
                    numbers: [...prevState.data.dayData.numbers, ...data.dayData.numbers],
                }
            },
            inactiveLabels: prevState.inactiveLabels.filter((item, _) => item != label),
            level: 0
        })))
    }

    componentDidMount = () => {
        let currentData = 'groups'
        let queryType = this.state.activeData.queryType
        fetch(`/api/stats/${currentData}/${queryType}`)
        .then(response => response.json())
        .then(data => {
            this.groupData(data, currentData, "genders")
            this.groupData(data, currentData, "ages")
            this.groupData(data, currentData, "times")
            this.groupData(data, currentData, "days")
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
                <div className="Stats-add-title-container" onClick={(e) => e.stopPropagation()}>
                    <span className="Stats-add-title">Add Labels</span>
                    <span className="Stats-add-button-close" onClick={this.closeInactiveLabels}/>
                </div>
                <div className="Stats-add-label-container">
                    {truncatedLabels.map((label, i) => {
                        return <span title={this.state.inactiveLabels[i]} className="Stats-add-label" onClick={this.addBar} key={i}>{label}</span>
                    })}
                </div>
            </div> : null
            
        let addButton = this.state.inactiveLabels.length !== 0 ? <div
            className="Stats-add-button"
            onClick={this.toggleInactiveVisible}
            ><img src="static/images/addGraph.png"/>{inactiveLabels}</div> : null
        
        let isChargeButtonActive = (this.state.activeData.barsActive != 'arrests' ||
            this.state.activeData.barsActive != 'tags' ||
            this.state.activeData.barsActive != 'groups')

        let queryTypeToSwitch = this.state.activeData.queryType == 'distinct' ? 'charges' : 'distinct'
        let queryTypeToSwitchIcon = `static/images/${queryTypeToSwitch}Icon.png`
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
                        removeReady={sortReady}
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
                                    handleclick={this.deleteGraph}
                                    ><img src="static/images/eraseGraph.png"/></GraphButton>
                                {addButton}
                                {isChargeButtonActive
                                    ? <GraphButton
                                        handleclick={this.toggleQuery}
                                        type={queryTypeToSwitch}
                                        ><img src={queryTypeToSwitchIcon}/></GraphButton> 
                                    : <GraphButton
                                        handleclick={()=>{}}>
                                        <img src={queryTypeToSwitchIcon} 
                                            style={{opacity: '20%'}}/>
                                    </GraphButton>}
                            </div>
                            <hr className="Stats-button-container-line"/>
                            <div className="Stats-button-container-group">
                                <GraphButton
                                    handleclick={this.getData}
                                    type="groups"
                                    ><img src="static/images/groupsIcon.png"/></GraphButton>
                                <GraphButton 
                                    handleclick={this.getData}
                                    type="tags"
                                    ><img src="static/images/tagsIcon.png"/></GraphButton>
                                <GraphButton
                                    handleclick={this.getData}
                                    type="arrests"
                                    ><img src="static/images/arrestsIcon.png"/></GraphButton>
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
                                    </GraphButton> : <LoadingContainer>
                                        <img style={{opacity: "50%"}} src="static/images/gendersIcon.png"/>
                                    </LoadingContainer> }
                                {this.state.activeData.barsActive != 'ages' &&
                                    this.state.data.ageData ? <GraphButton
                                    handleclick={this.toggleGrouping}
                                    type="ages"
                                    ><img src="static/images/agesIcon.png"/>
                                    <AnimatedBars/>
                                    </GraphButton> : <LoadingContainer>
                                        <img style={{opacity: "50%"}} src="static/images/agesIcon.png"/>
                                    </LoadingContainer> } 
                                {this.state.activeData.barsActive != 'times' &&
                                    this.state.data.timeData ? <GraphButton
                                    handleclick={this.toggleGrouping}
                                    type="times"
                                    ><img src="static/images/timesIcon.png"/>
                                    <AnimatedBars/>
                                    </GraphButton> : <LoadingContainer>
                                        <img style={{opacity: "50%"}} src="static/images/timesIcon.png"/>
                                    </LoadingContainer> }
                                {this.state.activeData.barsActive != 'dates' &&
                                    this.state.activeData.barsActive != 'days' &&
                                    this.state.data.dayData ? <GraphButton
                                    handleclick={this.toggleGrouping}
                                    type="days"
                                    ><img src="static/images/daysIcon.png"/>
                                    <AnimatedBars/>
                                    </GraphButton> : <LoadingContainer>
                                        <img style={{opacity: "50%"}} src="static/images/daysIcon.png"/>
                                    </LoadingContainer> }
                            </div>
                            <hr className="Stats-button-container-line"/>
                            <div className="Stats-button-container-group">
                                {sortReady ? <GraphButton
                                    handleclick={this.sortData}
                                    type="numeric"
                                    ><p>1</p><p>2</p><p>3</p></GraphButton> : <LoadingContainer>
                                        <div style={{opacity: "50%"}}><p>1</p><p>2</p><p>3</p></div>
                                    </LoadingContainer> }
                                {sortReady ? <GraphButton 
                                    handleclick={this.sortData}
                                    type="alpha"
                                    ><p>A</p><p>B</p><p>C</p></GraphButton> : <LoadingContainer>
                                        <div style={{opacity: "50%"}}><p>A</p><p>B</p><p>C</p></div>
                                    </LoadingContainer> }
                            </div>
                        </div>
                    </div>
                </div>
            </>
        )
    }
}