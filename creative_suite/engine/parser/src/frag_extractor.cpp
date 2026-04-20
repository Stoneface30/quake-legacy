#include "dm73/reader.h"
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

// ---------------------------------------------------------------------------
// frag_extractor.cpp — convenience JSON Lines extractor (FT-1 scaffold)
//
// extract_frags_jsonl() drives Dm73Reader and formats each FragEvent as a
// single-line JSON object.  No external JSON library dependency — the output
// is hand-assembled with snprintf so the scaffold builds without vcpkg/conan.
//
// When FT-1 alpha lands (real parse implemented), this file needs no changes:
// the callback and formatting logic is correct; only dm73_reader.cpp changes.
//
// JSON output schema per event (one object per line):
//   {
//     "server_time_ms": <int>,
//     "killer":         <int 0-63>,
//     "victim":         <int 0-63>,
//     "weapon":         <int MeansOfDeath>,
//     "headshot":       <bool>,
//     "telefrag":       <bool>
//   }
// ---------------------------------------------------------------------------

namespace dm73 {

std::string extract_frags_jsonl(const std::string& demo_path)
{
    Dm73Reader reader(demo_path);
    if (!reader.open()) {
        std::cerr << "[dm73] cannot open: " << demo_path << "\n";
        return "";
    }

    std::vector<std::string> lines;
    lines.reserve(256);

    int count = reader.read_frags([&](const FragEvent& f) {
        char buf[320];
        snprintf(buf, sizeof(buf),
            "{\"server_time_ms\":%d,"
            "\"killer\":%d,"
            "\"victim\":%d,"
            "\"weapon\":%d,"
            "\"headshot\":%s,"
            "\"telefrag\":%s}",
            f.server_time_ms,
            f.killer_client,
            f.victim_client,
            f.weapon,
            f.is_headshot ? "true" : "false",
            f.is_telefrag ? "true" : "false");
        lines.push_back(buf);
    });

    if (count < 0) {
        std::cerr << "[dm73] parse failed: " << reader.last_error() << "\n";
        return "";
    }

    std::string result;
    result.reserve(lines.size() * 128);
    for (const auto& line : lines) {
        result += line;
        result += '\n';
    }
    return result;
}

} // namespace dm73
