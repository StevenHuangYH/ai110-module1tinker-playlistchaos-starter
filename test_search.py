"""Assert tests for playlist search functionality."""

import unittest
from playlist_logic import search_songs


def sample_songs():
    return [
        {
            "title": "Thunderstruck",
            "artist": "ac/dc",
            "genre": "rock",
            "energy": 9,
            "tags": ["classic", "guitar"],
        },
        {
            "title": "Blinding Lights",
            "artist": "the weeknd",
            "genre": "pop",
            "energy": 8,
            "tags": ["synth", "dance"],
        },
        {
            "title": "Bad Guy",
            "artist": "billie eilish",
            "genre": "pop",
            "energy": 6,
            "tags": ["bass", "dark"],
        },
        {
            "title": "Bohemian Rhapsody",
            "artist": "queen",
            "genre": "rock",
            "energy": 8,
            "tags": ["classic", "opera"],
        },
    ]


class TestSearchSongs(unittest.TestCase):
    def test_partial_match_search(self):
        """Test that partial queries match artist names (the original bug)."""
        songs = sample_songs()

        # Searching for 'weeknd' should match 'the weeknd'
        result = search_songs(songs, "weeknd", field="artist")
        assert len(result) == 1, f"Expected 1 match for 'weeknd', got {len(result)}"
        assert result[0]["artist"] == "the weeknd"

        # Searching for 'billie' should match 'billie eilish'
        result = search_songs(songs, "billie", field="artist")
        assert len(result) == 1, f"Expected 1 match for 'billie', got {len(result)}"
        assert result[0]["artist"] == "billie eilish"

        # Searching for 'eilish' should match 'billie eilish'
        result = search_songs(songs, "eilish", field="artist")
        assert len(result) == 1, f"Expected 1 match for 'eilish', got {len(result)}"
        assert result[0]["artist"] == "billie eilish"

    def test_exact_match_search(self):
        """Test exact match works."""
        songs = sample_songs()
        result = search_songs(songs, "queen", field="artist")
        assert len(result) == 1
        assert result[0]["artist"] == "queen"

    def test_case_insensitive_search(self):
        """Test search is case-insensitive."""
        songs = sample_songs()
        result_upper = search_songs(songs, "AC/DC", field="artist")
        result_lower = search_songs(songs, "ac/dc", field="artist")
        result_mixed = search_songs(songs, "Ac/Dc", field="artist")
        assert len(result_upper) == 1
        assert len(result_lower) == 1
        assert len(result_mixed) == 1
        assert result_upper[0]["title"] == "Thunderstruck"

    def test_empty_or_whitespace_query(self):
        """Test empty or whitespace query returns all songs without filtering."""
        songs = sample_songs()
        assert search_songs(songs, "") == songs
        assert search_songs(songs, "   ") == songs

    def test_no_match_returns_empty(self):
        """Test queries with no matches return an empty list."""
        songs = sample_songs()
        result = search_songs(songs, "Mozart", field="artist")
        assert result == [], f"Expected empty list, got {result}"

    def test_search_by_title(self):
        """Test searching on the title field."""
        songs = sample_songs()
        result = search_songs(songs, "thunder", field="title")
        assert len(result) == 1
        assert result[0]["title"] == "Thunderstruck"

    def test_search_by_genre(self):
        """Test searching on the genre field."""
        songs = sample_songs()
        result = search_songs(songs, "rock", field="genre")
        assert len(result) == 2
        artists = {s["artist"] for s in result}
        assert artists == {"ac/dc", "queen"}

    def test_search_by_tags(self):
        """Test searching on a list field like tags."""
        songs = sample_songs()
        result = search_songs(songs, "classic", field="tags")
        assert len(result) == 2
        artists = {s["artist"] for s in result}
        assert artists == {"ac/dc", "queen"}


if __name__ == "__main__":
    unittest.main()
