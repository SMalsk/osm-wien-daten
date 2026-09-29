#!/usr/bin/env python3
"""
Erzeugt aus dem Geofabrik-Österreich-Extrakt eine kompakte OSM-Datendatei für die
Infrastrukturmatrix Wien (POIs als Punkte, Radverkehrsanlagen als Linien).

Aufruf:  python scripts/build_osm_wien.py austria-latest.osm.pbf site/
Benötigt: osmium-tool (CLI), Python >= 3.9 – keine weiteren Pakete.
"""
import json, subprocess, sys, os, datetime

# Wien + ca. 10 km Umland (für Autobahn-Anschlussstellen)
BBOX = "16.05,48.02,16.72,48.42"

AMENITY = "car_sharing,bicycle_rental,vehicle_rental,fuel,bank,atm,post_office,restaurant,cafe,ice_cream,fast_food,bar,pub,biergarten,nightclub,dentist,doctors,clinic,veterinary,cinema,theatre,townhall,place_of_worship,community_centre"
SHOP = "supermarket,convenience,bakery,butcher,deli,greengrocer,cheese,pastry,chemist,tobacco,newsagent,kiosk,hairdresser,beauty,dry_cleaning,laundry,mall,optician"
FILTERS = [
    f"nwr/amenity={AMENITY}", f"nwr/shop={SHOP}", "nwr/healthcare=doctor,dentist", "nwr/post_office=post_partner",
    "nwr/leisure=fitness_centre", "nwr/office=government", "nwr/railway=station,halt", "n/highway=motorway_junction",
    "w/highway=cycleway", "w/cycleway=lane,track,opposite_lane,opposite_track,shared_lane",
    "w/cycleway:right=lane,track", "w/cycleway:left=lane,track", "w/cycleway:both=lane,track", "w/bicycle=designated",
]
KEEP = {"amenity","shop","healthcare","healthcare:speciality","leisure","office","railway","station","subway","highway",
        "cycleway","cycleway:right","cycleway:left","cycleway:both","bicycle","rental","post_office","name","brand","operator","ref",
        "addr:street","addr:housenumber","addr:postcode","addr:city","addr:place"}
A_SET, S_SET = set(AMENITY.split(",")), set(SHOP.split(","))
LANE = {"lane","track","opposite_lane","opposite_track","shared_lane"}

def is_poi(t):
    return (t.get("amenity") in A_SET or t.get("shop") in S_SET or t.get("healthcare") in ("doctor","dentist")
            or t.get("post_office") == "post_partner" or t.get("leisure") == "fitness_centre" or t.get("office") == "government"
            or t.get("railway") in ("station","halt") or t.get("highway") == "motorway_junction")

def is_cycle(t):
    return (t.get("highway") == "cycleway" or t.get("cycleway") in LANE
            or any(t.get(k) in ("lane","track") for k in ("cycleway:right","cycleway:left","cycleway:both"))
            or (t.get("bicycle") == "designated" and t.get("highway") in ("path","footway")))

def centroid(geom):
    """Flächenschwerpunkt des größten äußeren Rings (Fallback: Mittelwert)."""
    rings = [geom["coordinates"][0]] if geom["type"] == "Polygon" else [p[0] for p in geom["coordinates"]]
    best, best_a = None, -1
    for r in rings:
        a = cx = cy = 0.0
        for (x1,y1),(x2,y2) in zip(r, r[1:]):
            f = x1*y2 - x2*y1; a += f; cx += (x1+x2)*f; cy += (y1+y2)*f
        if abs(a) > best_a:
            best_a = abs(a)
            best = (cx/(3*a), cy/(3*a)) if a else (sum(p[0] for p in r)/len(r), sum(p[1] for p in r)/len(r))
    return best

def run(*args):
    print("+", " ".join(args), flush=True); subprocess.run(args, check=True)

def main(src, out):
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, "_tmp"); os.makedirs(tmp, exist_ok=True)
    run("osmium", "extract", "-b", BBOX, "-s", "smart", src, "-o", f"{tmp}/wien.pbf", "--overwrite")
    run("osmium", "tags-filter", f"{tmp}/wien.pbf", *FILTERS, "-o", f"{tmp}/filtered.pbf", "--overwrite")
    run("osmium", "export", f"{tmp}/filtered.pbf", "-f", "geojsonseq", "-a", "type,id", "-o", f"{tmp}/features.geojsonseq", "--overwrite")
    try:
        stand = subprocess.run(["osmium","fileinfo","-g","header.option.osmosis_replication_timestamp",src],
                               capture_output=True, text=True).stdout.strip()
    except Exception:
        stand = ""
    pois, lines = {}, {}
    with open(f"{tmp}/features.geojsonseq", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip().lstrip("\x1e")
            if not raw: continue
            ft = json.loads(raw); p = ft.get("properties") or {}; g = ft.get("geometry")
            if not g: continue
            oid = f"{p.get('@type','x')[0]}/{p.get('@id','')}"
            t = {k:v for k,v in p.items() if k in KEEP}
            if g["type"] in ("LineString","MultiLineString") and is_cycle(t):
                parts = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
                for i, part in enumerate(parts):
                    if len(part) >= 2:
                        lines[f"{oid}#{i}" if i else oid] = [oid, t, [[round(x,5), round(y,5)] for x,y in part]]
            elif is_poi(t):
                # Priorität: Punkt/Fläche vor Linie (geschlossene Wege werden ggf. doppelt exportiert)
                rank = 1 if g["type"] in ("LineString","MultiLineString") else 2
                if oid in pois and pois[oid][4] >= rank: continue
                if g["type"] == "Point": x, y = g["coordinates"]
                elif g["type"] in ("Polygon","MultiPolygon"): x, y = centroid(g)
                elif g["type"] == "LineString": c = g["coordinates"]; x, y = c[len(c)//2]
                else: continue
                pois[oid] = [round(x,6), round(y,6), oid, t, rank]
    meta = {"erstellt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "osm_stand": stand, "quelle": "Geofabrik austria-latest.osm.pbf, © OpenStreetMap-Mitwirkende (ODbL)",
            "bbox": BBOX, "anzahl_pois": len(pois), "anzahl_linien": len(lines)}
    with open(os.path.join(out, "osm_wien.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "pois": [v[:4] for v in pois.values()], "lines": list(lines.values())}, f, ensure_ascii=False, separators=(",",":"))
    with open(os.path.join(out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    for fn in os.listdir(tmp): os.remove(os.path.join(tmp, fn))
    os.rmdir(tmp)
    print(json.dumps(meta, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
