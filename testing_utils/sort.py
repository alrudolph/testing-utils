from .models import Model, ModelRequest, ModelWithRequest


def topological_sort_and_fill(
    models: list[Model],
    requests: list[ModelRequest],
) -> list[ModelWithRequest]:
    models_with_requests: list[ModelWithRequest] = []
    request_model_names = {request.name for request in requests}

    for request in requests:
        model = next((m for m in models if m.name == request.name), None)

        assert model is not None, f"Model {request.name} not found in models list"

        models_with_requests.append(ModelWithRequest(model=model, request=request))

    visited_names = set[str]()
    stack: list[ModelWithRequest] = []

    def dfs(node: ModelWithRequest) -> None:
        visited_names.add(node.model.name)

        for dependency in node.model.requires:
            if (
                dependency not in request_model_names
                and dependency not in visited_names
            ):
                # user didn't specify this model, so add in default
                model_to_add = next(
                    (m for m in models if m.name == dependency),
                    None,
                )

                msg = f"Model {dependency} not found in models list"
                assert model_to_add is not None, msg

                node_to_add = ModelWithRequest(
                    model=model_to_add,
                    request=ModelRequest(
                        name=model_to_add.name,
                        args={},
                    ),
                )

                dfs(node_to_add)
            elif dependency not in visited_names:
                # add parent dependency
                user_specified_node_to_add: ModelWithRequest | None = next(
                    (m for m in models_with_requests if m.model.name == dependency),
                    None,
                )

                msg = f"Model {dependency} not found in models list"
                assert user_specified_node_to_add is not None, msg

                dfs(user_specified_node_to_add)

        stack.append(node)

    for node in models_with_requests:
        if node.model.name not in visited_names:
            dfs(node)

    return stack
