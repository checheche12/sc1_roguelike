#pragma once
// Derived from installed, read-only StatFluf JSON; original placeholder retained.
namespace sc1_native { namespace wave_timer_asset {
inline constexpr short kId=-32000,kCargoId=-31999;
inline constexpr char json[]=R"SC1_WAVE_HUD({"type":"DIALOG","name":"StatFluf","rect":[0,0,248,148],"style":[],"children":[{"type":"LTEXT","content":"statfluf-1","id":-1,"rect":[0,0,4,4],"flags":[],"children":null},{"type":"CTEXT","content":"공세 대기 · 기지 도착 후     ","id":-32000,"rect":[8,128,232,20],"flags":["RC_SMALLTEXT","WS_DISABLED"],"children":null},{"type":"PUSHBUTTON","content":"추가 승객 보기 / 앞쪽 승객 보기     ","id":-31999,"rect":[8,104,232,20],"flags":["RC_SMALLTEXT","WS_DISABLED"],"children":null}]})SC1_WAVE_HUD";
} }
