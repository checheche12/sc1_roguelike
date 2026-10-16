#pragma once
// Adapted from neivv/aise bw_dat/src/bw/structs.rs, commit42fba4276cbe30e73baefc7f3ad07cadaa2aa2b1.
// Public repr(C) x64 layout. No game executable addresses are used.
#include <cstddef>
#include <cstdint>
namespace bw {
struct Unit;struct Flingy;
struct alignas(8) UnitSpecific1 { std::uint8_t bytes[0x20]; };
struct alignas(8) UnitSpecific2 { std::uint8_t bytes[0x18]; };
struct alignas(8) RallyPylon { std::uint8_t bytes[0x10]; };
struct PointAndUnit { std::int16_t x,y; Unit* unit; };
struct DatTable {
    void* data;
    std::uint32_t entry_size;
    std::uint32_t entries;
};
struct Supplies {
    std::uint32_t provided[0xc];
    std::uint32_t used[0xc];
    std::uint32_t max[0xc];
};
struct Point {
    std::int16_t x;
    std::int16_t y;
};
struct Point32 {
    std::int32_t x;
    std::int32_t y;
};
struct Rect32 {
    std::int32_t left;
    std::int32_t top;
    std::int32_t right;
    std::int32_t bottom;
};
struct Location {
    Rect32 area;
    std::uint16_t unk;
    std::uint16_t flags;
};
struct Game {
    std::uint32_t minerals[0xc];
    std::uint32_t gas[0xc];
    std::uint8_t dc60[0x60];
    std::uint32_t starting_local_player_id;
    std::uint8_t starting_player_types[0xc];
    std::uint8_t starting_races[0xc];
    std::uint8_t team_game_main_player[4];
    std::uint16_t screen_pos_x_tiles;
    std::uint16_t screen_pos_y_tiles;
    std::uint16_t map_width_tiles;
    std::uint16_t map_height_tiles;
    std::uint8_t dce8[0x4];
    std::uint16_t tileset;
    std::uint16_t bgm_song;
    std::uint8_t dcf0;
    std::uint8_t active_net_players;
    std::uint8_t player_race;
    std::uint8_t custom_singleplayer;
    std::uint8_t dcf4[0x8];
    std::uint32_t visions[0xc];
    std::uint32_t player_randomization[0x8];
    std::uint32_t frame_count;
    std::uint32_t saved_elapsed_seconds;
    std::uint16_t campaign_mission;
    std::uint8_t next_scenario[0x20];
    std::uint8_t selected_singleplayer_race;
    std::uint8_t selected_singleplayer_computer_races[0x8];
    std::uint16_t saved_screen_positions[3][2];
    std::uint8_t unit_availability[0xc][0xe4];
    std::uint8_t dcc3c[0x10];
    std::uint8_t map_path[0x104];
    std::uint8_t map_title[0x20];
    std::uint32_t selection_hotkeys[0x8][0x12][0xc];
    std::uint8_t dc2870[0x400];
    std::uint8_t chat_dialog_recipient;
    std::uint8_t player_lose_type;
    std::uint8_t player_was_dropped[0x8];
    std::uint8_t self_alliance_colors[0xc];
    std::uint8_t player_color_palette[0xc][0x8];
    std::uint8_t player_minimap_color[0xc];
    std::uint32_t scores[0x12][0xc];
    Supplies supplies[0x3];
    std::uint32_t custom_score[0xc];
    std::uint32_t all_units_count[0xe4][0xc];
    std::uint32_t completed_units_count[0xe4][0xc];
    std::uint32_t unit_kills[0xe4][0xc];
    std::uint32_t deaths[0xe4][0xc];
    std::uint8_t tech_availability_sc[0xc][0x18];
    std::uint8_t tech_level_sc[0xc][0x18];
    std::uint8_t tech_in_progress_legacy[0x24];
    std::uint8_t upgrade_limit_sc[0xc][0x2e];
    std::uint8_t upgrade_level_sc[0xc][0x2e];
    std::uint8_t dce3e8[0xd8];
    std::uint8_t player_forces[0x8];
    std::uint8_t force_flags[0x4];
    std::uint8_t force_names[0x4][0x1e];
    std::uint8_t alliances[0xc][0xc];
    std::uint32_t player_objectives_string[0xc];
    std::uint32_t countdown_timer;
    std::uint32_t elapsed_seconds;
    std::uint8_t dce60c[0x4];
    std::uint8_t victory_state[0x8];
    std::uint32_t computers_in_leaderboard;
    std::uint8_t leaderboard_type;
    std::uint8_t leaderboard_location;
    std::uint16_t leaderboard_parameter;
    std::uint32_t leaderboard_goal;
    std::uint32_t leaderboard_string;
    std::uint8_t pauses_remaining[0x8];
    std::uint16_t start_position[0x8][0x2];
    Location locations_legacy[0x40];
    std::uint32_t switches[8]; // Native CHK switch states, 256 bits (BW-compatible Game layout).
    Location locations[0xff];
    std::uint8_t dcff5c[0x4];
    std::uint8_t tech_availability_bw[0xc][0x14];
    std::uint8_t tech_level_bw[0xc][0x14];
    std::uint8_t tech_in_progress[0xc][0x6];
    std::uint8_t upgrade_limit_bw[0xc][0xf];
    std::uint8_t upgrade_level_bw[0xc][0xf];
    std::uint8_t upgrade_in_progress[0xc][0x8];
    std::uint8_t is_bw;
    std::uint8_t unk10351;
    std::uint8_t scr_color_unk[0x8];
    std::uint8_t scr_init_color_rgba[8][4];
    std::uint8_t scr_unk1037a[0x10];
    std::uint8_t scr_player_color_preference[0x10];
    std::uint8_t padding[0x7366];
};
// Pinned SpriteScr x64 layout; overlay parent is the existing native main image.
struct SpriteScr {
    void* prev;void* next;
    std::uint16_t sprite_id;std::uint8_t player,selection_index,visibility_mask,elevation_level,flags,selection_flash_timer;
    std::uint16_t index;std::uint8_t width,height;
    std::size_t position[2];
    void* main_image;void* first_image;void* last_image;
};
static_assert(sizeof(SpriteScr)==0x48,"SpriteScr64");
static_assert(offsetof(SpriteScr,main_image)==0x30,"SpriteScr main image64");
struct Flingy {
    Flingy* prev;
    Flingy* next;
    std::int32_t hitpoints;
    void* sprite;
    PointAndUnit move_target;
    Point next_move_waypoint;
    Point unk_move_waypoint;
    std::uint8_t flingy_flags;
    std::uint8_t facing_direction;
    std::uint8_t turn_speed;
    std::uint8_t movement_direction;
    std::uint16_t flingy_id;
    std::uint8_t unk_26;
    std::uint8_t movement_type;
    Point position;
    Point32 exact_position;
    std::uint32_t top_speed;
    std::int32_t current_speed;
    std::int32_t next_speed;
    std::int32_t current_speed_x;
    std::int32_t current_speed_y;
    std::uint16_t acceleration;
    std::uint8_t new_direction;
    std::uint8_t target_direction;
};
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable:4324) // Required public repr(C) union alignment; size/offset assertions below.
#endif
struct Unit {
    Flingy flingy;
    std::uint8_t player;
    std::uint8_t order;
    std::uint8_t order_state;
    std::uint8_t order_signal;
    std::uint16_t order_fow_unit;
    std::uint16_t unused52;
    std::uint8_t order_timer;
    std::uint8_t ground_cooldown;
    std::uint8_t air_cooldown;
    std::uint8_t spell_cooldown;
    PointAndUnit order_target;
    std::int32_t shields;
    std::uint16_t unit_id;
    std::uint16_t unused66;
    Unit* prev_player_unit;
    Unit* next_player_unit;
    Unit* subunit;
    void* order_queue_begin;
    void* order_queue_end;
    Unit* previous_attacker;
    Unit* related;
    std::uint8_t highlight_order_count;
    std::uint8_t order_wait;
    std::uint8_t unk86;
    std::uint8_t attack_notify_timer;
    std::uint16_t previous_unit_id;
    std::uint8_t minimap_draw_counter;
    std::uint8_t minimap_draw_color;
    std::uint16_t unused8c;
    std::uint8_t rank;
    std::uint8_t kills;
    std::uint8_t last_attacking_player;
    std::uint8_t secondary_order_wait;
    std::uint8_t ai_spell_flags;
    std::uint8_t order_flags;
    std::uint16_t buttons;
    std::uint8_t invisibility_effects;
    std::uint8_t movement_state;
    std::uint16_t build_queue[5];
    std::uint16_t energy;
    std::uint8_t current_build_slot;
    std::uint8_t minor_unique_index;
    std::uint8_t secondary_order;
    std::uint8_t building_overlay_state;
    std::uint16_t build_hp_gain;
    std::uint16_t build_shield_gain;
    std::uint16_t remaining_build_time;
    std::uint16_t previous_hp;
    std::uint16_t loaded_units[8];
    UnitSpecific1 unit_specific;
    UnitSpecific2 unit_specific2;
    std::uint32_t flags;
    std::uint8_t carried_powerup_flags;
    std::uint8_t wireframe_seed;
    std::uint8_t secondary_order_state;
    std::uint8_t move_target_update_timer;
    std::uint32_t detection_status;
    PointAndUnit secondary_order_target;
    Unit* prev_invisible;
    Unit* next_invisible;
    RallyPylon rally_pylon;
    std::size_t unk_64bit_value;
    void* path;
    std::uint8_t path_frame;
    std::uint8_t pathing_flags;
    std::uint8_t _unk106;
    std::uint8_t is_being_healed;
    std::uint16_t collision_points[0x4];
    std::uint16_t death_timer;
    std::uint16_t defensive_matrix_dmg;
    std::uint8_t matrix_timer;
    std::uint8_t stim_timer;
    std::uint8_t ensnare_timer;
    std::uint8_t lockdown_timer;
    std::uint8_t irradiate_timer;
    std::uint8_t stasis_timer;
    std::uint8_t plague_timer;
    std::uint8_t is_under_storm;
    Unit* irradiated_by;
    std::uint8_t irradiate_player;
    std::uint8_t parasited_by_players;
    std::uint8_t master_spell_timer;
    std::uint8_t is_blind;
    std::uint8_t maelstrom_timer;
    std::uint8_t _unk125;
    std::uint8_t acid_spore_count;
    std::uint8_t acid_spore_timers[0x9];
    std::uint16_t bullet_spread_seed;
    std::uint16_t scr_carried_unit_high_bits;
    void* ai;
    std::uint16_t air_strength;
    std::uint16_t ground_strength;
    std::uint32_t position_search_indices[4];
    std::uint8_t repulse_misc;
    std::uint8_t repulse_direction;
    std::uint8_t repulse_chunk_x;
    std::uint8_t repulse_chunk_y;
};
// Pinned public Bullet prefix (same source commit as Unit); only player is
// inspected, so projectile effects remain attributed after the parent dies.
struct Bullet {
    Flingy flingy;
    std::uint8_t player,state,order_state,order_signal;
    std::uint16_t order_fow_unit,unused52;
    std::uint8_t order_timer,ground_cooldown,air_cooldown,spell_cooldown;
    PointAndUnit target;
    std::uint8_t weapon_id,death_timer,flags,bounces_remaining;
    Unit* parent;
};
static_assert(offsetof(Bullet,player)==0x68,"Bullet player64");
static_assert(offsetof(Bullet,parent)==0x90,"Bullet parent64");
static_assert(sizeof(DatTable)==16,"DatTable64");
static_assert(offsetof(Game,switches)==0xeb50,"Game trigger switches");
static_assert(sizeof(Game)==0x17700,"Game64");
static_assert(sizeof(Flingy)==0x68,"Flingy64");
static_assert(sizeof(Unit)==0x1e8,"Unit64");
static_assert(offsetof(Unit,unit_specific)==0x108,"Unit union1");
static_assert(offsetof(Unit,unit_specific2)==0x128,"Unit union2");
#ifdef _MSC_VER
#pragma warning(pop)
#endif
static_assert(offsetof(Unit,path)==0x188,"Unit path");
static_assert(offsetof(Unit,death_timer)==0x19c,"Unit death timer");
static_assert(offsetof(Game,campaign_mission)==0x154,"Game campaign");
static_assert(offsetof(Game,is_bw)==0x10350,"Game expansion flag");
}
