# Galerie o půlnoci

First-person hra v Unreal Engine 5.8, vytvořená za 1 hodinu.
Noční mramorová galerie za bouřky: posbírej všechna zlatá světla, než se galerie zamkne. Každé světlo „zpívá" — dá se najít po sluchu.

- **Odrazy:** leštěná mramorová podlaha (planární zrcadlení + SSR + reflection captures)
- **Zapečené světlo:** všechna světla scény jsou Static a pečou se Lightmassem do lightmap (měsíc skrz okna, reflektory nad exponáty, lustry)
- **Zvuk:** déšť, hrom po blesku, kroky po mramoru s dozvukem haly, 3D prostorový hlas světel (`Tools/make_audio.py`)
- **Assety:** PBR textury, modely a HDRI z [Poly Haven](https://polyhaven.com) (CC0)

## Spuštění
1. `SESTAVIT.bat` — zkompiluje C++, postaví mapu, zapeče světlo a spustí hru (poprvé trvá déle kvůli shaderům)
2. příště stačí `HRAT.bat`

Ovládání: WASD chůze · myš rozhled · Shift běh · mezerník skok · F baterka · R znovu · Esc konec

## Struktura
- `Source/Galerie/` — hra v C++ (hráč, světla, pravidla, HUD)
- `Tools/build_level.py` — import assetů, materiály a stavba mapy (Unreal Python)
- `Tools/make_audio.py`, `Tools/fetch_assets.py` — syntéza zvuku, stažení CC0 assetů
- `SourceAssets/` — zdrojové textury, modely, zvuky
