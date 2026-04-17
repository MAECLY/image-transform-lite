# Project Roadmap & TODOs - Image Transform Lite

## 🎯 UVP: "The Instant-Pipeline for macOS Power Users"

**Goal:** Win on Frictionless Velocity. Combine the power of ImageMagick with a modular visual UX, optimized for Apple Silicon.

---

## 🟢 Phase 1: Analysis & Strategy (Completed ✅)

- [x] **Market Research**: Analyze XnConvert, ImageMagick, and Squoosh.
- [x] **Unique Value Proposition (UVP)**: Defined as "Frictionless Velocity" for macOS.
- [x] **Technical Feasibility Study**: Identified `ProcessPoolExecutor` and CoreML as key drivers.

## 🟡 Phase 2: The "Squoosh" Experience (UX/DX)

- [x] **Live Preview Window**: Add a "Before/After" sample image that updates in real-time as sliders change.
- [x] **Output Format Expansion**: Support JPEG, PNG, TIFF (Remove WebP-only restriction).
- [x] **Preset System**: Save/Load transformation chains as JSON (Recetas).
- [ ] **Advanced Logging**: Per-image success/failure reports.

## 🟠 Phase 3: Apple Silicon Performance (The Differentiators)

- [ ] **Parallel Processing Engine**: Migrating `BatchProcessor` from single-thread to `ProcessPoolExecutor` for multi-core utilization.
- [ ] **AI Smart Crop**: Implement saliency-based cropping (Subject Detection) using a lightweight macOS-compatible model.
- [ ] **Siri/Shortcuts Integration**: Allow triggering transforms via macOS Shortcuts.
- [ ] **Advanced Color Profiles**: sRGB/AdobeRGB conversion pipeline.

## 🔴 Phase 4: Hardening & Distribution

- [ ] **Comprehensive Test Suite**: Regression tests for all transform combinations.
- [ ] **App Bundle Optimization**: Minimize binary size and optimize startup time.
- [ ] **User Feedback Loop**: Basic feedback mechanism.
