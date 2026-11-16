"""Vypne kolize u dekoraci, ktere nemaji hrace blokovat (kupole oblohy, mesic, zarici koule lamp).
Uprava kolizi nerusi zapecene svetlo, takze neni potreba novy bake."""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level('/Game/Maps/Galerie')
n = 0
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if any(lab.startswith(p) for p in ('SkyDome', 'Moon', 'LampGlow', 'ChandelierGlow', 'LampGlobe', 'LampBody', 'ParquetRunner')):
        a.set_actor_enable_collision(False)
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if c:
            c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        n += 1
les.save_current_level()
unreal.log('[GALERIE] collision off on %d actors' % n)
unreal.SystemLibrary.quit_editor()
