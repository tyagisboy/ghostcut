import os
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QCheckBox, QSlider, QFileDialog, QWidget, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon

import os
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QCheckBox, QSlider, QFileDialog, QWidget, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QMovie

class QueueItemWidget(QWidget):
    remove_requested = pyqtSignal(str)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(current_dir, "assets")

        # Export selection checkbox (checked by default, custom rounded styling)
        self.chk_export = QCheckBox()
        self.chk_export.setChecked(True)
        self.chk_export.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        checked_icon_path = os.path.join(self.assets_dir, "status_completed.svg").replace("\\", "/")
        self.chk_export.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1.5px solid #666666;
                border-radius: 4px;
                background-color: #242424;
            }}
            QCheckBox::indicator:hover {{
                border-color: #3b82f6;
            }}
            QCheckBox::indicator:checked {{
                background-color: #3b82f6;
                border-color: #3b82f6;
                image: url('{checked_icon_path}');
            }}
        """)
        layout.addWidget(self.chk_export)

        # Thumbnail label (enlarged gallery thumbnail card)
        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(38, 38)
        self.lbl_thumb.setStyleSheet("background-color: #161616; border-radius: 6px; border: 1px solid #444444;")
        self.lbl_thumb.setScaledContents(True)
        layout.addWidget(self.lbl_thumb)

        # Info layout (Filename & Status)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_filename = QLabel()
        self.lbl_filename.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        metrics = self.lbl_filename.fontMetrics()
        elided = metrics.elidedText(os.path.basename(self.file_path), Qt.TextElideMode.ElideMiddle, 110)
        self.lbl_filename.setText(elided)
        info_layout.addWidget(self.lbl_filename)

        self.lbl_status = QLabel("Queued")
        self.lbl_status.setStyleSheet("color: #888888; font-size: 11px;")
        info_layout.addWidget(self.lbl_status)

        layout.addLayout(info_layout, 1)

        # Visual Badge (status icon / pill)
        self.badge = QLabel()
        self.badge.setFixedSize(14, 14)
        self.badge.setScaledContents(True)
        layout.addWidget(self.badge)

        # Delete button
        self.btn_delete = QPushButton()
        self.btn_delete.setFixedSize(16, 16)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setToolTip("Remove image")
        self.btn_delete.setObjectName("btn_delete_item")
        self.btn_delete.setIcon(QIcon(os.path.join(self.assets_dir, "delete.svg")))
        self.btn_delete.setIconSize(QSize(10, 10))
        self.btn_delete.clicked.connect(lambda: self.remove_requested.emit(self.file_path))
        layout.addWidget(self.btn_delete)

        self.movie = QMovie(os.path.join(self.assets_dir, "status_processing.gif"))

        self.update_thumbnail()
        self.set_status("queued")

    def update_thumbnail(self):
        pixmap = QPixmap(self.file_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(38, 38, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.lbl_thumb.setPixmap(scaled)

    def set_status(self, status, message=None):
        if hasattr(self, 'movie'):
            self.movie.stop()
            self.badge.setMovie(None)

        if status == "queued":
            self.lbl_status.setText("In Queue")
            self.lbl_status.setStyleSheet("color: #888888; font-size: 11px;")
            self.badge.setPixmap(QPixmap(os.path.join(self.assets_dir, "status_waiting.svg")))
        elif status == "processing":
            self.lbl_status.setText("Processing...")
            self.lbl_status.setStyleSheet("color: #60a5fa; font-size: 11px;")
            self.badge.setMovie(self.movie)
            self.movie.start()
        elif status == "done":
            self.lbl_status.setText("Completed" if not message else message)
            self.lbl_status.setStyleSheet("color: #10b981; font-size: 11px;")
            self.badge.setPixmap(QPixmap(os.path.join(self.assets_dir, "status_completed.svg")))
        elif status == "failed":
            self.lbl_status.setText("Failed" if not message else f"Failed: {message}")
            self.lbl_status.setStyleSheet("color: #ef4444; font-size: 11px;")
            self.badge.setPixmap(QPixmap(os.path.join(self.assets_dir, "status_error.svg")))
        elif status == "warning":
            self.lbl_status.setText("Warning" if not message else message)
            self.lbl_status.setStyleSheet("color: #f97316; font-size: 11px;")
            self.badge.setPixmap(QPixmap(os.path.join(self.assets_dir, "status_error.svg")))


class Sidebar(QFrame):
    # Signals for parent window communication
    file_selected = pyqtSignal(str)                 # Emitted when an image is clicked in queue
    import_files_requested = pyqtSignal()           # Emitted when user clicks 'Add Images'
    ai_process_requested = pyqtSignal(str)          # Emitted to process current image with AI
    export_requested = pyqtSignal(str)              # Emitted to export current image (retained for fallback)
    export_all_requested = pyqtSignal()             # Emitted to export selected/processed images
    file_removed = pyqtSignal(str)                  # Emitted when an image is removed from queue

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarPanel")
        self.setFixedWidth(280)
        self.is_processing = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 1. Header and Add Images button
        header_layout = QHBoxLayout()
        self.lbl_header = QLabel("Imported Images (0/10)")
        self.lbl_header.setObjectName("HeaderLabel")
        header_layout.addWidget(self.lbl_header)
        
        self.btn_add = QPushButton("+ Add")
        self.btn_add.setToolTip("Add images to batch queue")
        self.btn_add.clicked.connect(self.import_files_requested.emit)
        header_layout.addWidget(self.btn_add)
        
        layout.addLayout(header_layout)

        # 2. Queue List Widget
        self.queue_list = QListWidget()
        self.queue_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue_list.currentItemChanged.connect(self.on_item_changed)
        
        # Setup context menu and keyboard listeners to remove files
        self.queue_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self.show_context_menu)
        
        def list_key_press(event):
            if event.key() == Qt.Key.Key_Delete:
                current_item = self.queue_list.currentItem()
                if current_item:
                    self.remove_item(current_item)
            else:
                QListWidget.keyPressEvent(self.queue_list, event)
        self.queue_list.keyPressEvent = list_key_press
        
        layout.addWidget(self.queue_list)

        # 4. Actions Layout (AI Run, Export Selected)
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        self.btn_run_ai = QPushButton("Remove Background")
        self.btn_run_ai.setObjectName("btn_run_ai")
        self.btn_run_ai.clicked.connect(self.on_run_ai_clicked)
        actions_layout.addWidget(self.btn_run_ai)

        self.btn_export = QPushButton("Export Selected Images")
        self.btn_export.setObjectName("ExportButton")
        self.btn_export.clicked.connect(self.export_all_requested.emit)
        actions_layout.addWidget(self.btn_export)

        layout.addLayout(actions_layout)
        
        self.update_button_states()
        self.update_header_text()

    def update_button_states(self):
        # Disable Add button if processing
        self.btn_add.setEnabled(not self.is_processing)
        
        # Disable Remove Background if processing or if no item is selected
        has_selection = self.queue_list.currentItem() is not None
        self.btn_run_ai.setEnabled(not self.is_processing and has_selection)

        # Disable Export Selected Images button if processing, or if there are no checked and completed images in the queue
        if self.is_processing:
            self.btn_export.setEnabled(False)
        else:
            has_checked_completed = False
            for idx in range(self.queue_list.count()):
                item = self.queue_list.item(idx)
                widget = self.queue_list.itemWidget(item)
                if widget and widget.chk_export.isChecked():
                    if item.text().startswith("✅"):
                        has_checked_completed = True
                        break
            self.btn_export.setEnabled(has_checked_completed)

    def set_processing_state(self, processing):
        self.is_processing = processing
        self.update_button_states()

    def add_image_to_queue(self, file_path):
        """
        Appends a file path to the list widget queue with custom widgets and maximum check.
        """
        # Exclude duplicates
        for idx in range(self.queue_list.count()):
            if self.queue_list.item(idx).data(Qt.ItemDataRole.UserRole) == file_path:
                return

        if self.queue_list.count() >= 10:
            QMessageBox.warning(self, "Batch Queue Limit", "Maximum of 10 images can be loaded at a time for batch processing.")
            return

        item = QListWidgetItem(self.queue_list)
        item.setSizeHint(QSize(220, 54))
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        item.setData(Qt.ItemDataRole.ToolTipRole, file_path)
        
        widget = QueueItemWidget(file_path)
        widget.chk_export.stateChanged.connect(self.update_button_states)
        widget.remove_requested.connect(self.on_remove_requested)
        self.queue_list.setItemWidget(item, widget)
        
        if self.queue_list.count() == 1:
            self.queue_list.setCurrentItem(item)
            
        self.update_button_states()
        self.update_header_text()

    def set_item_status(self, file_path, status, message=None):
        """
        Updates the status prefix/text of a file item in the list queue.
        """
        for idx in range(self.queue_list.count()):
            item = self.queue_list.item(idx)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                widget = self.queue_list.itemWidget(item)
                if widget:
                    widget.set_status(status, message)
                if status == "done":
                    item.setText("✅")
                else:
                    item.setText("")
                break
        self.update_button_states()

    def on_item_changed(self, current, previous):
        if current:
            file_path = current.data(Qt.ItemDataRole.UserRole)
            self.file_selected.emit(file_path)
        self.update_button_states()

    def on_run_ai_clicked(self):
        current = self.queue_list.currentItem()
        if current:
            file_path = current.data(Qt.ItemDataRole.UserRole)
            self.ai_process_requested.emit(file_path)

    def get_queue_files(self):
        """
        Returns list of all files in the batch queue.
        """
        files = []
        for idx in range(self.queue_list.count()):
            item = self.queue_list.item(idx)
            files.append(item.data(Qt.ItemDataRole.UserRole))
        return files
        
    def get_current_file(self):
        current = self.queue_list.currentItem()
        return current.data(Qt.ItemDataRole.UserRole) if current else None

    def remove_item(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        row = self.queue_list.row(item)
        self.queue_list.takeItem(row)
        self.file_removed.emit(file_path)
        self.update_button_states()
        self.update_header_text()

    def on_remove_requested(self, file_path):
        for idx in range(self.queue_list.count()):
            item = self.queue_list.item(idx)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                self.remove_item(item)
                break

    def update_header_text(self):
        count = self.queue_list.count()
        self.lbl_header.setText(f"Imported Images ({count}/10)")
        if count >= 10:
            self.lbl_header.setStyleSheet("color: #f87171;")
        else:
            self.lbl_header.setStyleSheet("")

    def show_context_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        item = self.queue_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2b2b2b;
                    color: #e0e0e0;
                    border: 1px solid #4d4d4d;
                    border-radius: 4px;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 4px 16px;
                    border-radius: 2px;
                }
                QMenu::item:selected {
                    background-color: #3b82f6;
                    color: #ffffff;
                }
            """)
            remove_action = menu.addAction("Remove Image")
            action = menu.exec(self.queue_list.mapToGlobal(pos))
            if action == remove_action:
                self.remove_item(item)
