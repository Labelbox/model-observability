import tensorflow as tf
import numpy as np
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc
import grpc

animal_classes = {
    16 : 'bird',
    17: 'cat',
    18: 'dog',
    19: 'horse',
    20: 'sheep',
    21: 'cow',
    22: 'elephant',
    23: 'bear',
    24: 'zebra',
    25: 'giraffe'
}

class Predictor:

    def __init__(self, host="inference-server", port=8500):
        addr = f"{host}:{port}"
        channel = grpc.insecure_channel(addr)
        self.stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
        self.request = predict_pb2.PredictRequest()
        self.request.model_spec.name = 'animaldet'
        self.request.model_spec.signature_name = "serving_default"

    def as_np(self, result):
        arr = np.array(result.float_val)
        return np.reshape(
            arr, tuple((int(dim.size) for dim in result.tensor_shape.dim)))

    def predict(self, image: np.ndarray, min_score=0.5):
        image = np.expand_dims(image, axis=0)

        self.request.inputs['input_tensor'].CopyFrom(
            tf.make_tensor_proto(image)
        )
        result = self.stub.Predict(self.request, 30.0)  # 10 secs timeout

        boxes = self.as_np(result.outputs['detection_boxes'])
        num_detections = self.as_np(result.outputs['num_detections'])
        scores = self.as_np(result.outputs['detection_scores'])
        detection_classes = self.as_np(result.outputs['detection_classes'])


        num_detections = np.squeeze(num_detections.astype(np.int32), axis=(0,))
        scores = np.squeeze(scores, axis=(0,))[:num_detections]
        boxes = np.squeeze(boxes, axis=(0,))[:num_detections]
        detection_classes = np.squeeze(detection_classes, axis=(0,))[:num_detections]

        animal_indices = np.isin(detection_classes, list(animal_classes.keys()))
        boxes = boxes[animal_indices]
        scores = scores[animal_indices]

        keep_indices = scores > min_score

        boxes = boxes[keep_indices]
        scores = scores[keep_indices]

        class_names = ["animal" for _ in range(len(boxes))]
        return boxes, scores, class_names


if __name__ == '__main__':
    predictor = Predictor(host = "localhost")
    predictor.predict(np.random.random((240, 240, 3)).astype(np.uint8))
