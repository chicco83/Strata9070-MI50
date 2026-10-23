// helper_plugin.cpp — strata-mi50, 2026-10-23
// strata_helper_gfx906.dll: the helper-GPU expert tier (RemoteExperts) built in the gfx906 / HIP 5.x tree and loaded by an engine
// that runs on another HIP runtime (the RX 9070 XT's).  Same class, same kernels as the in-process helper tier; only the device
// handling differs: here the runtime sees the helper GPU alone, so it is "standalone" (no primary device to keep clear of).
// ABI: include/strata/core/helper_plugin_abi.h.  Plan: PIANO_DUAL_GPU_2026-10-23.md.
#include "strata/core/helper_plugin_abi.h"
#include "strata/core/remote_experts.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"

#include <cuda_runtime.h>

#include <cstdio>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

namespace {
struct State {
    std::string pack;
    int64_t layers = 0, experts = 0;
    int device = 0;
    bool layout = false;
};
State& state() { static State s; return s; }

void put(char* err, int len, const std::string& msg) {
    if (err != nullptr && len > 0) std::snprintf(err, (size_t) len, "%s", msg.c_str());
}

struct Tier {
    strata::core::RemoteExperts remote;
};
}  // namespace

extern "C" {

STRATA_HELPER_EXPORT int strata_helper_abi_version(void) { return STRATA_HELPER_ABI_VERSION; }

STRATA_HELPER_EXPORT int strata_helper_init(const char* pack_dir, int64_t n_layers, int64_t n_expert, int device,
                                            double* free_gib, char* err, int err_len) {
    State& st = state();
    int count = 0;
    if (cudaGetDeviceCount(&count) != cudaSuccess || device < 0 || device >= count) {
        cudaGetLastError();
        put(err, err_len, "the plugin's HIP runtime sees " + std::to_string(count) + " device(s); device " + std::to_string(device) +
                              " is not one of them");
        return 1;
    }
    if (cudaSetDevice(device) != cudaSuccess) { put(err, err_len, "cudaSetDevice failed"); return 1; }
    st.device = device;
    size_t free_b = 0, total_b = 0;
    if (cudaMemGetInfo(&free_b, &total_b) != cudaSuccess) { put(err, err_len, "cudaMemGetInfo failed"); return 1; }
    if (free_gib != nullptr) *free_gib = (double) free_b / 1073741824.0;
    if (n_layers > 0 && (!st.layout || st.pack != pack_dir || st.layers != n_layers || st.experts != n_expert)) {
        std::string e;
        if (!strata::kernels::cpu::expert_layout_load(pack_dir, n_layers, n_expert, e)) {
            put(err, err_len, "expert layout: " + e);
            return 1;
        }
        st.pack = pack_dir;
        st.layers = n_layers;
        st.experts = n_expert;
        st.layout = true;
    }
    return 0;
}

STRATA_HELPER_EXPORT void* strata_helper_open(int slots, const int32_t* ranked, int64_t n_ranked, strata_helper_primary_fn primary,
                                              strata_helper_blob_fn blob, void* ctx, uint8_t* claimed, int auto_size,
                                              char* err, int err_len) {
    State& st = state();
    if (!st.layout) { put(err, err_len, "strata_helper_init with the model's layers first"); return nullptr; }
    std::vector<std::pair<int32_t, int32_t>> pairs;
    pairs.reserve((size_t) n_ranked);
    for (int64_t i = 0; i < n_ranked; ++i) pairs.emplace_back(ranked[2 * i], ranked[2 * i + 1]);
    const size_t n = (size_t) st.layers * (size_t) st.experts;
    std::vector<uint8_t> taken(claimed, claimed + n);
    auto tier = std::make_unique<Tier>();
    std::string e;
    const bool ok = tier->remote.open_with(
        st.device, slots, st.layers, st.experts, pairs,
        [&](int32_t l, int32_t x) { return primary != nullptr && primary(ctx, l, x) != 0; },
        [&](int64_t l, int64_t x) { return blob(ctx, l, x); }, taken, e, auto_size != 0, true);
    if (!ok) { put(err, err_len, e); return nullptr; }
    std::memcpy(claimed, taken.data(), n);
    return tier.release();
}

STRATA_HELPER_EXPORT void strata_helper_close(void* h) { delete (Tier*) h; }

STRATA_HELPER_EXPORT int strata_helper_begin(void* h, int64_t layer, const float* x, const int32_t* ids, int64_t n_tok, int64_t k,
                                             const int32_t* kind, const int32_t* primary_res, char* err, int err_len) {
    std::string e;
    if (!((Tier*) h)->remote.begin(layer, x, ids, n_tok, k, kind, primary_res, e)) { put(err, err_len, e); return 1; }
    return 0;
}

STRATA_HELPER_EXPORT int strata_helper_finish(void* h, float* out, char* err, int err_len) {
    std::string e;
    if (!((Tier*) h)->remote.finish(out, e)) { put(err, err_len, e); return 1; }
    return 0;
}

STRATA_HELPER_EXPORT int strata_helper_owns(void* h, int64_t index) { return ((Tier*) h)->remote.owns(index) ? 1 : 0; }

STRATA_HELPER_EXPORT int strata_helper_holds(void* h, int64_t layer, int32_t expert) {
    return ((Tier*) h)->remote.holds(layer, expert) ? 1 : 0;
}

STRATA_HELPER_EXPORT void strata_helper_stats(void* h, int64_t* c, double* d) {
    const auto& r = ((Tier*) h)->remote;
    c[0] = r.resident(); c[1] = r.computed(); c[2] = r.launched_layers();
    c[3] = (int64_t) r.returned_bytes(); c[4] = (int64_t) r.full_row_bytes();
    d[0] = r.gib(); d[1] = r.ms_begin(); d[2] = r.ms_wait();
}

}  // extern "C"
