from object_detection.builders import model_builder
from object_detection.utils import config_util
import numpy as np

NUM_CLASSES = 1
num_epochs = 10

IM_H, IM_W = 640, 640  #384,512

import tensorflow as tf

tf.keras.backend.clear_session()

print('Building model and restoring weights for fine-tuning...', flush=True)
num_classes = 1


def get_model():
    pipeline_config = 'object_detection/configs/tf2/ssd_resnet50_v1_fpn_640x640_coco17_tpu-8.config'
    checkpoint_path = 'object_detection/test_data/checkpoint/ckpt-0'
    configs = config_util.get_configs_from_pipeline_file(pipeline_config)
    model_config = configs['model']
    model_config.ssd.num_classes = num_classes
    model_config.ssd.freeze_batchnorm = True
    detection_model = model_builder.build(model_config=model_config,
                                          is_training=True)

    # Set up object-based checkpoint restore --- RetinaNet has two prediction
    # `heads` --- one for classification, the other for box regression.  We will
    # restore the box regression head but initialize the classification head
    # from scratch (we show the omission below by commenting out the line that
    # we would add if we wanted to restore both heads)
    fake_box_predictor = tf.compat.v2.train.Checkpoint(
        _base_tower_layers_for_heads=detection_model._box_predictor.
        _base_tower_layers_for_heads,
        # _prediction_heads=detection_model._box_predictor._prediction_heads,
        #    (i.e., the classification head that we *will not* restore)
        _box_prediction_head=detection_model._box_predictor.
        _box_prediction_head,
    )
    fake_model = tf.compat.v2.train.Checkpoint(
        _feature_extractor=detection_model._feature_extractor,
        _box_predictor=fake_box_predictor)
    ckpt = tf.compat.v2.train.Checkpoint(model=fake_model)
    ckpt.restore(checkpoint_path).expect_partial()

    # Run model through a dummy image so that variables are created
    image, shapes = detection_model.preprocess(tf.zeros([1, IM_H, IM_W, 3]))
    prediction_dict = detection_model.predict(image, shapes)
    _ = detection_model.postprocess(prediction_dict, shapes)
    return detection_model


detection_model = get_model()

tf.keras.backend.set_learning_phase(True)

# These parameters can be tuned; since our training set has 5 images
# it doesn't make sense to have a much larger batch size, though we could
# fit more examples in memory if we wanted to.
batch_size = 4
learning_rate = 0.001
num_batches = 1000

# Select variables in top layers to fine-tune.
trainable_variables = detection_model.trainable_variables
to_fine_tune = []
prefixes_to_train = [
    'WeightSharedConvolutionalBoxPredictor/WeightSharedConvolutionalBoxHead',
    'WeightSharedConvolutionalBoxPredictor/WeightSharedConvolutionalClassHead'
]
for var in trainable_variables:
    if any([var.name.startswith(prefix) for prefix in prefixes_to_train]):
        to_fine_tune.append(var)


# Set up forward + backward pass for a single train step.
def get_model_train_step_function(model, optimizer, vars_to_fine_tune):
    """Get a tf.function for training step."""

    # Use tf.function for a bit of speed.
    # Comment out the tf.function decorator if you want the inside of the
    # function to run eagerly.
    @tf.function
    def train_step_fn(image_tensors, groundtruth_boxes_list,
                      groundtruth_classes_list):
        """A single training iteration.

    Args:
      image_tensors: A list of [1, height, width, 3] Tensor of type tf.float32.
        Note that the height and width can vary across images, as they are
        reshaped within this function to be 640x640.
      groundtruth_boxes_list: A list of Tensors of shape [N_i, 4] with type
        tf.float32 representing groundtruth boxes for each image in the batch.
      groundtruth_classes_list: A list of Tensors of shape [N_i, num_classes]
        with type tf.float32 representing groundtruth boxes for each image in
        the batch.

    Returns:
      A scalar tensor representing the total loss for the input batch.
    """
        shapes = tf.constant(batch_size * [[IM_H, IM_W, 3]], dtype=tf.int32)
        model.provide_groundtruth(
            groundtruth_boxes_list=groundtruth_boxes_list,
            groundtruth_classes_list=groundtruth_classes_list)
        with tf.GradientTape() as tape:
            preprocessed_images = tf.concat([
                detection_model.preprocess(image_tensor)[0]
                for image_tensor in image_tensors
            ],
                                            axis=0)
            prediction_dict = model.predict(preprocessed_images, shapes)
            losses_dict = model.loss(prediction_dict, shapes)
            total_loss = losses_dict['Loss/localization_loss'] + losses_dict[
                'Loss/classification_loss']
            gradients = tape.gradient(total_loss, vars_to_fine_tune)
            optimizer.apply_gradients(zip(gradients, vars_to_fine_tune))
        return total_loss

    return train_step_fn


optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
train_step_fn = get_model_train_step_function(detection_model, optimizer,
                                              to_fine_tune)

feature_description = {
    'image': tf.io.FixedLenFeature((), tf.string, default_value=''),
    'xmin': tf.io.VarLenFeature(tf.float32),
    'xmax': tf.io.VarLenFeature(tf.float32),
    'ymin': tf.io.VarLenFeature(tf.float32),
    'ymax': tf.io.VarLenFeature(tf.float32),
    'label': tf.io.VarLenFeature(tf.int64),
}


def _parse_function(example_proto):
    # Parse the input `tf.train.Example` proto using the dictionary above.
    return tf.io.parse_single_example(example_proto, feature_description)


def decode_img(img):
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32) * 255
    img = tf.image.resize(img, [IM_H, IM_W])
    #img = tf.image.random_flip_left_right(img)
    #img = tf.image.random_flip_up_down(img)
    #img = tf.image.random_brightness(img, 0.3)
    return img


def get_label(path):
    part_list = tf.strings.split(path, "/")
    # in the case where each class of images is in one folder
    return part_list[-2] == class_names


def process_path(file_path):
    label = get_label(file_path)
    img = tf.io.read_file(file_path)
    img = decode_img(img)
    return img, label


def resss(parsed):
    image = decode_img(parsed['image'])
    #boxes = tf.stack([parsed[k] for k in ['xmin', 'xmax', 'ymin', 'ymax']], axis = 1)
    box = tf.stack([
        tf.sparse.to_dense(parsed[k]) for k in ['ymin', 'xmin', 'ymax', 'xmax']
    ],
                   axis=1)
    label = tf.cast(tf.sparse.to_dense(parsed['label']), tf.int32)
    label = tf.one_hot(label, NUM_CLASSES)
    return image, box, label


train_ds = tf.data.TFRecordDataset(["/tmp/train_data.tfr"])
train_ds = train_ds.cache()
train_ds = train_ds.map(_parse_function)
train_ds = train_ds.map(resss)
train_ds = train_ds.shuffle(500)
train_ds = train_ds.repeat(100000)
train_ds = iter(train_ds)

saver = tf.compat.v2.train.Checkpoint(model=detection_model)

print('Start fine-tuning!', flush=True)
for idx in range(num_batches):
    # Grab keys for a random subset of examples
    examples = [next(train_ds) for _ in range(batch_size)]
    images = [
        np.expand_dims(example[0].numpy(), axis=0) for example in examples
    ]
    boxes = [example[1].numpy() for example in examples]
    labels = [example[2].numpy() for example in examples]
    # Training step (forward pass + backwards pass)
    total_loss = train_step_fn(images, boxes, labels)

    if idx % 200 == 0:
        print('batch ' + str(idx) + ' of ' + str(num_batches) + ', loss=' +
              str(total_loss.numpy()),
              flush=True)
        saver.save('/outputs/adder')

print('Done fine-tuning!')
