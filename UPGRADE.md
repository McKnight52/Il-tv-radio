# IPTV repair upgrade

Upload only `maintain.py` and `config.json` into the root of the **iptv-v2** branch. Commit both in the same commit. Optionally upload `test_maintain.py` for developer use. Keep `israel.m3u`, `unavailable.m3u`, `status.json`, `replacements.json`, and `report.md` from your live branch. Do not overwrite your main-branch workflow.

Run Actions > Daily IPTV V2 maintenance > Run workflow > main. Review the new report on iptv-v2. No local installation or AI subscription required. If necessary, revert the upgrade commit on iptv-v2; the original main branch is unaffected.

## Policy

The source catalogues are refreshed each run, and exact IDs, compatible generic feed suffixes, and curated aliases are used. Unknown feeds and stations are not matched by fuzzy substring. Existing working URLs are kept. Candidate URLs from an approved broadcaster domain or explicitly configured public URL are tested; other discovered candidates are reported as needing review, with paths withheld to avoid publishing potentially sensitive URL components. The presence of an entry in an IPTV directory does not establish authorization. Do not approve unknown resellers, paid channels, expiring credentials, or access-control workarounds. Explicit URLs in `official_urls` must be public and authorized; do not add ordinary viewing webpages there. `official_pages` is informational only.

Two broadcaster-domain candidate URLs (Kan Educational and Makan Radio) are documented by public indexes; they have not been live-verified and may be stale or geographically restricted. The script tests them before changing anything. References:
- https://gist.github.com/Sk2025365/9c763ee9eec4eb289fa037a180b13a0d (Kan Educational)
- https://tingfm.com/radio/26295 (Makan Radio)
- https://github.com/iptv-org/api/blob/master/README.md (IPTV data schemas)
- https://docs.radio-browser.info/ (radio data)
- https://github.com/Free-TV/IPTV/blob/master/lists/israel.md (Knesset ID alias)

Foreign-runner HTTP 403/451, timeouts and connection errors are recorded as uncertain unless the exact URL was previously confirmed to return 403 on your own computer (`locally_failed_urls`, currently Keshet 12 and Knesset). Those two URLs become eligible for quarantine after three consecutive counted UTC days. Other failures from that same provider are not assumed confirmed locally; they are reported separately. Remove an entry from `locally_failed_urls` if the local result was affected by a VPN or a later local test succeeds. Quarantined entries are retested daily and automatically restored on success. Mass-failure protection is unchanged (35%).

## Testing and limits

Eight automated tests pass (run `python -m unittest -v test_maintain.py` with the existing requirements installed). Local HTTP fixture tests also verified direct MP3, HLS video, missing HLS segment, HTML response, HTTP 403 and HTTP 404 using actual FFprobe. External streams, the current GitHub branch, and Samsung playback have not been live-tested from this environment. The workflow uses an existing write-enabled GitHub token; do not run unfamiliar scripts or add secrets. Automated discovery is not a web search engine and cannot guarantee a new stream for every station. New domains must be reviewed and added per channel; a playback test does not establish channel identity or legal authorization on its own.
