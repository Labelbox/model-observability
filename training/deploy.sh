
docker run -t --rm -p 8500:8500 -p 8501:8501 -v $(pwd)/model:/models/animaldet -e MODEL_NAME=animaldet tensorflow/serving:latest

