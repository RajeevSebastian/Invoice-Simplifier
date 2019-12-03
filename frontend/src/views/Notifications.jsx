/*!

=========================================================
* Now UI Dashboard React - v1.2.0
=========================================================

* Product Page: https://www.creative-tim.com/product/now-ui-dashboard-react
* Copyright 2019 Creative Tim (https://www.creative-tim.com)
* Licensed under MIT (https://github.com/creativetimofficial/now-ui-dashboard-react/blob/master/LICENSE.md)

* Coded by Creative Tim

=========================================================

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

*/
import React from "react";
// react plugin for creating notifications over the dashboard
import NotificationAlert from "react-notification-alert";
import axios from 'axios';
import { Doughnut } from 'react-chartjs-2';
import firebase from 'firebase';

// reactstrap components
import {
  Alert,
  Card,
  CardTitle,
  CardBody,
  CardHeader,
  Row,
  Col,
  Button,
  Label,
  Form,
  FormGroup,
  Input
} from "reactstrap";

// core components
import PanelHeader from "../components/PanelHeader/PanelHeader.jsx";

class Notifications extends React.Component {
  
  state = {
    selectedFile: null,
    loaderClass: null,
    result: null,
    doughnutVisible: false,
    billIssuedBy: null,
    totalItemsPurchased: null,
    subtotal: null,
    tax: null,
    totalBillAfterTax: null,
    totalDiscount: null,
    invoiceId: null,
    showDoughnut: false,
    doughnutData: { data: { datasets:[], labels:[] } }
  }

  fileSelectedHandler = event => {
    this.setState({
      selectedFile: event.target.files[0]  
    });
  }

  fileUploadHandler = () => {
    const data = new FormData();
    var da = this.state.selectedFile.name;
    data.append('file', this.state.selectedFile);
    this.setState({loaderClass: "fa fa-spinner fa-spin"});
    axios.post("http://localhost:9000/users/uploadInvoice/" + firebase.auth().currentUser.uid, data, { 
      // receive two    parameter endpoint url ,form data
      headers: {
        "Authorization": "Bearer " + localStorage.getItem('token')
      }
    })
    .then(res => { // then print response status
      if(res.status == 200){        
        this.setState({
          result: res.data, 
          billIssuedBy: res.data.billIssuedBy,
          totalItemsPurchased: res.data.totalItemsPurchased,
          subtotal: res.data.subtotal,
          tax: res.data.tax,
          totalBillAfterTax: res.data.totalBillAfterTax,
          totalDiscount: res.data.totalDiscount,
          invoiceId: res.data.invoiceId
        });
      }
    })

  }

  fileEditHandler = () => {
    axios.put("http://localhost:9000/users/updateInvoice/" + firebase.auth().currentUser.uid, {
      "billIssuedBy": this.state.billIssuedBy,
      "totalItemsPurchased": this.state.totalItemsPurchased,
      "subtotal": this.state.subtotal,
      "tax": this.state.tax,
      "totalBillAfterTax": this.state.totalBillAfterTax,
      "totalDiscount": this.state.totalDiscount,
      "invoiceId": this.state.invoiceId
    },{
      headers: {
        "Authorization": "Bearer " + localStorage.getItem('token')
      }
    })
    .then(res => {
      var dat = {
        data : {
          labels: ['Subtotal', 'Tax', 'Total After Tax', 'Discount'],
          datasets: [{
            data: [this.state.subtotal, this.state.tax, this.state.totalBillAfterTax, this.state.totalDiscount],
            backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#123456'],
            hoverBackgroundColor: [
              '#FF6384',
              '#36A2EB',
              '#FFCE56',
              '#123456'
            ]
          }]
        }
      };
      this.setState({showDoughnut: true, doughnutData: dat, result: null});
    })
  }

  render() {
    var buttonText;
    var labelAppear;
    var uploadButton;
    if(this.state.selectedFile != null){
      buttonText = "Select a different file";
      labelAppear = <Label style={{'font-weight': 'bold', 'padding-left':'20px', 'font-size':'1.5em'}} >Selected file: {this.state.selectedFile.name}</Label>;
      uploadButton = <Button color="success" style={{'font-weight':'bold', 'font-size':'1.1em'}} onClick={this.fileUploadHandler}>Upload</Button>;
    }
    else{
      buttonText = "Choose a file";
      labelAppear = null;
      uploadButton = null;
    }
    console.log("in render data: " + this.state.doughnutData.data.labels);
    return (
      <>
        <PanelHeader
          content={
            <div className="header text-center">
              <h2 className="title">New Invoice</h2>
            </div>
          }
        />
        <div className="content">
          <NotificationAlert ref="notificationAlert" />
          {(this.state.result == null) && (this.state.showDoughnut == false) && <Row>
            <Col md={12} xs={12}>
              <Card>
                <CardHeader>
                  <CardTitle style={{'font-weight':'bold'}} tag="h4">Add a new invoice</CardTitle>
                </CardHeader>
                <CardBody>
                  <input 
                    style={{display: 'none'}}
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={this.fileSelectedHandler}
                    ref={fileInput => this.fileInput = fileInput}
                  />
                  <Button color="info" style={{'font-weight':'bold', 'font-size':'1.1em'}} onClick={() => this.fileInput.click()}>{buttonText}</Button>
                  {labelAppear}
                  <br/>
                  {uploadButton}
                    <i style={{'font-size':'2em', 'margin':'20px'}} className={this.state.loaderClass} />
                </CardBody>
              </Card>
            </Col>
          </Row>}
          {(this.state.result != null) && (this.state.showDoughnut == false) && <Row>
            <Col  md={12} xs={12}>
            <Card>
                <CardHeader>
                  <CardTitle style={{'font-weight':'bold'}} tag="h4">Invoice details</CardTitle>
                </CardHeader>
                <CardBody>
                  <p style={{'font-weight':'bold', 'font-size':'1.2em'}}>Make sure the information provided below is accurate</p>
                  <br/>
                  {/* <Form onSubmit={this.fileEditHandler} style={{'font-size':'1.5em','font-weight':'bold'}}>
                    <FormGroup> */}
                      <Label>Issued By:</Label>
                      <Input
                        type="text"
                        name="issuedBy"
                        value={this.state.billIssuedBy}
                        onChange={e => this.setState({ billIssuedBy: e.target.value })}
                      />
                    {/* </FormGroup>
                    <FormGroup> */}
                      <Label>Total Item Purchased:</Label>
                      <Input
                        type="text"
                        name="totalItems"
                        value={this.state.totalItemsPurchased}
                        onChange={e => this.setState({ totalItemsPurchased: e.target.value })}
                      />
                    {/* </FormGroup>
                    <FormGroup> */}
                      <Label>Total Before Tax:</Label>
                      <Input
                        type="text"
                        name="beforeTax"
                        value={this.state.subtotal}
                        onChange={e => this.setState({ subtotal: e.target.value })}
                      />
                    {/* </FormGroup>
                    <FormGroup> */}
                      <Label>Tax:</Label>
                      <Input
                        type="text"
                        name="tax"
                        value={this.state.tax}
                        onChange={e => this.setState({ tax: e.target.value })}
                      />
                    {/* </FormGroup>
                    <FormGroup> */}
                      <Label>Total After Tax:</Label>
                      <Input
                        type="text"
                        name="afterTax"
                        value={this.state.totalBillAfterTax}
                        onChange={e => this.setState({ totalBillAfterTax: e.target.value })}
                      />
                    {/* </FormGroup>
                    <FormGroup> */}
                      <Label>Total Discount:</Label>
                      <Input
                        type="text"
                        name="discount"
                        placeholder="Email"
                        value={this.state.totalDiscount}
                        onChange={e => this.setState({ totalDiscount: e.target.value })}
                      />
                    {/* </FormGroup> */}
                    <Button onClick={this.fileEditHandler} type="submit" color="primary">Save</Button>
                  {/* </Form> */}
                </CardBody>
              </Card>
            </Col> 
          </Row>}
          {(this.state.showDoughnut) && <Row>
            <Col md={12} xs={12}>
            <Card>
                <CardHeader>
                  <CardTitle style={{'font-weight':'bold'}} tag="h4">Distribution</CardTitle>
                </CardHeader>
                <CardBody>
              <Doughnut data={this.state.doughnutData.data} />
              </CardBody>
              </Card>
            </Col>
          </Row>}
        </div>
      </>
    );
  }
}

export default Notifications;
