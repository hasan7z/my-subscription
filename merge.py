import requests

with open("sources.txt", "r") as f:
    urls = [line.strip() for line in f if line.strip()]

all_configs = []

for url in urls:
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            all_configs.append(r.text)
    except:
        pass

with open("all.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(all_configs))

print("Done")
