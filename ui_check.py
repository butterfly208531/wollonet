import urllib.request

def get(url):
    return urllib.request.urlopen(url).read().decode()

print("=" * 50)
print("UI CHECK")
print("=" * 50)

# Homepage
h = get('http://127.0.0.1:8000/')
print("\n[HOME]")
print(f"  Logo image       : {'wollo_logo.png' in h}")
print(f"  WolloNet text    : {'wollonet-logo' in h}")
print(f"  Subtitle         : {'Local Language' in h}")
print(f"  Search box       : {'homeQuery' in h}")
print(f"  Search button    : {'btn-search-main' in h}")
print(f"  Theme toggle     : {'themeToggle' in h}")
print(f"  Dark theme CSS   : {'data-theme' in h}")

# Results
r = get('http://127.0.0.1:8000/search/?q=Wollo')
print("\n[RESULTS]")
print(f"  Logo in header   : {'wollo_logo.png' in r}")
print(f"  Result cards     : {'result-item' in r}")
print(f"  Score badge      : {'score-badge' in r}")
print(f"  VSM/BM25 toggle  : {'model-btn' in r}")
print(f"  Theme toggle     : {'themeToggle' in r}")

# Admin
a = get('http://127.0.0.1:8000/admin/')
print("\n[ADMIN]")
print(f"  Logo image       : {'wollo_logo.png' in a}")
print(f"  Blue theme       : {'#1a56db' in a}")
print(f"  Black header     : {'#111827' in a}")
print(f"  Remove toggle JS : {'theme-toggle' in a and 'remove()' in a}")

print("\n" + "=" * 50)
print("DONE")
print("=" * 50)
