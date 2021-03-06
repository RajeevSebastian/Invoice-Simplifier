import React, {Component} from 'react';
import {Redirect, withRouter} from 'react-router-dom';
import firebase from 'firebase';

class Logout extends Component {
    componentWillMount = () => {
        firebase.auth().signOut();
    }

    render(){
        return(
            <Redirect to="/" />
        )
    }

}

export default Logout;