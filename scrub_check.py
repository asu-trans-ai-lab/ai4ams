"""Pre-push sensitivity scrub (gui4gmns validate_no_private_data pattern).
Must print CLEAN (or only whitelisted warnings) before any git push."""
import os
import re
import sys

FORBID_FILES = re.compile(
    r"(readings.*\.csv|.*_pm\.(csv|bin)|.*_am\.(csv|bin)|link_performance.*\.csv|"
    r"trajectory_subarea.*\.(bin|parquet)|node\.csv|link\.csv|demand.*\.csv|.*\.omx)$", re.I)
FORBID_TEXT = [
    (re.compile(r"C:\\Users\\[A-Za-z0-9_]+"), "local user path", None),
    (re.compile(r"Drop" + "box", re.I), "personal cloud path", None),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(?:com|edu|gov|org)"), "email address", None),
    # field NAME in contract docs/templates is fine; actual payload = csv only
    (re.compile(r"measurement_tstamp", re.I), "probe reading payload marker", (".csv",)),
]
WHITELIST_NOTES = {"examples/dashboards": "license check pending (RELEASE_CHECKLIST #1/#2)"}

root = os.path.dirname(os.path.abspath(__file__))
issues, warns = [], []
for dp, _, fns in os.walk(root):
    for fn in fns:
        rel = os.path.relpath(os.path.join(dp, fn), root).replace("\\", "/")
        if fn == os.path.basename(__file__):
            continue
        if FORBID_FILES.match(fn):
            issues.append(f"FORBIDDEN FILE: {rel}")
            continue
        if fn.lower().endswith((".md", ".py", ".yml", ".yaml", ".csv", ".json", ".html")):
            try:
                txt = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for pat, why, only_ext in FORBID_TEXT:
                if only_ext and not fn.lower().endswith(only_ext):
                    continue
                if not pat.search(txt):
                    continue
                line = next((i + 1 for i, l in enumerate(txt.splitlines()) if pat.search(l)), 0)
                tgt = warns if any(rel.startswith(w) for w in WHITELIST_NOTES) else issues
                tgt.append(f"{why}: {rel}:{line}")

for w in warns:
    print("WARN (whitelisted):", w)
if issues:
    print("\n".join(sorted(set(issues))))
    print(f"\nNOT CLEAN: {len(set(issues))} issue(s) — fix or whitelist before push.")
    sys.exit(1)
print("CLEAN" + (f" ({len(warns)} whitelisted warnings)" if warns else ""))
