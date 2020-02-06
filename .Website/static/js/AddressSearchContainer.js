import React from "react";

import PlacesAutocomplete, {
    geocodeByAddress,
    getLatLng,
  } from 'react-places-autocomplete';
import './AddressSearchContainer.css';

export default class AddressSearchContainer extends React.Component {
    constructor(props){
        super(props);
        this.state = {
            active: true,
            address: ''
        };
    }

    handleCheck = () => {
        this.setState(prevState => ({
            active: !prevState.active
        }));
    }

    handleChange = address => {
        this.setState({ address });
      };
     
    handleSelect = address => {
        geocodeByAddress(address)
            .then(results => getLatLng(results[0]))
            .then(this.setState({ address }))
            .then(this.setState(prevState => ({
                active: !prevState.active
            })))
            .then(latLng => this.props.addressChange(latLng))
            .catch(error => {
                console.error('Error', error)
                this.setState({ address: '' })
        });
    };

    render = () => {
        let searchbar = <>
            <PlacesAutocomplete
                value={this.state.address}
                onChange={this.handleChange}
                onSelect={this.handleSelect}
            >
            {({ getInputProps, suggestions, getSuggestionItemProps, loading }) => (
                    <div className="AddressSearch-container">
                        <input
                        {...getInputProps({
                            placeholder: 'Type an address...',
                            className: 'AddressSearch-bar',
                        })}
                        />
                        <div className="AddressSearch-suggestion-container">
                        {suggestions.map(suggestion => {
                            return (
                            <div {...getSuggestionItemProps(suggestion)}>
                                <span className="AddressSearch-suggestion">
                                    {suggestion.description}
                                </span>
                            </div>
                            );
                        })}
                        </div>
                    </div>
                    )}
            </PlacesAutocomplete>
        </>
        return (
            <>

                {this.props.addressActive ? searchbar : null}
            </>
        )
    }
}