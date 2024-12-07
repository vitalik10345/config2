import pytest
import json
from unittest.mock import patch

from config2.main import load_config, get_dependencies, build_dependency_graph, generate_dot_code

@pytest.fixture
def mock_config_file(tmp_path):
    config_data = {
        "graph_tool_path": "/usr/bin/dot",
        "package_name": "curl",
        "output_file": str(tmp_path / "output.dot"),
        "max_depth": 1,
        "repository_url": "http://archive.ubuntu.com/ubuntu"
    }
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(config_data, f)
    return config_path

def test_load_config(mock_config_file):
    config = load_config(str(mock_config_file))
    assert config["package_name"] == "curl"
    assert config["max_depth"] == 1

@patch("subprocess.check_output")
def test_get_dependencies(mock_check_output):
    # Мокаем вывод apt-cache depends
    mock_output = """curl
  Depends: libcurl4 (= 7.68.0-1ubuntu2.12)
  Depends: libc6 (>= 2.17)
  Recommends: ca-certificates
"""
    mock_check_output.return_value = mock_output
    deps = get_dependencies("curl")
    # Ожидается что get_dependencies вернёт ['libcurl4', 'libc6']
    # Recommends не считаем зависимостью
    assert "libcurl4" in deps
    assert "libc6" in deps
    assert "ca-certificates" not in deps

@patch("main.get_dependencies")
def test_build_dependency_graph(mock_get_deps):
    # Предположим пакет 'A' зависит от 'B' и 'C', 'B' не имеет зависимостей, 'C' зависит от 'D'.
    # max_depth = 2
    mock_get_deps.side_effect = lambda p: {"A": ["B", "C"], "C": ["D"], "B": [], "D": []}[p]
    graph = build_dependency_graph("A", 2)
    assert "A" in graph
    assert "B" in graph["A"]
    assert "C" in graph["A"]
    assert "C" in graph
    assert "D" in graph["C"]
    # "D" тоже в графе, так как глубина позволяет
    assert "D" in graph
    # У "B" и "D" зависимостей нет
    assert graph["B"] == set()
    assert graph["D"] == set()

def test_generate_dot_code():
    graph = {
        "A": {"B", "C"},
        "B": set(),
        "C": {"D"},
        "D": set()
    }
    dot = generate_dot_code(graph, "A")
    # Проверим несколько ключевых моментов
    assert 'digraph G' in dot
    assert '"A" -> "B";' in dot
    assert '"A" -> "C";' in dot
    assert '"C" -> "D";' in dot
    assert 'label="A dependencies";' in dot
