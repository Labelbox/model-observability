# model-observability
Track model performance over time using Observe

| <img src="https://labelbox.com/blog/content/images/2021/02/logo-v4.svg" width="256" style="background-color:White;"> | <img src="https://www.observeinc.com/wp-content/themes/observe-rdc/theme/images/observe.jpg" width="256"> | 
| -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |

<br></br>
## Overview
* This project demonstrates how to do the following:
    1. Train a neural network using data from labelbox
    2. Deploy the trained model
    3. Monitor the model performance over time using Labelbox and Observe
<br></br>
## Components
1. Training Code
    - Use this to create a trained model
2. inference-svc
    - Service for predicting animal bounding boxes in images
3. Oberserve-svc
    - Uploads model inferences to labelbox
    - Once inferences are labeled it computes metrics and logs them so observe can injest performance statistics
4. Storage
    - Local deployment of s3 emulator so that infrences, labels, and user requests can be persisted
5. Deployment
    - Contains all of the configuration for the minikube deployment

<img src="images/design.png" height="384" >


## Usage:


### Train
1. Train a model
    * Run the ETL: `make etl`
        * This requires that you have access to a project with a class called animal and some associated labels
        * Update etl.py to use your project id
    * Train the model `make train`
    * Create a servable `make export`
    * The model artifacts are written to the `/tmp` dir by default.    

### Deployment
1. If you have never run before run the following:
    * `make configure-labelbox`
        - Creates a new labelbox config. This is where the model feedback will be sent to (see services/monitor-svc/project_conf.json)
    * `make configure-storage`
        - Creates the local storage directory structure under `./storage`
2. Deploy to minikube
    * Must have the following env vars set:
        - `LABELBOX_API_KEY` : Labelbox api key (https://docs.labelbox.com/en/introduction/faq#how-do-i-create-an-api-key-)
        - `NGROK_TOKEN` : Enables labelbox webhooks to make requests to deployments without public ip addresses (https://ngrok.com)
        - `OBSERVE_CUSTOMER_ID` and `OBSERVE_TOKEN` used to aggregate both machine and model metrics (https://www.observeinc.com)
    * `make deploy`
        - Runs the services.

### Client

* To produce metrics we can us the code in the `client` directory
* This simulates customer usage. 
    * Customers can post images of animals and the model will predict where the animals are in the image

* Note that the first request might fail due to a timeout since we did not add warm up to the tf-server.

### Labeling

* Once the service is up and running images posted to inference-svc and associated inferences will be uploaded to labelbox for labeling
* Click `Start Labeling` and label all of the images in the queue
* Once an image is reviewed and given a thumbs up, it will be sent back to monitor-svc, metrics will be computed, and the result will be logged out
* Watch the logs to see the metrics get calculated `kubectl logs svc/monitor-svc --follow`


### Metrics
* Make sure you made some requests and labeled some images first. You can use the code under the `clien` dir
* Go to <your account number>.observeinc.com
* I used a script under deployment/metrics-query.opal to create a metrics dataset
* The rest of the instructions can be found here (https://docs.observeinc.com/en/latest/content/metrics/MetricsIntro.html)
* Here are some cool charts that I made:


<img src="images/observe-dashboard.png" height="512" >

### Productionizing
- This is a POC with most of what users need to build a production system. 
* Remove the local s3 deployment in favor of a more permanent storage solution
* Needs test cases and error handling
* NGROK needs to be removed and use a public endpoint
* Model files will need to be stored somewhere other than the host tmp directory.
* The way that dates are kept track of is not ideal.
* Add a warmup file for the tensorflow server
* The sampling logic needs to be improved for production. 
