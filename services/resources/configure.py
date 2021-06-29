import json
from uuid import uuid4

from labelbox import LabelingFrontend, Client, Webhook
from labelbox.schema.ontology import OntologyBuilder, Tool, Classification

from resources.secrets import secret
from resources.settings import MODEL_CLASS_MAPPINGS, client


def configure_project():
    """
    * Creates a new:
       - project
       - dataset
       - mea model
       - mea model run
    * Sets up / connects everything
    * Saves all of the ids to be referenced later
    """

    project = client.create_project(name="observability-project")
    dataset = client.create_dataset(name="observability-dataset")
    project.datasets.connect(dataset)

    ontology_builder = OntologyBuilder(tools=[
        Tool(
            tool=Tool.Type.BBOX,
            name=name,
            classifications=[
                Classification(class_type=Classification.Type.TEXT,
                               instructions="confidence")
            ],
        ) for name in MODEL_CLASS_MAPPINGS.values()
    ])
    editor = next(
        client.get_labeling_frontends(where=LabelingFrontend.name == "editor"))
    project.setup(editor, ontology_builder.asdict())
    project.enable_model_assisted_labeling()
    ontology = ontology_builder.from_project(project)

    model_name = f"observability-model-{uuid4()}"
    model = client.create_model(name=model_name,
                                ontology_id=project.ontology().uid)
    model.create_model_run('production-data')

    with open("resources/project_conf.json", "w") as file:
        file.write(
            json.dumps({
                "project_id":
                    project.uid,
                "dataset_id":
                    dataset.uid,
                "bbox_feature_schema_id":
                    ontology.tools[0].feature_schema_id,
                "text_feature_schema_id":
                    ontology.tools[0].classifications[0].feature_schema_id,
                "model_id":
                    model.uid
            }))

    Webhook.create(
        client,
        topics=[Webhook.Topic.REVIEW_CREATED.value],
        url="set_at_runtime",
        secret=secret.decode(),
        project=project,
    )


if __name__ == "__main__":
    configure_project()
