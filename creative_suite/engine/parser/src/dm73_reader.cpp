#include "dm73/reader.h"
#include <cstdio>
#include <cstring>

// ---------------------------------------------------------------------------
// dm73_reader.cpp — FT-1 scaffold implementation
//
// All parse methods are STUBS.  They compile, link, and return safe/documented
// failure values.  Real bit-stream decoding (via vendored msg.c / huffman.c)
// will replace these bodies when FT-1 moves from scaffold to alpha.
//
// Status markers used in this file:
//   SCAFFOLD  — intentionally stubbed, replace in FT-1 alpha
//   WIRED     — real implementation present
// ---------------------------------------------------------------------------

namespace dm73 {

struct Dm73Reader::Impl {
    std::string path;
    std::string last_error;
    FILE*       fp          = nullptr;
    bool        is_open     = false;
};

// ---------------------------------------------------------------------------
// Constructor / destructor
// ---------------------------------------------------------------------------

Dm73Reader::Dm73Reader(const std::string& path)
    : impl_(std::make_unique<Impl>())
{
    impl_->path = path;
}

Dm73Reader::~Dm73Reader()
{
    close();
}

// ---------------------------------------------------------------------------
// open() — WIRED (actual file open needed for future real parse)
// ---------------------------------------------------------------------------

bool Dm73Reader::open()
{
    if (impl_->is_open) {
        impl_->last_error = "already open";
        return false;
    }
    impl_->fp = fopen(impl_->path.c_str(), "rb");
    if (!impl_->fp) {
        impl_->last_error = "cannot open file: " + impl_->path;
        return false;
    }
    impl_->is_open    = true;
    impl_->last_error = "";
    return true;
}

// ---------------------------------------------------------------------------
// close()
// ---------------------------------------------------------------------------

void Dm73Reader::close()
{
    if (impl_->fp) {
        fclose(impl_->fp);
        impl_->fp = nullptr;
    }
    impl_->is_open = false;
}

// ---------------------------------------------------------------------------
// read_frags() — SCAFFOLD
//
// Real implementation will:
//   1. Read 8-byte frame header (seqLE32 + lenLE32)
//   2. Decompress payload via huffman.c (MSG_ReadBits)
//   3. Dispatch svc_ops: skip gamestate/serverCommand, parse snapshot
//   4. Walk snapshot entities, find EV_OBITUARY (entity.event & ~0x300)
//   5. Emit FragEvent{server_time, otherEntityNum2, otherEntityNum, eventParm}
//
// See: docs/reference/dm73-format-deep-dive.md §4 (Snapshot) + §5 (Events)
// ---------------------------------------------------------------------------

int Dm73Reader::read_frags(std::function<void(const FragEvent&)> on_frag)
{
    (void)on_frag;
    impl_->last_error =
        "read_frags: not yet implemented (FT-1 scaffold — "
        "see src/dm73_reader.cpp SCAFFOLD markers)";
    return -1;
}

// ---------------------------------------------------------------------------
// read_header() — SCAFFOLD
//
// Real implementation will:
//   1. Seek to frame 0 of the demo file
//   2. Read first svc_gamestate message
//   3. Extract cs[0] (serverinfo configstring) → parse map, hostname, protocol
//
// See: docs/reference/dm73-format-deep-dive.md §2 (Gamestate)
// ---------------------------------------------------------------------------

bool Dm73Reader::read_header(DemoHeader& out)
{
    (void)out;
    impl_->last_error =
        "read_header: not yet implemented (FT-1 scaffold — "
        "see src/dm73_reader.cpp SCAFFOLD markers)";
    return false;
}

// ---------------------------------------------------------------------------
// last_error()
// ---------------------------------------------------------------------------

const std::string& Dm73Reader::last_error() const
{
    return impl_->last_error;
}

} // namespace dm73
