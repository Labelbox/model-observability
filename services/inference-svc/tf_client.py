import tensorflow as tf
import numpy as np
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc
import grpc


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
            tf.make_tensor_proto(image))
        result = self.stub.Predict(self.request, 10.0)  # 10 secs timeout

        boxes = self.as_np(result.outputs['detection_boxes'])
        num_detections = self.as_np(result.outputs['num_detections'])
        scores = self.as_np(result.outputs['detection_scores'])

        num_detections = np.squeeze(num_detections.astype(np.int32), axis=(0,))
        scores = np.squeeze(scores, axis=(0,))[0:num_detections]
        boxes = np.squeeze(boxes, axis=(0,))[0:num_detections]

        keep_indices = scores > min_score
        boxes = boxes[keep_indices]
        scores = scores[keep_indices]
        # TODO: Model returns index of class. Use that to get the name
        class_names = ["animal" for _ in range(len(boxes))]
        return boxes, scores, class_names


if __name__ == '__main__':
    predictor = Predictor()
    predictor.predict(np.random.random((640, 640, 3)).astype(np.uint8))
