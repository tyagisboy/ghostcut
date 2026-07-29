import os
from PyQt6.QtWidgets import QToolBar, QComboBox, QSlider, QLabel, QSizePolicy, QWidget, QHBoxLayout, QVBoxLayout, QCheckBox, QPushButton, QButtonGroup, QToolButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QPixmap

class ToolBar(QToolBar):
    """
    Vertical Selection Toolbar (Left side) containing selection and drawing tools.
    """
    tool_changed = pyqtSignal(str)            # "pan", "wand", "lasso", "grabcut", "brush_add", "brush_sub"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tool_mode = "pan"
        self.setMovable(False)
        self.setOrientation(Qt.Orientation.Vertical)
        self.setIconSize(QSize(22, 22))        # Sleek, clean icon sizing
        
        # Calculate assets path (src/gui/assets/)
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(current_dir, "assets")
        
        self.init_ui()

    def get_icon(self, name):
        icon = QIcon()
        line_svg = os.path.join(self.assets_dir, f"{name}_line.svg")
        fill_svg = os.path.join(self.assets_dir, f"{name}_fill.svg")
        line_png = os.path.join(self.assets_dir, f"{name}_line.png")
        fill_png = os.path.join(self.assets_dir, f"{name}_fill.png")
        
        line_path = line_svg if os.path.exists(line_svg) else line_png
        fill_path = fill_svg if os.path.exists(fill_svg) else fill_png
        
        if os.path.exists(line_path):
            icon.addFile(line_path, QSize(32, 32), QIcon.Mode.Normal, QIcon.State.Off)
        if os.path.exists(fill_path):
            icon.addFile(fill_path, QSize(32, 32), QIcon.Mode.Normal, QIcon.State.On)
            icon.addFile(fill_path, QSize(32, 32), QIcon.Mode.Active, QIcon.State.Off)
            icon.addFile(fill_path, QSize(32, 32), QIcon.Mode.Active, QIcon.State.On)
            icon.addFile(fill_path, QSize(32, 32), QIcon.Mode.Selected, QIcon.State.Off)
            icon.addFile(fill_path, QSize(32, 32), QIcon.Mode.Selected, QIcon.State.On)
        return icon

    def init_ui(self):
        # Selection Mode Actions (Exclusive)
        self.pan_action = QAction(self.get_icon("pan"), "Pan & Zoom", self)
        self.pan_action.setCheckable(True)
        self.pan_action.setChecked(True)
        self.pan_action.setToolTip("Pan and Zoom Tool")
        self.pan_action.triggered.connect(lambda: self.set_tool("pan"))
        
        self.wand_action = QAction(self.get_icon("wand"), "Magic Wand", self)
        self.wand_action.setCheckable(True)
        self.wand_action.setToolTip("Magic Wand Selection (CIELAB Color Match)")
        self.wand_action.triggered.connect(lambda: self.set_tool("wand"))

        self.lasso_action = QAction(self.get_icon("lasso"), "Lasso Selection", self)
        self.lasso_action.setCheckable(True)
        self.lasso_action.setToolTip("Polygon Lasso Selection (Double Click to Close)")
        self.lasso_action.triggered.connect(lambda: self.set_tool("lasso"))

        self.grabcut_action = QAction(self.get_icon("grabcut"), "GrabCut Box", self)
        self.grabcut_action.setCheckable(True)
        self.grabcut_action.setToolTip("GrabCut Bounding Box selection")
        self.grabcut_action.triggered.connect(lambda: self.set_tool("grabcut"))

        self.brush_add_action = QAction(self.get_icon("brush_add"), "Restore Brush", self)
        self.brush_add_action.setCheckable(True)
        self.brush_add_action.setToolTip("Restore Subject pixels (paint green outline)")
        self.brush_add_action.triggered.connect(lambda: self.set_tool("brush_add"))

        self.brush_sub_action = QAction(self.get_icon("brush_sub"), "Erase Brush", self)
        self.brush_sub_action.setCheckable(True)
        self.brush_sub_action.setToolTip("Erase Background pixels (paint red outline)")
        self.brush_sub_action.triggered.connect(lambda: self.set_tool("brush_sub"))

        self.refine_edge_action = QAction(self.get_icon("refine_edge"), "Refine Edges", self)
        self.refine_edge_action.setCheckable(True)
        self.refine_edge_action.setToolTip("Refine Edges (curly hair, long strands, complex edges)")
        self.refine_edge_action.triggered.connect(lambda: self.set_tool("refine_edge"))

        # Add to toolbar
        self.addAction(self.pan_action)
        self.addAction(self.wand_action)
        self.addAction(self.lasso_action)
        self.addAction(self.grabcut_action)
        self.addAction(self.brush_add_action)
        self.addAction(self.brush_sub_action)
        self.addAction(self.refine_edge_action)

        self.actions_group = [
            self.pan_action, self.wand_action, self.lasso_action, 
            self.grabcut_action, self.brush_add_action, self.brush_sub_action,
            self.refine_edge_action
        ]

    def set_tool(self, tool_name):
        self.tool_mode = tool_name
        
        selected_action = {
            "pan": self.pan_action,
            "wand": self.wand_action,
            "lasso": self.lasso_action,
            "grabcut": self.grabcut_action,
            "brush_add": self.brush_add_action,
            "brush_sub": self.brush_sub_action,
            "refine_edge": self.refine_edge_action
        }.get(tool_name)
        
        for act in self.actions_group:
            act.setChecked(act == selected_action)

        self.tool_changed.emit(tool_name)


class ParametersBar(QToolBar):
    """
    Horizontal Parameters/Options Toolbar (Top side) showing tool controls.
    Organized in a 2-row layout with minimal icons and manual refinement controls.
    """
    tolerance_changed = pyqtSignal(int)
    brush_size_changed = pyqtSignal(int)
    model_changed = pyqtSignal(str)
    undo_triggered = pyqtSignal()
    redo_triggered = pyqtSignal()
    matting_settings_changed = pyqtSignal(bool, int, bool, int, bool, str)
    smooth_edges_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setIconSize(QSize(20, 20))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(current_dir, "assets")
        
        self.last_applied_state = {
            "model": "birefnet-general",
            "processing_mode": "fast",
            "apply_matting": True,
            "erode_size": 7,
            "preserve_trans": False,
            "sharpness": 0,
            "decontaminate": True
        }
        
        self.init_ui()

    def get_icon(self, name):
        icon = QIcon()
        line_svg = os.path.join(self.assets_dir, f"{name}_line.svg")
        fill_svg = os.path.join(self.assets_dir, f"{name}_fill.svg")
        line_png = os.path.join(self.assets_dir, f"{name}_line.png")
        fill_png = os.path.join(self.assets_dir, f"{name}_fill.png")
        
        line_path = line_svg if os.path.exists(line_svg) else line_png
        fill_path = fill_svg if os.path.exists(fill_svg) else fill_png
        
        if os.path.exists(line_path):
            icon.addFile(line_path, QSize(32, 32), QIcon.Mode.Normal, QIcon.State.Off)
        if os.path.exists(fill_path):
            icon.addFile(fill_path, QSize(32, 32), QIcon.Mode.Normal, QIcon.State.On)
            icon.addFile(fill_path, QSize(32, 32), QIcon.Mode.Active, QIcon.State.Off)
            icon.addFile(fill_path, QSize(32, 32), QIcon.Mode.Active, QIcon.State.On)
            icon.addFile(fill_path, QSize(32, 32), QIcon.Mode.Selected, QIcon.State.Off)
            icon.addFile(fill_path, QSize(32, 32), QIcon.Mode.Selected, QIcon.State.On)
            
        # Fallback to direct name if line or fill not found
        if not os.path.exists(line_path) and not os.path.exists(fill_path):
            direct_svg = os.path.join(self.assets_dir, f"{name}.svg")
            direct_png = os.path.join(self.assets_dir, f"{name}.png")
            if os.path.exists(direct_svg):
                icon.addFile(direct_svg, QSize(32, 32))
            elif os.path.exists(direct_png):
                icon.addFile(direct_png, QSize(32, 32))
        return icon

    def create_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #4d4d4d; max-height: 20px; min-height: 20px;")
        return line

    def init_ui(self):
        # We put all elements in a central container widget to organize them in 2 rows
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #181818;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #aaaaaa;
                font-size: 11px;
                font-weight: 500;
            }
            QComboBox {
                background-color: #252525;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 4px 10px 4px 6px;
                color: #ffffff;
                font-size: 11px;
                min-width: 155px;
            }
            QComboBox:hover {
                border-color: #3b82f6;
                background-color: #2d2d2d;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 4px;
                selection-background-color: #3b82f6;
                selection-color: #ffffff;
                color: #d0d0d0;
                padding: 4px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #2a2a2a;
                height: 4px;
                background: #252525;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #666666;
                border: 1px solid #444444;
                width: 10px;
                height: 10px;
                margin: -3px 0;
                border-radius: 5px;
            }
            QSlider::handle:horizontal:hover {
                background: #3b82f6;
                border-color: #2563eb;
            }
            QCheckBox {
                color: #e0e0e0;
                font-size: 11px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #2b2b2b;
                border-color: #3d3d3d;
            }
            QToolButton:pressed {
                background-color: #1f1f1f;
            }
        """)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(6)

        # Row 1 Horizontal Layout
        row1_layout = QHBoxLayout()
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(10)

        # Row 2 Horizontal Layout
        row2_layout = QHBoxLayout()
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(10)

        # Create row 1 elements
        # 1. Undo / Redo
        self.btn_undo = QToolButton(self)
        self.btn_undo.setIcon(self.get_icon("undo"))
        self.btn_undo.setToolTip("Undo")
        self.btn_undo.setFixedWidth(32)
        self.btn_undo.clicked.connect(self.undo_triggered.emit)
        row1_layout.addWidget(self.btn_undo)

        self.btn_redo = QToolButton(self)
        self.btn_redo.setIcon(self.get_icon("redo"))
        self.btn_redo.setToolTip("Redo")
        self.btn_redo.setFixedWidth(32)
        self.btn_redo.clicked.connect(self.redo_triggered.emit)
        row1_layout.addWidget(self.btn_redo)

        row1_layout.addWidget(self.create_divider())

        # 2. Model Selection (with outline smart_toy robot icon label)
        model_icon_lbl = QLabel()
        model_icon_lbl.setPixmap(self.get_icon("smart_toy").pixmap(16, 16))
        model_icon_lbl.setToolTip("AI Segmentation Model")
        row1_layout.addWidget(model_icon_lbl)

        self.model_combo = QComboBox()
        self.model_combo.addItem("BiRefNet High-Res", "birefnet-general")
        self.model_combo.setItemData(0, "Best quality. Highly recommended for complex borders, hair, and fine details.", Qt.ItemDataRole.ToolTipRole)
        self.model_combo.addItem("BiRefNet Lite", "birefnet-general-lite")
        self.model_combo.setItemData(1, "Fast and lightweight version of BiRefNet. Good for quick previews.", Qt.ItemDataRole.ToolTipRole)
        self.model_combo.addItem("ISNet General Purpose", "isnet-general-use")
        self.model_combo.setItemData(2, "Optimized for general object segmentation and structured shapes.", Qt.ItemDataRole.ToolTipRole)
        self.model_combo.addItem("U2Net General", "u2net")
        self.model_combo.setItemData(3, "Traditional deep learning model. Good for general subject extraction.", Qt.ItemDataRole.ToolTipRole)
        self.model_combo.addItem("U2Netp Lite", "u2netp")
        self.model_combo.setItemData(4, "Ultra-lightweight U2Net model for very fast execution on lower-end hardware.", Qt.ItemDataRole.ToolTipRole)
        self.model_combo.currentIndexChanged.connect(self.on_model_changed_index)
        row1_layout.addWidget(self.model_combo)

        # 3. Processing Mode Selection (with outline tune sliders icon label)
        mode_icon_lbl = QLabel()
        mode_icon_lbl.setPixmap(self.get_icon("tune").pixmap(16, 16))
        mode_icon_lbl.setToolTip("Processing Mode (Matting Engine)")
        row1_layout.addWidget(mode_icon_lbl)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Fast (GF)", "fast")
        self.mode_combo.setItemData(0, "Guided Filter matting. Very fast (2-4s), great for standard objects with clean edges.", Qt.ItemDataRole.ToolTipRole)
        self.mode_combo.addItem("Quality (ViTMatte)", "quality")
        self.mode_combo.setItemData(1, "Trimap-guided ViTMatte matting. Excellent for curly hair and soft details (5-10s).", Qt.ItemDataRole.ToolTipRole)
        self.mode_combo.addItem("Ultra (Multi-Scale)", "ultra")
        self.mode_combo.setItemData(2, "Multi-scale ViTMatte matting at 1.0x and 0.5x resolutions. Best for complex hair and fine transparent details (10-20s).", Qt.ItemDataRole.ToolTipRole)
        self.mode_combo.currentIndexChanged.connect(self.on_matting_changed)
        row1_layout.addWidget(self.mode_combo)

        row1_layout.addWidget(self.create_divider())

        # 4. Wand & Brush Sliders (options layout)
        self.tol_label = QLabel("Wand Tol: 15")
        self.tol_label.setFixedWidth(85)
        self.tol_slider = QSlider(Qt.Orientation.Horizontal)
        self.tol_slider.setRange(1, 100)
        self.tol_slider.setValue(15)
        self.tol_slider.setFixedWidth(80)
        self.tol_slider.valueChanged.connect(self.on_tolerance_changed)
        row1_layout.addWidget(self.tol_label)
        row1_layout.addWidget(self.tol_slider)

        self.brush_label = QLabel("Brush Size: 20px")
        self.brush_label.setFixedWidth(95)
        self.brush_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_slider.setRange(1, 150)
        self.brush_slider.setValue(20)
        self.brush_slider.setFixedWidth(80)
        self.brush_slider.valueChanged.connect(self.on_brush_changed)
        row1_layout.addWidget(self.brush_label)
        row1_layout.addWidget(self.brush_slider)

        # Row 1 Spacer to push everything left
        row1_spacer = QWidget()
        row1_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row1_layout.addWidget(row1_spacer)

        # Create row 2 elements
        # 1. Edge Matting checkbox
        self.chk_matting = QCheckBox("Edge Matting (GF/ViT)")
        self.chk_matting.setChecked(True)
        self.chk_matting.setStyleSheet("color: #e0e0e0; font-size: 12px; font-weight: bold;")
        self.chk_matting.toggled.connect(self.on_matting_changed)
        row2_layout.addWidget(self.chk_matting)

        # 2. Radius Slider
        self.erode_label = QLabel("  Radius: 7px")
        self.erode_label.setFixedWidth(135)
        self.erode_slider = QSlider(Qt.Orientation.Horizontal)
        self.erode_slider.setRange(1, 25)
        self.erode_slider.setValue(7)
        self.erode_slider.setFixedWidth(80)
        self.erode_slider.valueChanged.connect(self.on_matting_changed)
        row2_layout.addWidget(self.erode_label)
        row2_layout.addWidget(self.erode_slider)

        # 3. Glass Mode
        self.chk_transparency = QCheckBox("Glass Mode")
        self.chk_transparency.setChecked(False)
        self.chk_transparency.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        self.chk_transparency.toggled.connect(self.on_matting_changed)
        row2_layout.addWidget(self.chk_transparency)

        # 4. Decontaminate
        self.chk_decontaminate = QCheckBox("Decontaminate")
        self.chk_decontaminate.setChecked(True)
        self.chk_decontaminate.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        self.chk_decontaminate.toggled.connect(self.on_matting_changed)
        row2_layout.addWidget(self.chk_decontaminate)

        # 5. Sharpness Slider
        self.sharp_label = QLabel("  Sharpness: 0")
        self.sharp_label.setFixedWidth(145)
        self.sharp_slider = QSlider(Qt.Orientation.Horizontal)
        self.sharp_slider.setRange(0, 10)
        self.sharp_slider.setValue(0)
        self.sharp_slider.setFixedWidth(80)
        self.sharp_slider.valueChanged.connect(self.on_matting_changed)
        row2_layout.addWidget(self.sharp_label)
        row2_layout.addWidget(self.sharp_slider)

        # 6. Smooth Edges (Manual) button
        self.btn_smooth = QPushButton("Smooth Edges (Manual)")
        self.btn_smooth.setToolTip("Smooth Edges of current active mask using Guided Filter")
        self.btn_smooth.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #333333;
                border-color: #4a4a4a;
            }
        """)
        self.btn_smooth.clicked.connect(self.smooth_edges_triggered.emit)
        row2_layout.addWidget(self.btn_smooth)

        row2_layout.addWidget(self.create_divider())

        # 7. Low-Config Safeguard: Auto-Apply / Apply / Cancel
        import onnxruntime as ort
        has_gpu = any(p in ort.get_available_providers() for p in ['CUDAExecutionProvider', 'DirectMLExecutionProvider'])
        
        self.chk_auto_apply = QCheckBox("Auto-Apply")
        self.chk_auto_apply.setChecked(has_gpu)
        self.chk_auto_apply.setToolTip("Enable for automatic live preview. Disable on slow hardware to run manually.")
        self.chk_auto_apply.setStyleSheet("color: #e0e0e0; font-size: 12px; font-weight: bold;")
        self.chk_auto_apply.toggled.connect(self.on_auto_apply_toggled)
        row2_layout.addWidget(self.chk_auto_apply)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setFixedWidth(60)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: 1px solid #3b82f6;
                border-radius: 5px;
                font-weight: bold;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
                border-color: #60a5fa;
            }
            QPushButton:disabled {
                background-color: #1c1c1c;
                color: #555555;
                border-color: #252525;
            }
        """)
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        row2_layout.addWidget(self.btn_apply)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedWidth(60)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #333333;
                border-color: #4a4a4a;
            }
            QPushButton:disabled {
                background-color: #1c1c1c;
                color: #555555;
                border-color: #252525;
            }
        """)
        self.btn_cancel.clicked.connect(self.on_cancel_clicked)
        row2_layout.addWidget(self.btn_cancel)

        # Row 2 Spacer to push everything left
        row2_spacer = QWidget()
        row2_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row2_layout.addWidget(row2_spacer)

        # Add layouts to main container layout
        main_layout.addLayout(row1_layout)
        main_layout.addLayout(row2_layout)

        # Add container widget to QToolBar
        self.addWidget(container)

        # Set up state monitoring
        self.check_pending_changes()
        self.refresh_controls_visibility()

    def update_slider_visibility(self, tool_name):
        is_wand = (tool_name == "wand")
        self.tol_label.setVisible(is_wand)
        self.tol_slider.setVisible(is_wand)
        
        is_brush = tool_name in ["brush_add", "brush_sub", "refine_edge"]
        self.brush_label.setVisible(is_brush)
        self.brush_slider.setVisible(is_brush)

    def on_tolerance_changed(self, val):
        self.tol_label.setText(f"Wand Tol: {val}")
        self.tolerance_changed.emit(val)

    def on_brush_changed(self, val):
        self.brush_label.setText(f"Brush: {val}px")
        self.brush_size_changed.emit(val)

    def on_model_changed_index(self, index):
        if self.chk_auto_apply.isChecked():
            model_id = self.model_combo.itemData(index)
            self.last_applied_state["model"] = model_id
            self.model_changed.emit(model_id)
        else:
            self.check_pending_changes()

    def on_matting_changed(self):
        self.refresh_controls_visibility()
        
        if self.chk_auto_apply.isChecked():
            self.last_applied_state["apply_matting"] = self.chk_matting.isChecked()
            self.last_applied_state["erode_size"] = self.erode_slider.value()
            self.last_applied_state["preserve_trans"] = self.chk_transparency.isChecked()
            self.last_applied_state["sharpness"] = self.sharp_slider.value()
            self.last_applied_state["decontaminate"] = self.chk_decontaminate.isChecked()
            self.last_applied_state["processing_mode"] = self.mode_combo.itemData(self.mode_combo.currentIndex())
            
            self.matting_settings_changed.emit(
                self.last_applied_state["apply_matting"],
                self.last_applied_state["erode_size"],
                self.last_applied_state["preserve_trans"],
                self.last_applied_state["sharpness"],
                self.last_applied_state["decontaminate"],
                self.last_applied_state["processing_mode"]
            )
        else:
            self.check_pending_changes()

    def check_pending_changes(self):
        if self.chk_auto_apply.isChecked():
            self.btn_apply.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            return
            
        model_changed = (self.model_combo.itemData(self.model_combo.currentIndex()) != self.last_applied_state["model"])
        mode_changed = (self.mode_combo.itemData(self.mode_combo.currentIndex()) != self.last_applied_state["processing_mode"])
        matting_changed = (self.chk_matting.isChecked() != self.last_applied_state["apply_matting"])
        radius_changed = (self.erode_slider.value() != self.last_applied_state["erode_size"])
        trans_changed = (self.chk_transparency.isChecked() != self.last_applied_state["preserve_trans"])
        sharpness_changed = (self.sharp_slider.value() != self.last_applied_state["sharpness"])
        decon_changed = (self.chk_decontaminate.isChecked() != self.last_applied_state["decontaminate"])
        
        has_changes = (model_changed or mode_changed or matting_changed or radius_changed or trans_changed or sharpness_changed or decon_changed)
        
        self.btn_apply.setEnabled(has_changes)
        self.btn_cancel.setEnabled(has_changes)
        
        erode_val = self.erode_slider.value()
        if radius_changed:
            self.erode_label.setText(f"  Radius: {erode_val}px (pending)")
        else:
            self.erode_label.setText(f"  Radius: {erode_val}px")
            
        sharp_val = self.sharp_slider.value()
        if sharpness_changed:
            self.sharp_label.setText(f"  Sharpness: {sharp_val} (pending)")
        else:
            self.sharp_label.setText(f"  Sharpness: {sharp_val}")

    def on_apply_clicked(self):
        self.last_applied_state["model"] = self.model_combo.itemData(self.model_combo.currentIndex())
        self.last_applied_state["processing_mode"] = self.mode_combo.itemData(self.mode_combo.currentIndex())
        self.last_applied_state["apply_matting"] = self.chk_matting.isChecked()
        self.last_applied_state["erode_size"] = self.erode_slider.value()
        self.last_applied_state["preserve_trans"] = self.chk_transparency.isChecked()
        self.last_applied_state["sharpness"] = self.sharp_slider.value()
        self.last_applied_state["decontaminate"] = self.chk_decontaminate.isChecked()
        
        self.matting_settings_changed.emit(
            self.last_applied_state["apply_matting"],
            self.last_applied_state["erode_size"],
            self.last_applied_state["preserve_trans"],
            self.last_applied_state["sharpness"],
            self.last_applied_state["decontaminate"],
            self.last_applied_state["processing_mode"]
        )
        
        self.check_pending_changes()

    def on_cancel_clicked(self):
        self.block_all_signals(True)
        
        idx = self.model_combo.findData(self.last_applied_state["model"])
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
            
        idx_mode = self.mode_combo.findData(self.last_applied_state["processing_mode"])
        if idx_mode >= 0:
            self.mode_combo.setCurrentIndex(idx_mode)
            
        self.chk_matting.setChecked(self.last_applied_state["apply_matting"])
        self.erode_slider.setValue(self.last_applied_state["erode_size"])
        self.chk_transparency.setChecked(self.last_applied_state["preserve_trans"])
        self.sharp_slider.setValue(self.last_applied_state["sharpness"])
        self.chk_decontaminate.setChecked(self.last_applied_state["decontaminate"])
        
        self.block_all_signals(False)
        
        self.refresh_controls_visibility()
        self.check_pending_changes()

    def on_auto_apply_toggled(self, checked):
        if checked:
            self.on_apply_clicked()
        else:
            self.check_pending_changes()

    def refresh_controls_visibility(self):
        apply_matting = self.chk_matting.isChecked()
        
        self.erode_label.setVisible(apply_matting)
        self.erode_slider.setVisible(apply_matting)
        self.chk_transparency.setVisible(apply_matting)
        self.sharp_label.setVisible(apply_matting)
        self.sharp_slider.setVisible(apply_matting)
        self.chk_decontaminate.setVisible(apply_matting)

    def block_all_signals(self, block):
        self.model_combo.blockSignals(block)
        self.mode_combo.blockSignals(block)
        self.chk_matting.blockSignals(block)
        self.erode_slider.blockSignals(block)
        self.chk_transparency.blockSignals(block)
        self.sharp_slider.blockSignals(block)
        self.chk_decontaminate.blockSignals(block)

    def sync_parameters(self, model, apply_matting, erode_size, preserve_trans, sharpness, decontaminate, processing_mode="fast"):
        self.block_all_signals(True)
        
        self.last_applied_state = {
            "model": model,
            "processing_mode": processing_mode,
            "apply_matting": apply_matting,
            "erode_size": erode_size,
            "preserve_trans": preserve_trans,
            "sharpness": sharpness,
            "decontaminate": decontaminate
        }
        
        idx = self.model_combo.findData(model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
            
        idx_mode = self.mode_combo.findData(processing_mode)
        if idx_mode >= 0:
            self.mode_combo.setCurrentIndex(idx_mode)
            
        self.chk_matting.setChecked(apply_matting)
        self.erode_slider.setValue(erode_size)
        self.chk_transparency.setChecked(preserve_trans)
        self.sharp_slider.setValue(sharpness)
        self.chk_decontaminate.setChecked(decontaminate)
        
        self.block_all_signals(False)
        
        self.refresh_controls_visibility()
        self.check_pending_changes()
