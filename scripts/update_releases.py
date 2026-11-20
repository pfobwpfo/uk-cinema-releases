#!/usr/bin/env python3
"""Refresh the weekly UK cinema release list from the FDA print schedule.
Editorial review summaries and running times are deliberately preserved rather
than guessed; add verified details to data/editorial.json.
"""
import json, re, datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
URL="https://filmdistributorsassociation.com/release-schedule/all-future-releases/"
WEEKDAYS=r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}"
SKIP={"Release Schedule","This week's releases","Event Cinema","VOD Only","Media Info Key","Access Formats","Film Formats","Print version"}
NON_FILM_EVENT=re.compile(r"\b(opera|theatre|concert|live viewing|finals in cinema|with peppa)\b",re.I)

def main():
    response=requests.get(URL,timeout=40,headers={"User-Agent":"UKCinemaReleases/1.0 (weekly public release list)"})
    response.raise_for_status()
    soup=BeautifulSoup(response.text,"html.parser")
    # FDA now renders release dates as ordinary text elements (verified Nov 2026) rather than
    # headings. Walk the document in order, recognising date text wherever it
    # appears while continuing to take film names only from h4/h5 elements.
    current_date=None; films=[]
    for node in soup.find_all(True):
        text=" ".join(node.get_text(" ",strip=True).split())
        if re.fullmatch(WEEKDAYS,text):
            current_date=datetime.datetime.strptime(text.split(" ",1)[1],"%d %B %Y").date()
            continue
        if node.name not in ("h4","h5") or not current_date or not text or text in SKIP or NON_FILM_EVENT.search(text):
            continue
        if len(text)>130 or text.lower().startswith(("week commencing","print date")):
            continue
        films.append({"title":text,"release_date":current_date.isoformat(),"rerelease":bool(re.search(r"restoration|anniversary|re-release",text,re.I))})
    if not films:
        raise RuntimeError("No release titles found; FDA page structure may have changed. Existing site data left untouched.")
    today=datetime.date.today()
    start=today-datetime.timedelta(days=today.weekday())
    end=start+datetime.timedelta(days=6)
    week_films=[f for f in films if start.isoformat()<=f["release_date"]<=end.isoformat()]
    if not week_films:
        # FDA may publish next week's schedule before the Thursday run.
        week_films=[f for f in films if f["release_date"]>=start.isoformat()][:60]
    if not week_films:
        raise RuntimeError("No current/upcoming releases found; refusing to overwrite the site.")
    editorial_path=ROOT/"data/editorial.json"
    editorial=json.loads(editorial_path.read_text()) if editorial_path.exists() else {}
    for film in week_films:
        extra=editorial.get(film["title"],{})
        film.update({k:v for k,v in extra.items() if k in ("genre","certificate","runtime","review","sources","synopsis","rerelease")})
    data={"week_label":f"Week commencing {start.strftime('%-d %B %Y')}","updated":today.strftime("%-d %B %Y"),"source":URL,"films":week_films}
    data_dir=ROOT/"data"; data_dir.mkdir(exist_ok=True)
    # Rolling four-week preview; only list films with an editorially supplied synopsis.
    def title_key(value):
        # Match minor FDA/editorial title variations (punctuation and leading/trailing "The").
        words=re.findall(r"[a-z0-9]+",value.casefold())
        return " ".join(w for w in words if w!="the")
    lookup={title_key(k):v for k,v in editorial.items()}
    upcoming=[]
    for film in films:
        release=datetime.date.fromisoformat(film["release_date"])
        key=title_key(film["title"])
        extra=editorial.get(film["title"],lookup.get(key,{}))
        if end < release <= today+datetime.timedelta(days=28) and extra.get("synopsis"):
            upcoming.append({"title":film["title"],"release_date":film["release_date"],**{k:extra[k] for k in ("genre","certificate","runtime") if extra.get(k)},"synopsis":extra["synopsis"]})
    (data_dir/"coming-soon.json").write_text(json.dumps({"updated":today.strftime("%-d %B %Y"),"films":upcoming},ensure_ascii=False,indent=2)+"\n")
    current=data_dir/"current.json"
    if current.exists():
        old=json.loads(current.read_text())
        if old.get("week_label")!=data["week_label"] and old.get("films"):
            archive=data_dir/"archive";archive.mkdir(exist_ok=True)
            stamp=re.sub(r"[^a-z0-9]+","-",old.get("week_label","week").lower()).strip("-")
            (archive/f"{stamp}.json").write_text(json.dumps(old,ensure_ascii=False,indent=2)+"\n")
    current.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    archive_dir=data_dir/"archive"
    archive_dir.mkdir(exist_ok=True)
    manifest=[]
    for item in sorted(archive_dir.glob("*.json")):
        if item.name=="index.json":
            continue
        try:
            saved=json.loads(item.read_text())
            manifest.append({"file":item.name,"week_label":saved.get("week_label",item.stem)})
        except (OSError,ValueError):
            continue
    (archive_dir/"index.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(f"Published {len(week_films)} releases for {data['week_label']}")

if __name__=="__main__": main()
