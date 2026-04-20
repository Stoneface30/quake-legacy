#include "dm73/reader.h"
#include <cstdio>
#include <cstring>
#include <iostream>

// ---------------------------------------------------------------------------
// dm73dump — CLI entry point
//
// Usage:
//   dm73dump <demo.dm_73>
//   dm73dump --header <demo.dm_73>
//
// Output:
//   Default: one JSON object per line (frag events) to stdout
//   --header: dump DemoHeader fields as JSON to stdout
//
// Exit codes:
//   0  success (or scaffold stub — events will be 0 until FT-1 alpha)
//   1  error (bad args, cannot open file, parse failure)
//
// FT-1 status: scaffold — read_frags currently returns -1 (stub).
// The CLI wires up correctly; once dm73_reader.cpp is implemented the output
// will contain real events with no changes needed here.
// ---------------------------------------------------------------------------

static void print_usage(const char* prog)
{
    std::cerr << "Usage: " << prog << " [--header] <demo.dm_73>\n";
    std::cerr << "  Default: emit frag events as JSON Lines to stdout\n";
    std::cerr << "  --header: emit DemoHeader as JSON to stdout\n";
}

int main(int argc, char* argv[])
{
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    bool        mode_header = false;
    const char* demo_path   = nullptr;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--header") == 0) {
            mode_header = true;
        } else {
            demo_path = argv[i];
        }
    }

    if (!demo_path) {
        print_usage(argv[0]);
        return 1;
    }

    dm73::Dm73Reader reader(demo_path);
    if (!reader.open()) {
        std::cerr << "Error: " << reader.last_error() << "\n";
        return 1;
    }

    // ------------------------------------------------------------------
    // --header mode: dump DemoHeader as JSON
    // ------------------------------------------------------------------
    if (mode_header) {
        dm73::DemoHeader hdr;
        if (!reader.read_header(hdr)) {
            std::cerr << "Header parse failed: " << reader.last_error() << "\n";
            // Scaffold: print a stub response so callers can detect FT-1 state
            std::cout << "{\"error\":\"scaffold\",\"message\":\""
                      << reader.last_error() << "\"}\n";
            return 0;  // non-fatal during scaffold phase
        }
        char buf[512];
        snprintf(buf, sizeof(buf),
            "{\"protocol\":%d,\"hostname\":\"%s\","
            "\"map_name\":\"%s\",\"num_clients\":%d}",
            hdr.protocol,
            hdr.hostname.c_str(),
            hdr.map_name.c_str(),
            hdr.num_clients);
        std::cout << buf << "\n";
        return 0;
    }

    // ------------------------------------------------------------------
    // Default mode: stream frag events as JSON Lines
    // ------------------------------------------------------------------
    int count = reader.read_frags([](const dm73::FragEvent& f) {
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
        std::cout << buf << "\n";
    });

    if (count < 0) {
        // Scaffold: read_frags returns -1 until FT-1 alpha
        std::cerr << "Note: " << reader.last_error() << "\n";
        std::cerr << "dm73dump is a scaffold — real parsing not yet implemented.\n";
        return 0;  // non-fatal during scaffold phase
    }

    std::cerr << count << " frag(s) extracted from " << demo_path << "\n";
    return 0;
}
