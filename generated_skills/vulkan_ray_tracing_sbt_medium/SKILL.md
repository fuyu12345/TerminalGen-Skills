---
name: fixing-vulkan-ray-tracing-sbt-strides
description: Compute correct Vulkan ray tracing SBT strides from device properties and shader record sizes, then emit machine-checkable output. Use when debugging SBT alignment/stride errors or generating stride values for raygen/miss/hit/callable regions.
---

# Fixing Vulkan Ray Tracing SBT Strides

## When to Use

- Fixing crashes/validation errors around `vkCmdTraceRaysKHR` SBT setup.
- Converting device RT properties + shader record layout into correct per-region strides.
- Producing a JSON/config artifact with stride bytes for raygen, miss, hit, callable.

## Minimal Reliable Workflow

1. **Extract required limits from device properties**
   - Read:
     - `shaderGroupHandleSize`
     - `shaderGroupHandleAlignment`
     - `shaderGroupBaseAlignment`
     - `maxShaderGroupStride`

2. **Extract per-record payload sizes from shader config**
   - For each region type: `raygen`, `miss`, `hit`, `callable`, get extra shader record bytes.
   - Define `rawSize = shaderGroupHandleSize + recordDataSize`.

3. **Apply the correct alignment rule per region**
   - Use `align_up(x, a) = ((x + a - 1) / a) * a`.
   - Compute:
     - `raygen_stride = align_up(raw_raygen, shaderGroupBaseAlignment)`
     - `miss_stride = align_up(raw_miss, shaderGroupHandleAlignment)`
     - `hit_stride = align_up(raw_hit, shaderGroupHandleAlignment)`
     - `callable_stride = align_up(raw_callable, shaderGroupHandleAlignment)`

4. **Enforce hard validity checks**
   - Ensure every stride is a positive integer.
   - Ensure every stride `>= shaderGroupHandleSize`.
   - Ensure every stride `<= maxShaderGroupStride`.

5. **Emit output in required schema**
   - Write:
   ```json
   {
     "raygen_stride": <int>,
     "miss_stride": <int>,
     "hit_stride": <int>,
     "callable_stride": <int>
   }
   ```

## Common Pitfalls

- **Aligning raygen stride to handle alignment instead of base alignment.**  
  Raygen uses stricter base-alignment requirements in typical Vulkan RT setups.

- **Ignoring shader record payload bytes.**  
  Stride must fit handle + record data, not just handle size.

- **Computing valid strides but forgetting max stride constraint.**  
  Always compare to `maxShaderGroupStride`.

- **Fixing only stride math while leaving region sizing/offset logic inconsistent.**  
  Region `size` and offsets must stay consistent with computed stride and group counts.

## Verification Strategy

1. **Numerical verification (must pass before any tests)**
   - Recompute all four strides from source data in one script/calc block.
   - Assert:
     - modulo checks against required alignment
     - `>= handle size`
     - `<= maxShaderGroupStride`

2. **Schema verification**
   - Validate JSON parses and includes exactly required fields with integer values.

3. **Harness sanity check (important from observed runs)**
   - If tests fail with parser errors (e.g., `IndexError` while parsing properties text), inspect test parsing logic before changing stride math.
   - In the observed runs, computed strides were consistent and likely correct, while failure came from brittle line parsing in the test harness rather than alignment arithmetic.

## References to Load On Demand

- Vulkan spec sections for `VkStridedDeviceAddressRegionKHR` alignment/stride constraints.
- Utility snippet for `align_up` and SBT layout validation assertions.
