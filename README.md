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
2. Animal-svc
    - Service for predicting animal bounding boxes in images
3. Oberserve-svc
    - Uploads model inferences to labelbox
    - Once inferences are labeled it computes metrics and logs them so observe can injest performance statistics
4. Storage
    - Local deployment of s3 emulator so that infrences, labels, and user requests can be persisted
5. Deployment
    - Contains all of the configuration for the minikube deployment

## Usage:


### Train and Deploy
1. Train a model
    * Change into the training dir: `cd training`
    * Run the ETL: `./etl.sh`
        * This requires that you have access to a project with a class called animal and some associated labels
        * Update etl.py to use your project id
    * Train the model `./train.sh`
    * Create a servable `./export.sh`    
2. Configure labelbox project
    * Change into the observe-svc dir: `cd observe-svc`
    * Run `configure_project.py`
3. Create the storage directories
    * `cd storage/config`
    * `./configure.sh`
3. Build the docker containers
    * Start minikube `minikube start`
    * Make docker commands work with minikube env `eval $(minikube docker-env)`
    * Build the images with `docker-compose build`
4. Deploy to minikube
    * Change into the deployment dir: `cd deployment`
    * Set the secrets `./create_secret.sh`
        * Must have `LABELBOX_API_KEY` and `NGROK_TOKEN` set
    * Mount the drives `nohup ./mount_drives.sh > mounts.out &`
    * Deploy the services
        * kubectl apply -f `animal-server-deployment.yaml,observe-svc-service.yaml,storage-service.yaml,animal-svc-service.yaml,observe-svc-deployment.yaml,animal-server-service.yaml,animal-svc-deployment.yaml,storage-deployment.yaml`
    * Deploy observe metrics with `./observe-metrics.sh`
        * Must have `OBSERVE_CUSTOMER_ID` and `OBSERVE_TOKEN` set
    * Make services accessible `nohup ./fwd-svc.sh > fwd.out &`


### Client

* To produce metrics we can us the code in the `client` directory
* This simulates customer usage. 
    * Customers can post images of animals and the model will predict where the animals are in the image

* Note that the first request might fail due to a timeout since we did not add warm up to the tf-server.

### Labeling

* Once the service is up and running images posted to animal-svc and associated inferences will be uploaded to labelbox for labeling
* Click `Start Labeling` and label all of the images in the queue
* Once an image is reviewed and given a thumbs up, it will be sent back to observe-svc, metrics will be computed, and the result will be logged out


### Metrics
* Make sure you made some requests and labeled some images first
* Go to <your account number>.observeinc.com
* Create a worksheet
* Filter on the logs (search for external_id to get logs related to iou scores)
* Create any reports you want! Learn more about using observe at docs.observeinc.com
* Here are some cool charts I made:



    
