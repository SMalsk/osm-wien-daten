# OSM-Daten Wien für die Infrastrukturmatrix

Dieses Repository erzeugt **jeden Montag automatisch** eine aktuelle OpenStreetMap-Datendatei für Wien
(`osm_wien.json`) und stellt sie kostenlos über GitHub Pages bereit. Die Infrastrukturmatrix lädt die
Datei direkt – ohne Overpass, ohne eigenen Server, ohne laufende Kosten.

Enthalten sind ausschließlich öffentliche OSM-Daten (© OpenStreetMap-Mitwirkende, ODbL).
**Die Infrastrukturmatrix selbst (Index.html, enthält den openrouteservice-Schlüssel) gehört NICHT in dieses Repository.**

## Einmalige Einrichtung (ca. 10 Minuten)

1. Auf github.com mit einem (kostenlosen) Konto ein neues **öffentliches** Repository `osm-wien-daten` anlegen.
   GitHub Pages ist nur für öffentliche Repositories kostenlos.
2. Dateien hochladen: *Add file → Upload files* → `README.md` und den Ordner `scripts` hineinziehen → *Commit*.
3. Den Workflow anlegen: *Add file → Create new file*, als Dateiname `.github/workflows/build.yml` eintippen
   (die Schrägstriche legen die Ordner an), den Inhalt der Datei `build.yml` aus diesem Paket einfügen → *Commit*.
   (Ordner, die mit einem Punkt beginnen, werden beim Hochladen per Drag & Drop oft übersprungen.)
4. *Settings → Pages → Build and deployment → Source:* **GitHub Actions** auswählen.
5. *Settings → Actions → General → Workflow permissions:* **Read and write permissions** aktivieren → *Save*.
6. *Actions → „OSM-Daten Wien aktualisieren“ → Run workflow*. Der erste Lauf dauert ca. 5 Minuten.
7. Danach ist die Datei erreichbar unter
   `https://<GITHUB-NAME>.github.io/osm-wien-daten/osm_wien.json`
   (Kontrolle des Datenstands: `.../meta.json`).
8. In der `Index.html` der Infrastrukturmatrix die Zeile mit `OSM_DATA_URL` suchen und `DEIN-GITHUB-NAME`
   durch den eigenen GitHub-Namen ersetzen.

## Laufender Betrieb

- Der Workflow läuft jeden Montag 04:30 UTC, lädt den Österreich-Extrakt von Geofabrik, schneidet Wien samt
  Umland zu, filtert die benötigten Kategorien und veröffentlicht das Ergebnis.
- Jeder Lauf schreibt `datenstand.json` ins Repository. Das hält den Zeitplan aktiv – GitHub deaktiviert
  zeitgesteuerte Workflows sonst nach 60 Tagen ohne Aktivität.
- Schlägt ein Lauf fehl (z. B. Geofabrik kurzzeitig nicht erreichbar), bleibt die letzte Datei online.
  GitHub schickt eine E-Mail an den Konto-Inhaber.
- Die Infrastrukturmatrix zeigt im Block „Datenquellen“ den OSM-Datenstand und warnt, wenn die Datei älter
  als 21 Tage ist. Ist die Datei nicht erreichbar, weicht das Tool automatisch auf Overpass aus.

## Lokal ausführen (optional)

```bash
sudo apt-get install osmium-tool
curl -o austria.osm.pbf https://download.geofabrik.de/europe/austria-latest.osm.pbf
python3 scripts/build_osm_wien.py austria.osm.pbf site
```
