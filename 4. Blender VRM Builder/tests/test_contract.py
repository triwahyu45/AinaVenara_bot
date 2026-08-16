from pathlib import Path


ROOT = Path(__file__).parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_builder_uses_direct_vrm_import_and_export():
    source = read("scripts/build_aina_v1.py")
    assert "bpy.ops.import_scene.vrm" in source
    assert "bpy.ops.export_scene.vrm" in source
    assert "sys.argv" in source


def test_seed_san_is_rejected():
    assert "Seed-san ditolak" in read("build_aina_v1.ps1")
    assert "seed-san" in read("scripts/build_aina_v1.py").lower()


def test_generated_assets_are_ignored():
    ignored = read(".gitignore").splitlines()
    assert "downloads/" in ignored
    assert "output/" in ignored
    assert "work/" in ignored


def test_setup_uses_official_repository():
    source = read("setup_vrm_addon.ps1")
    assert "saturday06/VRM-Addon-for-Blender" in source
    assert "VRM_Addon_for_Blender-Extension-*.zip" in source
    assert "extensions\\user_default" in source
    assert "check_vrm_addon.py" in source


def test_builder_has_required_aina_features():
    source = read("scripts/build_aina_v1.py")
    for feature in ("Aina_Hair_Cap", "Aina_Hair_Bob", "Aina_Hair_Tip", "Aina_Ahoge", "Aina_Glasses", "Aina_Hairclip", "Aina_Hoodie", "Aina_InnerShirt", "Aina_CamisoleStrap", "Aina_Shorts", "Aina_Sock", "Aina_Sneaker"):
        assert feature in source
    assert "Aina_SilverMetal" in source
    assert "strip_base_costume_geometry" in source


def test_validator_rejects_robot_artifacts():
    source = read("scripts/validate_output.py")
    for marker in ("robo", "robot", "backpack", "armgear"):
        assert marker in source
    for marker in ("bottoms", "shoes", "tops", "hairback"):
        assert marker in source
    assert "expression_keys" in source


def test_preview_contains_six_views():
    source = read("scripts/render_previews.py")
    for view in ("front", "left", "right", "back", "face", "top"):
        assert f'"{view}"' in source


def test_fit_renderer_uses_orthographic_camera_and_bounded_params():
    source = read("scripts/render_fit_views.py")
    assert 'scene.camera.data.type = "ORTHO"' in source
    for feature in ("hair_scale", "hoodie_width", "head_width", "body_width", "glasses_scale", "Aina_FitFaceCorrective"):
        assert feature in source


def test_fitter_writes_overlay_diff_metrics_and_best_candidate():
    source = read("scripts/fit_model.py")
    for feature in ("save_overlay", "save_edge_diff", "metrics.json", "best_candidate.json", "overlay_contact_sheet.png"):
        assert feature in source


def test_fitter_exports_and_reimports_best_candidate():
    source = read("scripts/fit_model.py")
    assert "export_fit_candidate.py" in source
    assert "validate_output.py" in source
    assert "Aina_Venara_fitted.vrm" in source
