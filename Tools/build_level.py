"""Galerie o pulnoci - import assetu, materialy a stavba mapy. Spousti se v editoru:
UnrealEditor.exe Galerie.uproject -ExecutePythonScript=Tools/build_level.py
Svetla jsou Static => nasledny Lightmass bake (Tools/go.sh bake) je zapece do lightmap."""
import os, traceback
import unreal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'SourceAssets')
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
V = unreal.Vector
QUIT = os.environ.get('GALERIE_NOQUIT') is None


def log(*a):
    unreal.log('[GALERIE] ' + ' '.join(str(x) for x in a))


def sp(obj, **kw):
    """set_editor_property, ktere kvuli jedne chybejici vlastnosti neshodi cely skript."""
    for k, v in kw.items():
        try:
            obj.set_editor_property(k, v)
        except Exception as e:
            log('WARN prop', type(obj).__name__, k, e)


def rot(pitch=0.0, yaw=0.0, roll=0.0):
    return unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw)


# ------------------------------------------------------------------ import
def imp(path, dest, options=None):
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', path)
    t.set_editor_property('destination_path', dest)
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    if options is not None:
        t.set_editor_property('options', options)
    AT.import_asset_tasks([t])
    out = []
    for p in t.get_editor_property('imported_object_paths'):
        a = unreal.load_asset(str(p).split('.')[0])
        if a:
            out.append(a)
    return out


def tex(path, dest, kind='c'):
    name = os.path.splitext(os.path.basename(path))[0]
    existing = dest + '/' + name
    a = unreal.load_asset(existing) if EAL.does_asset_exist(existing) else None
    if a is None:
        r = imp(path, dest)
        a = r[0] if r else None
    if a is None:
        log('WARN texture missing', path)
        return None
    if kind == 'n':
        sp(a, compression_settings=unreal.TextureCompressionSettings.TC_NORMALMAP, srgb=False)
    elif kind == 'm':
        sp(a, compression_settings=unreal.TextureCompressionSettings.TC_MASKS, srgb=False)
    EAL.save_loaded_asset(a)
    return a


# ------------------------------------------------------------------ materialy
def new_mat(name):
    path = '/Game/Mat/' + name
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    m = AT.create_asset(name, '/Game/Mat', unreal.Material, unreal.MaterialFactoryNew())
    sp(m, used_with_static_lighting=True)   # jinak se u zapecenych objektu ve hre pouzije vychozi material
    return m


def node(m, cls, x, y, **props):
    n = MEL.create_material_expression(m, cls, x, y)
    sp(n, **props)
    return n


def con(a, ao, b, bi):
    if not MEL.connect_material_expressions(a, ao, b, bi):
        log('WARN connect', a, ao, b, bi)


def prop(a, ao, p):
    if not MEL.connect_material_property(a, ao, p):
        log('WARN mat property', a, ao, p)


def finish(m):
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m


MP = unreal.MaterialProperty
ST = unreal.MaterialSamplerType


def pbr(name, d, n, arm, plane='uv', scale=300.0, tiling=(1.0, 1.0), tint=(1, 1, 1), rough_mul=1.0, rough_add=0.0,
        metal=None, use_metal_tex=False, flip_v=False):
    """PBR material. plane 'xy'/'xz'/'yz' = UV ze svetove pozice (stejna hustota textury na vsech zdech)."""
    m = new_mat(name)
    if plane == 'uv':
        uv = node(m, unreal.MaterialExpressionTextureCoordinate, -1100, 0, u_tiling=tiling[0], v_tiling=tiling[1])
    else:
        wp = node(m, unreal.MaterialExpressionWorldPosition, -1500, 0)
        mask = node(m, unreal.MaterialExpressionComponentMask, -1300, 0, r='x' in plane, g='y' in plane, b='z' in plane, a=False)
        con(wp, '', mask, '')
        uv = node(m, unreal.MaterialExpressionMultiply, -1100, 0, const_b=1.0 / scale)
        con(mask, '', uv, 'A')
    if d:
        td = node(m, unreal.MaterialExpressionTextureSample, -800, -300, texture=d, sampler_type=ST.SAMPLERTYPE_COLOR)
        con(uv, '', td, 'UVs')
        if tuple(tint) != (1, 1, 1):
            c = node(m, unreal.MaterialExpressionConstant3Vector, -800, -500, constant=unreal.LinearColor(tint[0], tint[1], tint[2], 1))
            mul = node(m, unreal.MaterialExpressionMultiply, -500, -350)
            con(td, 'RGB', mul, 'A'); con(c, '', mul, 'B')
            prop(mul, '', MP.MP_BASE_COLOR)
        else:
            prop(td, 'RGB', MP.MP_BASE_COLOR)
    else:
        c = node(m, unreal.MaterialExpressionConstant3Vector, -800, -500, constant=unreal.LinearColor(tint[0], tint[1], tint[2], 1))
        prop(c, '', MP.MP_BASE_COLOR)
    if n:
        tn = node(m, unreal.MaterialExpressionTextureSample, -800, 0, texture=n, sampler_type=ST.SAMPLERTYPE_NORMAL)
        con(uv, '', tn, 'UVs')
        prop(tn, 'RGB', MP.MP_NORMAL)
    if arm:
        ta = node(m, unreal.MaterialExpressionTextureSample, -800, 300, texture=arm, sampler_type=ST.SAMPLERTYPE_MASKS)
        con(uv, '', ta, 'UVs')
        r1 = node(m, unreal.MaterialExpressionMultiply, -500, 300, const_b=rough_mul)
        con(ta, 'G', r1, 'A')
        r2 = node(m, unreal.MaterialExpressionAdd, -350, 300, const_b=rough_add)
        con(r1, '', r2, 'A')
        prop(r2, '', MP.MP_ROUGHNESS)
        prop(ta, 'R', MP.MP_AMBIENT_OCCLUSION)
        if use_metal_tex:
            prop(ta, 'B', MP.MP_METALLIC)
    else:
        r = node(m, unreal.MaterialExpressionConstant, -500, 300, r=rough_add)
        prop(r, '', MP.MP_ROUGHNESS)
    if metal is not None:
        mt = node(m, unreal.MaterialExpressionConstant, -500, 150, r=metal)
        prop(mt, '', MP.MP_METALLIC)
    return finish(m)


def emissive(name, color, strength, unlit=True, two_sided=False):
    m = new_mat(name)
    c = node(m, unreal.MaterialExpressionConstant3Vector, -600, 0, constant=unreal.LinearColor(color[0], color[1], color[2], 1))
    mul = node(m, unreal.MaterialExpressionMultiply, -350, 0, const_b=strength)
    con(c, '', mul, 'A')
    prop(mul, '', MP.MP_EMISSIVE_COLOR)
    if unlit:
        sp(m, shading_model=unreal.MaterialShadingModel.MSM_UNLIT)
    sp(m, two_sided=two_sided)
    return finish(m)


# ------------------------------------------------------------------ mesh helpers
def own_shape(src, name):
    """Kopie zakladniho tvaru s vlastnim lightmap UV kanalem (kvuli zapeceni svetla)."""
    path = '/Game/Meshes/' + name
    try:
        m = unreal.load_asset(path) if EAL.does_asset_exist(path) else EAL.duplicate_asset(src, path)
        sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        bs = sms.get_lod_build_settings(m, 0)
        sp(bs, generate_lightmap_u_vs=True, min_lightmap_resolution=64, src_lightmap_index=0, dst_lightmap_index=1)
        sms.set_lod_build_settings(m, 0, bs)
        sp(m, light_map_coordinate_index=1, light_map_resolution=64)
        EAL.save_loaded_asset(m)
        return m
    except Exception as e:
        log('WARN own_shape', name, e)
        return unreal.load_asset(src)


def main():
    # ---------- textury ----------
    T = {}
    for base in ('marble_01', 'plastered_wall_04', 'herringbone_parquet', 'marble_tiles'):
        T[base] = (tex(os.path.join(SRC, 'Textures', base + '_diff.jpg'), '/Game/Tex', 'c'),
                   tex(os.path.join(SRC, 'Textures', base + '_nor.jpg'), '/Game/Tex', 'n'),
                   tex(os.path.join(SRC, 'Textures', base + '_arm.jpg'), '/Game/Tex', 'm'))
    log('textures ok')

    # ---------- zvuk ----------
    for f in sorted(os.listdir(os.path.join(SRC, 'Audio'))):
        try:
            r = imp(os.path.join(SRC, 'Audio', f), '/Game/Audio')
            if r and (f.startswith('amb_') or f.startswith('orb_')):
                sp(r[0], looping=True)
                EAL.save_loaded_asset(r[0])
        except Exception as e:
            log('WARN audio', f, e)
    log('audio ok')

    # ---------- materialy ----------
    mb, pl, pq = T['marble_01'], T['plastered_wall_04'], T['herringbone_parquet']
    M = {}
    # lestena mramorova podlaha: nizka drsnost => ostre odrazy
    M['floor'] = pbr('M_Floor', mb[0], mb[1], mb[2], 'xy', 420.0, tint=(0.62, 0.60, 0.58), rough_mul=0.22, rough_add=0.035)
    M['parquet'] = pbr('M_Parquet', pq[0], pq[1], pq[2], 'xy', 260.0, tint=(0.75, 0.62, 0.5), rough_mul=0.45, rough_add=0.05)
    M['wall_x'] = pbr('M_WallX', pl[0], pl[1], pl[2], 'xz', 380.0, tint=(0.40, 0.16, 0.13), rough_mul=1.0)   # tmave cervena galerie
    M['wall_y'] = pbr('M_WallY', pl[0], pl[1], pl[2], 'yz', 380.0, tint=(0.40, 0.16, 0.13), rough_mul=1.0)
    M['ceil'] = pbr('M_Ceil', pl[0], pl[1], pl[2], 'xy', 380.0, tint=(0.85, 0.82, 0.76))
    M['white_x'] = pbr('M_WhiteX', pl[0], pl[1], pl[2], 'xz', 380.0, tint=(0.82, 0.79, 0.73))
    M['dark'] = pbr('M_DarkMarble', mb[0], mb[1], mb[2], 'uv', tiling=(1, 1), tint=(0.24, 0.23, 0.23), rough_mul=0.3, rough_add=0.05)
    M['dark_x'] = pbr('M_DarkMarbleX', mb[0], mb[1], mb[2], 'xz', 300.0, tint=(0.24, 0.23, 0.23), rough_mul=0.3, rough_add=0.05)
    M['dark_y'] = pbr('M_DarkMarbleY', mb[0], mb[1], mb[2], 'yz', 300.0, tint=(0.24, 0.23, 0.23), rough_mul=0.3, rough_add=0.05)
    M['col'] = pbr('M_Column', mb[0], mb[1], mb[2], 'uv', tiling=(2, 3), tint=(0.9, 0.88, 0.84), rough_mul=0.5, rough_add=0.05)
    M['gold'] = pbr('M_Gold', None, None, None, tint=(1.0, 0.72, 0.30), rough_add=0.22, metal=1.0)
    M['iron'] = pbr('M_Iron', None, None, None, tint=(0.03, 0.03, 0.035), rough_add=0.45, metal=1.0)
    M['lamp'] = emissive('M_Lamp', (1.0, 0.78, 0.5), 45.0)
    M['orb'] = emissive('M_Orb', (1.0, 0.62, 0.18), 60.0)
    M['sky'] = emissive('M_Sky', (0.012, 0.02, 0.045), 1.0, two_sided=True)
    M['moon'] = emissive('M_Moon', (0.75, 0.85, 1.0), 14.0)
    log('materials ok')

    CUBE = own_shape('/Engine/BasicShapes/Cube', 'SM_Box')
    CYL = own_shape('/Engine/BasicShapes/Cylinder', 'SM_Cyl')
    SPH = unreal.load_asset('/Engine/BasicShapes/Sphere')

    # ---------- modely (Poly Haven, CC0) ----------
    MODELS = {}

    def model(name):
        try:
            d = os.path.join(SRC, 'Models', name)
            dest = '/Game/Models/' + name
            o = unreal.FbxImportUI()
            sp(o, import_mesh=True, import_textures=False, import_materials=False, import_as_skeletal=False, import_animations=False,
               mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH)
            sp(o.static_mesh_import_data, combine_meshes=True, generate_lightmap_u_vs=True, auto_generate_collision=False)
            res = imp(os.path.join(d, name + '.fbx'), dest, o)
            meshes = [a for a in res if isinstance(a, unreal.StaticMesh)]
            if not meshes:
                # Interchange muze vratit jine cesty - dohledat v cilove slozce
                for p in EAL.list_assets(dest, recursive=True):
                    a = unreal.load_asset(str(p).split('.')[0])
                    if isinstance(a, unreal.StaticMesh):
                        meshes.append(a)
            if not meshes:
                log('WARN model without mesh', name)
                return
            ue = os.path.join(d, 'ue')
            def t(fn, kind):
                p = os.path.join(ue, fn)
                return tex(p, dest, kind) if os.path.exists(p) else None
            mat = pbr('M_' + name, t('Diffuse.jpg', 'c'), t('nor_dx.jpg', 'n'), t('arm.jpg', 'm'), 'uv', use_metal_tex=True)
            canvas = None
            if os.path.exists(os.path.join(ue, 'canvas_diff.jpg')):
                canvas = pbr('M_' + name + '_canvas', t('canvas_diff.jpg', 'c'), t('canvas_nor_dx.jpg', 'n'), None, 'uv', rough_add=0.55)
            for sm in meshes:
                mats = sm.get_editor_property('static_materials')
                for i, s in enumerate(mats):
                    slot = str(s.get_editor_property('material_slot_name')).lower()
                    sm.set_material(i, canvas if (canvas and 'canvas' in slot) else mat)
                sp(sm, light_map_resolution=128)
                EAL.save_loaded_asset(sm)
            MODELS[name] = meshes
            b = meshes[0].get_bounds()
            log('model', name, len(meshes), 'meshes, extent', b.box_extent, 'origin', b.origin)
        except Exception:
            log('WARN model failed', name, traceback.format_exc())

    for n in ('marble_bust_01', 'horse_statue_01', 'gothic_statue', 'brass_vase_01', 'ceramic_vase_01', 'bronze_whale_statue',
              'fancy_picture_frame_01', 'fancy_picture_frame_02', 'painted_wooden_bench', 'Chandelier_01'):
        model(n)

    # ---------- nova mapa ----------
    MAP = '/Game/Maps/Galerie'
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if EAL.does_asset_exist(MAP):
        les.new_level('/Game/Maps/_tmp')
        EAL.delete_asset(MAP)
    les.new_level(MAP)

    def spawn(cls, loc, r=None, label=None, folder=None):
        a = eas.spawn_actor_from_class(cls, V(*loc), r or rot())
        if label:
            a.set_actor_label(label)
        if folder:
            a.set_folder_path(folder)
        return a

    def mesh_actor(mesh, loc, scale=(1, 1, 1), mat=None, lm=64, shadow=True, r=None, label='Mesh', folder='Hall', movable=False):
        a = spawn(unreal.StaticMeshActor, loc, r, label, folder)
        c = a.static_mesh_component
        c.set_static_mesh(mesh)
        a.set_actor_scale3d(V(*scale))
        if mat is not None:
            for i in range(max(1, c.get_num_materials())):
                c.set_material(i, mat)
        sp(c, override_light_map_res=True, overridden_light_map_res=int(lm), cast_shadow=shadow)
        c.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC)
        return a

    def box(center, size, mat, lm=64, shadow=True, label='Box', folder='Hall', r=None):
        return mesh_actor(CUBE, center, (size[0] / 100.0, size[1] / 100.0, size[2] / 100.0), mat, lm, shadow, r, label, folder)

    def place(name, x, y, z_bottom, height, yaw=0.0, lm=128, pitch=0.0, roll=0.0):
        """Model polozeny spodkem na z_bottom, zmenseny na danou vysku."""
        if name not in MODELS:
            return None
        acts = []
        big = max(MODELS[name], key=lambda s: s.get_bounds().box_extent.z)
        b = big.get_bounds()
        s = height / max(1e-3, 2.0 * b.box_extent.z)
        for sm in MODELS[name]:
            a = mesh_actor(sm, (x, y, z_bottom - (b.origin.z - b.box_extent.z) * s), (s, s, s), None, lm, True,
                           rot(pitch, yaw, roll), name, 'Exhibits')
            acts.append(a)
        return acts

    def light(cls, loc, intensity, color, r=None, radius=1200.0, label='Light', static=True, shadows=True, **extra):
        a = spawn(cls, loc, r, label, 'Lights')
        c = a.get_component_by_class(unreal.LightComponent)
        sp(c, intensity_units=unreal.LightUnits.UNITLESS) if not isinstance(a, unreal.DirectionalLight) else None
        sp(c, intensity=float(intensity), light_color=unreal.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255),
           cast_shadows=shadows, **extra)
        if not isinstance(a, unreal.DirectionalLight):
            sp(c, attenuation_radius=float(radius))
        c.set_mobility(unreal.ComponentMobility.STATIC if static else unreal.ComponentMobility.MOVABLE)
        return a

    # ---------- hala ----------
    L, W, H = 3600.0, 1400.0, 640.0
    hx, hy = L / 2, W / 2
    box((0, 0, -15), (L + 60, W + 60, 30), M['floor'], 1024, label='Floor')
    box((0, 0, 0.6), (L - 500, 420, 1.2), M['parquet'], 512, shadow=False, label='ParquetRunner')
    box((0, 0, H + 15), (L + 60, W + 60, 30), M['ceil'], 256, label='Ceiling')
    box((0, -hy - 15, H / 2), (L + 60, 30, H), M['wall_x'], 512, label='WallSouth')
    box((-hx - 15, 0, H / 2), (30, W, H), M['wall_y'], 256, label='WallWest')
    box((hx + 15, 0, H / 2), (30, W, H), M['wall_y'], 256, label='WallEast')
    # severni stena s vysokymi okny
    WIN_X = [-1500, -900, -300, 300, 900, 1500]
    WW, Z0, Z1 = 260.0, 110.0, 560.0
    box((0, hy + 15, Z0 / 2), (L + 60, 30, Z0), M['wall_x'], 256, label='WallNorthSill')
    box((0, hy + 15, (Z1 + H) / 2), (L + 60, 30, H - Z1), M['wall_x'], 256, label='WallNorthTop')
    edges = [-hx - 30] + [e for x in WIN_X for e in (x - WW / 2, x + WW / 2)] + [hx + 30]
    for i in range(0, len(edges), 2):
        a, b = edges[i], edges[i + 1]
        box(((a + b) / 2, hy + 15, (Z0 + Z1) / 2), (b - a, 30, Z1 - Z0), M['wall_x'], 128, label='WallNorthPier')
    for x in WIN_X:
        box((x, hy + 12, (Z0 + Z1) / 2), (7, 7, Z1 - Z0), M['iron'], 32, label='Mullion')
        for k in (1, 2, 3):
            box((x, hy + 12, Z0 + (Z1 - Z0) * k / 4.0), (WW, 7, 7), M['iron'], 32, label='Mullion')
        box((x, hy - 6, Z0 + 3), (WW + 30, 46, 6), M['dark'], 32, label='Sill')
    # sokl, rimsa, zlata lista
    for y, m in ((-hy + 4, M['dark_x']), (hy - 4, M['dark_x'])):
        box((0, y, 14), (L, 8, 28), m, 64, label='Skirting')
    for x in (-hx + 4, hx - 4):
        box((x, 0, 14), (8, W, 28), M['dark_y'], 64, label='Skirting')
    box((0, -hy + 3, 150), (L, 6, 5), M['gold'], 32, shadow=False, label='GoldRail')
    box((0, -hy + 5, H - 34), (L, 10, 8), M['gold'], 32, shadow=False, label='GoldCornice')
    box((0, -hy + 9, H - 14), (L, 18, 28), M['white_x'], 64, label='Cornice')
    # stropni tramy
    for x in range(-1500, 1501, 600):
        box((x, 0, H - 18), (36, W, 36), M['ceil'], 64, label='Beam')

    # sloupy mezi okny, dve rady
    for x in (-1200, -600, 0, 600, 1200):
        for y in (-400, 400):
            box((x, y, 18), (96, 96, 36), M['dark'], 64, label='ColBase')
            mesh_actor(CYL, (x, y, 36 + 277), (0.66, 0.66, 5.54), M['col'], 128, label='Column')
            box((x, y, H - 34), (100, 100, 32), M['col'], 64, label='ColCapital')
            box((x, y, H - 54), (84, 84, 8), M['gold'], 32, shadow=False, label='ColRing')

    # ---------- exponaty u jizni steny ----------
    EX = [(-1500, 'marble_bust_01', 135, 105), (-900, 'brass_vase_01', 105, 105), (-300, 'horse_statue_01', 150, 100),
          (300, 'bronze_whale_statue', 120, 100), (900, 'ceramic_vase_01', 100, 105), (1500, 'gothic_statue', 230, 30)]
    for x, name, h, ped in EX:
        y = -hy + 120
        box((x, y, ped / 2.0), (96, 96, ped), M['dark'], 64, label='Pedestal')
        box((x, y, ped + 2), (104, 104, 4), M['gold'], 32, shadow=False, label='PedestalTrim')
        place(name, x, y, ped + 4, h, yaw=90.0)
        # bodovy reflektor ze stropu + sviticí telo lampy (je videt v odrazech)
        light(unreal.SpotLight, (x, y + 150, H - 60), 42000, (1.0, 0.82, 0.62), rot(pitch=-72, yaw=-90), 950, 'ExhibitSpot',
              inner_cone_angle=14.0, outer_cone_angle=30.0)
        mesh_actor(CYL, (x, y + 150, H - 40), (0.16, 0.16, 0.36), M['iron'], 32, False, label='LampBody')
        mesh_actor(SPH, (x, y + 150, H - 60), (0.11, 0.11, 0.11), M['lamp'], 32, False, label='LampGlow', movable=True)

    # obrazy mezi exponaty
    for i, x in enumerate((-1200, -600, 0, 600, 1200)):
        place('fancy_picture_frame_0%d' % (1 + i % 2), x, -hy + 2, 230, 210, yaw=0.0)
        light(unreal.SpotLight, (x, -hy + 190, H - 60), 24000, (1.0, 0.86, 0.7), rot(pitch=-58, yaw=-90), 800, 'PictureSpot',
              inner_cone_angle=16.0, outer_cone_angle=34.0)
        mesh_actor(SPH, (x, -hy + 190, H - 60), (0.09, 0.09, 0.09), M['lamp'], 32, False, label='LampGlow', movable=True)

    # lavice a lustry v ose haly
    for x in (-750, 750):
        place('painted_wooden_bench', x, 0, 1.2, 118, yaw=0.0)
    for x in (-1050, 0, 1050):
        if place('Chandelier_01', x, 0, H - 190, 190) is None:
            mesh_actor(SPH, (x, 0, H - 120), (0.5, 0.5, 0.5), M['lamp'], 32, False, label='LampGlobe', movable=True)
        light(unreal.PointLight, (x, 0, H - 210), 15000, (1.0, 0.74, 0.46), None, 1500, 'ChandelierLight', source_radius=20.0)
        mesh_actor(SPH, (x, 0, H - 150), (0.14, 0.14, 0.14), M['lamp'], 32, False, label='ChandelierGlow', movable=True)

    # ---------- venek: mesic, obloha, blesky ----------
    mesh_actor(SPH, (0, 0, 0), (700, 700, 700), M['sky'], 32, False, label='SkyDome', folder='Outside', movable=True)
    mesh_actor(SPH, (5000, 16000, 12500), (9, 9, 9), M['moon'], 32, False, label='Moon', folder='Outside', movable=True)
    light(unreal.DirectionalLight, (0, 1500, 1500), 5.0, (0.55, 0.70, 1.0), rot(pitch=-37, yaw=-107), label='Moonlight',
          light_source_angle=1.2)
    sky = spawn(unreal.SkyLight, (0, 0, 900), None, 'SkyLight', 'Lights')
    sc = sky.get_component_by_class(unreal.SkyLightComponent)
    try:
        hdr = imp(os.path.join(SRC, 'HDRI', 'moonlit_golf.hdr'), '/Game/Tex')
        cube = [a for a in hdr if isinstance(a, unreal.TextureCube)]
        if cube:
            sp(sc, source_type=unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP, cubemap=cube[0])
    except Exception as e:
        log('WARN hdri', e)
    sp(sc, intensity=1.2, light_color=unreal.Color(170, 200, 255, 255))
    sc.set_mobility(unreal.ComponentMobility.STATIC)
    for x in (-1200, 0, 1200):
        a = light(unreal.PointLight, (x, hy + 420, 520), 0.0, (0.75, 0.85, 1.0), None, 3600, 'Lightning', static=False, shadows=True)
        sp(a, tags=[unreal.Name('Lightning')])

    # ---------- odrazy ----------
    for x in (-1350, -450, 450, 1350):
        rc = spawn(unreal.SphereReflectionCapture, (x, 0, 260), None, 'ReflectionCapture', 'Reflections')
        c = rc.get_component_by_class(unreal.SphereReflectionCaptureComponent)
        if c:
            sp(c, influence_radius=1100.0)
    try:
        pr = spawn(unreal.PlanarReflection, (0, 0, 1.5), None, 'FloorMirror', 'Reflections')
        pr.set_actor_scale3d(V(L / 200.0 + 2, W / 200.0 + 2, 1))
        c = pr.get_component_by_class(unreal.PlanarReflectionComponent)
        if c:
            sp(c, screen_percentage=60.0, prefilter_roughness=0.02, normal_distortion_strength=120.0,
               distance_from_plane_fadeout_start=40.0, distance_from_plane_fadeout_end=80.0)
    except Exception as e:
        log('WARN planar reflection', e)

    # ---------- postprocess ----------
    ppv = spawn(unreal.PostProcessVolume, (0, 0, 200), None, 'PostProcess', 'Lights')
    sp(ppv, unbound=True)
    s = ppv.get_editor_property('settings')
    PP = dict(auto_exposure_method=unreal.AutoExposureMethod.AEM_MANUAL, auto_exposure_bias=float(os.environ.get('GALERIE_EV', '1.0')),
              auto_exposure_apply_physical_camera_exposure=False,
              bloom_intensity=0.9, bloom_threshold=-1.0, vignette_intensity=0.55,
              screen_space_reflection_intensity=100.0, screen_space_reflection_quality=80.0, screen_space_reflection_max_roughness=0.6,
              ambient_occlusion_intensity=0.6, ambient_occlusion_radius=120.0,
              film_grain_intensity=0.12, scene_fringe_intensity=0.35,
              color_saturation=unreal.Vector4(1.04, 1.02, 1.0, 1.0), color_contrast=unreal.Vector4(1.06, 1.06, 1.06, 1.0),
              film_toe=0.6, lens_flare_intensity=0.15, motion_blur_amount=0.0)
    for k, v in PP.items():
        try:
            s.set_editor_property('override_' + k, True)
            s.set_editor_property(k, v)
        except Exception as e:
            log('WARN pp', k, e)
    sp(ppv, settings=s)

    # ---------- start hrace a znacky svetel ----------
    spawn(unreal.PlayerStart, (-1620, 0, 110), rot(yaw=0), 'PlayerStart', 'Game')
    for i, (x, y, z) in enumerate([(-1200, -470, 135), (0, -470, 135), (1200, -470, 135), (-900, 560, 150), (300, 560, 150),
                                   (1500, 540, 150), (-300, 0, 135), (900, 130, 135), (1640, -140, 135)]):
        spawn(unreal.TargetPoint, (x, y, z), None, 'OrbSpot%d' % i, 'Game')

    # ---------- nastaveni sveta ----------
    try:
        ws = unreal.EditorLevelLibrary.get_editor_world().get_world_settings()
        lm = ws.get_editor_property('lightmass_settings')
        sp(lm, num_indirect_lighting_bounces=6, indirect_lighting_quality=2.0, indirect_lighting_smoothness=0.8,
           static_lighting_level_scale=0.6, diffuse_boost=1.15)
        sp(ws, lightmass_settings=lm, force_no_precomputed_lighting=False)
    except Exception as e:
        log('WARN world settings', e)

    les.save_current_level()
    log('LEVEL DONE, actors:', len(eas.get_all_level_actors()))


try:
    main()
except Exception:
    log('FATAL', traceback.format_exc())
if QUIT:
    unreal.SystemLibrary.quit_editor()
