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
USER_AGENT = "Israel-TV-Radio-Playlist/4.1"


GROUPS = {
    "main": "Israel Radio | Main",
    "music": "Israel Radio | Music",
    "religious": "Israel Radio | Religious",
    "other": "Israel Radio | Other",
}


def station(
    label,
    group,
    aliases,
    preferred=None,
    fallback=None,
):
    return {
        "label": label,
        "group": group,
        "aliases": aliases,
        "preferred": preferred,
        "fallback": fallback,
    }


CURATED = {

    # ============================================================
    # MAIN RADIO STATIONS
    # ============================================================

    "galgalatz": station(
        "Galgalatz",
        "main",
        [
            "Galgalatz",
            "Galgalatz 91.8 FM",
            "Glglz",
            "גלגלצ",
            "גלגלצ - Glglz",
        ],
    ),

    "galei_zahal": station(
        "Galei Zahal",
        "main",
        [
            "Galei Zahal",
            "Glz",
            'גלי צה"ל',
            "גלצ",
        ],
    ),

    "kan_88": station(
        "KAN 88",
        "main",
        [
            "KAN 88",
            "88 FM",
            "88FM",
            "כאן 88",
            "Kan Israel 88 FM",
        ],
    ),

    "kan_bet": station(
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
    ),

    "kan_gimel": station(
        "KAN Gimel",
        "main",
        [
            "KAN Gimel",
            "KAN Gimel כאן גימל",
            "KAN gimel (real)",
            "כאן גימל",
        ],
    ),

    "kan_kol_hamusica": station(
        "KAN Kol HaMusica",
        "main",
        [
            "KAN Kol HaMusica",
            "KAN Kol HaMusica כאן קול המוזיקה",
            "כאן קול המוזיקה",
        ],
    ),

    "kan_tarbut": station(
        "KAN Tarbut",
        "main",
        [
            "KAN TARBUT",
            "Kan Tarbut",
            "Kan Israel Tarbut",
            "כאן תרבות",
        ],
    ),

    "kan_reka": station(
        "KAN Reka",
        "main",
        [
            "Kan Reka",
            "reka",
            "כאן רקע",
            "כאן רקע Kan Reka",
        ],
    ),

    "kan_moreshet": station(
        "KAN Moreshet",
        "main",
        [
            "Kan Moreshet",
            "Kan Israel Reshet Moreshet 92.5 FM",
            "כאן מורשת",
            "כאן מורשת - Kan Moreshet",
        ],
        fallback=(
            "https://kanlivep2event-i.akamaihd.net/"
            "hls/live/749629/749629/playlist.m3u8"
        ),
    ),

    "makan": station(
        "Makan Radio",
        "main",
        [
            "Makan Radio",
            "Kan Makan",
            "Kan Israel Makan",
            "راديو مكان",
            "راديو مكان - Kan Israel Makan",
        ],
        fallback=(
            "https://kanlivep2event-i.akamaihd.net/"
            "hls/live/749628/749628/playlist.m3u8"
        ),
    ),

    "103fm": station(
        "103FM",
        "main",
        [
            "Radio 103FM",
            "103FM",
            "רדיו 103FM",
        ],
    ),

    "eco99": station(
        "Eco 99FM",
        "main",
        [
            "Eco 99fm",
            "ECO99FM",
            "אקו eco 99fm",
            "99FM",
        ],
    ),

    "radios100": station(
        "Radios 100FM",
        "main",
        [
            "Radios 100FM",
            "Radios 100FM רדיוס",
            "רדיוס 100FM",
        ],
        preferred=(
            "https://cdn.cybercdn.live/"
            "Radios_100FM/Audio/icecast.audio"
        ),
        fallback=(
            "https://cdn.cybercdn.live/"
            "Radios_100FM/Audio/icecast.audio"
        ),
    ),

    "102fm": station(
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
    ),

    "haifa": station(
        "Radio Haifa 107.5FM",
        "main",
        [
            "Radio Haifa",
            "Radio Haifa רדיו חיפה",
            "רדיו חיפה",
            "רדיו חיפה 107.5FM",
        ],
    ),

    "darom": station(
        "Radio Darom",
        "main",
        [
            "Radio Darom",
            "radio darom 95.8fm 97fm",
            "101.5fm נותנים למוזיקה לדבר רדיו דרום",
            "רדיו דרום",
        ],
    ),

    "hatahana": station(
        "Radio Hatahana 101.5FM",
        "main",
        [
            "101.5fm רדיו התחנה",
            "Radio Hatahana",
            "רדיו התחנה",
        ],
    ),

    "jerusalem": station(
        "Radio Jerusalem 101FM",
        "main",
        [
            "101fm radio jerusalem",
            "Radio Jerusalem",
            "רדיו ירושלים",
        ],
    ),

    "north": station(
        "Radio North 104.5FM",
        "main",
        [
            "104.5FM צפון",
            "104.5fm radio זשכםמ",
            "Radio North 104.5FM",
            "רדיו צפון 104.5FM",
        ],
    ),

    "galei_israel": station(
        "Galei Israel",
        "main",
        [
            "94fm רדיו גלי ישראל",
            "גלי ישראל Galey Yisrael",
            "Galei Israel",
            "גלי ישראל",
        ],
    ),

    "kol_rega": station(
        "Kol Rega",
        "main",
        [
            "Kol Rega",
            "Kol Rega קול רגע 91.5/96",
            "קול רגע",
        ],
    ),

    "kol_chai": station(
        "Kol Chai",
        "main",
        [
            "Kol Chai",
            "קול חי",
            "קול חי - Kol Chai",
        ],
    ),

    "kol_barama": station(
        "Kol Barama",
        "main",
        [
            "Kol Barama",
            "קול ברמה",
            "קול ברמה - Kol Barama",
        ],
    ),

    "lev_hamedina": station(
        "Radio Lev HaMedina",
        "main",
        [
            "Radio Lev Hamedina",
            "radio lev hamedina",
            "רדיו לב המדינה",
        ],
    ),

    "radio90": station(
        "Radio 90FM",
        "main",
        [
            "Radio 90FM",
            "90FM",
        ],
    ),

    "pervoe": station(
        "Pervoe Radio 89.1FM",
        "main",
        [
            "Первое радио 89.1FM",
            "Pervoe Radio 89.1FM",
        ],
    ),

    "ashams": station(
        "Radio A-Shams 98.1FM",
        "main",
        [
            "اذاعة الشمس - A-Shams",
            "A-Shams",
            "Radio A-Shams",
        ],
    ),

    "nas": station(
        "Radio Nas 103.3FM",
        "main",
        [
            "Radio Nas",
            "Nas Radio",
            "راديو الناس",
        ],
    ),

    "kol_hashfela": station(
        "Kol Hashfela 103.6FM",
        "main",
        [
            "קול השפלה - Kol Hashfela",
            "Kol Hashfela",
        ],
    ),

    "nostalgia963": station(
        "Radios Nostalgia 96.3FM",
        "main",
        [
            "Radios Nostalgia 96.3FM (רדיוס נוסטלגי)",
            "Radios Nostalgia 96.3FM",
            "רדיוס נוסטלגיה 96.3FM",
        ],
    ),


    # ============================================================
    # MUSIC
    # ============================================================

    "galgalatz_rock": station(
        "Galgalatz - Rock",
        "music",
        [
            "Glglz - Rock",
            "Galgalatz - Rock",
        ],
    ),

    "glglz_relaxed": station(
        "Galgalatz - Relaxed (Weekend)",
        "music",
        [
            "Glglz - רגוע (סופשבוע)",
            "Galgalatz - Relaxed (Weekend)",
        ],
    ),

    "glglz_decades": station(
        "Galgalatz - Decades",
        "music",
        [
            "גלגלצ עשורים",
            "Galgalatz - Decades",
        ],
    ),

    "kol_chai_music": station(
        "Kol Chai Music",
        "music",
        [
            "קול חי מיוזיק - Kol Chai Music",
            "Kol Chai Music",
            "kol hai",
            "Kcm FM Channel 01 Live",
        ],
        preferred=(
            "https://live.kcm.fm/livemusic"
        ),
        fallback=(
            "https://live.kcm.fm/livemusic"
        ),
    ),

    "kol_play": station(
        "Kol Play",
        "music",
        [
            "קול פליי | kol-play",
            "Kol Play",
        ],
        preferred=(
            "https://cdn.cybercdn.live/"
            "Kol_Barama/Music/icecast.audio"
        ),
        fallback=(
            "https://cdn.cybercdn.live/"
            "Kol_Barama/Music/icecast.audio"
        ),
    ),

    "eli_nisman": station(
        "Eli Nisman Radio",
        "music",
        [
            "ELI NISMAN",
            "Eli Nisman Radio",
        ],
        preferred=(
            "https://listen6.myradio24.com/25715"
        ),
    ),

    "radio_cs": station(
        "Radio CS",
        "music",
        [
            "#Radio CS",
            "Radio CS",
        ],
    ),

    "john_williams": station(
        "John Williams Guitar",
        "music",
        [
            "GUITAR - J. WILLIAMS",
            "John Williams Guitar",
        ],
    ),

    "israeli_voice": station(
        "Israeli Voice Radio",
        "music",
        [
            "Israeli voice radio",
            "Israeli Voice Radio",
            "Hedva Shaltiel",
        ],
    ),

    "ivri6": station(
        "Ivri 6",
        "music",
        [
            "Ivri 6",
        ],
    ),

    "radioplus": station(
        "Radio Plus",
        "music",
        [
            "RadioPlus",
            "Radio Plus",
        ],
    ),

    "radio_love": station(
        "Radio Love Soft Romantic",
        "music",
        [
            "Radio Love Soft Romantic",
        ],
    ),

    "radio_yasoo": station(
        "Radio Yasoo",
        "music",
        [
            "Radio Yasoo",
        ],
    ),

    "hakatze": station(
        "Hakatze (KZRadio)",
        "music",
        [
            "הקצה - Hakatze",
            "Hakatze",
            "kzradio",
        ],
    ),

    "rak_musica": station(
        "Rak Musica",
        "music",
        [
            "Rak Musica",
        ],
    ),

    "timbr": station(
        "TIMBR Radio",
        "music",
        [
            "TIMBR Radio",
        ],
    ),

    "ystream": station(
        "yStream",
        "music",
        [
            "yStream",
        ],
    ),

    "zerock": station(
        "Ze Rock Radio",
        "music",
        [
            "Ze Rock Radio",
        ],
    ),

    "noshmim": station(
        "Noshmim Mizrahit",
        "music",
        [
            "Mizrahit FM Best",
            "Mizrahit_Fm",
            "נושמים מזרחית - Noshmim Mizrahit",
            "Noshmim Mizrahit",
        ],
        preferred=(
            "https://rs.mizrahit.fm:7777/arabellavie"
        ),
        fallback=(
            "https://rs.mizrahit.fm:7777/arabellavie"
        ),
    ),

    "nineties100": station(
        "Radios 100FM - 100% 90s",
        "music",
        [
            "Radio 100% 90s",
            "Radios 100FM - 100% 90s",
        ],
    ),

    "movies100": station(
        "Radios 100FM - 100% Movies",
        "music",
        [
            "100fm - 100% Movies",
            "Radios 100FM - 100% Movies",
        ],
    ),

    "latin100": station(
        "Radios 100FM - 100% Latin",
        "music",
        [
            "Radio 100% Latina",
            "Radios 100FM - 100% Latin",
        ],
    ),


    # ============================================================
    # RELIGIOUS
    # ============================================================

    "toker": station(
        "Toker FM",
        "religious",
        [
            "toker",
            "toker fm",
            "Toker FM",
        ],
        preferred=(
            "https://broadcast.adpronet.com/"
            "radio/6060/radio.mp3"
        ),
        fallback=(
            "https://broadcast.adpronet.com/"
            "radio/6060/radio.mp3"
        ),
    ),

    "prayer_radio": station(
        "إذاعة الصلاة | Prayer Radio",
        "religious",
        [
            "????? ?????? | Prayer Radio",
            "إذاعة الصلاة | Prayer Radio",
            "Prayer Radio",
        ],
    ),

    "assalam": station(
        "Assalam Quran Radio",
        "religious",
        [
            ".assalam",
            "assalam",
            "Assalam Quran Radio",
        ],
    ),

    "abdulbasit": station(
        "Abdulbasit Abdulsamad",
        "religious",
        [
            "Abdulbasit Abdulsamad",
        ],
    ),

    "orenu": station(
        "Radio Orenu",
        "religious",
        [
            "Мессианское радио Орэну",
            "Мессианское онлайн радио Орэну",
            "Radio Orenu",
        ],
    ),

    "breslev": station(
        "Breslev For You",
        "religious",
        [
            "Nachman",
            "ברסלב פוריו: דעת רבנו",
            "Breslev For You",
        ],
    ),


    # ============================================================
    # OTHER / MIXED
    # ============================================================

    "radio_sahar": station(
        "Radio Sahar",
        "other",
        [
            "Radio Sahar",
        ],
    ),
}


# A bad/mislabeled duplicate that previously pointed to
# the wrong-language Kabbalah stream.
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


# Cosmetic normalization for feeds that otherwise do not
# need a dedicated CURATED entry.
DISPLAY_NAME_OVERRIDES = {
    "radios100fm100kpop":
        "Radios 100FM - 100% K-Pop",

    "radios100fm100tiktok":
        "Radios 100FM - 100% TikTok",

    "radios100fm100top40":
        "Radios 100FM - 100% Top 40",

    "radios100fm100standup":
        "Radios 100FM - 100% Stand-Up",
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

for key, info in CURATED.items():
    for alias in [
        info["label"],
        *info["aliases"],
    ]:
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
            url
            .casefold()
            .strip()
        )


def clean_attribute(
    value,
):
    return (
        str(value or "")
        .replace('"', "'")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )


def clean_station_name(
    value,
):
    return re.sub(
        r"\s+",
        " ",
        clean_attribute(value),
    ).strip()


def auto_group(
    station_data,
    name,
):
    lowered_name = (
        name.casefold()
    )

    tags = (
        station_data.get("tags")
        or ""
    ).casefold()

    combined = (
        f"{lowered_name} {tags}"
    )


    # Radios 100FM specialty channels.
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
            or "stand-up"
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


    uuid = clean_attribute(
        uuid
    )

    if uuid:
        attrs.append(
            f'tvg-id="radio-{uuid}"'
        )


    logo = clean_attribute(
        logo
    )

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

    # Prefer the most established version of a duplicate.
    stations = sorted(
        stations,
        key=lambda station_data: (
            int(
                station_data.get(
                    "votes"
                )
                or 0
            ),
            int(
                station_data.get(
                    "bitrate"
                )
                or 0
            ),
        ),
        reverse=True,
    )


    seen_names = set()
    seen_streams = set()
    seen_curated = set()

    result = []


    for station_data in stations:

        if int(
            station_data.get(
                "lastcheckok"
            )
            or 0
        ) != 1:
            continue


        original_name = (
            clean_station_name(
                station_data.get(
                    "name"
                )
            )
        )

        if not original_name:
            continue


        original_name_key = (
            normalize_name(
                original_name
            )
        )

        if (
            original_name_key
            in SKIP_KEYS
        ):
            continue


        # url_resolved is preferable because Radio Browser
        # has already followed redirects when possible.
        url = (
            station_data.get(
                "url_resolved"
            )
            or station_data.get(
                "url"
            )
            or ""
        ).strip()

        if not url:
            continue


        curated_key = (
            ALIASES.get(
                original_name_key
            )
        )


        if curated_key:

            info = CURATED[
                curated_key
            ]

            name = info[
                "label"
            ]

            group = GROUPS[
                info["group"]
            ]

            if info[
                "preferred"
            ]:
                url = info[
                    "preferred"
                ]


        else:

            name = (
                DISPLAY_NAME_OVERRIDES
                .get(
                    original_name_key,
                    original_name,
                )
            )

            group = auto_group(
                station_data,
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
                group=group,
                name=name,
                url=url,
                uuid=(
                    station_data.get(
                        "stationuuid"
                    )
                    or ""
                ),
                logo=(
                    station_data.get(
                        "favicon"
                    )
                    or ""
                ),
                curated_key=(
                    curated_key
                ),
            )
        )


    # ============================================================
    # FALLBACK STATIONS
    # ============================================================

    for key, info in CURATED.items():

        fallback = info[
            "fallback"
        ]

        if (
            not fallback
            or key
            in seen_curated
        ):
            continue


        name_key = (
            normalize_name(
                info["label"]
            )
        )

        stream_key = (
            canonical_stream_key(
                fallback
            )
        )


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


        result.append(
            make_item(
                group=GROUPS[
                    info["group"]
                ],
                name=info[
                    "label"
                ],
                url=fallback,
                uuid=(
                    f"fallback-{key}"
                ),
                curated_key=key,
            )
        )


        seen_curated.add(
            key
        )

        seen_names.add(
            name_key
        )


        if stream_key:
            seen_streams.add(
                stream_key
            )


    # ============================================================
    # SORTING
    # ============================================================

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

        lines.append(
            item[
                "extinf"
            ]
        )

        lines.append(
            item[
                "url"
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

    tv_playlist = download_text(
        TV_URL
    )


    print(
        "Downloading Israeli radio database..."
    )

    radio_stations = download_radio()


    tv_lines = (
        make_tv_section(
            tv_playlist
        )
    )


    (
        radio_lines,
        radio_count,
    ) = build_radio_section(
        radio_stations
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
        f"Included {radio_count} "
        "deduplicated Israeli "
        "radio stations."
    )


if __name__ == "__main__":
    main()
