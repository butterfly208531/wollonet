import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'wollo_search.settings'
import django
django.setup()
import urllib.request

print("=" * 55)
print("TOGGLE BUTTON DIAGNOSTIC")
print("=" * 55)

# Check homepage
r = urllib.request.urlopen('http://127.0.0.1:8000/')
html = r.read().decode()

print("\n[1] HOMEPAGE")
print(f"  themeToggle button present : {'themeToggle' in html}")
print(f"  themeIcon present          : {'themeIcon' in html}")
print(f"  wollonet.js loaded         : {'wollonet.js' in html}")
print(f"  bootstrap-icons loaded     : {'bootstrap-icons' in html}")
print(f"  bi-moon-fill icon          : {'bi-moon-fill' in html}")
print(f"  data-theme attribute       : {'data-theme' in html}")
print(f"  wn-theme localStorage key  : {'wn-theme' in html}")
print(f"  theme-toggle-btn CSS class : {'theme-toggle-btn' in html}")

# Check results page
r2 = urllib.request.urlopen('http://127.0.0.1:8000/search/?q=Wollo')
html2 = r2.read().decode()
print("\n[2] RESULTS PAGE")
print(f"  themeToggle button present : {'themeToggle' in html2}")
print(f"  wollonet.js loaded         : {'wollonet.js' in html2}")

# Check admin page
r3 = urllib.request.urlopen('http://127.0.0.1:8000/admin/')
html3 = r3.read().decode()
print("\n[3] ADMIN PAGE")
print(f"  themeToggle present (BAD)  : {'themeToggle' in html3}")
print(f"  wnDarkBtn present (BAD)    : {'wnDarkBtn' in html3}")
print(f"  No toggle on admin (GOOD)  : {'themeToggle' not in html3 and 'wnDarkBtn' not in html3}")

# Check JS file
r4 = urllib.request.urlopen('http://127.0.0.1:8000/static/js/wollonet.js')
js = r4.read().decode()
print("\n[4] wollonet.js")
print(f"  applyTheme function        : {'applyTheme' in js}")
print(f"  click event listener       : {'addEventListener' in js}")
print(f"  localStorage.setItem       : {'localStorage.setItem' in js}")
print(f"  data-theme attribute set   : {'data-theme' in js}")
print(f"  bi-sun-fill (dark icon)    : {'bi-sun-fill' in js}")
print(f"  bi-moon-fill (light icon)  : {'bi-moon-fill' in js}")

# Check CSS file
r5 = urllib.request.urlopen('http://127.0.0.1:8000/static/css/wollonet.css')
css = r5.read().decode()
print("\n[5] wollonet.css")
print(f"  .theme-toggle-btn defined  : {'.theme-toggle-btn' in css}")
print(f"  [data-theme=dark] defined  : {'data-theme=\"dark\"' in css}")
print(f"  [data-theme=light] defined : {'data-theme=\"light\"' in css}")
print(f"  position: fixed            : {'position: fixed' in css}")

print("\n" + "=" * 55)
print("DIAGNOSIS")
print("=" * 55)

issues = []
if 'themeToggle' not in html:
    issues.append("FAIL: themeToggle button missing from homepage HTML")
if 'wollonet.js' not in html:
    issues.append("FAIL: wollonet.js not loaded")
if 'applyTheme' not in js:
    issues.append("FAIL: applyTheme function missing from JS")
if '.theme-toggle-btn' not in css:
    issues.append("FAIL: .theme-toggle-btn CSS missing")
if 'data-theme="dark"' not in css:
    issues.append("FAIL: dark theme CSS variables missing")
if 'themeToggle' in html3 or 'wnDarkBtn' in html3:
    issues.append("FAIL: toggle button still present on admin page")

if not issues:
    print("  All toggle button checks PASSED")
    print("  If button still not working, it may be a browser cache issue")
    print("  Solution: Press Ctrl+Shift+R to hard refresh")
else:
    for i in issues:
        print(f"  {i}")
