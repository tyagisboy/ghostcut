import os
import math
from PIL import Image, ImageDraw

def draw_star(draw, cx, cy, r1, r2, fill=None, outline=None, width=2):
    pts = [
        (cx, cy - r1),
        (cx + r2, cy - r2),
        (cx + r1, cy),
        (cx + r2, cy + r2),
        (cx, cy + r1),
        (cx - r2, cy + r2),
        (cx - r1, cy),
        (cx - r2, cy - r2)
    ]
    draw.polygon(pts, fill=fill, outline=outline, width=width)

def draw_dashed_polygon(draw, points, fill, width, dash_len=8, gap_len=6):
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist == 0:
            continue
        ux = dx / dist
        uy = dy / dist
        curr = 0
        while curr < dist:
            start_x = p1[0] + ux * curr
            start_y = p1[1] + uy * curr
            end_x = p1[0] + ux * min(curr + dash_len, dist)
            end_y = p1[1] + uy * min(curr + dash_len, dist)
            draw.line([(start_x, start_y), (end_x, end_y)], fill=fill, width=width)
            curr += dash_len + gap_len

def get_arc_points(cx, cy, r_out, r_in, start_angle, end_angle, num_steps=24):
    outer_pts = []
    inner_pts = []
    for i in range(num_steps + 1):
        theta = math.radians(start_angle + (end_angle - start_angle) * i / num_steps)
        outer_pts.append((cx + r_out * math.cos(theta), cy + r_out * math.sin(theta)))
        inner_pts.append((cx + r_in * math.cos(theta), cy + r_in * math.sin(theta)))
    return outer_pts + inner_pts[::-1]

def get_bezier_points(p0, p1, p2, p3, steps=10):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts

def generate_icons(dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    
    # 1. Generate SVG representations (100% vector, crisp)
    svgs = {
        "pan_line": '<polygon points="24,20 24,96 44,76 68,108 80,96 56,64 84,64" fill="none" stroke="#F1F5F9" stroke-width="6" stroke-linejoin="round"/>',
        "pan_fill": '<polygon points="24,20 24,96 44,76 68,108 80,96 56,64 84,64" fill="#FFFFFF" stroke="#F1F5F9" stroke-width="4" stroke-linejoin="round"/>',
        "wand_line": '<line x1="24" y1="104" x2="64" y2="64" stroke="#F1F5F9" stroke-width="8" stroke-linecap="round"/><line x1="64" y1="64" x2="80" y2="48" stroke="#8C9196" stroke-width="10" stroke-linecap="round"/><line x1="80" y1="48" x2="88" y2="40" stroke="#F1F5F9" stroke-width="10" stroke-linecap="round"/><path d="M96,14 L98,24 L108,28 L98,32 L96,42 L94,32 L84,28 L94,24 Z" fill="none" stroke="#F1F5F9" stroke-width="2"/><path d="M108,48 L110,55 L120,58 L110,61 L108,68 L106,61 L96,58 L106,55 Z" fill="none" stroke="#F1F5F9" stroke-width="2"/><path d="M64,14 L66,21 L76,24 L66,27 L64,34 L62,27 L52,24 L62,21 Z" fill="none" stroke="#F1F5F9" stroke-width="2"/>',
        "wand_fill": '<line x1="24" y1="104" x2="64" y2="64" stroke="#F1F5F9" stroke-width="10" stroke-linecap="round"/><line x1="64" y1="64" x2="80" y2="48" stroke="#B4B9BC" stroke-width="12" stroke-linecap="round"/><line x1="80" y1="48" x2="88" y2="40" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round"/><path d="M96,14 L98,24 L108,28 L98,32 L96,42 L94,32 L84,28 L94,24 Z" fill="#FFFFFF"/><path d="M108,48 L110,55 L120,58 L110,61 L108,68 L106,61 L96,58 L106,55 Z" fill="#FFFFFF"/><path d="M64,14 L66,21 L76,24 L66,27 L64,34 L62,27 L52,24 L62,21 Z" fill="#FFFFFF"/>',
        "lasso_line": '<path d="M64,24 C88,30 100,52 88,74 C64,80 40,74 28,52 C40,30 64,24 64,24" fill="none" stroke="#F1F5F9" stroke-width="4" stroke-dasharray="8,6"/><circle cx="76" cy="80" r="8" fill="none" stroke="#F1F5F9" stroke-width="4"/><line x1="76" y1="88" x2="88" y2="104" stroke="#F1F5F9" stroke-width="6" stroke-linecap="round"/>',
        "lasso_fill": '<path d="M64,24 C88,30 100,52 88,74 C64,80 40,74 28,52 C40,30 64,24 64,24" fill="rgba(255,255,255,0.25)" stroke="#F1F5F9" stroke-width="4" stroke-dasharray="8,6"/><circle cx="76" cy="80" r="8" fill="#F1F5F9" stroke="#F1F5F9" stroke-width="2"/><line x1="76" y1="88" x2="88" y2="104" stroke="#F1F5F9" stroke-width="8" stroke-linecap="round"/>',
        "grabcut_line": '<path d="M20,20 L40,20 M20,20 L20,40 M108,20 L88,20 M108,20 L108,40 M20,108 L40,108 M20,108 L20,88 M108,108 L88,108 M108,108 L108,88" fill="none" stroke="#F1F5F9" stroke-width="6" stroke-linecap="round"/><rect x="28" y="28" width="72" height="72" fill="none" stroke="#F1F5F9" stroke-width="4" stroke-dasharray="8,6"/>',
        "grabcut_fill": '<path d="M20,20 L40,20 M20,20 L20,40 M108,20 L88,20 M108,20 L108,40 M20,108 L40,108 M20,108 L20,88 M108,108 L88,108 M108,108 L108,88" fill="none" stroke="#F1F5F9" stroke-width="8" stroke-linecap="round"/><rect x="28" y="28" width="72" height="72" fill="rgba(255,255,255,0.25)" stroke="#F1F5F9" stroke-width="4" stroke-dasharray="8,6"/>',
        "brush_add_line": '<polygon points="24,96 32,104 68,76 52,60" fill="none" stroke="#F1F5F9" stroke-width="4" stroke-linejoin="round"/><polygon points="52,60 68,76 86,62 66,42" fill="none" stroke="#F1F5F9" stroke-width="4" stroke-linejoin="round"/><polygon points="66,42 86,62 96,32" fill="none" stroke="#F1F5F9" stroke-width="4" stroke-linejoin="round"/><line x1="84" y1="96" x2="108" y2="96" stroke="#34D399" stroke-width="8" stroke-linecap="round"/><line x1="96" y1="84" x2="96" y2="108" stroke="#34D399" stroke-width="8" stroke-linecap="round"/>',
        "brush_add_fill": '<polygon points="24,96 32,104 68,76 52,60" fill="#B4B9BC" stroke="#F1F5F9" stroke-width="2" stroke-linejoin="round"/><polygon points="52,60 68,76 86,62 66,42" fill="#8C9196" stroke="#F1F5F9" stroke-width="2" stroke-linejoin="round"/><polygon points="66,42 86,62 96,32" fill="#FFFFFF" stroke="#F1F5F9" stroke-width="2" stroke-linejoin="round"/><line x1="84" y1="96" x2="108" y2="96" stroke="#34D399" stroke-width="10" stroke-linecap="round"/><line x1="96" y1="84" x2="96" y2="108" stroke="#34D399" stroke-width="10" stroke-linecap="round"/>',
        "brush_sub_line": '<polygon points="64,32 96,44 80,70 48,58" fill="none" stroke="#F1F5F9" stroke-width="4" stroke-linejoin="round"/><polygon points="48,58 80,70 64,96 32,84" fill="none" stroke="#F1F5F9" stroke-width="4" stroke-linejoin="round"/><line x1="84" y1="96" x2="108" y2="96" stroke="#F87171" stroke-width="8" stroke-linecap="round"/>',
        "brush_sub_fill": '<polygon points="64,32 96,44 80,70 48,58" fill="#FFFFFF" stroke="#F1F5F9" stroke-width="2" stroke-linejoin="round"/><polygon points="48,58 80,70 64,96 32,84" fill="#A0A5A9" stroke="#F1F5F9" stroke-width="2" stroke-linejoin="round"/><line x1="84" y1="96" x2="108" y2="96" stroke="#F87171" stroke-width="10" stroke-linecap="round"/>',
        "refine_edge_line": '<polygon points="26,98 30,102 69,69 59,59" fill="none" stroke="#F1F5F9" stroke-width="3" stroke-linejoin="round"/><polygon points="59,59 69,69 84,56 72,44" fill="none" stroke="#F1F5F9" stroke-width="3" stroke-linejoin="round"/><polygon points="72,44 84,56 96,32" fill="none" stroke="#F1F5F9" stroke-width="3" stroke-linejoin="round"/><path d="M96,32 C104,20 112,24 120,16" fill="none" stroke="#3B82F6" stroke-width="3" stroke-linecap="round"/><line x1="84" y1="96" x2="108" y2="96" stroke="#3B82F6" stroke-width="4"/><line x1="96" y1="84" x2="96" y2="108" stroke="#3B82F6" stroke-width="4"/><line x1="88" y1="88" x2="104" y2="104" stroke="#3B82F6" stroke-width="4"/><line x1="88" y1="104" x2="104" y2="88" stroke="#3B82F6" stroke-width="4"/>',
        "refine_edge_fill": '<polygon points="26,98 30,102 69,69 59,59" fill="#B4B9BC" stroke="#F1F5F9" stroke-width="2" stroke-linejoin="round"/><polygon points="59,59 69,69 84,56 72,44" fill="#8C9196" stroke="#F1F5F9" stroke-width="2" stroke-linejoin="round"/><polygon points="72,44 84,56 96,32" fill="#FFFFFF" stroke="#F1F5F9" stroke-width="2" stroke-linejoin="round"/><path d="M96,32 C104,20 112,24 120,16" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/><line x1="84" y1="96" x2="108" y2="96" stroke="#FFFFFF" stroke-width="6"/><line x1="96" y1="84" x2="96" y2="108" stroke="#FFFFFF" stroke-width="6"/><line x1="88" y1="88" x2="104" y2="104" stroke="#FFFFFF" stroke-width="6"/><line x1="88" y1="104" x2="104" y2="88" stroke="#FFFFFF" stroke-width="6"/>',
        "undo_line": '<path d="M44,76 L80,76 C98,76 98,40 80,40 L44,40" fill="none" stroke="#F1F5F9" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="60,24 44,40 60,56" fill="none" stroke="#F1F5F9" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>',
        "undo_fill": '<path d="M44,76 L80,76 C98,76 98,40 80,40 L44,40" fill="none" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/><polyline points="60,24 44,40 60,56" fill="none" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>',
        "redo_line": '<path d="M84,76 L48,76 C30,76 30,40 48,40 L84,40" fill="none" stroke="#F1F5F9" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="68,24 84,40 68,56" fill="none" stroke="#F1F5F9" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>',
        "redo_fill": '<path d="M84,76 L48,76 C30,76 30,40 48,40 L84,40" fill="none" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/><polyline points="68,24 84,40 68,56" fill="none" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>',
        "status_completed": '<path d="M24,64 L52,92 L104,40" fill="none" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>',
        "status_waiting": '<line x1="36" y1="24" x2="92" y2="24" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round"/><line x1="36" y1="104" x2="92" y2="104" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round"/><polygon points="36,24 92,24 74,52 74,76 92,104 36,104 54,76 54,52" fill="none" stroke="#FFFFFF" stroke-width="8" stroke-linejoin="round"/><polygon points="46,88 82,88 72,76 56,76" fill="#FFFFFF"/><line x1="64" y1="44" x2="64" y2="84" stroke="#FFFFFF" stroke-width="4"/>',
        "status_error": '<polygon points="64,20 20,108 108,108" fill="none" stroke="#FFFFFF" stroke-width="8" stroke-linejoin="round"/><line x1="64" y1="48" x2="64" y2="80" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round"/><circle cx="64" cy="92" r="6" fill="#FFFFFF"/>',
        "status_info": '<circle cx="64" cy="64" r="50" fill="none" stroke="#FFFFFF" stroke-width="8"/><circle cx="64" cy="44" r="6" fill="#FFFFFF"/><line x1="64" y1="58" x2="64" y2="88" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round"/><line x1="56" y1="88" x2="72" y2="88" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round"/>',
        "delete": '<line x1="32" y1="32" x2="96" y2="96" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round"/><line x1="96" y1="32" x2="32" y2="96" stroke="#FFFFFF" stroke-width="12" stroke-linecap="round"/>',
        "thumbs_up_line": '<path d="M24,104 V56 H44 V104 Z M44,96 H84 C90,96 94,92 96,86 L108,58 C109,56 110,54 110,52 V40 C110,34 104,28 98,28 H66 L70,16 C71,12 68,8 64,8 L58,12 L44,40" fill="none" stroke="#F1F5F9" stroke-width="8" stroke-linejoin="round" stroke-linecap="round"/>',
        "thumbs_up_fill": '<path d="M24,104 V56 H44 V104 Z M44,96 H84 C90,96 94,92 96,86 L108,58 C109,56 110,54 110,52 V40 C110,34 104,28 98,28 H66 L70,16 C71,12 68,8 64,8 L58,12 L44,40 Z" fill="#34D399" stroke="#F1F5F9" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>',
        "thumbs_down_line": '<path d="M104,24 V72 H84 V24 Z M84,32 H44 C38,32 34,36 32,42 L20,70 C19,72 18,74 18,76 V88 C18,94 24,100 30,100 H62 L58,112 C57,116 60,120 64,120 L70,116 L84,88" fill="none" stroke="#F1F5F9" stroke-width="8" stroke-linejoin="round" stroke-linecap="round"/>',
        "thumbs_down_fill": '<path d="M104,24 V72 H84 V24 Z M84,32 H44 C38,32 34,36 34,42 L20,70 C19,72 18,74 18,76 V88 C18,94 24,100 30,100 H62 L58,112 C57,116 60,120 64,120 L70,116 L84,88 Z" fill="#F87171" stroke="#F1F5F9" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>'
    }

    for name, content in svgs.items():
        svg_path = os.path.join(dest_dir, f"{name}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">{content}</svg>')
        print(f"[+] Compiled vector SVG: {svg_path}")

    # 2. Keep PNG fallback drawing routines (high-res 128x128 downsampled to 32x32)
    def draw_pan_line(draw):
        pts = [(24, 20), (24, 96), (44, 76), (68, 108), (80, 96), (56, 64), (84, 64)]
        draw.polygon(pts, outline=(241, 245, 249, 255), width=6)
    def draw_pan_fill(draw):
        pts = [(24, 20), (24, 96), (44, 76), (68, 108), (80, 96), (56, 64), (84, 64)]
        draw.polygon(pts, fill=(255, 255, 255, 255), outline=(241, 245, 249, 255), width=4)
    def draw_wand_line(draw):
        draw.line([(24, 104), (64, 64)], fill=(241, 245, 249, 255), width=8)
        draw.line([(64, 64), (80, 48)], fill=(140, 145, 150, 255), width=10)
        draw.line([(80, 48), (88, 40)], fill=(241, 245, 249, 255), width=10)
        draw_star(draw, 96, 28, 14, 4, fill=None, outline=(241, 245, 249, 255), width=2)
        draw_star(draw, 108, 58, 10, 3, fill=None, outline=(241, 245, 249, 255), width=2)
        draw_star(draw, 64, 24, 10, 3, fill=None, outline=(241, 245, 249, 255), width=2)
    def draw_wand_fill(draw):
        draw.line([(24, 104), (64, 64)], fill=(241, 245, 249, 255), width=10)
        draw.line([(64, 64), (80, 48)], fill=(180, 185, 190, 255), width=12)
        draw.line([(80, 48), (88, 40)], fill=(255, 255, 255, 255), width=12)
        draw_star(draw, 96, 28, 14, 4, fill=(255, 255, 255, 255), outline=None)
        draw_star(draw, 108, 58, 10, 3, fill=(255, 255, 255, 255), outline=None)
        draw_star(draw, 64, 24, 10, 3, fill=(255, 255, 255, 255), outline=None)
    def draw_lasso_line(draw):
        pts = [(64, 24), (88, 30), (100, 52), (88, 74), (64, 80), (40, 74), (28, 52), (40, 30)]
        draw_dashed_polygon(draw, pts, fill=(241, 245, 249, 255), width=4, dash_len=8, gap_len=6)
        draw.ellipse([(68, 72), (84, 88)], outline=(241, 245, 249, 255), width=4)
        draw.line([(76, 88), (88, 104)], fill=(241, 245, 249, 255), width=6)
    def draw_lasso_fill(draw):
        pts = [(64, 24), (88, 30), (100, 52), (88, 74), (64, 80), (40, 74), (28, 52), (40, 30)]
        draw.polygon(pts, fill=(255, 255, 255, 60))
        draw_dashed_polygon(draw, pts, fill=(241, 245, 249, 255), width=4, dash_len=8, gap_len=6)
        draw.ellipse([(68, 72), (84, 88)], fill=(241, 245, 249, 255), outline=(241, 245, 249, 255), width=2)
        draw.line([(76, 88), (88, 104)], fill=(241, 245, 249, 255), width=8)
    def draw_grabcut_line(draw):
        draw.line([(20, 20), (40, 20)], fill=(241, 245, 249, 255), width=6)
        draw.line([(20, 20), (20, 40)], fill=(241, 245, 249, 255), width=6)
        draw.line([(108, 20), (88, 20)], fill=(241, 245, 249, 255), width=6)
        draw.line([(108, 20), (108, 40)], fill=(241, 245, 249, 255), width=6)
        draw.line([(20, 108), (40, 108)], fill=(241, 245, 249, 255), width=6)
        draw.line([(20, 108), (20, 88)], fill=(241, 245, 249, 255), width=6)
        draw.line([(108, 108), (88, 108)], fill=(241, 245, 249, 255), width=6)
        draw.line([(108, 108), (108, 88)], fill=(241, 245, 249, 255), width=6)
        pts = [(28, 28), (100, 28), (100, 100), (28, 100)]
        draw_dashed_polygon(draw, pts, fill=(241, 245, 249, 255), width=4, dash_len=8, gap_len=6)
    def draw_grabcut_fill(draw):
        draw.line([(20, 20), (40, 20)], fill=(241, 245, 249, 255), width=8)
        draw.line([(20, 20), (20, 40)], fill=(241, 245, 249, 255), width=8)
        draw.line([(108, 20), (88, 20)], fill=(241, 245, 249, 255), width=8)
        draw.line([(108, 20), (108, 40)], fill=(241, 245, 249, 255), width=8)
        draw.line([(20, 108), (40, 108)], fill=(241, 245, 249, 255), width=8)
        draw.line([(20, 108), (20, 88)], fill=(241, 245, 249, 255), width=8)
        draw.line([(108, 108), (88, 108)], fill=(241, 245, 249, 255), width=8)
        draw.line([(108, 108), (108, 88)], fill=(241, 245, 249, 255), width=8)
        draw.rectangle([(28, 28), (100, 100)], fill=(255, 255, 255, 60))
        pts = [(28, 28), (100, 28), (100, 100), (28, 100)]
        draw_dashed_polygon(draw, pts, fill=(241, 245, 249, 255), width=4, dash_len=8, gap_len=6)
    def draw_brush_add_line(draw):
        draw.polygon([(24, 96), (32, 104), (68, 76), (52, 60)], outline=(241, 245, 249, 255), width=4)
        draw.polygon([(52, 60), (68, 76), (86, 62), (66, 42)], outline=(241, 245, 249, 255), width=4)
        draw.polygon([(66, 42), (86, 62), (96, 32)], outline=(241, 245, 249, 255), width=4)
        draw.line([(84, 96), (108, 96)], fill=(52, 211, 153, 255), width=8)
        draw.line([(96, 84), (96, 108)], fill=(52, 211, 153, 255), width=8)
    def draw_brush_add_fill(draw):
        draw.polygon([(24, 96), (32, 104), (68, 76), (52, 60)], fill=(180, 185, 190, 255), outline=(241, 245, 249, 255), width=2)
        draw.polygon([(52, 60), (68, 76), (86, 62), (66, 42)], fill=(140, 145, 150, 255), outline=(241, 245, 249, 255), width=2)
        draw.polygon([(66, 42), (86, 62), (96, 32)], fill=(255, 255, 255, 255), outline=(241, 245, 249, 255), width=2)
        draw.line([(84, 96), (108, 96)], fill=(52, 211, 153, 255), width=10)
        draw.line([(96, 84), (96, 108)], fill=(52, 211, 153, 255), width=10)
    def draw_brush_sub_line(draw):
        draw.polygon([(64, 32), (96, 44), (80, 70), (48, 58)], outline=(241, 245, 249, 255), width=4)
        draw.polygon([(48, 58), (80, 70), (64, 96), (32, 84)], outline=(241, 245, 249, 255), width=4)
        draw.line([(84, 96), (108, 96)], fill=(248, 113, 113, 255), width=8)
    def draw_brush_sub_fill(draw):
        draw.polygon([(64, 32), (96, 44), (80, 70), (48, 58)], fill=(255, 255, 255, 255), outline=(241, 245, 249, 255), width=2)
        draw.polygon([(48, 58), (80, 70), (64, 96), (32, 84)], fill=(160, 165, 170, 255), outline=(241, 245, 249, 255), width=2)
        draw.line([(84, 96), (108, 96)], fill=(248, 113, 113, 255), width=10)
    def draw_refine_edge_line(draw):
        draw.polygon([(26, 98), (30, 102), (69, 69), (59, 59)], outline=(241, 245, 249, 255), width=3)
        draw.polygon([(59, 59), (69, 69), (84, 56), (72, 44)], outline=(241, 245, 249, 255), width=3)
        draw.polygon([(72, 44), (84, 56), (96, 32)], outline=(241, 245, 249, 255), width=3)
        draw.arc([(90, 8), (114, 32)], start=120, end=300, fill=(59, 130, 246, 255), width=3)
        cx, cy = 96, 96
        for angle in [0, 45, 90, 135]:
            rad = math.radians(angle)
            dx = 12 * math.cos(rad)
            dy = 12 * math.sin(rad)
            draw.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=(59, 130, 246, 255), width=4)
    def draw_refine_edge_fill(draw):
        draw.polygon([(26, 98), (30, 102), (69, 69), (59, 59)], fill=(180, 185, 190, 255), outline=(241, 245, 249, 255), width=2)
        draw.polygon([(59, 59), (69, 69), (84, 56), (72, 44)], fill=(140, 145, 150, 255), outline=(241, 245, 249, 255), width=2)
        draw.polygon([(72, 44), (84, 56), (96, 32)], fill=(255, 255, 255, 255), outline=(241, 245, 249, 255), width=2)
        draw.arc([(90, 8), (114, 32)], start=120, end=300, fill=(255, 255, 255, 255), width=4)
        cx, cy = 96, 96
        for angle in [0, 45, 90, 135]:
            rad = math.radians(angle)
            dx = 12 * math.cos(rad)
            dy = 12 * math.sin(rad)
            draw.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=(255, 255, 255, 255), width=6)
    def draw_undo_line(draw):
        bezier_pts = get_bezier_points((80, 76), (98, 76), (98, 40), (80, 40))
        pts = [(44, 76)] + bezier_pts + [(44, 40)]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(241, 245, 249, 255), width=8)
        for p in pts:
            draw.ellipse([(p[0]-4, p[1]-4), (p[0]+4, p[1]+4)], fill=(241, 245, 249, 255))
        draw.line([(60, 24), (44, 40)], fill=(241, 245, 249, 255), width=8)
        draw.line([(44, 40), (60, 56)], fill=(241, 245, 249, 255), width=8)
        for p in [(60, 24), (44, 40), (60, 56)]:
            draw.ellipse([(p[0]-4, p[1]-4), (p[0]+4, p[1]+4)], fill=(241, 245, 249, 255))
    def draw_undo_fill(draw):
        bezier_pts = get_bezier_points((80, 76), (98, 76), (98, 40), (80, 40))
        pts = [(44, 76)] + bezier_pts + [(44, 40)]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(255, 255, 255, 255), width=12)
        for p in pts:
            draw.ellipse([(p[0]-6, p[1]-6), (p[0]+6, p[1]+6)], fill=(255, 255, 255, 255))
        draw.line([(60, 24), (44, 40)], fill=(255, 255, 255, 255), width=12)
        draw.line([(44, 40), (60, 56)], fill=(255, 255, 255, 255), width=12)
        for p in [(60, 24), (44, 40), (60, 56)]:
            draw.ellipse([(p[0]-6, p[1]-6), (p[0]+6, p[1]+6)], fill=(255, 255, 255, 255))
    def draw_redo_line(draw):
        bezier_pts = get_bezier_points((48, 76), (30, 76), (30, 40), (48, 40))
        pts = [(84, 76)] + bezier_pts + [(84, 40)]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(241, 245, 249, 255), width=8)
        for p in pts:
            draw.ellipse([(p[0]-4, p[1]-4), (p[0]+4, p[1]+4)], fill=(241, 245, 249, 255))
        draw.line([(68, 24), (84, 40)], fill=(241, 245, 249, 255), width=8)
        draw.line([(84, 40), (68, 56)], fill=(241, 245, 249, 255), width=8)
        for p in [(68, 24), (84, 40), (68, 56)]:
            draw.ellipse([(p[0]-4, p[1]-4), (p[0]+4, p[1]+4)], fill=(241, 245, 249, 255))
    def draw_redo_fill(draw):
        bezier_pts = get_bezier_points((48, 76), (30, 76), (30, 40), (48, 40))
        pts = [(84, 76)] + bezier_pts + [(84, 40)]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(255, 255, 255, 255), width=12)
        for p in pts:
            draw.ellipse([(p[0]-6, p[1]-6), (p[0]+6, p[1]+6)], fill=(255, 255, 255, 255))
        draw.line([(68, 24), (84, 40)], fill=(255, 255, 255, 255), width=12)
        draw.line([(84, 40), (68, 56)], fill=(255, 255, 255, 255), width=12)
        for p in [(68, 24), (84, 40), (68, 56)]:
            draw.ellipse([(p[0]-6, p[1]-6), (p[0]+6, p[1]+6)], fill=(255, 255, 255, 255))
    def draw_status_completed(draw):
        draw.line([(32, 68), (56, 92), (96, 44)], fill=(255, 255, 255, 255), width=12)
        for pt in [(32, 68), (56, 92), (96, 44)]:
            draw.ellipse([(pt[0] - 6, pt[1] - 6), (pt[0] + 6, pt[1] + 6)], fill=(255, 255, 255, 255))
    def draw_status_waiting(draw):
        draw.line([(36, 24), (92, 24)], fill=(255, 255, 255, 255), width=10)
        draw.line([(36, 104), (92, 104)], fill=(255, 255, 255, 255), width=10)
        pts = [(36, 24), (92, 24), (74, 52), (74, 76), (92, 104), (36, 104), (54, 76), (54, 52)]
        draw.polygon(pts, outline=(255, 255, 255, 255), width=8)
        draw.polygon([(46, 88), (82, 88), (72, 76), (56, 76)], fill=(255, 255, 255, 255))
        draw.line([(64, 44), (64, 84)], fill=(255, 255, 255, 255), width=4)
    def draw_status_error(draw):
        draw.polygon([(64, 20), (20, 108), (108, 108)], outline=(255, 255, 255, 255), width=8)
        draw.line([(64, 48), (64, 80)], fill=(255, 255, 255, 255), width=8)
        draw.ellipse([(60, 88), (68, 96)], fill=(255, 255, 255, 255))
    def draw_status_info(draw):
        draw.ellipse([(20, 20), (108, 108)], outline=(255, 255, 255, 255), width=8)
        draw.ellipse([(60, 40), (68, 48)], fill=(255, 255, 255, 255))
        draw.line([(64, 56), (64, 88)], fill=(255, 255, 255, 255), width=8)
        draw.line([(56, 88), (72, 88)], fill=(255, 255, 255, 255), width=8)
    def draw_delete(draw):
        draw.line([(32, 32), (96, 96)], fill=(255, 255, 255, 255), width=12)
        draw.line([(96, 32), (32, 96)], fill=(255, 255, 255, 255), width=12)
    def draw_thumbs_up_line(draw):
        draw.rectangle([(24, 56), (44, 104)], outline=(241, 245, 249, 255), width=8)
        pts = [(44, 96), (84, 96), (96, 86), (108, 58), (108, 40), (98, 28), (66, 28), (70, 16), (64, 8), (58, 12), (44, 40)]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(241, 245, 249, 255), width=8)
    def draw_thumbs_up_fill(draw):
        draw.rectangle([(24, 56), (44, 104)], fill=(52, 211, 153, 255), outline=(241, 245, 249, 255), width=6)
        pts = [(44, 96), (84, 96), (96, 86), (108, 58), (108, 40), (98, 28), (66, 28), (70, 16), (64, 8), (58, 12), (44, 40)]
        draw.polygon(pts, fill=(52, 211, 153, 255), outline=(241, 245, 249, 255), width=6)
    def draw_thumbs_down_line(draw):
        draw.rectangle([(84, 24), (104, 72)], outline=(241, 245, 249, 255), width=8)
        pts = [(84, 32), (44, 32), (32, 42), (20, 70), (20, 88), (30, 100), (62, 100), (58, 112), (64, 120), (70, 116), (84, 88)]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=(241, 245, 249, 255), width=8)
    def draw_thumbs_down_fill(draw):
        draw.rectangle([(84, 24), (104, 72)], fill=(248, 113, 113, 255), outline=(241, 245, 249, 255), width=6)
        pts = [(84, 32), (44, 32), (32, 42), (20, 70), (20, 88), (30, 100), (62, 100), (58, 112), (64, 120), (70, 116), (84, 88)]
        draw.polygon(pts, fill=(248, 113, 113, 255), outline=(241, 245, 249, 255), width=6)

    icons = {
        "pan_line": draw_pan_line,
        "pan_fill": draw_pan_fill,
        "wand_line": draw_wand_line,
        "wand_fill": draw_wand_fill,
        "lasso_line": draw_lasso_line,
        "lasso_fill": draw_lasso_fill,
        "grabcut_line": draw_grabcut_line,
        "grabcut_fill": draw_grabcut_fill,
        "brush_add_line": draw_brush_add_line,
        "brush_add_fill": draw_brush_add_fill,
        "brush_sub_line": draw_brush_sub_line,
        "brush_sub_fill": draw_brush_sub_fill,
        "refine_edge_line": draw_refine_edge_line,
        "refine_edge_fill": draw_refine_edge_fill,
        "undo_line": draw_undo_line,
        "undo_fill": draw_undo_fill,
        "redo_line": draw_redo_line,
        "redo_fill": draw_redo_fill,
        "status_completed": draw_status_completed,
        "status_waiting": draw_status_waiting,
        "status_error": draw_status_error,
        "status_info": draw_status_info,
        "delete": draw_delete,
        "thumbs_up_line": draw_thumbs_up_line,
        "thumbs_up_fill": draw_thumbs_up_fill,
        "thumbs_down_line": draw_thumbs_down_line,
        "thumbs_down_fill": draw_thumbs_down_fill
    }
    
    for name, draw_func in icons.items():
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw_func(draw)
        
        img_resized = img.resize((32, 32), Image.Resampling.LANCZOS)
        dest_path = os.path.join(dest_dir, f"{name}.png")
        img_resized.save(dest_path, "PNG")
        print(f"[+] Compiled PNG fallback: {dest_path}")

    # 3. Compile animated loader GIF (status_processing.gif)
    gif_frames = []
    # Create 12 frames of rotating circle dots spinner
    for f in range(12):
        frame = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)
        cx, cy = 16, 16
        r_spin = 10
        # Draw 8 circles around
        for i in range(8):
            angle = math.radians(i * 45)
            x = cx + r_spin * math.cos(angle)
            y = cy + r_spin * math.sin(angle)
            # Size varies based on current rotation frame
            diff_idx = (i - f) % 8
            dot_r = 1.0 + (7.0 - diff_idx) * 0.4  # diameter from 2 to 7 pixels
            alpha = int(40 + (7 - diff_idx) * 30)  # opacity from 40 to 250
            draw.ellipse([(x - dot_r/2, y - dot_r/2), (x + dot_r/2, y + dot_r/2)], fill=(255, 255, 255, alpha))
        gif_frames.append(frame)
        
    gif_path = os.path.join(dest_dir, "status_processing.gif")
    gif_frames[0].save(
        gif_path, save_all=True, append_images=gif_frames[1:], 
        duration=70, loop=0, disposal=2
    )
    print(f"[+] Compiled animated processing GIF: {gif_path}")

if __name__ == "__main__":
    assets_dir = os.path.dirname(os.path.abspath(__file__))
    generate_icons(assets_dir)
