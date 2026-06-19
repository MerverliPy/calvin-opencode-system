---
profile_name: "Local Host PC Hardware Specification Profile"
intended_use: "Give ChatGPT, coding agents, opencode workflows, and local AI planning tools a precise hardware/software profile of this PC."
created_from: "User-provided screenshots of Geekbench 6, Geekbench Browser, CPU-Z, and GPU-Z"
created_date: "2026-06-19"
confidence_policy: "Only values visible in screenshots are listed as observed. Missing values are explicitly marked unknown."
---

# Local Host PC Specification Profile

## Purpose

This file is designed to be pasted into or uploaded to ChatGPT, an AI coding agent, an opencode workflow, or a local-model planning assistant so it can understand the local host PC specifications accurately.

The information below is extracted from screenshots of:

- Geekbench 6 desktop app
- Geekbench Browser result page
- CPU-Z
- GPU-Z

Where a value is not visible in the screenshots, it is marked **Unknown / not shown** rather than guessed.

---

# 1. High-Level System Summary

| Category | Specification |
|---|---|
| Operating System | Microsoft Windows 10 Pro 64-bit |
| Motherboard | ASUSTeK COMPUTER INC. PRIME Z390-A |
| CPU | Intel Core i7-9700K |
| CPU Generation / Codename | 9th Gen Intel / Coffee Lake |
| CPU Socket | LGA 1151 |
| CPU Cores / Threads | 8 cores / 8 threads |
| RAM | 48.0 GB DDR4 SDRAM |
| Memory Channels | 2 channels / dual-channel |
| GPU | NVIDIA GeForce RTX 4070 |
| GPU VRAM | 12,288 MB / 12 GB GDDR6X |
| Primary AI-Relevant Compute | NVIDIA CUDA-capable RTX 4070 with 12 GB VRAM |
| Geekbench 6 CPU Single-Core Score | 1693 |
| Geekbench 6 CPU Multi-Core Score | 7079 |

---

# 2. Machine-Readable Hardware Profile

```json
{
  "profile_name": "Local Host PC Hardware Specification Profile",
  "source": "User-provided screenshots: Geekbench 6, Geekbench Browser, CPU-Z, GPU-Z",
  "confidence_policy": "Only observed screenshot values are listed as observed. Unknown values are marked unknown.",
  "system": {
    "operating_system": {
      "name": "Microsoft Windows 10 Pro",
      "architecture": "64-bit",
      "source": "Geekbench screenshots"
    },
    "model": {
      "reported_model": "System manufacturer System Product Name",
      "note": "Generic SMBIOS model string; not a branded OEM model.",
      "source": "Geekbench screenshots"
    },
    "motherboard": {
      "manufacturer": "ASUSTeK COMPUTER INC.",
      "model": "PRIME Z390-A",
      "chipset_platform": "Intel Z390 platform",
      "source": "Geekbench screenshots"
    },
    "power_plan": {
      "windows_power_plan": "High performance",
      "source": "Geekbench Browser screenshot"
    }
  },
  "cpu": {
    "name": "Intel Core i7-9700K",
    "specification": "Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz",
    "generation": "9th Gen Intel Core",
    "codename": "Coffee Lake",
    "socket": "Socket 1151 LGA",
    "process_node": "14 nm",
    "max_tdp_watts": 95,
    "physical_processors": 1,
    "cores": 8,
    "threads": 8,
    "base_frequency_ghz": 3.60,
    "maximum_frequency_observed_mhz": 4913,
    "cpu_z_core_speed_mhz": 4915.53,
    "cpu_z_multiplier": "x49.0 (8.0 - 49.0)",
    "cpu_z_bus_speed_mhz": 100.32,
    "cpu_z_core_voltage_volts": 0.941,
    "family": "6",
    "model": "E",
    "stepping": "D",
    "ext_family": "6",
    "ext_model": "9E",
    "revision": "R0",
    "identifier": "GenuineIntel Family 6 Model 158 Stepping 13",
    "instruction_sets_observed": [
      "MMX",
      "SSE",
      "SSE2",
      "SSE3",
      "SSSE3",
      "SSE4.1",
      "SSE4.2",
      "EM64T",
      "AES",
      "AVX",
      "AVX2",
      "FMA3"
    ],
    "cache": {
      "l1_data": "8 x 32 KB, 8-way",
      "l1_instruction": "8 x 32 KB, 8-way",
      "l2": "8 x 256 KB, 4-way",
      "l3": "12 MB, 12-way"
    },
    "source": "CPU-Z and Geekbench screenshots"
  },
  "memory": {
    "total_memory_gb": 48.0,
    "type": "DDR4 SDRAM",
    "transfer_rate_mt_s": 2674,
    "channels": 2,
    "ram_stick_layout": "Unknown / not shown",
    "timings": "Unknown / not shown",
    "xmp_status": "Unknown / not shown",
    "source": "Geekbench Browser screenshot"
  },
  "gpu": {
    "name": "NVIDIA GeForce RTX 4070",
    "gpu_die_reported": "AD103",
    "revision": "A1",
    "technology": "5 nm",
    "die_size_mm2": 379,
    "transistors_million": 45900,
    "release_date_reported_by_gpu_z": "Mar 2024",
    "bios_version": "95.03.3C.00.40",
    "subvendor": "NVIDIA",
    "device_id": "10DE 2709 - 10DE 1802",
    "uefi": true,
    "rops_tmus": "64 / 184",
    "bus_interface": "PCIe x16 3.0 @ x16 1.1",
    "shaders_cuda_cores_reported": 5888,
    "directx_support": "12 (12_2)",
    "pixel_fillrate_gpixels_s": 162.2,
    "texture_fillrate_gtexels_s": 466.4,
    "memory_type": "GDDR6X (Micron)",
    "memory_size_mb": 12288,
    "memory_size_gb": 12,
    "memory_bus_width_bit": 192,
    "memory_bandwidth_gb_s": 504.2,
    "driver_version": "32.0.15.9186 (NVIDIA 591.86) DCH / Win10 64",
    "driver_date": "Jan 20, 2026",
    "digital_signature": "WHQL",
    "gpu_clock_mhz": 1920,
    "memory_clock_mhz": 1313,
    "boost_clock_mhz": 2535,
    "default_gpu_clock_mhz": 1920,
    "default_memory_clock_mhz": 1313,
    "default_boost_clock_mhz": 2535,
    "nvidia_sli": "Disabled",
    "resizable_bar": "Disabled",
    "compute_support": [
      "OpenCL",
      "CUDA",
      "DirectCompute",
      "DirectML"
    ],
    "graphics_technology_support": [
      "Vulkan",
      "Ray Tracing",
      "PhysX",
      "OpenGL 4.6"
    ],
    "source": "GPU-Z screenshot"
  },
  "benchmarks": {
    "geekbench_6_cpu": {
      "version": "Geekbench 6.7.1 for Windows AVX2",
      "single_core_score": 1693,
      "multi_core_score": 7079,
      "valid_result": true,
      "upload_date": "June 10, 2026 11:22 AM",
      "browser_result_url_visible": "https://browser.geekbench.com/v6/cpu/18304280",
      "source": "Geekbench Browser screenshot"
    }
  },
  "local_ai_relevance": {
    "best_local_model_range": "7B to 14B parameter models, preferably quantized",
    "comfortable_models": [
      "3B to 4B models",
      "7B to 8B models",
      "9B to 12B quantized models"
    ],
    "possible_but_tight": [
      "13B to 14B quantized models"
    ],
    "not_ideal_locally": [
      "30B+ models unless heavily quantized and/or CPU/RAM offloaded"
    ],
    "primary_constraint": "12 GB GPU VRAM",
    "secondary_constraint": "8-core / 8-thread CPU without Hyper-Threading",
    "recommended_runtime_types": [
      "Ollama",
      "LM Studio",
      "llama.cpp",
      "Open WebUI",
      "CUDA-enabled local inference runtimes"
    ]
  },
  "unknown_or_not_visible": {
    "storage_drives": "Unknown / not shown",
    "ssd_or_nvme_model": "Unknown / not shown",
    "power_supply_wattage": "Unknown / not shown",
    "cpu_cooler": "Unknown / not shown",
    "case_airflow": "Unknown / not shown",
    "bios_version": "Unknown / not shown",
    "ram_stick_layout": "Unknown / not shown",
    "ram_timings": "Unknown / not shown",
    "xmp_enabled": "Unknown / not shown",
    "cpu_temperature": "Unknown / not shown",
    "gpu_temperature": "Unknown / not shown"
  }
}
```

---

# 3. Detailed CPU Specification

| Field | Value |
|---|---|
| CPU | Intel Core i7-9700K |
| Specification String | Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz |
| Codename | Coffee Lake |
| Generation | 9th Gen Intel Core |
| Socket | Socket 1151 LGA |
| Process | 14 nm |
| Max TDP | 95 W |
| Physical CPU Count | 1 |
| Cores | 8 |
| Threads | 8 |
| Base Frequency | 3.60 GHz |
| Max Frequency Shown | 4913 MHz / ~4.91 GHz |
| CPU-Z Core Speed Shown | 4915.53 MHz |
| Multiplier | x49.0, range x8.0 to x49.0 |
| Bus Speed | 100.32 MHz |
| Core Voltage Shown | 0.941 V |
| Revision | R0 |
| Identifier | GenuineIntel Family 6 Model 158 Stepping 13 |
| Instruction Sets Shown | MMX, SSE, SSE2, SSE3, SSSE3, SSE4.1, SSE4.2, EM64T, AES, AVX, AVX2, FMA3 |

## CPU Cache

| Cache Level | Value |
|---|---|
| L1 Data Cache | 8 × 32 KB, 8-way |
| L1 Instruction Cache | 8 × 32 KB, 8-way |
| L2 Cache | 8 × 256 KB, 4-way |
| L3 Cache | 12 MB, 12-way |

---

# 4. Detailed Memory Specification

| Field | Value |
|---|---|
| Total RAM | 48.0 GB |
| Type | DDR4 SDRAM |
| Transfer Rate Shown | 2674 MT/s |
| Channels | 2 / dual-channel |
| Stick Layout | Unknown / not shown |
| Timings | Unknown / not shown |
| XMP Status | Unknown / not shown |

## Memory Notes

The system has enough system RAM for coding agents, WSL, Docker, IDEs, browser-heavy research, and local LLM workflows. The exact RAM module layout is not visible. Because the system has 48 GB, it may use a mixed-capacity configuration. Confirm with CPU-Z SPD tab or BIOS if exact module layout matters.

---

# 5. Detailed GPU Specification

| Field | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 4070 |
| GPU Die Reported | AD103 |
| Revision | A1 |
| Process | 5 nm |
| Die Size | 379 mm² |
| Transistors | 45,900 million |
| BIOS Version | 95.03.3C.00.40 |
| Subvendor | NVIDIA |
| Device ID | 10DE 2709 - 10DE 1802 |
| UEFI | Enabled / checked |
| ROPs / TMUs | 64 / 184 |
| Bus Interface Shown | PCIe x16 3.0 @ x16 1.1 |
| CUDA Cores / Shaders Reported | 5,888 |
| DirectX Support | 12 / feature level 12_2 |
| Pixel Fillrate | 162.2 GPixel/s |
| Texture Fillrate | 466.4 GTexel/s |
| VRAM Type | GDDR6X Micron |
| VRAM Size | 12,288 MB / 12 GB |
| Memory Bus Width | 192-bit |
| Memory Bandwidth | 504.2 GB/s |
| Driver Version | 32.0.15.9186 / NVIDIA 591.86 DCH / Win10 64 |
| Driver Date | Jan 20, 2026 |
| Digital Signature | WHQL |
| GPU Clock | 1920 MHz |
| Memory Clock | 1313 MHz |
| Boost Clock | 2535 MHz |
| NVIDIA SLI | Disabled |
| Resizable BAR | Disabled |

## GPU Compute / API Support

| API / Feature | Status |
|---|---|
| CUDA | Supported |
| OpenCL | Supported |
| DirectCompute | Supported |
| DirectML | Supported |
| Vulkan | Supported |
| Ray Tracing | Supported |
| PhysX | Supported |
| OpenGL | OpenGL 4.6 supported |

## GPU Notes

The RTX 4070 is the strongest component in this system for AI inference and GPU-accelerated workloads. The main limitation for local LLMs is the 12 GB VRAM capacity.

Resizable BAR is shown as disabled. For best modern GPU configuration, check BIOS settings for:

- Above 4G Decoding
- Resizable BAR
- UEFI boot / CSM disabled if required by the motherboard BIOS

---

# 6. Geekbench 6 CPU Result

| Field | Value |
|---|---|
| Geekbench Version | Geekbench 6.7.1 for Windows AVX2 |
| Single-Core Score | 1693 |
| Multi-Core Score | 7079 |
| Valid Result | Yes |
| Upload Date Shown | June 10, 2026 11:22 AM |
| Visible Result URL | https://browser.geekbench.com/v6/cpu/18304280 |
| Windows Power Plan | High performance |

---

# 7. Local AI / Coding Agent Suitability

## Recommended Local Model Class

This PC is best suited for:

- 3B to 4B models: fast and comfortable
- 7B to 8B models: strong fit
- 9B to 12B quantized models: usable and practical
- 13B to 14B quantized models: possible but VRAM-constrained
- 30B+ models: not ideal locally unless heavily quantized, offloaded to system RAM, or run with lower context/performance expectations

## Best-Fit Local AI Use Cases

| Use Case | Suitability |
|---|---|
| opencode coding assistant with cloud fallback | Good |
| Local coding model for small/medium tasks | Good |
| Local LLM experimentation | Good |
| RAG with small-to-medium embeddings and local models | Good |
| Stable Diffusion / image generation | Good |
| Heavy multi-agent local-only workflows | Limited by CPU threads and VRAM |
| Large 30B+ local coding models | Not ideal |
| Large-context local inference | Limited by VRAM and RAM bandwidth |

## Main Bottlenecks

| Bottleneck | Reason |
|---|---|
| CPU | i7-9700K has 8 cores and 8 threads, no Hyper-Threading |
| VRAM | RTX 4070 has 12 GB VRAM, which limits larger local LLMs |
| RAM speed/configuration | DDR4 shown at 2674 MT/s; exact module layout and timings unknown |
| Platform age | Z390 / LGA1151 platform is older compared with modern DDR5 systems |

---

# 8. Recommended Agent/LLM Configuration Assumption

When another ChatGPT or AI agent uses this file, it should assume the following baseline:

```text
Local host PC: Windows 10 Pro 64-bit desktop with ASUS PRIME Z390-A motherboard, Intel Core i7-9700K 8C/8T CPU, 48 GB DDR4 RAM, and NVIDIA GeForce RTX 4070 12 GB GDDR6X GPU. Best local LLM target is 7B-14B quantized models. Use CUDA acceleration where possible. Avoid assuming this PC can comfortably run 30B+ models fully on GPU. For opencode/coding-agent workflows, use this machine as a strong GPU-assisted local workstation but pair it with cloud APIs for larger models, long-context reasoning, or heavy multi-agent orchestration.
```

---

# 9. Unknown / Missing Hardware Data

The following information was not visible in the screenshots and should be collected separately for a complete hardware inventory:

| Missing Spec | Why It Matters |
|---|---|
| Storage drive model(s) | Determines repo indexing, build, Docker, and model-loading performance |
| NVMe/SATA status | Determines disk I/O bottlenecks |
| PSU wattage and model | Important for GPU stability and upgrade planning |
| CPU cooler | Important for sustained i7-9700K boost clocks |
| Case airflow and temperatures | Important for sustained GPU and CPU workloads |
| BIOS version | Important for Resizable BAR, stability, and CPU/memory compatibility |
| RAM module layout | Important because 48 GB may be mixed-capacity DIMMs |
| RAM timings / XMP | Important for CPU-bound workload performance |
| WSL/Docker configuration | Important for opencode and agentic coding workflows |
| NVIDIA CUDA Toolkit version | Important for local AI runtime compatibility |

---

# 10. Suggested One-Line Description

**Windows 10 Pro workstation with ASUS PRIME Z390-A, Intel Core i7-9700K 8C/8T, 48 GB DDR4, and NVIDIA RTX 4070 12 GB; suitable for CUDA-accelerated local AI, 7B-14B quantized LLMs, coding agents, WSL/Docker workflows, and cloud-assisted opencode development.**
