import cv2
import numpy as np
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QBrush, QColor, QPixmap, QImage, QPen, QCursor, QFont

class InteractiveCanvas(QGraphicsView):
    # Signals emitted when user performs manual edits on the canvas
    mask_changed = pyqtSignal(np.ndarray)       # Emitted after manual drawing stroke / change
    wand_clicked = pyqtSignal(int, int)          # Emitted for Magic Wand (x, y) coordinates
    grabcut_selected = pyqtSignal(int, int, int, int) # Emitted with (x, y, w, h) bounding box

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Pixmap item representing active loaded image
        self.pixmap_item = None
        
        # Original BGR image matrix and current single-channel mask matrix
        self.original_img = None
        self.mask = None
        
        # Editor tool parameters
        self.tool_mode = "pan"                   # "pan", "wand", "lasso", "grabcut", "brush_add", "brush_sub", "refine_edge"
        self.brush_size = 20
        self.tolerance = 15
        self.zoom_factor = 1.0
        self.show_original = False
        self.decontaminate_colors = True
        self.refine_stroke_mask = None

        # State tracking variables for mouse drawing operations
        self.pan_active = False
        self.pan_last_pos = QPoint()
        
        self.lasso_points = []
        
        self.grabcut_start_pos = None
        self.grabcut_rect_item = None

        self.brush_active = False
        self.current_mouse_scene_pos = QPointF()

        self.init_canvas()

    def init_canvas(self):
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setBackgroundBrush(self.create_checkerboard_brush())
        self.setMouseTracking(True)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        
        # Premium zooming UX: anchor transformations centered on the cursor position
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

    def create_checkerboard_brush(self):
        """
        Creates a custom 20x20 grayscale grid texture for transparent canvas backing.
        """
        pixmap = QPixmap(20, 20)
        pixmap.fill(QColor(255, 255, 255))
        painter = QPainter(pixmap)
        grid_color = QColor(240, 240, 240)
        painter.fillRect(0, 0, 10, 10, grid_color)
        painter.fillRect(10, 10, 10, 10, grid_color)
        painter.end()
        return QBrush(pixmap)

    def set_image(self, bgr_img, mask=None):
        """
        Loads the image matrices onto the canvas scene and renders transparency.
        """
        self.original_img = bgr_img.copy()
        h, w = bgr_img.shape[:2]
        
        if mask is None:
            self.mask = np.full((h, w), 255, dtype=np.uint8)
        else:
            self.mask = mask.copy()
            
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        self.scene.setSceneRect(0, 0, w, h)
        
        self.update_composite_view()
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_factor = 1.0
        self.lasso_points.clear()

    def clear_canvas(self):
        self.scene.clear()
        self.original_img = None
        self.mask = None
        self.pixmap_item = None
        self.lasso_points.clear()
        if self.grabcut_rect_item:
            self.grabcut_rect_item = None
        self.viewport().update()

    def update_composite_view(self):
        """
        Blends the BGR image and grayscale mask into an ARGB pixmap and updates the canvas display.
        """
        if self.original_img is None or self.mask is None:
            return
            
        h, w = self.original_img.shape[:2]
        
        # Apply color decontamination if enabled
        if getattr(self, 'decontaminate_colors', True) and not self.show_original:
            from src.core.segmentation import decontaminate_colors
            bgr_decon = decontaminate_colors(self.original_img, self.mask)
        else:
            bgr_decon = self.original_img
            
        rgba = cv2.cvtColor(bgr_decon, cv2.COLOR_BGR2BGRA)
        if self.show_original:
            rgba[:, :, 3] = 255
        else:
            rgba[:, :, 3] = self.mask
        
        qimg = QImage(rgba.data, w, h, w * 4, QImage.Format.Format_ARGB32)
        pixmap = QPixmap.fromImage(qimg.copy())
        self.pixmap_item.setPixmap(pixmap)

    def set_tool_mode(self, mode):
        self.tool_mode = mode
        self.lasso_points.clear()
        if self.grabcut_rect_item:
            self.scene.removeItem(self.grabcut_rect_item)
            self.grabcut_rect_item = None
        self.viewport().update()

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            scale_factor = zoom_in_factor
            self.zoom_factor *= scale_factor
        else:
            scale_factor = zoom_out_factor
            self.zoom_factor *= scale_factor
            
        self.scale(scale_factor, scale_factor)

    def get_constrained_coords(self, scene_pos):
        """
        Helper method to get scene coordinates clipped to image dimensions.
        """
        x, y = int(scene_pos.x()), int(scene_pos.y())
        if self.original_img is not None:
            h, w = self.original_img.shape[:2]
            cx = max(0, min(x, w - 1))
            cy = max(0, min(y, h - 1))
            return cx, cy, True
        return x, y, False

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.position().toPoint())
        cx, cy, valid = self.get_constrained_coords(scene_pos)

        # Pan support (middle click or pan tool drag)
        if event.button() == Qt.MouseButton.MiddleButton or (self.tool_mode == "pan" and event.button() == Qt.MouseButton.LeftButton):
            self.pan_active = True
            self.pan_last_pos = event.position().toPoint()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
            return

        if not valid:
            super().mousePressEvent(event)
            return

        # Magic Wand Selection
        if self.tool_mode == "wand" and event.button() == Qt.MouseButton.LeftButton:
            self.wand_clicked.emit(cx, cy)
            event.accept()
            return

        # Brush Restoration / Eraser
        if self.tool_mode in ["brush_add", "brush_sub"] and event.button() == Qt.MouseButton.LeftButton:
            self.brush_active = True
            self.paint_mask_stroke(QPointF(cx, cy))
            event.accept()
            return

        # Refine Edge Brush
        if self.tool_mode == "refine_edge" and event.button() == Qt.MouseButton.LeftButton:
            self.brush_active = True
            if self.mask is not None:
                self.refine_stroke_mask = np.zeros(self.mask.shape, dtype=np.uint8)
                self.paint_refine_stroke(QPointF(cx, cy))
            event.accept()
            return

        # GrabCut Box Selection
        if self.tool_mode == "grabcut" and event.button() == Qt.MouseButton.LeftButton:
            self.grabcut_start_pos = QPointF(cx, cy)
            self.grabcut_rect_item = self.scene.addRect(
                QRectF(self.grabcut_start_pos, self.grabcut_start_pos),
                QPen(QColor(99, 102, 241), 2, Qt.PenStyle.DashLine),
                QBrush(QColor(99, 102, 241, 40))
            )
            event.accept()
            return

        # Lasso Vector Selection
        if self.tool_mode == "lasso" and event.button() == Qt.MouseButton.LeftButton:
            self.lasso_points.append((cx, cy))
            self.viewport().update()
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.position().toPoint())
        cx, cy, valid = self.get_constrained_coords(scene_pos)
        self.current_mouse_scene_pos = QPointF(cx, cy)

        # Panning Action
        if self.pan_active:
            delta = event.position().toPoint() - self.pan_last_pos
            self.pan_last_pos = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        # Brush Drawing Action
        if self.brush_active and self.tool_mode in ["brush_add", "brush_sub"] and valid:
            self.paint_mask_stroke(QPointF(cx, cy))
            event.accept()
            return

        # Refine Edge Brush Drawing Action
        if self.brush_active and self.tool_mode == "refine_edge" and valid:
            self.paint_refine_stroke(QPointF(cx, cy))
            event.accept()
            return

        # GrabCut Drag Action
        if self.grabcut_start_pos and self.grabcut_rect_item and valid:
            rect = QRectF(self.grabcut_start_pos, QPointF(cx, cy)).normalized()
            self.grabcut_rect_item.setRect(rect)
            event.accept()
            return

        if self.tool_mode in ["lasso", "brush_add", "brush_sub", "refine_edge"]:
            self.viewport().update()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.pan_active:
            self.pan_active = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            event.accept()
            return

        if self.brush_active:
            self.brush_active = False
            if self.tool_mode == "refine_edge":
                self.apply_refine_edge_filter()
            else:
                self.mask_changed.emit(self.mask)
            event.accept()
            return

        # GrabCut Finish Action
        if self.grabcut_start_pos and self.grabcut_rect_item:
            rect = self.grabcut_rect_item.rect()
            x, y, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
            
            self.scene.removeItem(self.grabcut_rect_item)
            self.grabcut_rect_item = None
            self.grabcut_start_pos = None
            
            if w > 5 and h > 5:
                self.grabcut_selected.emit(x, y, w, h)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.tool_mode == "lasso" and len(self.lasso_points) >= 3:
            action = "ADD"
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                action = "SUB"
                
            from src.core.manual_refine import apply_lasso_mask
            self.mask = apply_lasso_mask(self.mask, self.lasso_points, action=action)
            self.update_composite_view()
            self.mask_changed.emit(self.mask)
            
            self.lasso_points.clear()
            self.viewport().update()
            event.accept()
            return
            
        super().mouseDoubleClickEvent(event)

    def paint_mask_stroke(self, scene_pos):
        if self.original_img is None or self.mask is None:
            return
            
        x, y = int(scene_pos.x()), int(scene_pos.y())
        center = (x, y)
        action = "ADD" if self.tool_mode == "brush_add" else "SUB"
        
        from src.core.manual_refine import apply_brush_draw
        self.mask = apply_brush_draw(self.mask, center, self.brush_size, action)
        self.update_composite_view()

    def paint_refine_stroke(self, scene_pos):
        if self.mask is None or self.refine_stroke_mask is None:
            return
        x, y = int(scene_pos.x()), int(scene_pos.y())
        cv2.circle(self.refine_stroke_mask, (x, y), int(self.brush_size), 255, -1)
        self.viewport().update()

    def apply_refine_edge_filter(self):
        if self.original_img is None or self.mask is None or self.refine_stroke_mask is None:
            return
        from src.core.manual_refine import apply_refine_edge_brush
        new_mask = apply_refine_edge_brush(
            self.original_img, self.mask, self.refine_stroke_mask, self.brush_size
        )
        self.mask = new_mask
        self.update_composite_view()
        self.mask_changed.emit(self.mask)
        self.refine_stroke_mask = None

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)

        # 1. Render Brush circular cursor outline
        if self.tool_mode in ["brush_add", "brush_sub", "refine_edge"] and self.original_img is not None:
            pos = self.current_mouse_scene_pos
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            if self.tool_mode == "brush_add":
                pen_color = QColor(99, 102, 241)
            elif self.tool_mode == "brush_sub":
                pen_color = QColor(239, 68, 68)
            else: # refine_edge
                pen_color = QColor(245, 158, 11) # Amber/Orange for Refine
                
            painter.setPen(QPen(pen_color, 1.5, Qt.PenStyle.SolidLine))
            painter.drawEllipse(pos, self.brush_size, self.brush_size)
            
            painter.setPen(QPen(pen_color, 2, Qt.PenStyle.SolidLine))
            painter.drawPoint(pos)

        # 1b. Render Refine Edge path overlay while drawing
        if self.tool_mode == "refine_edge" and self.brush_active and getattr(self, 'refine_stroke_mask', None) is not None:
            h, w = self.refine_stroke_mask.shape
            overlay = np.zeros((h, w, 4), dtype=np.uint8)
            overlay[self.refine_stroke_mask > 0] = [245, 158, 11, 80] # Amber with opacity 80
            
            qimg = QImage(overlay.data, w, h, w * 4, QImage.Format.Format_ARGB32)
            pixmap = QPixmap.fromImage(qimg)
            painter.drawPixmap(0, 0, pixmap)

        # 1c. Render "BEFORE" comparison overlay
        if self.show_original:
            painter.save()
            painter.setPen(QPen(QColor(239, 68, 68, 200), 2))
            painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            painter.drawText(20, 40, "BEFORE (Original Image)")
            painter.restore()

        # 2. Render Lasso path selection lines
        if self.tool_mode == "lasso" and len(self.lasso_points) > 0:
            pen = QPen(QColor(99, 102, 241), 2 / self.zoom_factor)
            pen.setCosmetic(True)
            painter.setPen(pen)
            
            for i in range(len(self.lasso_points) - 1):
                p1 = QPointF(*self.lasso_points[i])
                p2 = QPointF(*self.lasso_points[i+1])
                painter.drawLine(p1, p2)
                
            p_last = QPointF(*self.lasso_points[-1])
            painter.drawLine(p_last, self.current_mouse_scene_pos)
            
            pen_dash = QPen(QColor(99, 102, 241, 150), 1 / self.zoom_factor, Qt.PenStyle.DashLine)
            pen_dash.setCosmetic(True)
            painter.setPen(pen_dash)
            p_start = QPointF(*self.lasso_points[0])
            painter.drawLine(self.current_mouse_scene_pos, p_start)
