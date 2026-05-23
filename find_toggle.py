import urllib.request, re
r = urllib.request.urlopen('http://127.0.0.1:8000/admin/')
c = r.read().decode()
# Find all buttons
btns = re.findall(r'<button[^>]{0,300}>', c)
for b in btns:
    print(b)
print("---")
# Find theme-related
for line in c.split('\n'):
    if 'theme' in line.lower() or 'toggle' in line.lower() or 'dark' in line.lower():
        print(line.strip()[:150])
