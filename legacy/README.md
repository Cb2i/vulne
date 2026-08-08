# Legacy prototype

`vuln_manager_prototype.html` is the original single-file, client-side proof of concept that
VulnAssist replaces. It first prototyped the "CVSS + asset context → adjusted score" idea that
became the backend's CAA engine (`backend/app/rules/caa/engine.py`).

It is kept here for historical reference only. It is **not** part of the deployed application —
it calls the Anthropic API directly from the browser (no backend, no persistence, no auth) and
must not be served or linked from VulnAssist.
