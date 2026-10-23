// helper_plugin_abi.h — strata-mi50, 2026-10-23
// C ABI between the engine and a helper-GPU plugin DLL: an expert tier (RemoteExperts) on a GPU that only another HIP runtime
// sees.  On Windows the Radeon Pro VII / MI50 (gfx906) is listed only by the HIP 5.x runtime (amdhip64.dll) and the RX 9070 XT
// only by HIP 6.x/7.x, so one process loads both: the engine (HIP 6/7) and strata_helper_gfx906.dll (HIP 5.x), each with its own
// runtime.  Everything that crosses this boundary is host memory: activations in, compact expert rows out, expert blobs read
// through a callback.  PIANO_DUAL_GPU_2026-10-23.md.
#pragma once
#include <stdint.h>

#define STRATA_HELPER_ABI_VERSION 1

#if defined(_WIN32)
#define STRATA_HELPER_EXPORT __declspec(dllexport)
#else
#define STRATA_HELPER_EXPORT __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

/// (layer, expert) -> the expert's blob in host memory, as the engine's ExpertSource::blob gives it; nullptr = not available.
typedef const uint8_t* (*strata_helper_blob_fn)(void* ctx, int64_t layer, int64_t expert);
/// (layer, expert) -> nonzero when the engine's own GPU cache already holds it (the helper then skips it).
typedef int (*strata_helper_primary_fn)(void* ctx, int32_t layer, int32_t expert);

typedef int (*strata_helper_abi_version_t)(void);
/// Loads the pack's expert layout (and Hadamard spec) into the plugin's own globals, picks the plugin runtime's device
/// `device` and reports its free memory.  0 = ok; otherwise `err` holds the reason.
typedef int (*strata_helper_init_t)(const char* pack_dir, int64_t n_layers, int64_t n_expert, int device,
                                    double* free_gib, char* err, int err_len);
/// Opens the tier: fills up to `slots` experts from `ranked` (pairs layer, expert, in rank order), skipping the ones
/// `primary` reports and the ones `claimed[layer * n_expert + expert]` marks; marks what it takes in `claimed`.
/// `auto_size` != 0: as many as fit with 512 MiB free.  Returns a handle, nullptr on failure.
typedef void* (*strata_helper_open_t)(int slots, const int32_t* ranked, int64_t n_ranked, strata_helper_primary_fn primary,
                                      strata_helper_blob_fn blob, void* ctx, uint8_t* claimed, int auto_size,
                                      char* err, int err_len);
typedef void (*strata_helper_close_t)(void* h);
/// RemoteExperts::begin: `x` is n_tok rows of H floats, `ids` n_tok * k expert ids; `kind` / `primary_res` may be null.
typedef int (*strata_helper_begin_t)(void* h, int64_t layer, const float* x, const int32_t* ids, int64_t n_tok, int64_t k,
                                     const int32_t* kind, const int32_t* primary_res, char* err, int err_len);
/// RemoteExperts::finish: writes the rows it owns into `out` (n_tok * k rows of H floats).
typedef int (*strata_helper_finish_t)(void* h, float* out, char* err, int err_len);
typedef int (*strata_helper_owns_t)(void* h, int64_t index);
typedef int (*strata_helper_holds_t)(void* h, int64_t layer, int32_t expert);
/// Counters, in this order: resident, computed, launched_layers, returned_bytes, full_row_bytes; doubles: gib, ms_begin, ms_wait.
typedef void (*strata_helper_stats_t)(void* h, int64_t* counters5, double* doubles3);

#ifdef __cplusplus
}
#endif
