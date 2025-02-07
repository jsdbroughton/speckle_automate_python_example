import typer
from pydantic import BaseModel, ConfigDict
from stringcase import camelcase
from specklepy.transports.memory import MemoryTransport
from specklepy.transports.server import ServerTransport
from specklepy.api.operations import receive
from specklepy.api.client import SpeckleClient
import random

from flatten import flatten_base
from make_comment import make_comment


class SpeckleProjectData(BaseModel):
    """Values of the project / model that triggered the run of this function."""

    project_id: str
    model_id: str
    version_id: str
    speckle_server_url: str

    model_config = ConfigDict(alias_generator=camelcase, protected_namespaces=())


class FunctionInputs(BaseModel):
    """
    These are function author defined values, automate will make sure to supply them.
    """

    comment_text: str

    class Config:
        alias_generator = camelcase


def main(speckle_project_data: str, function_inputs: str, speckle_token: str):
    project_data = SpeckleProjectData.model_validate_json(speckle_project_data)
    inputs = FunctionInputs.model_validate_json(function_inputs)

    client = SpeckleClient(project_data.speckle_server_url, use_ssl=False)
    client.authenticate_with_token(speckle_token)
    commit = client.commit.get(project_data.project_id, project_data.version_id)
    branch = client.branch.get(project_data.project_id, project_data.model_id, 1)

    memory_transport = MemoryTransport()
    server_transport = ServerTransport(project_data.project_id, client)



    try:
        base = receive(commit.referencedObject, server_transport, memory_transport)

        random_space = random.choice(
            [b for b in flatten_base(base) if b.speckle_type == "Objects.BuiltElements.Space"]
        )

        make_comment(
            client,
            project_data.project_id,
            branch.id,
            project_data.version_id,
            inputs.comment_text,
            random_space.id,
        )

        print(
            "Ran function with",
            f"{speckle_project_data} {function_inputs}",
        )
    except ValueError as e:
        error_message = str(e)
        print(error_message)    


if __name__ == "__main__":
    typer.run(main)
