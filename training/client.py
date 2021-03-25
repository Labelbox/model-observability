
import tensorflow as tf
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc
import grpc 


host, port = "localhost", 8501 
channel = implementations.insecure_channel(host, int(port))
stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)

# Create prediction request object
request = predict_pb2.PredictRequest()

request.model_spec.name = 'animaldet'

request.model_spec.signature_name = "default_signature"
request.inputs['input_tensor'].CopyFrom(tf.make_tensor_proto({image}))

result = stub.Predict(request, 10.0)  # 10 secs timeout

category_index = load_label_map(FLAGS.path_to_labels)
boxes = result.outputs['detection_boxes'].float_val
classes = result.outputs['detection_classes'].float_val
scores = result.outputs['detection_scores'].float_val

num_detections = np.squeeze(pred['num_detections'].numpy().astype(np.int32), axis=(0,))
detection_scores = np.squeeze(pred['detection_scores'].numpy(), axis=(0,))[0:num_detections]
class_indices =  np.squeeze(pred['detection_classes'].numpy().astype(np.int32), axis=(0,))[0:num_detections]
#boxes = np.squeeze(pred['detection_boxes'].numpy() * np.array([640,640, 640,640]), axis=(0,))[0:num_detections]
boxes = np.squeeze(pred['detection_boxes'].numpy(), axis=(0,))[0:num_detections]
#ymin, xmin, ymax, xmax = np.split(boxes, 4, axis=-1)
#processed_boxes = np.concatenate([xmin, ymin, xmax - xmin, ymax - ymin], axis=-1)
min_score = 0.5
keep_indices = detection_scores > min_score
boxes = boxes[keep_indices]
