import React from "react";
import MapButton from './MapButton';
import DateRangePicker from 'react-daterange-picker';
import './DateContainer.css';

export default class DateContainer extends React.Component {
    constructor(props){
        super(props);
        this.state = {
            isCalendarVisible: false
        };
    }

    toggleCalendar = () => {
        this.setState(prevState => ({
            isCalendarVisible: !prevState.isCalendarVisible
        }));
    }

    render = () => {
        return(
            <>
                <MapButton class="button-calendar" handlecheck={this.toggleCalendar}>
                    <img style={{width: '26px', height: '26px', margin: '7px'}} src="static/images/calendar.png"/>
                </MapButton>
                {this.state.isCalendarVisible && (
                    <div className="CalendarContainer" onMouseLeave={this.toggleCalendar}>
                        <DateRangePicker onSelect={this.props.updatedates} singleDateRange={true} value={this.props.dateinfo.range} maximumDate={this.props.dateinfo.max} minimumDate={this.props.dateinfo.min}/>
                    </div>
                )}
            </>
        );
    }
}