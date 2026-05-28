# find_apps.py — Run this to find exact paths for all your apps
# Run with: python find_apps.py

import os
import subprocess
import winreg
import glob

def find_app(name, search_terms, common_paths=[]):
    """Find an app by searching registry, common paths, and AppData."""
    print(f"\n{'='*50}")
    print(f"Searching for: {name}")
    print('='*50)

    found = []

    # 1. Check common hardcoded paths
    for path in common_paths:
        expanded = os.path.expandvars(path)
        if os.path.isfile(expanded):
            print(f"  ✓ Found at: {expanded}")
            found.append(expanded)

    # 2. Search AppData folders
    appdata_roots = [
        os.environ.get("APPDATA", ""),
        os.environ.get("LOCALAPPDATA", ""),
        os.path.expandvars(r"%APPDATA%\..\Local"),
    ]

    for root in appdata_roots:
        for term in search_terms:
            pattern = os.path.join(root, "**", f"{term}.exe")
            matches = glob.glob(pattern, recursive=True)
            for m in matches:
                if m not in found:
                    print(f"  ✓ Found in AppData: {m}")
                    found.append(m)

    # 3. Search Program Files
    pf_roots = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
    ]
    for root in pf_roots:
        for term in search_terms:
            pattern = os.path.join(root, "**", f"{term}.exe")
            matches = glob.glob(pattern, recursive=True)
            for m in matches:
                if m not in found:
                    print(f"  ✓ Found in Program Files: {m}")
                    found.append(m)

    # 4. Check Windows Registry (App Paths)
    try:
        for term in search_terms:
            reg_key = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{term}.exe"
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    key = winreg.OpenKey(hive, reg_key)
                    path, _ = winreg.QueryValueEx(key, "")
                    if path and os.path.isfile(path) and path not in found:
                        print(f"  ✓ Found in Registry: {path}")
                        found.append(path)
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    pass
    except Exception as e:
        print(f"  Registry search error: {e}")

    # 5. Try 'where' command (checks PATH)
    for term in search_terms:
        try:
            result = subprocess.run(
                f"where {term}",
                shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                for line in result.stdout.strip().splitlines():
                    if line and os.path.isfile(line) and line not in found:
                        print(f"  ✓ Found in PATH: {line}")
                        found.append(line)
        except Exception:
            pass

    # 6. Check UWP / Store apps
    try:
        result = subprocess.run(
            'powershell -Command "Get-AppxPackage | Where-Object {$_.Name -like \'*' +
            search_terms[0] + '*\'} | Select-Object Name, PackageFamilyName | Format-List"',
            shell=True, capture_output=True, text=True, timeout=15
        )
        if result.stdout.strip():
            print(f"  ✓ Found as UWP/Store app:")
            print(f"    {result.stdout.strip()}")
            found.append("UWP:" + result.stdout.strip())
    except Exception:
        pass

    if not found:
        print(f"  ✗ NOT FOUND on this system")

    return found


if __name__ == "__main__":
    print("Charli App Path Finder")
    print("Scanning your system... (may take 30-60 seconds)\n")

    apps = [
        ("CMD",        ["cmd"],       [r"C:\Windows\System32\cmd.exe"]),
        ("PowerShell", ["powershell", "pwsh"], [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            r"C:\Program Files\PowerShell\7\pwsh.exe",
        ]),
        ("WhatsApp",   ["WhatsApp"],  [
            r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe",
            r"%APPDATA%\WhatsApp\WhatsApp.exe",
        ]),
        ("Telegram",   ["Telegram"],  [
            r"%APPDATA%\Telegram Desktop\Telegram.exe",
            r"%LOCALAPPDATA%\Telegram Desktop\Telegram.exe",
        ]),
        ("Discord",    ["Discord"],   [
            r"%LOCALAPPDATA%\Discord\Update.exe",
            r"%LOCALAPPDATA%\Discord\app-*\Discord.exe",
        ]),
        ("Zoom",       ["Zoom"],      [
            r"%APPDATA%\Zoom\bin\Zoom.exe",
            r"%LOCALAPPDATA%\Zoom\bin\Zoom.exe",
            r"C:\Program Files\Zoom\bin\Zoom.exe",
        ]),
        ("Chrome",     ["chrome"],    [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
        ]),
        ("Slack",      ["slack"],     [
            r"%LOCALAPPDATA%\slack\slack.exe",
        ]),
        ("Teams",      ["Teams"],     [
            r"%LOCALAPPDATA%\Microsoft\Teams\current\Teams.exe",
            r"%LOCALAPPDATA%\Microsoft\Teams\Teams.exe",
        ]),
        ("Word",       ["WINWORD"],   [
            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
        ]),
        ("Excel",      ["EXCEL"],     [
            r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
        ]),
    ]

    results = {}
    for app_name, search_terms, common_paths in apps:
        found = find_app(app_name, search_terms, common_paths)
        results[app_name] = found

    # Print final summary
    print("\n\n" + "="*60)
    print("FINAL SUMMARY — Copy these into your APP_REGISTRY")
    print("="*60)
    for app_name, paths in results.items():
        real_paths = [p for p in paths if not p.startswith("UWP:")]
        uwp_paths  = [p for p in paths if p.startswith("UWP:")]

        if real_paths:
            print(f"\n# {app_name}")
            print(f'  "{app_name.lower()}": r"{real_paths[0]}",')
        elif uwp_paths:
            print(f"\n# {app_name} — Store/UWP app")
            print(f"  # Use os.startfile with shell:AppsFolder\\<PackageFamilyName>!App")
            print(f"  {uwp_paths[0]}")
        else:
            print(f"\n# {app_name} — NOT FOUND (app may not be installed)")