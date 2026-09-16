from typing import Dict, List, Optional, Tuple

Song = Dict[str, object]
PlaylistMap = Dict[str, List[Song]]

DEFAULT_PROFILE = {
    "name": "Default",
    "hype_min_energy": 7,
    "chill_max_energy": 3,
    "favorite_genre": "rock",
    "include_mixed": True,
}


def normalize_title(title: str) -> str:
    """Normalize a song title for comparisons."""
    if not isinstance(title, str):
        return ""
    return title.strip()


def normalize_artist(artist: str) -> str:
    """Normalize an artist name for comparisons."""
    if not artist:
        return ""
    return artist.strip().lower()


def normalize_genre(genre: str) -> str:
    """Normalize a genre name for comparisons."""
    return genre.lower().strip()


def normalize_song(raw: Song) -> Song:
    """Return a normalized song dict with expected keys."""
    title = normalize_title(str(raw.get("title", "")))
    artist = normalize_artist(str(raw.get("artist", "")))
    genre = normalize_genre(str(raw.get("genre", "")))
    energy = raw.get("energy", 0)

    if isinstance(energy, str):
        try:
            energy = int(energy)
        except ValueError:
            energy = 0

    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    return {
        "title": title,
        "artist": artist,
        "genre": genre,
        "energy": energy,
        "tags": tags,
    }


def classify_song(song: Song, profile: Dict[str, object]) -> str:
    """Return a mood label given a song and user profile."""
    energy = int(song.get("energy", 0))
    genre = str(song.get("genre", "")).lower().strip()
    title = str(song.get("title", "")).lower().strip()
    tags = [str(t).lower().strip() for t in song.get("tags", [])]

    hype_min_energy = int(profile.get("hype_min_energy", 7))
    chill_max_energy = int(profile.get("chill_max_energy", 3))
    favorite_genre = str(profile.get("favorite_genre", "")).lower().strip()

    hype_keywords = ["rock", "punk", "party"]
    chill_keywords = ["lofi", "ambient", "sleep"]

    # Search keywords case-insensitively across genre, tags, and title
    combined_info = f"{genre} {' '.join(tags)} {title}"
    is_hype_keyword = any(k in combined_info for k in hype_keywords)
    is_chill_keyword = any(k in combined_info for k in chill_keywords)

    # Fix (Issue #1 - Song Mislabeling in Classification):
    # Prevent quiet/low-energy songs from being mislabeled as "Hype".
    # 1. High energy (>= hype_min_energy) -> Hype.
    # 2. Low energy (<= chill_max_energy) or chill keywords -> Chill.
    # 3. Mid-energy songs matching favorite_genre or hype keywords lean Hype, otherwise Mixed.
    if energy >= hype_min_energy:
        return "Hype"
    if energy <= chill_max_energy or (is_chill_keyword and not is_hype_keyword):
        return "Chill"
    if genre == favorite_genre or is_hype_keyword:
        return "Hype"
    return "Mixed"


def build_playlists(songs: List[Song], profile: Dict[str, object]) -> PlaylistMap:
    """Group songs into playlists based on mood and profile."""
    playlists: PlaylistMap = {
        "Hype": [],
        "Chill": [],
        "Mixed": [],
    }

    for song in songs:
        normalized = normalize_song(song)
        mood = classify_song(normalized, profile)
        normalized["mood"] = mood
        playlists[mood].append(normalized)

    return playlists


def merge_playlists(a: PlaylistMap, b: PlaylistMap) -> PlaylistMap:
    """Merge two playlist maps into a new map."""
    merged: PlaylistMap = {}
    for key in set(list(a.keys()) + list(b.keys())):
        # Fix (Issue #2 - In-place Input Mutation During Merge):
        # Create a shallow copy list(a.get(...)) to avoid mutating input playlist 'a' in-place.
        merged[key] = list(a.get(key, []))
        merged[key].extend(b.get(key, []))
    return merged


def compute_playlist_stats(playlists: PlaylistMap) -> Dict[str, object]:
    """Compute statistics across all playlists."""
    all_songs: List[Song] = []
    for songs in playlists.values():
        all_songs.extend(songs)

    hype = playlists.get("Hype", [])
    chill = playlists.get("Chill", [])
    mixed = playlists.get("Mixed", [])

    # Fix (Issue #3 - Erroneous Statistics Calculations):
    # Calculate hype_ratio against len(all_songs) rather than len(hype),
    # which previously caused hype_ratio to always evaluate to 1.0 (100%).
    total = len(all_songs)
    hype_ratio = len(hype) / total if total > 0 else 0.0

    # Fix (Issue #3 - Erroneous Statistics Calculations):
    # Sum energy across all_songs rather than just hype, preventing deflated average energy.
    avg_energy = 0.0
    if all_songs:
        total_energy = sum(int(song.get("energy", 0)) for song in all_songs)
        avg_energy = total_energy / len(all_songs)

    top_artist, top_count = most_common_artist(all_songs)

    return {
        "total_songs": len(all_songs),
        "hype_count": len(hype),
        "chill_count": len(chill),
        "mixed_count": len(mixed),
        "hype_ratio": hype_ratio,
        "avg_energy": avg_energy,
        "top_artist": top_artist,
        "top_artist_count": top_count,
    }


def most_common_artist(songs: List[Song]) -> Tuple[str, int]:
    """Return the most common artist and count."""
    counts: Dict[str, int] = {}
    for song in songs:
        artist = str(song.get("artist", ""))
        if not artist:
            continue
        counts[artist] = counts.get(artist, 0) + 1

    if not counts:
        return "", 0

    items = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return items[0]


def search_songs(
    songs: List[Song],
    query: str,
    field: str = "artist",
) -> List[Song]:
    """Return songs matching the query on a given field."""
    if not query:
        return songs

    q = query.lower().strip()
    if not q:
        return songs

    filtered: List[Song] = []

    for song in songs:
        val = song.get(field, "")
        # Fix (Issue #4 - Inverted Substring Match & List Field Support in Search):
        # Check if query substring is contained in the song's field value (q in str(item).lower()),
        # rather than inverted (value in q). Also handles both scalar values and lists (e.g. tags).
        raw_values = val if isinstance(val, list) else [val]
        if any(q in str(item).lower() for item in raw_values if item is not None):
            filtered.append(song)

    return filtered


def lucky_pick(
    playlists: PlaylistMap,
    mode: str = "any",
) -> Optional[Song]:
    """Pick a song from the playlists according to mode."""
    if mode == "hype":
        songs = playlists.get("Hype", [])
    elif mode == "chill":
        songs = playlists.get("Chill", [])
    else:
        # Fix (Issue #5 - Lucky Pick "Any" Mode Excluded Mixed Songs):
        # Include all playlists (Hype, Chill, Mixed) when mode is "any".
        songs = playlists.get("Hype", []) + playlists.get("Chill", []) + playlists.get("Mixed", [])

    return random_choice_or_none(songs)


def random_choice_or_none(songs: List[Song]) -> Optional[Song]:
    """Return a random song or None."""
    import random

    # Fix (Issue #6 - Empty Playlist Crash in Lucky Pick):
    # Return None on empty list instead of raising IndexError.
    if not songs:
        return None
    return random.choice(songs)


def history_summary(history: List[Song]) -> Dict[str, int]:
    """Return a summary of moods seen in the history."""
    counts = {"Hype": 0, "Chill": 0, "Mixed": 0}
    for song in history:
        mood = song.get("mood", "Mixed")
        if mood not in counts:
            counts["Mixed"] += 1
        else:
            counts[mood] += 1
    return counts
