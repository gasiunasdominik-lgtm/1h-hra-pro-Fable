"""Zapne u vsech materialu hry pouziti se statickym (zapecenym) osvetlenim - bez prestavby mapy a noveho baku."""
import unreal
EAL = unreal.EditorAssetLibrary
n = 0
for p in EAL.list_assets('/Game/Mat', recursive=True):
    m = unreal.load_asset(str(p).split('.')[0])
    if isinstance(m, unreal.Material):
        m.set_editor_property('used_with_static_lighting', True)
        unreal.MaterialEditingLibrary.recompile_material(m)
        EAL.save_loaded_asset(m)
        n += 1
unreal.log('[GALERIE] FIXED materials: %d' % n)
unreal.SystemLibrary.quit_editor()
