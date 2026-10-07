import urllib.request

TV_URL = "https://iptv-org.github.io/iptv/countries/il.m3u"
RADIO_URL = (
    "https://de1.api.radio-browser.info/m3u/"
    "stations/bycountrycodeexact/IL"
    "?hidebroken=true&order=name"
)

OUTPUT = "israel.m3u"


def download(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Israel-TV-Radio-Playlist/1.0"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def remove_header(playlist):
    lines = playlist.splitlines()

    if lines and lines[0].strip().startswith("#EXTM3U"):
        lines = lines[1:]

    return "\n".join(lines).strip()


tv = remove_header(download(TV_URL))
radio = remove_header(download(RADIO_URL))

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n\n")
    f.write("# Israel TV\n")
    f.write(tv)
    f.write("\n\n# Israel Radio\n")
    f.write(radio)
    f.write("\n")

print(f"Created {OUTPUT}")
