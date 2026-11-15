"""Stahne CC0 assety z Poly Haven (polyhaven.com, licence CC0) do SourceAssets/."""
import json, os, sys, urllib.request
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'SourceAssets')
UA = {'User-Agent': 'game-asset-fetch'}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
def save(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0: return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb').write(get(url)); print('ok', os.path.relpath(path, ROOT), flush=True)
TEX = ['marble_01', 'plastered_wall_04', 'herringbone_parquet', 'marble_tiles']
MODELS = ['marble_bust_01', 'horse_statue_01', 'gothic_statue', 'brass_vase_01', 'ceramic_vase_01',
          'fancy_picture_frame_01', 'fancy_picture_frame_02', 'painted_wooden_bench', 'Chandelier_01', 'potted_plant_01',
          'bronze_whale_statue']
HDRI = ['moonlit_golf']
for s in TEX:
    try:
        f = json.loads(get('https://api.polyhaven.com/files/' + s))
        for key, out in (('Diffuse', 'diff'), ('nor_dx', 'nor'), ('arm', 'arm')):
            u = f[key]['2k']['jpg']['url']
            save(u, os.path.join(ROOT, 'Textures', '%s_%s.jpg' % (s, out)))
    except Exception as e: print('FAIL', s, e, flush=True)
for s in MODELS:
    try:
        f = json.loads(get('https://api.polyhaven.com/files/' + s))
        fb = f['fbx']['1k']['fbx']
        d = os.path.join(ROOT, 'Models', s)
        save(fb['url'], os.path.join(d, s + '.fbx'))
        for rel, inc in fb.get('include', {}).items():
            save(inc['url'], os.path.join(d, rel))
    except Exception as e: print('FAIL', s, e, flush=True)
for s in HDRI:
    try:
        f = json.loads(get('https://api.polyhaven.com/files/' + s))
        save(f['hdri']['2k']['hdr']['url'], os.path.join(ROOT, 'HDRI', s + '.hdr'))
    except Exception as e: print('FAIL', s, e, flush=True)
print('DONE')

# mapy modelu jako JPG (UE je importuje primo; nor_dx = DirectX normaly)
for s in MODELS:
    try:
        f = json.loads(get('https://api.polyhaven.com/files/' + s))
        for key, v in f.items():
            if key in ('blend', 'gltf', 'fbx', 'usd', 'mtlx') or 'nor_gl' in key: continue
            r = v.get('1k', {}); fmt = r.get('jpg') or r.get('png')
            if not fmt: continue
            ext = fmt['url'].rsplit('.', 1)[1]
            save(fmt['url'], os.path.join(ROOT, 'Models', s, 'ue', '%s.%s' % (key, ext)))
    except Exception as e: print('FAIL maps', s, e, flush=True)
print('DONE maps')
