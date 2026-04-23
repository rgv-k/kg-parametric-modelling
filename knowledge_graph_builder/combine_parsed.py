import json, glob
files = glob.glob("data/parsed/*_parsed.json")
all_verses = []
for f in files:
    data = json.load(open(f))
    all_verses.extend(data["verses"])
json.dump(all_verses, open("data/parsed/MAYAMATA_COMBINED.json","w"), indent=2)