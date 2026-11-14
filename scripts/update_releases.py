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
URL="https://filmdistributorsassociation.com/print-release-schedule/"
WEEKDAYS=r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\\s+\\d{1,2}\\s+[A-Za-z]+\\s+\\d{4}"
SKIP={"Release Schedule","This week's releases","Event Cinema","VOD Only","Media Info Key","Access Formats","Film Formats","Print version"}

def main():
    response=requests.get(URL,timeout=40,headers={"User-Agent":"UKCinemaReleases/1.0 (weekly public release list)"})
    response.raise_for_status()
    soup=BeautifulSoup(response.text,"html.parser")
    headings=soup.find_all(["h2","h3","h4","h5"])
    current_date=None; films=[]
    for h in headings:
        text=" ".join(h.get_text(" ",strip=True).split())
        if re.fullmatch(WEEKDAYS,text):
            current_date=datetime.datetime.strptime(text.split(" ",1)[1],"%d %B %Y").date()
            continue
        if h.name not in ("h4","h5") or not current_date or not text or text in SKIP:
            continue
        if len(text)>130 or text.lower().startswith(("week commencing","print date")):
            continue
        films.append({"title":text,"release_date":current_date.isoformat(),"rerelease":bool(re.search(r"restoration|anniversary|re-release|re-release",text,re.I))})
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
        film.update({k:v for k,v in extra.items() if k in ("certificate","runtime","review","sources","rerelease")})
    data={"week_label":f"Week commencing {start.strftime('%-d %B %Y')}","updated":today.strftime("%-d %B %Y"),"source":URL,"films":week_films}
    data_dir=ROOT/"data"; data_dir.mkdir(exist_ok=True)
    current=data_dir/"current.json"
    if current.exists():
        old=json.loads(current.read_text())
        if old.get("week_label")!=data["week_label"] and old.get("films"):
            archive=data_dir/"archive";archive.mkdir(exist_ok=True)
            stamp=re.sub(r"[^a-z0-9]+","-",old.get("week_label","week").lower()).strip("-")
            (archive/f"{stamp}.json").write_text(json.dumps(old,ensure_ascii=False,indent=2)+"\\n")
    current.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\\n")
    print(f"Published {len(week_films)} releases for {data['week_label']}")

if __name__=="__main__": main()
