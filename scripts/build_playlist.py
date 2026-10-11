import json
import re
import unicodedata
import urllib.request
from urllib.parse import urlsplit

TV_URL = "https://iptv-org.github.io/iptv/countries/il.m3u"

RADIO_URLS = [
    "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/IL?hidebroken=true&order=votes&reverse=true&limit=1000",
    "https://nl1.api.radio-browser.info/json/stations/bycountrycodeexact/IL?hidebroken=true&order=votes&reverse=true&limit=1000",
]

OUTPUT = "israel.m3u"
USER_AGENT = "Israel-TV-Radio-Playlist/3.0"

GROUPS = {
    "main": "Israel Radio | Main",
    "music": "Israel Radio | Music",
    "religious": "Israel Radio | Religious",
    "other": "Israel Radio | Other",
}


# key:
# (
#     display name,
#     group,
#     aliases,
#     preferred stream,
#     fallback stream
# )
#
# Preferred stream:
# Overrides Radio Browser when we know its chosen stream is wrong/outdated.
#
# Fallback stream:
# Adds the station if Radio Browser temporarily omits it.
CURATED = {
    "galgalatz": (
        "Galgalatz",
        "main",
        [
            "Galgalatz",
            "Galgalatz 91.8 FM",
            "Glglz",
            "גלגלצ",
            "גלגלצ - Glglz",
        ],
        None,
        None,
    ),

    "galei_zahal": (
        "Galei Zahal",
        "main",
        [
            "Galei Zahal",
            "Glz",
            'גלי צה"ל',
            "גלצ",
        ],
        None,
        None,
    ),

    "kan_88": (
        "KAN 88",
        "main",
        [
            "KAN 88",
            "88 FM",
            "88FM",
            "כאן 88",
        ],
        None,
        None,
    ),

    "kan_bet": (
        "KAN Bet",
        "main",
        [
            "Kan Bet",
            "Kan Bet 64K",
            "KAN BET",
            "Kan Reshet Bet",
            "כאן ב",
            "כאן ב׳",
        ],
        None,
        None,
    ),

    "kan_gimel": (
        "KAN Gimel",
        "main",
        [
            "KAN Gimel",
            "KAN Gimel כאן גימל",
            "KAN gimel (real)",
            "כאן גימל",
        ],
        None,
        None,
    ),

    "kan_kol_hamusica": (
        "KAN Kol HaMusica",
        "main",
        [
            "KAN Kol HaMusica",
            "KAN Kol HaMusica כאן קול המוזיקה",
            "כאן קול המוזיקה",
        ],
        None,
        None,
    ),

    "kan_tarbut": (
        "KAN Tarbut",
        "main",
        [
            "KAN TARBUT",
            "Kan Tarbut",
            "Kan Israel Tarbut",
            "כאן תרבות",
        ],
        None,
        None,
    ),

    "kan_reka": (
        "KAN Reka",
        "main",
        [
            "Kan Reka",
            "reka",
            "כאן רקע",
            "כאן רקע Kan Reka",
        ],
        None,
        None,
    ),

    "kan_moreshet": (
        "KAN Moreshet",
        "main",
        [
            "Kan Moreshet",
            "Kan Israel Reshet Moreshet 92.5 FM",
            "כאן מורשת",
            "כאן מורשת - Kan Moreshet",
        ],
        None,
        "https://kanlivep2event-i.akamaihd.net/hls/live/749629/749629/playlist.m3u8",
    ),

    "makan": (
        "Makan Radio",
        "main",
        [
            "Makan Radio",
            "Kan Makan",
            "Kan Israel Makan",
            "راديو مكان",
            "راديو مكان - Kan Israel Makan",
        ],
        None,
        "https://kanlivep2event-i.akamaihd.net/hls/live/749628/749628/playlist.m3u8",
    ),

    "103fm": (
        "103FM",
        "main",
        [
            "Radio 103FM",
            "103FM",
            "רדיו 103FM",
        ],
        None,
        None,
    ),

    "eco99": (
        "Eco 99FM",
        "main",
        [
            "Eco 99fm",
            "ECO99FM",
            "אקו eco 99fm",
            "99FM",
        ],
        None,
        None,
    ),

    "radios100": (
        "Radios 100FM",
        "main",
        [
            "Radios 100FM",
            "Radios 100FM רדיוס",
            "רדיוס 100FM",
        ],
        "https://cdn.cybercdn.live/Radios_100FM/Audio/icecast.audio",
        "https://cdn.cybercdn.live/Radios_100FM/Audio/icecast.audio",
    ),

    "102fm": (
        "Radio Tel Aviv 102FM",
        "main",
        [
            "Tel Aviv 102FM",
            "Tel Aviv 102FM רדיו תל אביב",
            "תל אביב Tel Aviv 102FM",
            "רדיו תל אביב 102FM",
            "רדיו תל אביב 102 FM",
            "102FM",
        ],
        None,
        None,
    ),

    "haifa": (
        "Radio Haifa 107.5FM",
        "main",
        [
            "Radio Haifa",
            "Radio Haifa רדיו חיפה",
            "רדיו חיפה",
            "רדיו חיפה 107.5FM",
        ],
        None,
        None,
    ),

    "darom": (
        "Radio Darom",
        "main",
        [
            "Radio Darom",
            "radio darom 95.8fm 97fm",
            "101.5fm נותנים למוזיקה לדבר רדיו דרום",
            "רדיו דרום",
        ],
        None,
        None,
    ),

    "hatahana": (
        "Radio Hatahana 101.5FM",
        "main",
        [
            "101.5fm רדיו התחנה",
            "Radio Hatahana",
            "רדיו התחנה",
        ],
        None,
        None,
    ),

    "jerusalem": (
        "Radio Jerusalem 101FM",
        "main",
        [
            "101fm radio jerusalem",
            "Radio Jerusalem",
            "רדיו ירושלים",
        ],
        None,
        None,
    ),

    "north": (
        "Radio North 104.5FM",
        "main",
        [
            "104.5FM צפון",
            "104.5fm radio זשכםמ",
            "Radio North 104.5FM",
            "רדיו צפון 104.5FM",
        ],
        None,
        None,
    ),

    "galei_israel": (
        "Galei Israel",
        "main",
        [
            "94fm רדיו גלי ישראל",
            "גלי ישראל Galey Yisrael",
            "Galei Israel",
            "גלי ישראל",
        ],
        None,
        None,
    ),

    "kol_rega": (
        "Kol Rega",
        "main",
        [
            "Kol Rega",
            "Kol Rega קול רגע 91.5/96",
            "קול רגע",
        ],
        None,
        None,
    ),

    "kol_chai": (
        "Kol Chai",
        "main",
        [
            "Kol Chai",
            "קול חי",
            "קול חי - Kol Chai",
        ],
        None,
        None,
    ),

    "kol_barama": (
        "Kol Barama",
        "main",
        [
            "Kol Barama",
            "קול ברמה",
            "קול ברמה - Kol Barama",
        ],
        None,
        None,
    ),

    "lev_hamedina": (
        "Radio Lev HaMedina",
        "main",
        [
            "Radio Lev Hamedina",
            "radio lev hamedina",
            "רדיו לב המדינה",
        ],
        None,
        None,
    ),

    "radio90": (
        "Radio 90FM",
        "main",
        [
            "Radio 90FM",
            "90FM",
        ],
        None,
        None,
    ),

    "pervoe": (
        "Pervoe Radio 89.1FM",
        "main",
        [
            "Первое радио 89.1FM",
            "Pervoe Radio 89.1FM",
        ],
        None,
        None,
    ),

    "ashams": (
        "Radio A-Shams 98.1FM",
        "main",
        [
            "اذاعة الشمس - A-Shams",
            "A-Shams",
            "Radio A-Shams",
        ],
        None,
        None,
    ),

    "nas": (
        "Radio Nas 103.3FM",
        "main",
        [
            "Radio Nas",
            "Nas Radio",
            "راديو الناس",
        ],
        None,
        None,
    ),

    "kol_hashfela": (
        "Kol Hashfela 103.6FM",
        "main",
        [
            "קול השפלה - Kol Hashfela",
            "Kol Hashfela",
        ],
        None,
        None,
    ),

    "nostalgia963": (
        "Radios Nostalgia 96.3FM",
        "main",
        [
            "Radios Nostalgia 96.3FM (רדיוס נוסטלגי)",
            "Radios Nostalgia 96.3FM",
            "רדיוס נוסטלגיה 96.3FM",
        ],
        None,
        None,
    ),

    "kol_chai_music": (
        "Kol Chai Music",
        "music",
        [
            "קול חי מיוזיק - Kol Chai Music",
            "Kol Chai Music",
            "kol hai",
            "Kcm FM Channel 01 Live",
        ],
        "https://live.kcm.fm/livemusic",
        "https://live.kcm.fm/livemusic",
    ),

    "kol_play": (
        "Kol Play",
        "music",
        [
            "קול פליי | kol-play",
            "Kol Play",
        ],
        "https://cdn.cybercdn.live/Kol_Barama/Music/icecast.audio",
        "https://cdn.cybercdn.live/Kol_Barama/Music/icecast.audio",
    ),

    "eli_nisman": (
        "Eli Nisman Radio",
        "music",
        [
            "ELI NISMAN",
            "Eli Nisman Radio",
        ],
        "https://listen6.myradio24.com/25715",
        None,
    ),

    "radio_cs": (
        "Radio CS",
        "music",
        [
            "#Radio CS",
            "Radio CS",
        ],
        None,
        None,
    ),

    "john_williams": (
        "John Williams Guitar",
        "music",
        [
            "GUITAR - J. WILLIAMS",
        ],
        None,
        None,
    ),

    "israeli_voice": (
        "Israeli Voice Radio",
        "music",
        [
            "Israeli voice radio",
            "Hedva Shaltiel",
        ],
        None,
        None,
    ),

    "ivri6": (
        "Ivri 6",
        "music",
        [
            "Ivri 6",
        ],
        None,
        None,
    ),

    "radioplus": (
        "Radio Plus",
        "music",
        [
            "RadioPlus",
            "Radio Plus",
        ],
        None,
        None,
    ),

    "radio_love": (
        "Radio Love Soft Romantic",
        "music",
        [
            "Radio Love Soft Romantic",
        ],
        None,
        None,
    ),

    "radio_yasoo": (
        "Radio Yasoo",
        "music",
        [
            "Radio Yasoo",
        ],
        None,
        None,
    ),

    "glglz_relaxed": (
        "Galgalatz - Relaxed (Weekend)",
        "music",
        [
            "Glglz - רגוע (סופשבוע)",
        ],
        None,
        None,
    ),

    "glglz_decades": (
        "Galgalatz - Decades",
        "music",
        [
            "גלגלצ עשורים",
        ],
        None,
        None,
    ),

    "hakatze": (
        "Hakatze (KZRadio)",
        "music",
        [
            "הקצה - Hakatze",
            "kzradio",
        ],
        None,
        None,
    ),

    "rak_musica": (
        "Rak Musica",
        "music",
        [
            "Rak Musica",
        ],
        None,
        None,
    ),

    "timbr": (
        "TIMBR Radio",
        "music",
        [
            "TIMBR Radio",
        ],
        None,
        None,
    ),

    "movies100": (
        "Radios 100FM - 100% Movies",
        "music",
        [
            "100fm - 100% Movies",
            "Radios 100FM - 100% Movies",
        ],
        None,
        None,
    ),

    "latin100": (
        "Radios 100FM - 100% Latin",
        "music",
        [
            "Radio 100% Latina",
            "Radios 100FM - 100% Latin",
        ],
        None,
        None,
    ),

    "noshmim": (
        "Noshmim Mizrahit",
        "music",
        [
            "Mizrahit FM Best",
            "Mizrahit_Fm",
            "נושמים מזרחית - Noshmim Mizrahit",
        ],
        "https://rs.mizrahit.fm:7777/arabellavie",
        "https://rs.mizrahit.fm:7777/arabellavie",
    ),

    "toker": (
        "Toker FM",
        "religious",
        [
            "toker",
            "toker fm",
            "Toker FM",
        ],
        "https://broadcast.adpronet.com/radio/6060/radio.mp3",
        "https://broadcast.adpronet.com/radio/6060/radio.mp3",
    ),

    "prayer_radio": (
        "إذاعة الصلاة | Prayer Radio",
        "religious",
        [
            "????? ?????? | Prayer Radio",
            "إذاعة الصلاة | Prayer Radio",
            "Prayer Radio",
        ],
        None,
        None,
    ),

    "assalam": (
        "Assalam Quran Radio",
        "religious",
        [
            ".assalam",
            "assalam",
        ],
        None,
        None,
    ),

    "abdulbasit": (
        "Abdulbasit Abdulsamad",
        "religious",
        [
            "Abdulbasit Abdulsamad",
        ],
        None,
        None,
    ),

    "orenu": (
        "Radio Orenu",
        "religious",
        [
            "Мессианское радио Орэну",
            "Мессианское онлайн радио Орэну",
            "Radio Orenu",
        ],
        None,
        None,
    ),

    "breslev": (
        "Breslev For You",
        "religious",
        [
            "Nachman",
            "ברסלב פוריו: דעת רבנו",
        ],
        None,
        None,
    ),

    "radio_sahar": (
        "Radio Sahar",
        "other",
        [
            "Radio Sahar",
        ],
        None,
        None,
    ),
}


# This Radio Browser entry currently resolves to the Spanish Kabbalah
# stream even though it is labelled "Fr". A separate correct French
# station is already present, so discard the broken/mislabeled duplicate.
SKIP_NAMES = {
    "Kabbalah Fr",
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
    "gospel",
    "christian",
    "messianic",
    "orthodox",
    "תורה",
    "ברסלב",
    "קבלה",
    "יהודי",
    "דתי",
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
    "electronic",
    "edm",
    "house",
    "relax",
    "nostalgia",
    "romantic",
    "top40",
    "top 40",
    "80s",
    "80's",
    "90s",
    "90's",
    "70s",
    "70's",
    "60s",
    "60's",
    "movie music",
    "world music",
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


ALIASES = {}

for key, (
    label,
    _,
    aliases,
    _,
    _,
) in CURATED.items():

    # Include both the chosen display label and every known alias.
    for alias in [label, *aliases]:
        ALIASES[
            normalize_name(alias)
        ] = key


SKIP_KEYS = {
    normalize_name(name)
    for name in SKIP_NAMES
}


def download_text(
    url,
    accept="text/plain",
):
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


def make_tv_section(
    playlist,
):
    output = []

    for line in playlist.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith(
            "#EXTM3U"
        ):
            continue

        if stripped.startswith(
            "#EXTINF:"
        ):
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


def canonical_stream_key(
    url,
):
    """
    Make a comparison key for duplicate streams.

    Query parameters are deliberately ignored because the
    same stream often appears with different tracking tokens.
    """

    try:
        parts = urlsplit(url)

        host = (
            parts.hostname
            or ""
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

        return (
            f"{host}{port}{path}"
        )

    except Exception:
        return (
            url.casefold().strip()
        )


def clean(
    value,
):
    return (
        str(value or "")
        .replace('"', "'")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )


def clean_name(
    value,
):
    return re.sub(
        r"\s+",
        " ",
        clean(value),
    ).strip()


def auto_group(
    station,
    name,
):
    lowered_name = (
        name.casefold()
    )

    tags = (
        station.get("tags")
        or ""
    ).casefold()

    combined = (
        f"{lowered_name} {tags}"
    )

    # All Radios 100FM specialty channels are music
    # except the explicitly religious and spoken-comedy feeds.
    if (
        "radios 100fm - 100%"
        in lowered_name
        or "radio 100%"
        in lowered_name
    ):
        if (
            "yehudi"
            in lowered_name
            or "יהודי"
            in lowered_name
        ):
            return GROUPS[
                "religious"
            ]

        if (
            "standup"
            in lowered_name
        ):
            return GROUPS[
                "other"
            ]

        return GROUPS[
            "music"
        ]

    if any(
        word in combined
        for word
        in RELIGIOUS_WORDS
    ):
        return GROUPS[
            "religious"
        ]

    if any(
        word in combined
        for word
        in MUSIC_WORDS
    ):
        return GROUPS[
            "music"
        ]

    return GROUPS[
        "other"
    ]


def make_item(
    group,
    name,
    url,
    uuid="",
    logo="",
    curated_key=None,
):
    attrs = [
        'radio="true"',
        f'group-title="{group}"',
    ]

    if uuid:
        attrs.append(
            f'tvg-id="radio-{clean(uuid)}"'
        )

    logo = clean(logo)

    if logo.startswith(
        (
            "http://",
            "https://",
        )
    ):
        attrs.append(
            f'tvg-logo="{logo}"'
        )

    return {
        "group": group,
        "name": name,
        "url": url,
        "curated_key": curated_key,
        "extinf": (
            "#EXTINF:-1 "
            + " ".join(attrs)
            + ","
            + name
        ),
    }


def build_radio_section(
    stations,
):
    # Prefer well-voted / higher-bitrate entries when
    # Radio Browser contains several versions of a station.
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
    seen_curated = set()

    result = []

    for station in stations:

        if int(
            station.get(
                "lastcheckok"
            )
            or 0
        ) != 1:
            continue

        original_name = (
            clean_name(
                station.get(
                    "name"
                )
            )
        )

        if not original_name:
            continue

        if (
            normalize_name(
                original_name
            )
            in SKIP_KEYS
        ):
            continue

        url = (
            station.get(
                "url_resolved"
            )
            or station.get(
                "url"
            )
            or ""
        ).strip()

        if not url:
            continue

        curated_key = (
            ALIASES.get(
                normalize_name(
                    original_name
                )
            )
        )

        if curated_key:
            (
                label,
                group_key,
                _,
                preferred_stream,
                _,
            ) = CURATED[
                curated_key
            ]

            name = label
            group = GROUPS[
                group_key
            ]

            if preferred_stream:
                url = (
                    preferred_stream
                )

        else:
            name = original_name

            group = auto_group(
                station,
                name,
            )

        name_key = (
            normalize_name(
                name
            )
        )

        stream_key = (
            canonical_stream_key(
                url
            )
        )

        # Curated aliases such as:
        # ELI NISMAN / Eli Nisman Radio
        # are treated as one station.
        if (
            curated_key
            and curated_key
            in seen_curated
        ):
            continue

        if (
            name_key
            in seen_names
        ):
            continue

        if (
            stream_key
            and stream_key
            in seen_streams
        ):
            continue

        if curated_key:
            seen_curated.add(
                curated_key
            )

        seen_names.add(
            name_key
        )

        if stream_key:
            seen_streams.add(
                stream_key
            )

        result.append(
            make_item(
                group,
                name,
                url,
                station.get(
                    "stationuuid"
                )
                or "",
                station.get(
                    "favicon"
                )
                or "",
                curated_key,
            )
        )


    # Add important stations that Radio Browser may
    # occasionally omit from its currently healthy set.
    for key, (
        label,
        group_key,
        _,
        _,
        fallback_stream,
    ) in CURATED.items():

        if not fallback_stream:
            continue

        if key in seen_curated:
            continue

        stream_key = (
            canonical_stream_key(
                fallback_stream
            )
        )

        if (
            stream_key
            in seen_streams
        ):
            continue

        result.append(
            make_item(
                GROUPS[
                    group_key
                ],
                label,
                fallback_stream,
                f"fallback-{key}",
                "",
                key,
            )
        )

        seen_curated.add(
            key
        )

        seen_names.add(
            normalize_name(
                label
            )
        )

        seen_streams.add(
            stream_key
        )


    group_order = {
        GROUPS["main"]: 0,
        GROUPS["music"]: 1,
        GROUPS["religious"]: 2,
        GROUPS["other"]: 3,
    }

    curated_order = {
        key: index
        for index, key
        in enumerate(
            CURATED
        )
    }


    def sort_key(
        item,
    ):
        if (
            item["group"]
            == GROUPS["main"]
        ):
            return (
                0,
                curated_order.get(
                    item[
                        "curated_key"
                    ],
                    9999,
                ),
                item[
                    "name"
                ].casefold(),
            )

        return (
            group_order.get(
                item["group"],
                99,
            ),
            item[
                "name"
            ].casefold(),
            "",
        )


    result.sort(
        key=sort_key
    )

    lines = []

    for item in result:
        lines.extend(
            [
                item[
                    "extinf"
                ],
                item[
                    "url"
                ],
            ]
        )

    return (
        lines,
        len(result),
    )


def main():

    print(
        "Downloading Israeli TV playlist..."
    )

    tv = download_text(
        TV_URL
    )


    print(
        "Downloading Israeli radio database..."
    )

    radio = download_radio()


    tv_lines = (
        make_tv_section(
            tv
        )
    )

    (
        radio_lines,
        radio_count,
    ) = build_radio_section(
        radio
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

        file.write(
            "\n"
        )


    print(
        f"Created {OUTPUT}"
    )

    print(
        f"Included "
        f"{radio_count} "
        f"deduplicated Israeli "
        f"radio stations."
    )


if __name__ == "__main__":
    main()
