# Implementation Plan v9.2.0: Interactive Export Feedback Form & Self-Tuning Policy Loop

## Context & User Requirement
The user selected Option 1 to test v9.1.0 on new images, and requested a new interactive export feedback feature:
> *"once a user export an output it gets exported by user get the feedback and get the feedback on all the parameter you have and detected for the image, take users input on those pointers. Make a simple form to get the feedback on all output pointers so that app can refine in itself and do self critic and do local repair, and improvise all the policies used in that particular scene."*

---

## Technical Overhaul in v9.2.0

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        GhostCut Offline v9.2.0 GUI (PyQt6)                             │
│                                                                                        │
│   [ Image Canvas ]  ──► [ Export Output Image ]                                        │
│                                   │                                                    │
│                                   ▼                                                    │
│               ┌──────────────────────────────────────────────┐                         │
│               │   Export Feedback & Quality Tuning Modal     │                         │
│               ├──────────────────────────────────────────────┤                         │
│               │ 1. AI Analysis & Detected Parameters:         │                         │
│               │    • Dominant Material: Hair 68%, Skin 32%   │                         │
│               │    • Model Used: birefnet-general            │                         │
│               │    • Self-Critic Score: 98.3% (Grade A)      │                         │
│               │                                              │                         │
│               │ 2. User Quality Ratings & Feedback:          │                         │
│               │    • Rating: ★★★★★                           │                         │
│               │    • Defect Checkboxes:                      │                         │
│               │      [ ] Hair Flyaways Missing               │                         │
│               │      [ ] Clothing Edge Blurry / Halo         │                         │
│               │      [ ] Color Bleed / Studio Light Haze     │                         │
│               │    • Notes: [ User input text box ]          │                         │
│               │                                              │                         │
│               │   [ Submit Feedback & Train AI ]  [ Skip ]   │                         │
│               └──────────────────────┬───────────────────────┘                         │
└──────────────────────────────────────┼─────────────────────────────────────────────────┘
                                       │
                                       ▼
       ┌──────────────────────────────────────────────────────────────┐
       │   Adaptive Learning Engine & Self-Critic Policy Tuning       │
       │   - Logs user feedback into offline JSON memory              │
       │   - Auto-adjusts strategy weights for similar material scenes│
       └──────────────────────────────────────────────────────────────┘
```

### 1. PyQt6 Feedback Dialog Component (`src/gui/components/feedback_dialog.py`)
- Modern, glassmorphic dark-mode PyQt6 `QDialog`.
- **Detected Parameters Card**:
  - Displays detected Material Confidence Breakdown (Skin, Hair, Fabric, Fur %).
  - Displays Vision Intelligence Flags (Face Detected, Glasses, Fabric Texture).
  - Displays Active Engine Config (Model weights, Erode size, Matting mode, Decontamination mode).
  - Displays Self-Critic Quality Metrics (Edge score, Alpha score, Halo score, Overall grade).
- **User Feedback Form**:
  - Star Rating Widget (1 to 5 Stars).
  - Specific Defect Checkboxes:
    - `Hair Flyaways Missing`
    - `Clothing Edge Blurry / Halo`
    - `Studio Light Bleed / Color Haze`
    - `Foreground Cut Off`
    - `Background Noise Left`
  - Feedback Notes Text Area.

### 2. MainWindow Export Integration (`src/gui/main_window.py`)
- Automatically opens the `FeedbackDialog` upon successful export (with a toggle option "Show feedback dialog after export" in settings/sidebar).
- Adds a **"Rate & Fine-Tune AI"** CTA button in the main window toolbar for manual access at any time.

### 3. Self-Tuning Policy Memory (`src/core/adaptive_learning.py`)
- Records user ratings, defect checkboxes, and scene parameters into `user_feedback_history.json`.
- When user flags a defect (e.g. "Hair Flyaways Missing"), the **Adaptive Learning Recipe Ranking Engine** automatically updates its rule overrides for that material profile, boosting subpixel flyaway protection and tuning local repair thresholds for future runs.

---

## User Review Required

> [!IMPORTANT]
> **Interactive Feedback & Self-Tuning Loop**: Upon exporting an image, GhostCut will display an interactive modal summarizing all AI-detected parameters and quality scores, allowing you to rate the result, report specific edge/hair defects, and automatically refine the AI's internal policies for that scene type.

---

## Proposed Changes

### [Component: GUI & Feedback Modal]

#### [NEW] [feedback_dialog.py](file:///H:/AI%20Tools/Background%20Removal/Ai%20Project/src/gui/components/feedback_dialog.py)
- Interactive PyQt6 dialog displaying AI parameters, star rating, defect checkboxes, and feedback submission.

#### [MODIFY] [main_window.py](file:///H:/AI%20Tools/Background%20Removal/Ai%20Project/src/gui/main_window.py)
- Connect image export handler to launch `FeedbackDialog`.
- Add "Rate & Fine-Tune AI" toolbar button.

### [Component: Core Adaptive Learning & Policy Storage]

#### [MODIFY] [adaptive_learning.py](file:///H:/AI%20Tools/Background%20Removal/Ai%20Project/src/core/adaptive_learning.py)
- Implement `log_user_feedback()` and auto-tuning parameter overrides based on user rating history.

---

## Verification Plan

### Automated Verification
- Run `py -u test_run.py` to ensure unit test suite passes.

### Manual GUI Verification
- Run `py -m src.main` to launch GhostCut GUI.
- Process and export an image, verifying the Feedback Dialog renders cleanly, displays all detected parameters, and logs feedback into offline memory.
