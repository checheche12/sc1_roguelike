#pragma once
// C ABI adaptation of neivv/samase_plugin API44.
// Source commit c01a88f00b1aaf6286f96940b0f04498cea6c7b7, src/lib.rs.
// Every field retained in source order; unused function signatures are never called.
#include <cstdint>
#include <cstddef>
namespace samase {
using GenericFn = void (__cdecl*)();
using SetSaveData = void (__cdecl*)(const std::uint8_t*,std::size_t);
using SaveHook = void (__cdecl*)(SetSaveData);
using LoadHook = std::uint32_t (__cdecl*)(const std::uint8_t*,std::size_t);
struct ExtendedArray { std::uint8_t* pointer; std::uint8_t* end; std::size_t unused,unused2; };
struct PluginApi {
    std::uint16_t version, max_func_id;
    void (__cdecl* free_memory)(std::uint8_t*);
    GenericFn write_exe_memory;
    GenericFn warn_unsupported_feature;
    GenericFn read_file;
    GenericFn (__cdecl* game)();
    GenericFn rng_seed;
    std::uint32_t (__cdecl* hook_step_objects)(GenericFn,std::uint32_t);
    GenericFn hook_aiscript_opcode;
    GenericFn ai_regions;
    GenericFn player_ai;
    GenericFn get_region;
    GenericFn change_ai_region_state;
    GenericFn (__cdecl* first_active_unit)();
    GenericFn (__cdecl* first_hidden_unit)();
    GenericFn (__cdecl* issue_order)();
    GenericFn (__cdecl* print_text)();
    GenericFn hook_on_first_file_access;
    GenericFn hook_step_order;
    GenericFn hook_step_order_hidden;
    GenericFn dat;
    GenericFn hook_process_commands;
    GenericFn hook_process_lobby_commands;
    GenericFn hook_send_command;
    GenericFn hook_step_secondary_order;
    std::uint32_t (__cdecl* extend_save)(const std::uint8_t*,SaveHook,LoadHook,GenericFn);
    GenericFn hook_ingame_command;
    GenericFn units;
    GenericFn selections;
    GenericFn first_ai_script;
    GenericFn hook_game_screen_rclick;
    GenericFn client_selection;
    GenericFn dat_requirements;
    GenericFn first_guard_ai;
    GenericFn pathing;
    GenericFn set_first_ai_script;
    GenericFn first_free_ai_script;
    GenericFn set_first_free_ai_script;
    GenericFn player_ai_towns;
    GenericFn map_tile_flags;
    GenericFn players;
    GenericFn hook_draw_image;
    GenericFn hook_renderer;
    GenericFn get_iscript_bin;
    GenericFn set_iscript_bin;
    GenericFn hook_iscript_opcode;
    GenericFn sprite_hlines;
    GenericFn sprite_hlines_end;
    GenericFn hook_file_read;
    GenericFn first_active_bullet;
    GenericFn first_lone_sprite;
    GenericFn add_overlay_iscript;
    GenericFn set_campaigns;
    GenericFn hook_run_dialog;
    GenericFn send_command;
    GenericFn ai_update_attack_target;
    GenericFn update_visibility_point;
    GenericFn create_lone_sprite;
    GenericFn step_iscript;
    GenericFn is_outside_game_screen;
    GenericFn screen_pos;
    GenericFn ui_scale;
    GenericFn first_fow_sprite;
    GenericFn (__cdecl* is_replay)();
    GenericFn local_player_id;
    GenericFn (__cdecl* unit_array_len)();
    GenericFn draw_cursor_marker;
    GenericFn hook_spawn_dialog;
    GenericFn misc_ui_state;
    GenericFn create_bullet;
    GenericFn hook_create_bullet;
    GenericFn (__cdecl* create_unit)();
    GenericFn hook_create_unit;
    GenericFn (__cdecl* finish_unit_pre)();
    GenericFn (__cdecl* finish_unit_post)();
    GenericFn get_sprite_position;
    GenericFn set_sprite_position;
    std::uint32_t (__cdecl* hook_init_units)(void (__cdecl*)(GenericFn));
    GenericFn get_tooltip_draw_func;
    GenericFn set_tooltip_draw_func;
    GenericFn hook_layout_draw_text;
    GenericFn hook_draw_graphic_layers;
    GenericFn graphic_layers;
    GenericFn set_prism_shaders;
    GenericFn crash_with_message;
    GenericFn ai_attack_prepare;
    GenericFn hook_ai_step_region;
    std::size_t (__cdecl* extended_arrays)(ExtendedArray**);
    GenericFn (__cdecl* extended_dat)(std::uint32_t);
    GenericFn give_ai;
    GenericFn hook_play_sound;
    GenericFn (__cdecl* is_multiplayer)();
    GenericFn hook_game_loop_start;
    GenericFn active_iscript_objects;
    GenericFn hook_ai_focus_disabled;
    GenericFn hook_ai_focus_air;
    GenericFn unit_base_strength;
    GenericFn (__cdecl* read_map_file)();
    GenericFn hook_func;
    GenericFn (__cdecl* get_func)(std::uint16_t);
    void (__cdecl* load_vars)(const std::uint16_t*,std::uint8_t*,std::size_t);
    void (__cdecl* read_vars)(const std::uint16_t*,std::size_t*,std::size_t);
    GenericFn write_vars;
    GenericFn debug_ui_add_tab;
    GenericFn debug_ui_add_log;
    GenericFn debug_log_add_data;
    GenericFn debug_log_clear;
    GenericFn create_extended_unit_field;
    GenericFn read_extended_unit_field;
    GenericFn write_extended_unit_field;
    void* (__cdecl* mutate_dat)(std::uint32_t,std::uint32_t);
};
static_assert(sizeof(void*)==8,"This plugin requires x64");
static_assert(offsetof(PluginApi,free_memory)==8,"API44 free_memory ABI");
static_assert(offsetof(PluginApi,write_exe_memory)==16,"API44 write_exe_memory ABI");
static_assert(offsetof(PluginApi,warn_unsupported_feature)==24,"API44 warn_unsupported_feature ABI");
static_assert(offsetof(PluginApi,read_file)==32,"API44 read_file ABI");
static_assert(offsetof(PluginApi,game)==40,"API44 game ABI");
static_assert(offsetof(PluginApi,rng_seed)==48,"API44 rng_seed ABI");
static_assert(offsetof(PluginApi,hook_step_objects)==56,"API44 hook_step_objects ABI");
static_assert(offsetof(PluginApi,hook_aiscript_opcode)==64,"API44 hook_aiscript_opcode ABI");
static_assert(offsetof(PluginApi,ai_regions)==72,"API44 ai_regions ABI");
static_assert(offsetof(PluginApi,player_ai)==80,"API44 player_ai ABI");
static_assert(offsetof(PluginApi,get_region)==88,"API44 get_region ABI");
static_assert(offsetof(PluginApi,change_ai_region_state)==96,"API44 change_ai_region_state ABI");
static_assert(offsetof(PluginApi,first_active_unit)==104,"API44 first_active_unit ABI");
static_assert(offsetof(PluginApi,first_hidden_unit)==112,"API44 first_hidden_unit ABI");
static_assert(offsetof(PluginApi,issue_order)==120,"API44 issue_order ABI");
static_assert(offsetof(PluginApi,print_text)==128,"API44 print_text ABI");
static_assert(offsetof(PluginApi,hook_on_first_file_access)==136,"API44 hook_on_first_file_access ABI");
static_assert(offsetof(PluginApi,hook_step_order)==144,"API44 hook_step_order ABI");
static_assert(offsetof(PluginApi,hook_step_order_hidden)==152,"API44 hook_step_order_hidden ABI");
static_assert(offsetof(PluginApi,dat)==160,"API44 dat ABI");
static_assert(offsetof(PluginApi,hook_process_commands)==168,"API44 hook_process_commands ABI");
static_assert(offsetof(PluginApi,hook_process_lobby_commands)==176,"API44 hook_process_lobby_commands ABI");
static_assert(offsetof(PluginApi,hook_send_command)==184,"API44 hook_send_command ABI");
static_assert(offsetof(PluginApi,hook_step_secondary_order)==192,"API44 hook_step_secondary_order ABI");
static_assert(offsetof(PluginApi,extend_save)==200,"API44 extend_save ABI");
static_assert(offsetof(PluginApi,hook_ingame_command)==208,"API44 hook_ingame_command ABI");
static_assert(offsetof(PluginApi,units)==216,"API44 units ABI");
static_assert(offsetof(PluginApi,selections)==224,"API44 selections ABI");
static_assert(offsetof(PluginApi,first_ai_script)==232,"API44 first_ai_script ABI");
static_assert(offsetof(PluginApi,hook_game_screen_rclick)==240,"API44 hook_game_screen_rclick ABI");
static_assert(offsetof(PluginApi,client_selection)==248,"API44 client_selection ABI");
static_assert(offsetof(PluginApi,dat_requirements)==256,"API44 dat_requirements ABI");
static_assert(offsetof(PluginApi,first_guard_ai)==264,"API44 first_guard_ai ABI");
static_assert(offsetof(PluginApi,pathing)==272,"API44 pathing ABI");
static_assert(offsetof(PluginApi,set_first_ai_script)==280,"API44 set_first_ai_script ABI");
static_assert(offsetof(PluginApi,first_free_ai_script)==288,"API44 first_free_ai_script ABI");
static_assert(offsetof(PluginApi,set_first_free_ai_script)==296,"API44 set_first_free_ai_script ABI");
static_assert(offsetof(PluginApi,player_ai_towns)==304,"API44 player_ai_towns ABI");
static_assert(offsetof(PluginApi,map_tile_flags)==312,"API44 map_tile_flags ABI");
static_assert(offsetof(PluginApi,players)==320,"API44 players ABI");
static_assert(offsetof(PluginApi,hook_draw_image)==328,"API44 hook_draw_image ABI");
static_assert(offsetof(PluginApi,hook_renderer)==336,"API44 hook_renderer ABI");
static_assert(offsetof(PluginApi,get_iscript_bin)==344,"API44 get_iscript_bin ABI");
static_assert(offsetof(PluginApi,set_iscript_bin)==352,"API44 set_iscript_bin ABI");
static_assert(offsetof(PluginApi,hook_iscript_opcode)==360,"API44 hook_iscript_opcode ABI");
static_assert(offsetof(PluginApi,sprite_hlines)==368,"API44 sprite_hlines ABI");
static_assert(offsetof(PluginApi,sprite_hlines_end)==376,"API44 sprite_hlines_end ABI");
static_assert(offsetof(PluginApi,hook_file_read)==384,"API44 hook_file_read ABI");
static_assert(offsetof(PluginApi,first_active_bullet)==392,"API44 first_active_bullet ABI");
static_assert(offsetof(PluginApi,first_lone_sprite)==400,"API44 first_lone_sprite ABI");
static_assert(offsetof(PluginApi,add_overlay_iscript)==408,"API44 add_overlay_iscript ABI");
static_assert(offsetof(PluginApi,set_campaigns)==416,"API44 set_campaigns ABI");
static_assert(offsetof(PluginApi,hook_run_dialog)==424,"API44 hook_run_dialog ABI");
static_assert(offsetof(PluginApi,send_command)==432,"API44 send_command ABI");
static_assert(offsetof(PluginApi,ai_update_attack_target)==440,"API44 ai_update_attack_target ABI");
static_assert(offsetof(PluginApi,update_visibility_point)==448,"API44 update_visibility_point ABI");
static_assert(offsetof(PluginApi,create_lone_sprite)==456,"API44 create_lone_sprite ABI");
static_assert(offsetof(PluginApi,step_iscript)==464,"API44 step_iscript ABI");
static_assert(offsetof(PluginApi,is_outside_game_screen)==472,"API44 is_outside_game_screen ABI");
static_assert(offsetof(PluginApi,screen_pos)==480,"API44 screen_pos ABI");
static_assert(offsetof(PluginApi,ui_scale)==488,"API44 ui_scale ABI");
static_assert(offsetof(PluginApi,first_fow_sprite)==496,"API44 first_fow_sprite ABI");
static_assert(offsetof(PluginApi,is_replay)==504,"API44 is_replay ABI");
static_assert(offsetof(PluginApi,local_player_id)==512,"API44 local_player_id ABI");
static_assert(offsetof(PluginApi,unit_array_len)==520,"API44 unit_array_len ABI");
static_assert(offsetof(PluginApi,draw_cursor_marker)==528,"API44 draw_cursor_marker ABI");
static_assert(offsetof(PluginApi,hook_spawn_dialog)==536,"API44 hook_spawn_dialog ABI");
static_assert(offsetof(PluginApi,misc_ui_state)==544,"API44 misc_ui_state ABI");
static_assert(offsetof(PluginApi,create_bullet)==552,"API44 create_bullet ABI");
static_assert(offsetof(PluginApi,hook_create_bullet)==560,"API44 hook_create_bullet ABI");
static_assert(offsetof(PluginApi,create_unit)==568,"API44 create_unit ABI");
static_assert(offsetof(PluginApi,hook_create_unit)==576,"API44 hook_create_unit ABI");
static_assert(offsetof(PluginApi,finish_unit_pre)==584,"API44 finish_unit_pre ABI");
static_assert(offsetof(PluginApi,finish_unit_post)==592,"API44 finish_unit_post ABI");
static_assert(offsetof(PluginApi,get_sprite_position)==600,"API44 get_sprite_position ABI");
static_assert(offsetof(PluginApi,set_sprite_position)==608,"API44 set_sprite_position ABI");
static_assert(offsetof(PluginApi,hook_init_units)==616,"API44 hook_init_units ABI");
static_assert(offsetof(PluginApi,get_tooltip_draw_func)==624,"API44 get_tooltip_draw_func ABI");
static_assert(offsetof(PluginApi,set_tooltip_draw_func)==632,"API44 set_tooltip_draw_func ABI");
static_assert(offsetof(PluginApi,hook_layout_draw_text)==640,"API44 hook_layout_draw_text ABI");
static_assert(offsetof(PluginApi,hook_draw_graphic_layers)==648,"API44 hook_draw_graphic_layers ABI");
static_assert(offsetof(PluginApi,graphic_layers)==656,"API44 graphic_layers ABI");
static_assert(offsetof(PluginApi,set_prism_shaders)==664,"API44 set_prism_shaders ABI");
static_assert(offsetof(PluginApi,crash_with_message)==672,"API44 crash_with_message ABI");
static_assert(offsetof(PluginApi,ai_attack_prepare)==680,"API44 ai_attack_prepare ABI");
static_assert(offsetof(PluginApi,hook_ai_step_region)==688,"API44 hook_ai_step_region ABI");
static_assert(offsetof(PluginApi,extended_arrays)==696,"API44 extended_arrays ABI");
static_assert(offsetof(PluginApi,extended_dat)==704,"API44 extended_dat ABI");
static_assert(offsetof(PluginApi,give_ai)==712,"API44 give_ai ABI");
static_assert(offsetof(PluginApi,hook_play_sound)==720,"API44 hook_play_sound ABI");
static_assert(offsetof(PluginApi,is_multiplayer)==728,"API44 is_multiplayer ABI");
static_assert(offsetof(PluginApi,hook_game_loop_start)==736,"API44 hook_game_loop_start ABI");
static_assert(offsetof(PluginApi,active_iscript_objects)==744,"API44 active_iscript_objects ABI");
static_assert(offsetof(PluginApi,hook_ai_focus_disabled)==752,"API44 hook_ai_focus_disabled ABI");
static_assert(offsetof(PluginApi,hook_ai_focus_air)==760,"API44 hook_ai_focus_air ABI");
static_assert(offsetof(PluginApi,unit_base_strength)==768,"API44 unit_base_strength ABI");
static_assert(offsetof(PluginApi,read_map_file)==776,"API44 read_map_file ABI");
static_assert(offsetof(PluginApi,hook_func)==784,"API44 hook_func ABI");
static_assert(offsetof(PluginApi,get_func)==792,"API44 get_func ABI");
static_assert(offsetof(PluginApi,load_vars)==800,"API44 load_vars ABI");
static_assert(offsetof(PluginApi,read_vars)==808,"API44 read_vars ABI");
static_assert(offsetof(PluginApi,write_vars)==816,"API44 write_vars ABI");
static_assert(offsetof(PluginApi,debug_ui_add_tab)==824,"API44 debug_ui_add_tab ABI");
static_assert(offsetof(PluginApi,debug_ui_add_log)==832,"API44 debug_ui_add_log ABI");
static_assert(offsetof(PluginApi,debug_log_add_data)==840,"API44 debug_log_add_data ABI");
static_assert(offsetof(PluginApi,debug_log_clear)==848,"API44 debug_log_clear ABI");
static_assert(offsetof(PluginApi,create_extended_unit_field)==856,"API44 create_extended_unit_field ABI");
static_assert(offsetof(PluginApi,read_extended_unit_field)==864,"API44 read_extended_unit_field ABI");
static_assert(offsetof(PluginApi,write_extended_unit_field)==872,"API44 write_extended_unit_field ABI");
static_assert(offsetof(PluginApi,mutate_dat)==880,"API44 mutate_dat ABI");
enum class FuncId : std::uint16_t {
    UnitCanRally = 0,
    UnitCanBeInfested = 1,
    DoMissileDamage = 2,
    HitUnit = 3,
    HallucinationHit = 4,
    DamageUnit = 5,
    KillUnit = 6,
    UnitSetHp = 7,
    TransformUnit = 8,
    GiveUnit = 9,
    PlaceCreepRect = 10,
    PlaceFinishedUnitCreep = 11,
    AddAiToTrainedUnit = 12,
    AddBuildingAi = 13,
    AddTownUnitAi = 14,
    AddMilitaryAi = 15,
    AiRemoveUnit = 16,
    AiRemoveUnitMilitary = 17,
    AiRemoveUnitTown = 18,
    UnitMaxEnergy = 19,
    UnitAttackRange = 20,
    UnitTargetAcquisitionRange = 21,
    UnitSightRange = 22,
    CheckWeaponTargetingFlags = 23,
    CheckTechTargeting = 24,
    CheckOrderTargeting = 25,
    CheckFowOrderTargeting = 26,
    HideUnit = 27,
    ShowUnit = 28,
    GetRenderTarget = 29,
    MoveScreen = 30,
    SelectUnits = 31,
    AiAddMilitaryToRegion = 32,
    AiTrainMilitary = 33,
    AiAttackPrepare = 34,
    AiAttackClear = 35,
    AiRegionUpdateStrength = 36,
    AiRegionUpdateTarget = 37,
    AiRegionAbandonIfOverwhelmed = 38,
    AiRegionPickAttackTarget = 39,
    AiStepRegion = 40,
    AiTargetExpansion = 41,
    StepGameLogic = 42,
    StepUnitTimers = 43,
    StartCloaking = 44,
    UnitAiWorker = 45,
    UnitAiMilitary = 46,
    UnitAiBuilding = 47,
    FindNearestUnitInArea = 48,
    FindNearestUnitAroundUnit = 49,
    CanAttackUnit = 50,
    IsOutsideAttackRange = 51,
    AiCanTargetAttackThis = 52,
    AiTryReturnHome = 53,
    ForEachUnitInArea = 54,
    PrepareBuildUnit = 55,
    CalculatePath = 56,
    AiPlaceBuilding = 57,
    GetChokePointRegions = 58,
    AiUpdateBuildingPlacementState = 59,
    UpdateBuildingPlacementState = 60,
    FindNearestUnitInAreaPoint = 61,
    AiPickBestPlacementPosition = 62,
    AiPlacementFlags = 63,
    AiAddToAttackForce = 64,
    AiRemoveFromAttackForce = 65,
    CreateLoneSprite = 66,
    LobbyScreenOnWebUiMessage = 67,
    ShowInfoMessageWithSound = 68,
    CreateStartingUnits = 69,
    CreateTeamGameStartingUnits = 70,
    UnitSetDirection = 71,
    AiGetAttackForce = 72,
    CancelUnit = 73,
    FinishUnitPre = 74,
    FinishUnitPost = 75,
    DoSave = 76,
    RenderScreen = 77,
    StepGameLoop = 78,
    ProcessEvents = 79,
    _Last = 80
};
enum class VarId : std::uint16_t {
    Game = 0,
    RngSeed = 1,
    RngEnable = 2,
    AiRegions = 3,
    PlayerAi = 4,
    FirstActiveUnit = 5,
    FirstHiddenUnit = 6,
    Units = 7,
    UnitsVector = 8,
    FirstAiScript = 9,
    FirstFreeAiScript = 10,
    FirstGuardAi = 11,
    ActiveAiTowns = 12,
    Pathing = 13,
    Selections = 14,
    ClientSelection = 15,
    LoadedSave = 16,
    MapTileFlags = 17,
    Players = 18,
    IscriptBin = 19,
    SpriteHlines = 20,
    SpriteHlinesEnd = 21,
    FirstActiveBullet = 22,
    FirstLoneSprite = 23,
    ScreenX = 24,
    ScreenY = 25,
    Zoom = 26,
    FirstFowSprite = 27,
    DrawCursorMarker = 28,
    IsPaused = 29,
    IsTargeting = 30,
    IsPlacingBuilding = 31,
    TooltipDrawFunc = 32,
    GraphicLayers = 33,
    ActiveIscriptFlingy = 34,
    ActiveIscriptUnit = 35,
    ActiveIscriptBullet = 36,
    CmdIconsDdsGrp = 37,
    CmdBtnsDdsGrp = 38,
    StatusScreenMode = 39,
    DatRequirementError = 40,
    FirstPlayerUnit = 41,
    UnitShouldRevealArea = 42,
    Allocator = 43,
    GameData = 44,
    ReplayData = 45,
    ReplayHeader = 46,
    ScMainState = 47,
    CommandUser = 48,
    UniqueCommandUser = 49,
    IsReplay = 50,
    LocalPlayerId = 51,
    LocalUniquePlayerId = 52,
    IsMultiplayer = 53,
    LastLoneSprite = 54,
    FirstFreeLoneSprite = 55,
    LastFreeLoneSprite = 56,
    LastFowSprite = 57,
    FirstFreeFowSprite = 58,
    LastFreeFowSprite = 59,
    CursorMarker = 60,
    ResourceAreas = 61,
    DrawCommands = 62,
    VertexBuffer = 63,
    Renderer = 64,
    FirstDialog = 65,
    MainPalette = 66,
    RgbColors = 67,
    UseRgbColors = 68,
    GameScreenWidthBwpx = 69,
    GameScreenHeightBwpx = 70,
    StepGameFrames = 71,
    StatportTalkingPortraitActive = 72,
    TilesetCv5 = 73,
    MinitileData = 74,
    TilesetIndexedMapTiles = 75,
    CreepOriginalTiles = 76,
    CreepTileBorders = 77,
    SpritesVector = 78,
    ImagesVector = 79,
    SelectionCircleImages = 80,
    HpBarImages = 81,
    FirstFreeSelectionCircle = 82,
    LastFreeSelectionCircle = 83,
    FirstFreeHpBar = 84,
    LastFreeHpBar = 85,
    HpBarState = 86,
    PlacementImages = 87,
    FirstFreePlacementImage = 88,
    LastFreePlacementImage = 89,
    PlacementRects = 90,
    FirstFreePlacementRect = 91,
    LastFreePlacementRect = 92,
    AiScriptListHead = 93,
    _Last = 94
};
}
