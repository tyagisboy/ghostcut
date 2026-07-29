"""
GhostCut Offline - Interactive Export Quality Feedback Dialog
Allows users to rate output quality, report edge/hair defects, and automatically
tune AI self-critic and repair policies for similar material scenes.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QTextEdit, QFrame, QGroupBox, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class FeedbackDialog(QDialog):
    """
    Dialog displayed upon image export (or on demand) summarizing AI detected parameters
    and capturing user rating & defect flags to drive adaptive self-tuning learning.
    """
    feedback_submitted = pyqtSignal(dict)

    def __init__(self, parent=None, scene_metadata=None):
        super().__init__(parent)
        self.scene_metadata = scene_metadata or {}
        self.setWindowTitle("GhostCut AI Output Feedback & Policy Tuning")
        self.setMinimumWidth(560)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame#cardFrame {
                background-color: #252538;
                border-radius: 8px;
                border: 1px solid #313244;
                padding: 12px;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLabel#headerTitle {
                color: #89b4fa;
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#subTitle {
                color: #a6adc8;
                font-size: 12px;
            }
            QLabel#paramLabel {
                color: #94e2d5;
                font-size: 11px;
            }
            QLabel#paramValue {
                color: #f5e0dc;
                font-size: 11px;
                font-weight: bold;
            }
            QCheckBox {
                color: #cdd6f4;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #45475a;
                background-color: #313244;
            }
            QCheckBox::indicator:checked {
                background-color: #89b4fa;
                border: 1px solid #89b4fa;
            }
            QTextEdit {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                color: #cdd6f4;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton#btnSubmit {
                background-color: #89b4fa;
                color: #11111b;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton#btnSubmit:hover {
                background-color: #b4befe;
            }
            QPushButton#btnSkip {
                background-color: #313244;
                color: #cdd6f4;
                font-size: 12px;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton#btnSkip:hover {
                background-color: #45475a;
            }
            QRadioButton {
                color: #f9e2af;
                font-size: 13px;
                font-weight: bold;
            }
        """)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # Title Header
        title_label = QLabel("✨ GhostCut Output Quality & AI Self-Tuning Feedback")
        title_label.setObjectName("headerTitle")
        subtitle_label = QLabel("Rate the cutout quality to automatically optimize AI edge & alpha policies for this scene profile.")
        subtitle_label.setObjectName("subTitle")
        subtitle_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

        # 1. Detected AI Scene Parameters Card
        card_frame = QFrame()
        card_frame.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setSpacing(8)

        card_title = QLabel("📊 Detected Scene Parameters & Self-Critic Scores")
        card_title.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 13px;")
        card_layout.addWidget(card_title)

        # Extract metadata metrics
        dominant_mat = self.scene_metadata.get("dominant_material", "Hair & Skin")
        model_name = self.scene_metadata.get("model_name", "birefnet-general")
        critic_grade = self.scene_metadata.get("quality_grade", "A")
        overall_score = self.scene_metadata.get("overall_score", 0.983) * 100

        grid_layout = QHBoxLayout()
        
        col1 = QVBoxLayout()
        col1.addWidget(self._make_param_row("Dominant Material:", f"{dominant_mat}"))
        col1.addWidget(self._make_param_row("Active AI Model:", f"{model_name}"))
        
        col2 = QVBoxLayout()
        col2.addWidget(self._make_param_row("Self-Critic Grade:", f"Grade {critic_grade}"))
        col2.addWidget(self._make_param_row("Estimated Score:", f"{overall_score:.1f}%"))

        grid_layout.addLayout(col1)
        grid_layout.addLayout(col2)
        card_layout.addLayout(grid_layout)

        layout.addWidget(card_frame)

        # 2. Rating Group (1 to 5 Stars)
        rating_group = QGroupBox("⭐ Overall Cutout Rating")
        rating_group.setStyleSheet("QGroupBox { color: #89b4fa; font-weight: bold; border: 1px solid #313244; border-radius: 6px; margin-top: 6px; padding-top: 12px; }")
        rating_layout = QHBoxLayout(rating_group)

        self.rating_button_group = QButtonGroup(self)
        ratings = [("5 - Perfect", 5), ("4 - Good", 4), ("3 - Average", 3), ("2 - Poor", 2), ("1 - Severe Issues", 1)]
        
        for text, val in ratings:
            rb = QRadioButton(text)
            if val == 5:
                rb.setChecked(True)
            self.rating_button_group.addButton(rb, val)
            rating_layout.addWidget(rb)

        layout.addWidget(rating_group)

        # 3. Specific Defect Checkboxes
        defect_group = QGroupBox("🔍 Report Specific Defects (If Any)")
        defect_group.setStyleSheet("QGroupBox { color: #89b4fa; font-weight: bold; border: 1px solid #313244; border-radius: 6px; margin-top: 6px; padding-top: 12px; }")
        defect_layout = QVBoxLayout(defect_group)
        defect_layout.setSpacing(6)

        self.cb_flyaway = QCheckBox("Hair Flyaways Missing / Trimmed (Subpixel Hair Loss)")
        self.cb_blur_halo = QCheckBox("Clothing / Solid Edge Blurry (Grey Foggy Halo)")
        self.cb_color_bleed = QCheckBox("Studio Light Bleed / Color Spill Trapped in Hair")
        self.cb_cut_off = QCheckBox("Foreground Body Part / Subject Trimmed")
        self.cb_bg_noise = QCheckBox("Background Artifacts / Holes Remaining")

        defect_layout.addWidget(self.cb_flyaway)
        defect_layout.addWidget(self.cb_blur_halo)
        defect_layout.addWidget(self.cb_color_bleed)
        defect_layout.addWidget(self.cb_cut_off)
        defect_layout.addWidget(self.cb_bg_noise)

        layout.addWidget(defect_group)

        # 4. Optional Feedback Notes
        notes_label = QLabel("💬 Custom Feedback / Tuning Notes (Optional):")
        notes_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px;")
        layout.addWidget(notes_label)

        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Describe any specific area or edge defect you noticed...")
        self.txt_notes.setMaximumHeight(65)
        layout.addWidget(self.txt_notes)

        # 5. Buttons Layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_skip = QPushButton("Skip")
        self.btn_skip.setObjectName("btnSkip")
        self.btn_skip.clicked.connect(self.reject)

        self.btn_submit = QPushButton("Submit Feedback & Train AI")
        self.btn_submit.setObjectName("btnSubmit")
        self.btn_submit.clicked.connect(self._on_submit)

        btn_layout.addWidget(self.btn_skip)
        btn_layout.addWidget(self.btn_submit)

        layout.addLayout(btn_layout)

    def _make_param_row(self, label_text, val_text):
        row = QFrame()
        l = QHBoxLayout(row)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setObjectName("paramLabel")
        val = QLabel(val_text)
        val.setObjectName("paramValue")
        l.addWidget(lbl)
        l.addWidget(val)
        l.addStretch()
        return row

    def _on_submit(self):
        rating_val = self.rating_button_group.checkedId()
        defects = []
        if self.cb_flyaway.isChecked(): defects.append("hair_flyaways_missing")
        if self.cb_blur_halo.isChecked(): defects.append("clothing_edge_halo")
        if self.cb_color_bleed.isChecked(): defects.append("studio_light_bleed")
        if self.cb_cut_off.isChecked(): defects.append("foreground_cut_off")
        if self.cb_bg_noise.isChecked(): defects.append("background_noise_left")

        feedback_data = {
            "rating": rating_val,
            "defects": defects,
            "notes": self.txt_notes.toPlainText().strip(),
            "scene_metadata": self.scene_metadata
        }

        self.feedback_submitted.emit(feedback_data)
        self.accept()
