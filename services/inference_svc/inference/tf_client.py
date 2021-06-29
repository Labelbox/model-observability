from typing import Tuple, List

import grpc
import numpy as np
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc
import tensorflow as tf

from resources.settings import MODEL_CLASS_MAPPINGS


class Predictor:

    def __init__(self, host="inference-server", port=8500):
        addr = f"{host}:{port}"
        channel = grpc.insecure_channel(addr)
        self.stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)
        self.request = predict_pb2.PredictRequest()
        self.request.model_spec.name = 'detmodel'
        self.request.model_spec.signature_name = "serving_default"

    def as_np(self, result: predict_pb2.PredictResponse) -> np.ndarray:
        """ Converts prediction to numpy array """
        arr = np.array(result.float_val)
        return np.reshape(
            arr, tuple((int(dim.size) for dim in result.tensor_shape.dim)))

    def predict(self,
                image: np.ndarray,
                min_score=0.5) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Makes a request to the tensorflow server.
        Processes the result:
            - Convert to numpy arrays
            - Filter out results with low confidence thresholds
            - Map prediction indicies to class names
        """
        image = np.expand_dims(image, axis=0)
        self.request.inputs['input_tensor'].CopyFrom(
            tf.make_tensor_proto(image))
        result = self.stub.Predict(self.request, 30.0)  # 30 second timeout
        scores, boxes, detection_classes = self.process_predictions(result)
        valid_indices = np.isin(detection_classes,
                                list(MODEL_CLASS_MAPPINGS.keys()))
        boxes = boxes[valid_indices]
        scores = scores[valid_indices]
        class_indices = detection_classes[valid_indices]
        keep_indices = scores > min_score
        boxes = boxes[keep_indices]
        scores = scores[keep_indices]
        class_indices = class_indices[keep_indices]
        class_names = [MODEL_CLASS_MAPPINGS[idx] for idx in class_indices]
        return boxes, scores, class_names

    def process_predictions(
        self, result: predict_pb2.PredictResponse
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Converts a PredictResponse into numpy arrays
        """
        boxes = self.as_np(result.outputs['detection_boxes'])
        num_detections = self.as_np(result.outputs['num_detections'])
        scores = self.as_np(result.outputs['detection_scores'])
        detection_classes = self.as_np(result.outputs['detection_classes'])

        num_detections = np.squeeze(num_detections.astype(np.int32), axis=(0,))
        scores = np.squeeze(scores, axis=(0,))[:num_detections]
        boxes = np.squeeze(boxes, axis=(0,))[:num_detections]
        detection_classes = np.squeeze(detection_classes,
                                       axis=(0,))[:num_detections]
        return scores, boxes, detection_classes


if __name__ == '__main__':
    # Test case for calling the tensorflow server
    predictor = Predictor(host="localhost")
    predictor.predict(np.random.random((320, 320, 3)).astype(np.uint8))
