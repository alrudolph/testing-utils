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
    cannot_create_default_names = set[str]()
    stack: list[ModelWithRequest] = []

    def dfs(node: ModelWithRequest) -> None:
        visited_names.add(node.model.name)

        for dependency in node.model.requires:
            not_visited = dependency not in visited_names

            if not not_visited:
                continue

            not_yet_requested = dependency not in request_model_names

            if not_yet_requested:
                # user didn't specify this model, so add in default
                model_to_add = next(
                    (m for m in models if m.name == dependency),
                    None,
                )

                msg = f"Model {dependency} not found in models list"
                assert model_to_add is not None, msg

                if model_to_add.name in cannot_create_default_names:
                    raise ValueError(
                        f"Model {model_to_add.name} cannot be created because it is a parent of an existing request"
                    )

                node_to_add = ModelWithRequest(
                    model=model_to_add,
                    request=ModelRequest.create(
                        name=model_to_add.name,
                        args={},
                    ),
                )

                dfs(node_to_add)
            else:
                # add parent dependency
                user_specified_node_to_add: ModelWithRequest | None = next(
                    (m for m in models_with_requests if m.model.name == dependency),
                    None,
                )

                msg = f"Model {dependency} not found in models list"
                assert user_specified_node_to_add is not None, msg

                dfs(user_specified_node_to_add)

        stack.append(node)

    # remove existing models parents
    for node in models_with_requests:
        if not node.request.is_existing_request(node.request):
            continue

        # mark visited so we don't try to create any parents
        visited_names.add(node.model.name)

        # add to stack so get is ran
        stack.append(node)

        # make sure other requests dont access parent values
        def mark_cannot_request(model: Model) -> None:
            for dependency in model.requires:
                dependency_model = next(
                    (m for m in models if m.name == dependency),
                    None,
                )

                msg = f"Model {dependency} not found in models list"
                assert dependency_model is not None, msg

                cannot_create_default_names.add(dependency_model.name)

                mark_cannot_request(dependency_model)

        mark_cannot_request(node.model)

    # add in new
    for node in models_with_requests:
        if not node.request.is_create_request(node.request):
            continue

        if node.model.name not in visited_names:
            dfs(node)

    return stack
