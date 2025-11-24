from .models import Model, FixtureSpec, ModelWithFixture


def topological_sort_and_fill(
    models: list[Model],
    fixtures: list[FixtureSpec],
) -> list[ModelWithFixture]:
    models_with_fixtures: list[ModelWithFixture] = []
    fixture_model_names = {fixture.name for fixture in fixtures}

    for fixture in fixtures:
        model = next((m for m in models if m.name == fixture.name), None)

        assert model is not None, f"Model {fixture.name} not found in models list"

        models_with_fixtures.append(ModelWithFixture(model=model, fixture=fixture))

    visited_names = set[str]()
    stack: list[ModelWithFixture] = []

    def dfs(node: ModelWithFixture) -> None:
        visited_names.add(node.model.name)

        for dependency in node.model.requires:
            if (
                dependency not in fixture_model_names
                and dependency not in visited_names
            ):
                # user didn't specify this model, so add in default
                model_to_add = next(
                    (m for m in models if m.name == dependency),
                    None,
                )

                msg = f"Model {dependency} not found in models list"
                assert model_to_add is not None, msg

                node_to_add = ModelWithFixture(
                    model=model_to_add,
                    fixture=FixtureSpec(
                        name=model_to_add.name,
                        args={},
                    ),
                )

                dfs(node_to_add)
            elif dependency not in visited_names:
                # add parent dependency
                user_specified_node_to_add: ModelWithFixture | None = next(
                    (m for m in models_with_fixtures if m.model.name == dependency),
                    None,
                )

                msg = f"Model {dependency} not found in models list"
                assert user_specified_node_to_add is not None, msg

                dfs(user_specified_node_to_add)

        stack.append(node)

    for node in models_with_fixtures:
        if node.model.name not in visited_names:
            dfs(node)

    return stack
