# Invoice Simplifier 


Invoice simplifier is a productivity application that tracks and analyses your expenses using invoice photos, thus eliminating the need for you to spend hours managing your expenses and budget.

# Hill Statement
## Who : 
Small Business owners who cannot afford manual labour and time to analyze their purchases. Example Persona: John is small scale business owner who has just started his computer business. Due to the current crunch in his workforce, proper purchase management is getting ignored. John decides to use Invoice Simplifier to get his work done which simplifies his work as well as saves crucial manhours.

## What :
Decoding a complex invoice and reconciliation can be tedious and time consuming. In addition, in this cumbersome process, missing crucial details and spotting errors in the invoice can be an added overhead. To take care of all these day to day issues Invoice-Simplifier extracts key elements from your invoices, and gives you a simplified and informative summary

## Wow :
Cost effective as compared to sofisticated costly products. In addition cumulative summary of all purchases till now gives a comprehensive summary of overall expenses in different fields.


# Abstract
In today’s scenario, where time is of prime importance, decoding a complex invoice and reconciliation can be tedious and time consuming. In addition, in this cumbersome process, missing crucial details and spotting errors in the invoice can be an added overhead. To take care of all these day to day issues Invoice-Simplifier extracts key elements from your invoices, and gives you a simplified and informative summary, while also analysing and categorizing the different products / services that drain your wallet the most. Pie charts and graphs has been included as an added advantage to get a better visual understanding of the expenditures. Our application plans to reduce all the overheads from the users’ perspective and make invoice analysis a seamless experience.

The user particpation can be as simple as just uploading a snapshot of the invoice and hit the submit button. The invoice will be directly sent to our backend python data processing service that will take care of all the complex stuffs. Once done the processed data will be displayed to the user for a final confirmation. That's it, it will be ingested into the database summary reports and charts will pop up on the user dashboard.

# Target Users
Small & medium sized business owners specially in developing countries(e.g. India etc.) where printed invoices are still a regular practice and not the digitized ones.

# Impact Of Product
1. Reduce the cost of manual effort: The application allows for automatic categorization of invoices and does not require any manual effort for digitization of paper invoices.
2. Automate processes: This involves automatic processing of invoices and reducing the errors that are caused by manual entry.
3. Easy Access and Real time monitoring: With the dashboard business owners can have access to all the payments processed and greater visibility of where the money is being sent.
4. Analytics: With all the invoices stored in one place analysis and accounting becomes easier.

# Architecture Diagram
![Architecture Diagram](https://github.com/SJSUFall2019-CMPE272/Invoice-Simplifier/blob/master/Architecture.jpg)

# Technology Stack
1. __Frontend__ - React / Vue
2. __Backend__ - Nodejs and related libraries
3. __Python__ - data processing. Libraries used:
    * __Numpy, pillow and openCV__ - Image upscaling and segmentation
    * __Pytesseract__ - OCR
    * __Spacy / NLTK__ - Named entity recognition and catagorization
    * __Numpy and pandas__ - Data processing
    
    
# Team
1. __Shivan Desai__ - Will be working on frontend design and functionality implementations.
2. __Samik Biswas__ - Handling image upscaling, segmentation, OCR and NER.
3. __Shubhangi Yadav__ - Planning and implementing backend solutions along with security authentication and data validation.
4. __Rajeev Sebastian__ - Integrating different parts of the project and interfacing between different technologies and cloud deployment.

###### Original Professor Feedback :-
Name entity recognition using OCR from a invoice

Develop a service that takes invoices as input and generates a csv with important name and entities which can be ingested into a database. The end to end flow will show the extracted data which user will acknowledge before it gets ingested into db.

use state of the art OCR and language model to build this. take a couple of invoices as examples ..

