import json
import re
import unicodedata
import urllib.request
from urllib.parse import urlsplit


TV_URL = "https://iptv-org.github.io/iptv/countries/il.m3u"

RADIO_URLS = [
    (
        "https://de1.api.radio-browser.info/json/stations/"
        "bycountrycodeexact/IL"
        "?hidebroken=true&order=votes&reverse=true&limit=1000"
    ),
    (
        "https://nl1.api.radio-browser.info/json/stations/"
        "bycountrycodeexact/IL"
        "?hidebroken=true&order=votes&reverse=true&limit=1000"
    ),
]

OUTPUT = "israel.m3u"
USER_AGENT = "Israel-TV-Radio-Playlist/2.1"


# Well-known/main Israeli stations.
# Aliases are also used to collapse obvious duplicate listings.
MAIN_STATIONS = {
    "galgalatz": {
        "label": "Galgalatz",
        "aliases": [
            "Galgalatz",
            "Galgalatz 91.8 FM",
            "Glglz",
            "גלגלצ",
            "גלגלצ - Glglz",
        ],
    },

    "galei_zahal": {
        "label": "Galei Zahal",
        "aliases": [
            "Galei Zahal",
            "Glz",
            'גלי צה"ל',
            "גלצ",
        ],
    },

    "kan_88": {
        "label": "KAN 88",
        "aliases": [
            "KAN 88",
            "88 FM",
            "כאן 88",
        ],
    },

    "kan_bet": {
        "label": "KAN Bet",
        "aliases": [
            "Kan Bet",
            "Kan Bet 64K",
            "KAN BET",
            "כאן ב",
            "כאן ב׳",
        ],
    },

    "kan_gimel": {
        "label": "KAN Gimel",
        "aliases": [
            "KAN Gimel",
            "KAN Gimel כאן גימל",
            "כאן גימל",
        ],
    },

    "kan_kol_hamusica": {
        "label": "KAN Kol HaMusica",
        "aliases": [
            "KAN Kol HaMusica",
            "KAN Kol HaMusica כאן קול המוזיקה",
            "כאן קול המוזיקה",
        ],
    },

    "kan_tarbut": {
        "label": "KAN Tarbut",
        "aliases": [
            "KAN TARBUT",
            "Kan Tarbut",
            "כאן תרבות",
        ],
    },

    "kan_reka": {
        "label": "KAN Reka",
        "aliases": [
            "Kan Reka",
            "כאן רקע",
            "כאן רקע Kan Reka",
        ],
    },

    "103fm": {
        "label": "103FM",
        "aliases": [
            "Radio 103FM",
            "103FM",
            "רדיו 103FM",
        ],
    },

    "eco99": {
        "label": "Eco 99FM",
        "aliases": [
            "Eco 99fm",
            "ECO99FM",
            "אקו eco 99fm",
            "99FM",
        ],
    },

    "radios100": {
        "label": "Radios 100FM",
        "aliases": [
            "Radios 100FM",
            "Radios 100FM רדיוס",
            "רדיוס 100FM",
        ],
    },

    "102fm": {
        "label": "Radio Tel Aviv 102FM",
        "aliases": [
            "Tel Aviv 102FM",
            "Tel Aviv 102FM רדיו תל אביב",
            "תל אביב Tel Aviv 102FM",
            "רדיו תל אביב 102FM",
            "102FM",
        ],
    },

    "radio_haifa": {
        "label": "Radio Haifa",
        "aliases": [
            "Radio Haifa",
            "Radio Haifa רדיו חיפה",
            "רדיו חיפה",
        ],
    },

    "radio_darom": {
        "label": "Radio Darom",
        "aliases": [
            "Radio Darom",
            "radio darom 95.8fm 97fm",
            "101.5fm נותנים למוזיקה לדבר רדיו דרום",
            "רדיו דרום",
        ],
    },

    "radio_jerusalem": {
        "label": "Radio Jerusalem 101FM",
        "aliases": [
            "101fm radio jerusalem",
            "Radio Jerusalem",
            "רדיו ירושלים",
        ],
    },

    "radio_north": {
        "label": "Radio North 104.5FM",
        "aliases": [
            "104.5FM צפון",
            "104.5fm radio זשכםמ",
            "Radio North 104.5FM",
            "רדיו צפון 104.5FM",
        ],
    },

    "galei_israel": {
        "label": "Galei Israel",
        "aliases": [
            "94fm רדיו גלי ישראל",
            "גלי ישראל Galey Yisrael",
            "Galei Israel",
            "גלי ישראל",
        ],
    },

    "kol_rega": {
        "label": "Kol Rega",
        "aliases": [
            "Kol Rega",
            "Kol Rega קול רגע 91.5/96",
            "קול רגע",
        ],
    },

    "kol_chai": {
        "label": "Kol Chai",
        "aliases": [
            "Kol Chai",
            "קול חי",
            "קול חי - Kol Chai",
        ],
    },

    "kol_barama": {
        "label": "Kol Barama",
        "aliases": [
            "Kol Barama",
            "קול ברמה",
            "קול ברמה - Kol Barama",
        ],
    },

    "lev_hamedina": {
        "label": "Radio Lev HaMedina",
        "aliases": [
            "Radio Lev Hamedina",
            "radio lev hamedina",
            "רדיו לב המדינה",
        ],
    },

    "90fm": {
        "label": "Radio 90FM",
        "aliases": [
            "Radio 90FM",
            "90FM",
        ],
    },
}


# Known-good streams for cases where Radio Browser may associate
# a main station name with one of its themed/subchannel streams.
PREFERRED_STREAMS = {
    "radios100": (
        "https://cdn.cybercdn.live/"
        "Radios_100FM/Audio/icecast.audio"
    ),
}


RELIGIOUS_WORDS = {
    "religious",
    "religion",
    "jewish",
    "judaism",
    "torah",
    "tora",
    "breslev",
    "kabbalah",
    "quran",
    "islam",
    "prayer",
    "תורה",
    "ברסלב",
    "קבלה",
    "יהודי",
}


MUSIC_WORDS = {
    "music",
    "rock",
    "pop",
    "jazz",
    "blues",
    "dance",
    "trance",
    "reggae",
    "country",
    "chill",
    "oldies",
    "retro",
    "hits",
    "classic",
    "classical",
    "latin",
    "latina",
    "k-pop",
    "kpop",
    "mizrahit",
    "מזרח",
    "מוזיקה",
}


def normalize_name(text):
    text = unicodedata.normalize(
        "NFKC",
        text or "",
    ).casefold()

    return re.sub(
        r"[\W_]+",
        "",
        text,
        flags=re.UNICODE,
    )


MAIN_ALIAS_LOOKUP = {}

for station_key, info in MAIN_STATIONS.items():
    for alias in info["aliases"]:
        MAIN_ALIAS_LOOKUP[
            normalize_name(alias)
        ] = station_key


def download_text(url, accept="text/plain"):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        return response.read().decode(
            "utf-8-sig"
        )


def download_radio():
    errors = []

    for url in RADIO_URLS:
        try:
            return json.loads(
                download_text(
                    url,
                    "application/json",
                )
            )

        except Exception as exc:
            errors.append(
                f"{url}: {exc}"
            )

    raise RuntimeError(
        "All Radio Browser mirrors failed:\n"
        + "\n".join(errors)
    )


def make_tv_section(playlist):
    lines = playlist.splitlines()
    output = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("#EXTM3U"):
            continue

        if stripped.startswith("#EXTINF:"):
            # Put every television channel under
            # one clear TV group.
            if re.search(
                r'group-title="[^"]*"',
                line,
            ):
                line = re.sub(
                    r'group-title="[^"]*"',
                    'group-title="Israel TV"',
                    line,
                )

            else:
                comma = line.find(",")

                if comma != -1:
                    line = (
                        line[:comma]
                        + ' group-title="Israel TV"'
                        + line[comma:]
                    )

        output.append(line)

    return output


def canonical_stream_key(url):
    """
    Make a comparison key for duplicate detection.

    Query strings are deliberately ignored because
    Radio Browser sometimes contains the same station
    with different tracking parameters.
    """

    try:
        parts = urlsplit(url)

        host = (
            parts.hostname or ""
        ).casefold()

        port = (
            f":{parts.port}"
            if parts.port
            else ""
        )

        path = (
            parts.path
            .rstrip("/")
            .casefold()
        )

        return f"{host}{port}{path}"

    except Exception:
        return (
            url
            .casefold()
            .strip()
        )


def identify_main_station(name):
    return MAIN_ALIAS_LOOKUP.get(
        normalize_name(name)
    )


def choose_radio_group(
    station,
    main_key,
):
    if main_key:
        return "Israel Radio | Main"

    name = (
        station.get("name") or ""
    ).casefold()

    tags = (
        station.get("tags") or ""
    ).casefold()

    combined = f"{name} {tags}"

    if any(
        word in combined
        for word in RELIGIOUS_WORDS
    ):
        return "Israel Radio | Religious"

    if any(
        word in combined
        for word in MUSIC_WORDS
    ):
        return "Israel Radio | Music"

    return "Israel Radio | Other"


def clean_attribute(value):
    return (
        str(value or "")
        .replace('"', "'")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )


def clean_station_name(value):
    value = clean_attribute(value)

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def build_radio_section(stations):
    # Prefer higher-voted / higher-bitrate entries
    # when duplicate stations exist.
    stations = sorted(
        stations,
        key=lambda station: (
            int(
                station.get("votes")
                or 0
            ),
            int(
                station.get("bitrate")
                or 0
            ),
        ),
        reverse=True,
    )

    seen_names = set()
    seen_streams = set()
    seen_main_stations = set()

    result = []

    for station in stations:
        if int(
            station.get("lastcheckok")
            or 0
        ) != 1:
            continue

        name = clean_station_name(
            station.get("name")
        )

        if not name:
            continue

        # Prefer url_resolved because Radio Browser
        # has already resolved redirects when possible.
        stream_url = (
            station.get("url_resolved")
            or station.get("url")
            or ""
        ).strip()

        if not stream_url:
            continue

        name_key = normalize_name(name)

        main_key = identify_main_station(
            name
        )

        # Override known problematic main stations
        # with a verified preferred stream.
        if main_key in PREFERRED_STREAMS:
            stream_url = (
                PREFERRED_STREAMS[
                    main_key
                ]
            )

        stream_key = canonical_stream_key(
            stream_url
        )

        # Collapse duplicate main station aliases.
        if (
            main_key
            and main_key
            in seen_main_stations
        ):
            continue

        # Collapse duplicate station names.
        if name_key in seen_names:
            continue

        # Collapse duplicate stream URLs.
        if (
            stream_key
            and stream_key
            in seen_streams
        ):
            continue

        seen_names.add(name_key)

        if stream_key:
            seen_streams.add(
                stream_key
            )

        if main_key:
            seen_main_stations.add(
                main_key
            )

            display_name = (
                MAIN_STATIONS[
                    main_key
                ]["label"]
            )

        else:
            display_name = name

        group = choose_radio_group(
            station,
            main_key,
        )

        favicon = clean_attribute(
            station.get("favicon")
        )

        uuid = clean_attribute(
            station.get("stationuuid")
        )

        attrs = [
            'radio="true"',
            f'group-title="{group}"',
        ]

        if uuid:
            attrs.append(
                f'tvg-id="radio-{uuid}"'
            )

        if favicon.startswith(
            ("http://", "https://")
        ):
            attrs.append(
                f'tvg-logo="{favicon}"'
            )

        extinf = (
            "#EXTINF:-1 "
            + " ".join(attrs)
            + ","
            + display_name
        )

        result.append(
            {
                "group": group,
                "name": display_name,
                "extinf": extinf,
                "url": stream_url,
                "main_key": main_key,
            }
        )

    group_order = {
        "Israel Radio | Main": 0,
        "Israel Radio | Music": 1,
        "Israel Radio | Religious": 2,
        "Israel Radio | Other": 3,
    }

    main_order = {
        key: number
        for number, key
        in enumerate(
            MAIN_STATIONS.keys()
        )
    }

    def sort_key(item):
        if (
            item["group"]
            == "Israel Radio | Main"
        ):
            secondary = (
                main_order.get(
                    item["main_key"],
                    9999,
                )
            )

        else:
            secondary = (
                item["name"]
                .casefold()
            )

        return (
            group_order.get(
                item["group"],
                99,
            ),
            secondary,
        )

    result.sort(
        key=sort_key
    )

    lines = []

    for item in result:
        lines.append(
            item["extinf"]
        )

        lines.append(
            item["url"]
        )

    return lines, len(result)


def main():
    print(
        "Downloading Israeli TV playlist..."
    )

    tv_playlist = download_text(
        TV_URL
    )

    print(
        "Downloading Israeli radio database..."
    )

    radio_stations = download_radio()

    tv_lines = make_tv_section(
        tv_playlist
    )

    radio_lines, radio_count = (
        build_radio_section(
            radio_stations
        )
    )

    with open(
        OUTPUT,
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:

        file.write(
            "#EXTM3U\n\n"
        )

        file.write(
            "# Israel TV\n"
        )

        file.write(
            "\n".join(
                tv_lines
            )
        )

        file.write(
            "\n\n# Israel Radio\n"
        )

        file.write(
            "\n".join(
                radio_lines
            )
        )

        file.write("\n")

    print(
        f"Created {OUTPUT}"
    )

    print(
        f"Included {radio_count} "
        "deduplicated Israeli "
        "radio stations."
    )


if __name__ == "__main__":
    main()
