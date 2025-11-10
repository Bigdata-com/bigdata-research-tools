import pytest

from src.bigdata_research_tools.utils.distance import levenshtein_distance


@pytest.mark.parametrize(
    "a,b,expected",
    [
        # Basic
        ("kitten", "sitting", 3),
        ("flaw", "lawn", 2),
        ("gumbo", "gambol", 2),
        ("book", "back", 2),
        # Empty strings
        ("", "", 0),
        ("abc", "", 3),
        ("", "abc", 3),
        # Identical strings
        ("test", "test", 0),
        ("a", "a", 0),
        # Case sensitivity
        ("Test", "test", 1),
        # Unicode characters
        ("café", "cafe", 1),
        ("mañana", "manana", 1),
    ],
)
def test_levenshtein_distance(a, b, expected):
    assert levenshtein_distance(a, b) == expected
