from labelbox.schema.ontology import OntologyBuilder, Tool, Classification, Option
from labelbox import Project, Dataset, Client, LabelingFrontend, Client, Webhook
from datetime import datetime
from shared import secret
import json
import boto3
import uuid

client = Client()


def create_conf():
    project = client.create_project(name="model-observe-project")
    dataset = client.create_dataset(name="model-observe-dataset")
    project.datasets.connect(dataset)

    ontology_builder = OntologyBuilder(tools=[
        Tool(tool=Tool.Type.BBOX,
             name="person",
             classifications=[
                 Classification(class_type=Classification.Type.TEXT,
                                instructions="confidence")
             ]),
    ])
    editor = next(
        client.get_labeling_frontends(where=LabelingFrontend.name == 'editor'))
    project.setup(editor, ontology_builder.asdict())
    project.enable_model_assisted_labeling()
    ontology = ontology_builder.from_project(project)

    conf = {
        'project_id':
            project.uid,
        'dataset_id':
            dataset.uid,
        'bbox_feature_schema_id':
            ontology.tools[0].feature_schema_id,
        'text_feature_schema_id':
            ontology.tools[0].classifications[0].feature_schema_id
    }

    with open('project_conf.json', 'w') as file:
        file.write(json.dumps(conf))

    topic = Webhook.Topic.REVIEW_CREATED.value
    webhook = Webhook.create(client,
                             topics=[topic],
                             url="set_at_runtime",
                             secret=secret.decode(),
                             project=project)


if __name__ == '__main__':
    create_conf()
