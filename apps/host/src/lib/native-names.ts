/**
 * A short name for a downloaded optimized model: the family and the quantization ("Swift IQ2_XS", "Gyro-S", "IQ3_S"), made from the id the
 * installation gives it (the family tag in front of the lower-cased quantization). The long name stays available as a tooltip.
 */
const FAMILIES: [string, string][] = [['swift-', 'Swift'], ['coder-', 'Coder'], ['unsloth-', 'Unsloth'], ['gyro-gyro-', 'Gyro'], ['gyro-', 'Gyro'], ['nvfp4-', 'NVFP4'], ['qwen36-', 'Qwen3.6']];

/**
 * The three NVFP4 versions, named by who made the weights (the plain model names NVFP4 / NVFP4-NVIDIA / NVFP4-QAD looked like the same thing):
 *  - NVFP4: Strata's own GPTQ conversion of Qwen's weights, the best quality of the three;
 *  - NVFP4-NVIDIA: NVIDIA's own NVFP4 checkpoint (plain rounding), converted for Strata, the same size and speed;
 *  - NVFP4-QAD: NVIDIA's FP4 checkpoint that was trained for FP4 (quantization-aware distillation), slightly faster on short prompts.
 * `note` is the one line that says how they differ.
 */
export const NVFP4_VERSIONS: Record<string, { name: string; note: string }> = {
  'NVFP4': { name: 'NVFP4 (Strata’s version)', note: 'Strata’s own conversion. The best quality of the NVFP4 versions.' },
  'NVFP4-NVIDIA': { name: 'NVFP4 (NVIDIA’s version)', note: 'NVIDIA’s own NVFP4 checkpoint, converted for Strata. Same size and speed.' },
  'NVFP4-QAD': { name: 'NVFP4 (NVIDIA, trained for FP4)', note: 'NVIDIA’s FP4 checkpoint, trained for FP4. Slightly faster on short prompts.' },
};
export const nvfp4Version = (model: string) => NVFP4_VERSIONS[String(model ?? '').toUpperCase()];

/**
 * One line on what each version is for, from the catalog (setup.py `about`), the model cards and docs/MODELS.md; versions with nothing verifiable
 * to say have no line. Keyed `family:model` (the engine's family id); every Swift size shares one line. The NVFP4 versions have their own
 * notes above. Each line is a key of the English catalog (locales/en.json), so it is translated like the rest.
 */
export const VERSION_ABOUT: Record<string, string> = {
  'qwen:Q2_0': 'The fastest size. The lowest quality of the four.',
  'qwen:IQ2_XS': 'Close to Q2_0 in speed, with a little better quality.',
  'qwen:IQ3_XXS': 'Better quality, but slower: more CPU work per token.',
  'qwen:IQ3_S': 'The best quality of the four, matching the full model on published benchmarks, and the slowest. Needs a 64 GB PC.',
  'swift:*': 'Thinks much shorter before answering, with about the same quality. Speed and memory like the same size of the original.',
  'coder:IQ1_M': 'For code: keeps the half of the experts that code, tools and pictures use. Weaker outside coding. Needs about 32 GB of RAM.',
  'unsloth:UD-IQ4_XS': 'About 4-bit: more quality than IQ3_S. With less than about 80 GB of RAM, part of the model is read from the SSD.',
  'unsloth:UD-Q4_K_XL': '4-bit: more quality than UD-IQ4_XS, and more memory.',
  'unsloth:UD-Q5_K_XL': '5-bit: close to Q8_0 in quality.',
  'unsloth:UD-Q6_K_XL': '6-bit: closer still to the full model.',
  'unsloth:Q8_0': '8-bit: the reference quality, for a PC with about 192 GB of RAM.',
  'gyro:Gyro-S': 'The smallest option, for PCs with little memory. Lower quality.',
  'gyro:Gyro-M': 'About IQ3_XXS quality with about 20% less graphics memory. A little slower.',
  'qwen36:UD-Q4_K_XL': 'A smaller model (35B, 3B active). 4-bit: the smallest of the three versions.',
  'qwen36:UD-Q6_K_XL': 'A smaller model (35B, 3B active). 6-bit: closer to the full model.',
  'qwen36:Q8_0': 'A smaller model (35B, 3B active). 8-bit: the closest to the full model.',
};
export const versionAboutText = (family: string, model: string): string => VERSION_ABOUT[`${family}:${model}`] ?? (family === 'swift' ? VERSION_ABOUT['swift:*'] : '');

export function nativeShortName(id: string): string {
  const lower = String(id ?? '').toLowerCase();
  for (const [prefix, label] of FAMILIES) {
    if (!lower.startsWith(prefix)) continue;
    const rest = lower.slice(prefix.length).toUpperCase();
    if (!rest) return label;
    if (label === 'NVFP4') return nvfp4Version(rest)?.name ?? `${label} ${rest}`;
    return label === 'Gyro' ? `Gyro-${rest.replace(/^GYRO-/, '')}` : `${label} ${rest}`;
  }
  return lower.toUpperCase() || String(id);
}
