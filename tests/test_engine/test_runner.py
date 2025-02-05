import json

import pandas as pd
import pytest

from retrack import Parser, Runner


@pytest.mark.parametrize(
    "filename, in_values, expected_out_values",
    [
        (
            "multiple-ifs",
            {"number": 1},
            [
                {"message": "first", "output": "1"},
            ],
        ),
        (
            "age-negative",
            {"age": 10},
            [
                {"message": "underage", "output": False},
            ],
        ),
    ],
)
def test_flows_with_single_element(filename, in_values, expected_out_values):
    with open(f"tests/resources/{filename}.json", "r") as f:
        rule = json.load(f)

    runner = Runner(Parser(rule))
    out_values = runner.execute(pd.DataFrame([in_values]))

    assert isinstance(out_values, pd.DataFrame)
    assert out_values.to_dict(orient="records") == expected_out_values


@pytest.mark.parametrize(
    "filename, in_values, expected_out_values",
    [
        (
            "multiple-ifs",
            [{"number": 1}, {"number": 2}, {"number": 3}, {"number": 4}],
            [
                {"message": "first", "output": "1"},
                {"message": "second", "output": "2"},
                {"message": "third", "output": "3"},
                {"message": "other", "output": "0"},
            ],
        ),
        (
            "age-negative",
            [{"age": 10}, {"age": -10}, {"age": 18}, {"age": 19}, {"age": 100}],
            [
                {"message": "underage", "output": False},
                {"message": "invalid age", "output": False},
                {"message": "valid age", "output": True},
                {"message": "valid age", "output": True},
                {"message": "valid age", "output": True},
            ],
        ),
        (
            "age-categorizer",
            [
                {"age": 0},
                {"age": 17},
                {"age": 18},
                {"age": 23},
                {"age": 24},
                {"age": 39},
                {"age": 40},
                {"age": 99},
            ],
            [
                {"message": None, "output": "invalid"},
                {"message": None, "output": "invalid"},
                {"message": None, "output": "group 1"},
                {"message": None, "output": "group 1"},
                {"message": None, "output": "group 2"},
                {"message": None, "output": "group 2"},
                {"message": None, "output": "group 3"},
                {"message": None, "output": "group 3"},
            ],
        ),
        (
            "rule-with-version",
            [{"variable": 0}, {"variable": 100}, {"variable": 200}],
            [
                {"message": None, "output": False},
                {"message": None, "output": True},
                {"message": None, "output": False},
            ],
        ),
        (
            "to-lowercase",
            [{"var": "EXAMPLE"}, {"var": "test with numbers 120"}, {"var": 200}],
            [
                {"message": None, "output": "example"},
                {"message": None, "output": "test with numbers 120"},
                {"message": None, "output": "200"},
            ],
        ),
    ],
)
def test_flows(filename, in_values, expected_out_values):
    with open(f"tests/resources/{filename}.json", "r") as f:
        rule = json.load(f)

    runner = Runner(Parser(rule))
    out_values = runner.execute(pd.DataFrame(in_values))

    assert isinstance(out_values, pd.DataFrame)
    assert out_values.to_dict(orient="records") == expected_out_values


@pytest.mark.parametrize(
    "filename, in_values, expected_out_values",
    [
        (
            "multiple-ifs",
            [{"number": 1}, {"number": 2}, {"number": 3}, {"number": 4}],
            [
                {"message": "first", "output": "1"},
                {"message": "second", "output": "2"},
                {"message": "third", "output": "3"},
                {"message": "other", "output": "0"},
            ],
        ),
        (
            "age-negative",
            [{"age": 10}, {"age": -10}, {"age": 18}, {"age": 19}, {"age": 100}],
            [
                {"message": "underage", "output": False},
                {"message": "invalid age", "output": False},
                {"message": "valid age", "output": True},
                {"message": "valid age", "output": True},
                {"message": "valid age", "output": True},
            ],
        ),
        (
            "round-node",
            [{"var_a": 1.1, "var_b": 1.5}, {"var_a": 3.6, "var_b": 2.1}],
            [
                {"output": 2, "message": None},
                {"output": 8, "message": None},
            ],
        ),
        (
            "rule-of-rules",
            [
                {"example_a": 1, "var_b": 2},
                {"example_a": 3, "var_b": 2},
                {"example_a": 4, "var_b": 2},
                {"example_a": 5, "var_b": 5},
            ],
            [
                {"output": 2, "message": None},
                {"output": 6, "message": None},
                {"output": 8, "message": None},
                {"output": 25, "message": None},
            ],
        ),
    ],
)
def test_create_from_json(filename, in_values, expected_out_values):
    runner = Runner.from_json(f"tests/resources/{filename}.json")
    out_values = runner.execute(pd.DataFrame(in_values))

    assert isinstance(out_values, pd.DataFrame)
    assert out_values.to_dict(orient="records") == expected_out_values


def test_create_from_json_with_invalid_type():
    with pytest.raises(ValueError):
        Runner.from_json(1)


def test_csv_table_with_if():
    runner = Runner.from_json("tests/resources/csv-table-with-if.json")

    in_values = [
        {"in_a": 0, "in_b": 0, "in_d": 0, "in_e": 0},
        {"in_a": 0, "in_b": 1, "in_d": 0, "in_e": 0},
        {"in_a": 1, "in_b": 0, "in_d": 0, "in_e": 0},
        {"in_a": 1, "in_b": 1, "in_d": 0, "in_e": 1},
        {"in_a": 1, "in_b": 1, "in_d": 1, "in_e": 0},
        {"in_a": 1, "in_b": 1, "in_d": 0, "in_e": 0},
        {"in_a": 1, "in_b": 1, "in_d": -1, "in_e": 0},
    ]

    out_values = runner.execute(pd.DataFrame(in_values))

    assert isinstance(out_values, pd.DataFrame)
    assert len(out_values) == len(in_values)
    assert out_values["output"].astype(int).values.tolist() == [-1, -1, -1, 1, 1, 0, 3]
    assert out_values["message"].values.tolist() == [
        "else",
        "else",
        "else",
        "then",
        "then",
        "then",
        "then",
    ]
