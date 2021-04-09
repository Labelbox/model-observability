import json

from labelbox import LabelingFrontend, Client, Webhook
from labelbox.schema.ontology import OntologyBuilder, Tool, Classification

from monitor.settings import secret


def configure_project():
    client = Client()

    project = client.create_project(name="model-observe-project")
    dataset = client.create_dataset(name="model-observe-dataset")
    project.datasets.connect(dataset)

    # If you are adding more classes add them here
    ontology_builder = OntologyBuilder(
        tools=[
            Tool(
                tool=Tool.Type.BBOX,
                name="animal",
                classifications=[
                    Classification(
                        class_type=Classification.Type.TEXT, instructions="confidence"
                    )
                ],
            ),
        ]
    )
    editor = next(
        client.get_labeling_frontends(where=LabelingFrontend.name == "editor")
    )
    project.setup(editor, ontology_builder.asdict())
    project.enable_model_assisted_labeling()
    ontology = ontology_builder.from_project(project)

    conf = {
        "project_id": project.uid,
        "dataset_id": dataset.uid,
        "bbox_feature_schema_id": ontology.tools[0].feature_schema_id,
        "text_feature_schema_id": ontology.tools[0]
            .classifications[0]
            .feature_schema_id,
    }

    with open("project_conf.json", "w") as file:
        file.write(json.dumps(conf))

    Webhook.create(
        client,
        topics=[Webhook.Topic.REVIEW_CREATED.value],
        url="set_at_runtime",
        secret=secret.decode(),
        project=project,
    )


if __name__ == "__main__":
    configure_project()
