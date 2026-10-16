"""Compile production stock-native UI against a synthetic SDK constructor.

No installed asset, game process, real user database or game allocator is used.
This is offline candidate evidence; earlier synthetic coverage missed a real
native-constructor crash and does not establish real-engine UI compatibility.
"""
from __future__ import annotations
import hashlib
import json
import copy
import re
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "sc1/native_campaign/plugin"
ASSETS = Path(__file__).resolve().parent
SOURCES = [PLUGIN / "dialog_ui.cpp", PLUGIN / "dialog_ui.h",
           PLUGIN / "include/dialog_x64.h", PLUGIN / "dialog_ui_tests.cpp",
           ASSETS / "plain_panel_templates.generated.h",
           ASSETS / "stock_gamemenu.ui.json", ASSETS / "stock_gamemenusocial.ui.json",
           ASSETS / "stock_UISchema.json", ASSETS / "plain_gamemenu.ui.json",
           ASSETS / "plain_gamemenusocial.ui.json"]


def hashes():
    return {str(path.relative_to(ROOT)).replace("\\", "/"):
            hashlib.sha256(path.read_bytes()).hexdigest() for path in SOURCES}


def verify_constructor_assets():
    schema = json.loads((ASSETS / "stock_UISchema.json").read_bytes())
    child_schema = schema["properties"]["children"]["items"]["properties"]
    types = child_schema["type"]["enum"]
    flags = child_schema["flags"]["items"]["enum"]
    templates = dict(re.findall(r'inline constexpr char (normal|social)\[\] = R"SC1\((.*?)\)SC1";',
                               (ASSETS / "plain_panel_templates.generated.h").read_text(encoding="utf-8")))
    checks = 0
    for filename, symbol in (("gamemenu.ui.json", "normal"), ("gamemenusocial.ui.json", "social")):
        stock = json.loads((ASSETS / ("stock_" + filename)).read_bytes())
        plain = json.loads((ASSETS / ("plain_" + filename)).read_bytes())
        expected = copy.deepcopy(stock)
        for control in expected["children"]:
            slot = [1, 2, 3, 5]
            if control["id"] == -1:
                control["rect"] = [8, 8, 248, 208]
                control["content"] = "SC1_NATIVE_CHOICE_BODY"
            elif control["id"] in slot:
                control["rect"] = [20 + 56 * slot.index(control["id"]), 220, 48, 28]
            elif control["id"] == -3:
                control["rect"] = [20, 252, 224, 28]
        assert plain == expected, "Only declared header content/rect and number/confirm rect may differ"
        assert json.loads(templates[symbol]) == plain, "Compiled embedded template differs from validated asset"
        assert plain["type"] == "DIALOG" and plain["name"] == "GameMenu"
        assert plain["rect"] == stock["rect"] and plain["style"] == stock["style"]
        checks += 4
        for control in plain["children"]:
            assert control["type"] in types and isinstance(control["content"], str)
            assert all(flag in flags for flag in control["flags"])
            assert len(control["rect"]) == 4 and control["rect"][2] > 0 and control["rect"][3] > 0
            assert control["children"] is None
            checks += 4
        body = next(c for c in plain["children"] if c["id"] == -1)
        assert body["type"] == "CTEXT" and "WS_HOTKEY" not in body["flags"]
        assert body["rect"][0] + body["rect"][2] <= plain["rect"][2]
        assert body["rect"][1] + body["rect"][3] <= plain["rect"][3]
        for slot in [1, 2, 3, 5, -3]:
            button = next(c for c in plain["children"] if c["id"] == slot)
            x, y, w, h = button["rect"]
            assert x >= 0 and y >= 216 and x + w <= plain["rect"][2] and y + h <= plain["rect"][3]
            checks += 1
        checks += 3
    return checks


def main():
    before = hashes()
    asset_checks = verify_constructor_assets()
    vcvars = Path("C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat")
    if not vcvars.is_file():
        raise FileNotFoundError(vcvars)
    with tempfile.TemporaryDirectory(prefix="sc1-stock-native-ui-") as folder:
        temporary = Path(folder)
        # No NOMINMAX workaround: production TU itself must compile correctly.
        compiler = ["cl", "/nologo", "/std:c++17", "/EHsc", "/utf-8", "/W4", "/WX", "/O2",
                    str(PLUGIN / "dialog_ui_tests.cpp"), str(PLUGIN / "dialog_ui.cpp"),
                    "/Fo:.\\", "/Fe:dialog_ui_tests.exe"]
        script = temporary / "compile.bat"
        script.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\n' +
                          subprocess.list2cmdline(compiler) + "\n", encoding="utf-8")
        build = subprocess.run(["cmd", "/d", "/c", str(script)], cwd=temporary,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
        if build.returncode:
            raise RuntimeError(build.stdout + build.stderr)
        executable = temporary / "dialog_ui_tests.exe"
        run = subprocess.run([str(executable)], cwd=temporary,
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        if run.returncode:
            raise RuntimeError(run.stdout + run.stderr)
        native = json.loads(run.stdout)
        executable_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
        regression = subprocess.run([str(executable), "native_metadata"], cwd=temporary,
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
        if regression.returncode:
            raise RuntimeError(regression.stdout + regression.stderr)
        current_regression = json.loads(regression.stdout)
        # Mutate only the guard in a temporary source copy; real TU/DLL/game/DB
        # remain unchanged. The same live-metadata regression must fail there.
        source = (PLUGIN / "dialog_ui.cpp").read_text(encoding="utf-8")
        definitions = ("    const bool sized=title->image.width>=248 && title->image.height>=208;\n"
                       "    const bool empty=!title->image.data && !title->image.width && !title->image.height;\n")
        assert definitions in source and source.count("|| (!sized && !empty)") == 1
        source = source.replace(definitions, "").replace("|| (!sized && !empty)",
                 "|| (title->image.data ? (title->image.width<248 || title->image.height<208) : (title->image.width!=0 || title->image.height!=0))")
        mutant = temporary / "mutant_dialog_ui.cpp"
        mutant.write_text(source, encoding="utf-8")
        old_compiler = ["cl", "/nologo", "/std:c++17", "/EHsc", "/utf-8", "/W4", "/WX", "/O2",
                        "/I" + str(PLUGIN), str(PLUGIN / "dialog_ui_tests.cpp"), str(mutant),
                        "/Fo:.\\", "/Fe:mutant_ui_tests.exe"]
        script.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\n' +
                          subprocess.list2cmdline(old_compiler) + "\n", encoding="utf-8")
        old_build = subprocess.run(["cmd", "/d", "/c", str(script)], cwd=temporary,
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
        if old_build.returncode:
            raise RuntimeError(old_build.stdout + old_build.stderr)
        old_run = subprocess.run([str(temporary / "mutant_ui_tests.exe"), "native_metadata"], cwd=temporary,
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")
        expected_failure = "observed native232-capacity/null-data/sized metadata keeps reward menu open"
        assert old_run.returncode != 0 and expected_failure in old_run.stderr, "Old guard did not reproduce the live metadata failure"
        metadata_regression = {"current_passed": current_regression["passed"],
                               "current_assertions": current_regression["assertions"],
                               "old_guard_expected_failure": True, "old_guard_exit_code": old_run.returncode,
                               "old_guard_stderr": old_run.stderr.strip(),
                               "scope": "Temporary source copy/SDK executable only; actual production source unchanged"}
    assert before == hashes(), "Production/test sources changed during verification"
    receipt = {
        "schema_version": 7,
        "passed": bool(native["passed"]),
        "status": "native_spawn_resume_lifetime_fix_offline_verified_live_retest_pending",
        "cpp_groups": native["groups"], "cpp_assertions": native["assertions"],
        "constructor_asset_assertions": asset_checks,
        "assertions_total": native["assertions"] + asset_checks,
        "metadata_regression": metadata_regression,
        "spawn_lifetime_regression": {
            "case": "spawn_no_delete",
            "three_talent_curse_pairs_without_delete": True,
            "reused_native_address_rebound": True,
            "all_native_delegates_restored_before_resume": True,
            "closing_nested_pump_skips_native_widgets": True,
            "epoch_reset_and_poisoned_widgets_detach_safely": True,
            "synchronous_delete_and_Run_return_preserved": True,
            "native_widget_access_after_resume_return": 0
        },
        "phase_body_budget": {"distinct_talent_combinations_audited": 2380,
                              "talent_intro_utf8_min": 179, "talent_intro_utf8_max": 253,
                              "curse_intro_utf8": 165, "detail_utf8_conservative_max": 84,
                              "observed_native_capacity": 232,
                              "scope": "Frozen17talents/3curses, same-phase talent-to-curse; selected detail and curse introduction both fit even the smallest first talent intro"},
        "source_sha256": before, "source_unchanged_during_verification": True,
        "synthetic_executable_sha256": executable_hash,
        "compiler": "MSVC x64 /std:c++17 /W4 /WX /O2 /utf-8, no warning workaround",
        "reproduce": "python -B sc1/native_campaign/dialog_assets/verify_dialog_ui.py",
        "custom_json_override": True,
        "custom_menu_json": True,
        "native_upper_text_control": True,
        "choice_number_buttons": True,
        "file_read_hooks_registered": 2,
        "game_string_allocations": 0,
        "deployed_ui_assets": [],
        "embedded_template_source": "sc1/native_campaign/dialog_assets/plain_panel_templates.generated.h",
        "source_asset_mirrors": ["stock_gamemenu.ui.json", "stock_gamemenusocial.ui.json", "stock_UISchema.json", "plain_gamemenu.ui.json", "plain_gamemenusocial.ui.json"],
        "actual_game_accessed": False, "user_database_accessed": False,
        "installed_assets_modified": False,
        "extra_deployed_ui_asset_required": False,
        "frozen_information": {
            "talents": 17, "curses": 3, "maximum_full_utf8_bytes": 77,
            "text_control_id": -1, "text_control_type": "CTEXT",
            "button_explanation_controls": [],
            "native_body": "Meaningful stage/instruction plus current candidate names and rarities supplied to native JSON constructor. Full selected name/rarity/effect copied into that original native allocation; insufficient capacity blocks confirmation.",
            "number_buttons": [1, 2, 3, 5], "explicit_confirmation_id": -3,
            "capacity_semantics": "payload bytes plus separate NUL; original data/capacity/ownership remain native"
        },
        "verified": [
            "Exact API44 void file-prefix registration and Run/Spawn/ProcessEvents79/LayoutDrawText signatures",
            "Only title content/rectangle, number-button rectangles and confirm rectangle differ from read-only stock GameMenu/Social assets",
            "Original root style/size, child IDs/order/types/flags and non-title localization keys retained",
            "Native schema type/flag enums, positive rectangles, body and number/confirm bounds; embedded source exactly matches validated template mirrors",
            "Pending validated same-thread session replaces only the two original menu filenames; no-offer/inactive/foreign/other-file/already-modal reads preserve original file and out-size",
            "Meaningful full current candidate names/rarities/instruction in each generated JSON are longer than corresponding full details; no space padding",
            "Documented MTL process-heap allocation used only for file payload; no game string allocator, constructor replay, post-init type or Surface change",
            "Actual synthetic native CTEXT buffer contains complete full name/rarity/effect without renderer dependence",
            "Explanation buttons6/8/9 and unused native actions remain hidden; lower choices contain short ASCII numbers only",
            "Insufficient native body storage or stale stock title geometry cannot submit and dismisses through original Resume",
            "Post-constructor storage geometry/capacity and actual full_write result logged on UI thread",
            "Actual232-byte capacity/null image data/248x208 native metadata regression stays open, displays full talent/curse bodies and closes only after snapshot",
            "Temporary-copy old guard fails the same native metadata regression; partial/undersized or nonempty zero metadata remains rejected",
            "Original constructor and handlers finish before binding; every area/flag restores before original Resume/init/delete",
            "Only explicit matching confirmation submits; preview changes no durable record and waiting ACK blocks duplicate selection",
            "Spawn Resume restores every root/child delegate and layout before original-3, then drops only owned menu state even without root delete1",
            "Three no-delete Spawn pairs reopen at the same native address; global epoch reset plus poisoned returned widgets remains safe",
            "Closing nested ProcessEvents polls protocol without native bind/refresh/repeated Resume; Run detaches on original loop return",
            "Three checkpoint pairs, legacy compatibility, deferred publication close, stock modal arrival, automatic HUD same-thread lifecycle and nested paused polling",
            "Renderer immutable snapshots, exact/owned-prefix matching, unchanged original8args/result, suffix lifetime, foreign thread without native/API/report access",
            "Bounded renderer atomics sampled once by UI owner; unknown offsets and unrelated input retain original drawing"
        ],
        "not_verified": [
            "Literal UTF8 content is retained rather than treated as a missing localization key by the actual native constructor; schema permits display strings but no exact engine fallback implementation was found",
            "Actual CTEXT long text line wrapping and clean appearance after accepting the observed sized/null metadata",
            "Native initialization may draw original extra buttons before the post-construction binding hides them",
            "Actual localized native BwString capacity is sufficient after native GameMenu initialization; capacity/full_write diagnostics have not run live for this candidate",
            "Actual48px numeric button skin and current child activation dispatch",
            "GameMenu LayoutDrawText exact/reserved-prefix alias on the live build; full native body copying no longer depends on it",
            "Post-ProcessEvents is not a published Run construction completion guarantee; guarded native init/list/callback validation remains a candidate boundary",
            "Exact cause of the previous execute-AV at0xfffffffbfffffffb"
        ],
        "latest_live_observation": {
            "build": "04cd9842c8d7c16d7825d1c07facf2ddaeea11aadf0059fcbe9b1fc829930e9c",
            "source": "Root inspected actual GameMenu screenshot; this UI agent accessed no game process or inputs.",
            "automatic_popup_observed": True, "actual_screenshot_observed": True,
            "visual_pass": False,
            "symptoms": ["CTEXT title began correctly", "PUSHBUTTON explanation/candidate labels lost their first Korean glyph and were truncated", "Backed-title fallback had button borders"],
            "candidate_response": "Remove all button explanation rows; declare a real large CTEXT before native construction; display only ASCII numbers on choice buttons.",
            "new_candidate_live_visual_verified": False
        },
        "previous_model_limit": "Synthetic JSON/menu tests missed a native constructor crash and exact-pointer renderer tests missed04cd visual failure. Current success proves offline contracts, not live appearance.",
        "runtime_layout": {
            "root_minimum": [264, 288], "root_size_changed": False,
            "constructor_body_xywh": [8, 8, 248, 208],
            "body_rectangle_inclusive": [8, 8, 255, 215],
            "body_surface_guard": "At least248x208 metadata regardless of image.data, or null/zero metadata. No image.data dereference, allocation, resize or ownership change.",
            "candidate_ids": [1, 2, 3, 5], "candidate_x": [20, 76, 132, 188],
            "candidate_y": 220, "candidate_size": [48, 28],
            "confirm_id": -3, "confirm_xywh": [20, 252, 224, 28],
            "unused_hidden_ids": [4, 6, 7, 8, 9],
            "post_constructor_rectangle_changes": 0,
            "post_constructor_type_or_surface_changes": 0,
            "plugin_surface_allocations": 0, "new_widget_ids_or_types": 0,
            "restore_before": ["native Resume", "native init0/init7", "native delete1"]
        },
        "file_payload_contract": {
            "scope": "Validated active pending owner-thread offer, menu not open, native Run depth0; only rez/gamemenu.ui.json and rez/gamemenusocial.ui.json",
            "ownership": "HeapAlloc(GetProcessHeap(),0,payload_length), exact bytes/out_size; published MTL file-hook pattern. Native parser owns resulting widget/string/Surface memory independently.",
            "unknown_or_unowned": "Return null with original out_size unchanged",
            "literal_limit": "Native UTF8 literal/localization resolution remains live-unverified; no guessed native allocation fallback"
        },
        "latest_runtime_failure": {
            "log_backup": "sc1/backups/popup_disappears_20261015_020907/sc1_native.log",
            "observed_at_local": ["2026-10-15 02:04:33", "2026-10-15 02:05:22", "2026-10-15 02:05:29", "2026-10-15 02:05:42"],
            "native_ctext": {"capacity": 232, "length": 232, "rect": [8,8,255,215], "metadata": [248,208], "data_null": True},
            "cause": "Old arrange_menu falsely required width/height0 whenever image.data was null. It rejected the native descriptor before any body write; the generic text-capacity message hid that layout failure.",
            "fix": "Accept the observed native sized/null descriptor without modifying any native metadata; keep exact constructor rectangles and minimum valid dimensions.",
            "new_candidate_live_verified": False
        },
        "spawn_lifetime_boundary": {
            "source_issue": "Previously Spawn menu_ cleared only on hooked root delete1 or owned Run return. A native close lacking those callbacks could retain open=true and block later phase gates.",
            "live_status": "44f2 phase1 talent/curse and DAT snapshot succeeded. Live menu/closing fields were unavailable after the user closed the game; actual residue was not directly observed.",
            "log_backup": "sc1/backups/phase_milestone_20261015_023204/sc1_native.log",
            "fix": "Restore original delegates/layout while live, activate original-3, then compare captured menu and captured owned menu_epoch using own fields only. Spawn detaches on return; Run keeps original-loop return lifetime.",
            "independent_core_issue": "Root owns completed-unit count extended-array8 fix; it independently blocked the phase milestone and is outside this UI component."
        },
        "render_contract": {
            "registration": "API44 hook_layout_draw_text only during plugin initialization",
            "key": "Immutable native string.data and one-byte reserved-prefix body address for owned WS_HOTKEY controls",
            "hotkey_prefix": "ASCII blank in original short numeric/confirmation allocation; exact replacement retains blank, offset1 begins at content",
            "body": "Actual full native CTEXT bytes are the primary display; immutable fulltext substitution is auxiliary",
            "text_lifetime": "Atomic shared snapshots, TLS returned lease and immutable interned strings until DLL destruction",
            "return": "Original pointer returned verbatim including continuation suffix",
            "fallback": "Other addresses preserve all8args/result without text/native pointer reads",
            "render_thread_game_or_ui_api_calls": 0,
            "native_string_descriptor_replaced": False,
            "renderer_match_logging": True,
            "diagnostics": "Atomic calls/exact/hotkey_offset/near_miss and first offset/scalars; one owner-thread log per popup after1000ms",
            "raw_pointer_logging": False, "live_match_verified": False
        },
        "integration_receipt": "sc1/native_campaign/plugin/dialog_protocol_verification.json",
        "research_receipt": "sc1/campaign/ingame_native_dialog_research.json"
    }
    (ASSETS / "dialog_ui_verification.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": receipt["passed"], "groups": native["groups"],
                      "assertions_total": receipt["assertions_total"], "source_sha256": before}, ensure_ascii=False))


if __name__ == "__main__":
    main()
