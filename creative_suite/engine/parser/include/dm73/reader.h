#pragma once
#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace dm73 {

// ---------------------------------------------------------------------------
// Protocol 73 constants (Quake Live)
// ---------------------------------------------------------------------------
constexpr int PROTOCOL      = 73;
constexpr int MAX_CLIENTS   = 64;

// ---------------------------------------------------------------------------
// MeansOfDeath (MOD_*) seed values
// Full list: docs/reference/dm73-format-deep-dive.md
// Source:    engine/engines/_canonical/code/game/bg_public.h
// WolfcamQL additions confirmed via PE analysis of qagamex86.dll (CREDITS-wolfcam.txt)
// ---------------------------------------------------------------------------
enum MeansOfDeath : int {
    MOD_UNKNOWN         = 0,
    MOD_SHOTGUN         = 1,
    MOD_GAUNTLET        = 2,
    MOD_MACHINEGUN      = 3,
    MOD_GRENADE         = 4,
    MOD_GRENADE_SPLASH  = 5,
    MOD_ROCKET          = 6,
    MOD_ROCKET_SPLASH   = 7,
    MOD_PLASMA          = 8,
    MOD_PLASMA_SPLASH   = 9,
    MOD_RAILGUN         = 10,
    MOD_LIGHTNING       = 11,
    MOD_BFG             = 12,
    MOD_BFG_SPLASH      = 13,
    MOD_TELEFRAG        = 14,
    MOD_FALL            = 15,
    MOD_RAILGUN_HEADSHOT = 16,  // wolfcam-specific (confirmed via qagamex86.dll DWARF)
    MOD_SUICIDE         = 17,
    MOD_TARGET_LASER    = 18,
    MOD_TRIGGER_HURT    = 19,
    MOD_HMG             = 20,   // wolfcam-specific — confirms protocol 73 is wolfcam-extended
    MOD_NAIL            = 21,   // wolfcam-specific
    MOD_CHAINGUN        = 22,   // wolfcam-specific
    MOD_PROXIMITY_MINE  = 23,   // wolfcam-specific
    MOD_KAMIKAZE        = 24,   // wolfcam-specific
    MOD_JUICED          = 25,   // wolfcam-specific
    MOD_GRAPPLE         = 26,   // wolfcam-specific
};

// ---------------------------------------------------------------------------
// EV_OBITUARY event constant
// Used to detect frag events in snapshot entity-state streams.
// Source: engine/engines/_canonical/code/game/bg_public.h (EV_OBITUARY)
// Toggle-bit mask: entity.event & ~0x300 == EV_OBITUARY
// ---------------------------------------------------------------------------
constexpr int EV_OBITUARY = 42;    // seed — verify against bg_public.h at parse time

// ---------------------------------------------------------------------------
// FragEvent — one kill event decoded from a snapshot
// ---------------------------------------------------------------------------
struct FragEvent {
    int     server_time_ms;   // snapshot server_time field (milliseconds)
    int     killer_client;    // otherEntityNum2 — client slot 0-63
    int     victim_client;    // otherEntityNum  — client slot 0-63
    int     weapon;           // eventParm = MeansOfDeath value
    bool    is_headshot;      // weapon == MOD_RAILGUN_HEADSHOT
    bool    is_telefrag;      // weapon == MOD_TELEFRAG
};

// ---------------------------------------------------------------------------
// DemoHeader — parsed from the initial svc_gamestate message
// ---------------------------------------------------------------------------
struct DemoHeader {
    int         protocol;       // should be 73
    std::string hostname;
    std::string map_name;
    int         num_clients;
};

// ---------------------------------------------------------------------------
// Dm73Reader — callback-based streaming reader
//
// Usage:
//   Dm73Reader reader("/path/to/demo.dm_73");
//   if (!reader.open()) { /* error */ }
//   int n = reader.read_frags([](const FragEvent& f) { ... });
//   reader.close();
//
// FT-1 status: scaffold only — read_frags / read_header return stubs.
// See src/dm73_reader.cpp.
// ---------------------------------------------------------------------------
class Dm73Reader {
public:
    explicit Dm73Reader(const std::string& path);
    ~Dm73Reader();

    // Disable copy; allow move
    Dm73Reader(const Dm73Reader&) = delete;
    Dm73Reader& operator=(const Dm73Reader&) = delete;

    bool open();
    void close();

    // Read all frag events via callback.
    // Returns total frag count, or -1 on parse error.
    int read_frags(std::function<void(const FragEvent&)> on_frag);

    // Read just the header (fast — stops after first svc_gamestate).
    bool read_header(DemoHeader& out);

    const std::string& last_error() const;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

// ---------------------------------------------------------------------------
// Convenience: extract all frags as JSON Lines string
// Declared in frag_extractor.cpp
// ---------------------------------------------------------------------------
std::string extract_frags_jsonl(const std::string& demo_path);

} // namespace dm73
