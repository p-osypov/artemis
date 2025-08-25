from Artemis import *
from framebuf import FrameBuffer, RGB565
import time, math, random
# ---------- RGB565 helpers ----------
import math

def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def make_asteroid_fb(w=36, h=37):
    # Background is 0 (use this as the transparent color when blitting)
    data = bytearray(w * h * 2)

    def setpx(x, y, color):
        i = 2 * (y * w + x)
        data[i] = (color >> 8) & 0xFF
        data[i + 1] = color & 0xFF

    # 4 brown/gray asteroid shades (dark -> light)
    PALETTE = [
        rgb565(40, 30, 25),    # darkest brown
        rgb565(70, 50, 40),    # dark brown
        rgb565(100, 70, 55),   # mid brown
        rgb565(130, 95, 75)    # light brown highlight
    ]

    cx, cy = w // 2, h // 2
    base_r = min(w, h) // 2 - 2

    # build round asteroid with slight surface irregularity
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            r = math.sqrt(dx*dx + dy*dy)
            ang = math.atan2(dy, dx)
            
            # Much smaller irregularity for round shape (not star-fish)
            # Just small surface bumps and dents
            irregular = 0.8 * math.sin(7*ang) + 0.5 * math.sin(11*ang + 2.1)
            radius = base_r + irregular
            
            if r <= radius:
                # fake lighting from upper-left
                nx, ny = (dx / (r + 1e-6)), (dy / (r + 1e-6))
                lx, ly = -0.4, -0.9
                lambert = max(0.0, -(nx*lx + ny*ly))  # 0..1
                if lambert < 0.25: shade = 0
                elif lambert < 0.50: shade = 1
                elif lambert < 0.75: shade = 2
                else: shade = 3
                setpx(x, y, PALETTE[shade])
            else:
                setpx(x, y, 0)  # transparent background

    # add some darker craters (smaller and fewer)
    def darken_circle(cx0, cy0, rad, deep=1):
        r2 = rad*rad
        for yy in range(max(0, cy0-rad), min(h, cy0+rad+1)):
            for xx in range(max(0, cx0-rad), min(w, cx0+rad+1)):
                dx, dy = xx - cx0, yy - cy0
                if dx*dx + dy*dy <= r2:
                    i = 2 * (yy * w + xx)
                    col = (data[i] << 8) | data[i+1]
                    if col != 0:
                        # map to palette index and darken
                        try:
                            k = PALETTE.index(col)
                        except ValueError:
                            k = 1
                        k = max(0, k - deep)
                        newc = PALETTE[k]
                        data[i]   = (newc >> 8) & 0xFF
                        data[i+1] = newc & 0xFF

    # Smaller, more realistic craters
    darken_circle(cx-4, cy-3, 3, deep=2)
    darken_circle(cx+3, cy-1, 2, deep=1)
    darken_circle(cx-1, cy+4, 2, deep=2)

    return FrameBuffer(data, w, h, RGB565)

def make_rotating_asteroid_fb(w=20, h=18, rotation_offset=0):
    """Create an asteroid with rotation baked into the generation"""
    # Background is 0 (use this as the transparent color when blitting)
    data = bytearray(w * h * 2)

    def setpx(x, y, color):
        i = 2 * (y * w + x)
        data[i] = (color >> 8) & 0xFF
        data[i + 1] = color & 0xFF

    # 4 brown/gray asteroid shades (dark -> light)
    PALETTE = [
        rgb565(40, 30, 25),    # darkest brown
        rgb565(70, 50, 40),    # dark brown
        rgb565(100, 70, 55),   # mid brown
        rgb565(130, 95, 75)    # light brown highlight
    ]

    cx, cy = w // 2, h // 2
    base_r = min(w, h) // 2 - 2

    # build round asteroid with surface irregularity rotated by rotation_offset
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            r = math.sqrt(dx*dx + dy*dy)
            ang = math.atan2(dy, dx) + rotation_offset  # Add rotation offset
            
            # Small surface bumps and dents for natural look
            irregular = 0.8 * math.sin(7*ang) + 0.5 * math.sin(11*ang + 2.1)
            radius = base_r + irregular
            
            if r <= radius:
                # fake lighting from upper-left (also rotated)
                light_angle = rotation_offset
                nx, ny = (dx / (r + 1e-6)), (dy / (r + 1e-6))
                lx, ly = -0.4 * math.cos(light_angle) - 0.9 * math.sin(light_angle), 0.4 * math.sin(light_angle) - 0.9 * math.cos(light_angle)
                lambert = max(0.0, -(nx*lx + ny*ly))  # 0..1
                if lambert < 0.25: shade = 0
                elif lambert < 0.50: shade = 1
                elif lambert < 0.75: shade = 2
                else: shade = 3
                setpx(x, y, PALETTE[shade])
            else:
                setpx(x, y, 0)  # transparent background

    # add some craters (also rotated)
    def darken_circle(cx0, cy0, rad, deep=1):
        r2 = rad*rad
        # Rotate crater position
        crater_angle = math.atan2(cy0 - cy, cx0 - cx) + rotation_offset
        crater_dist = math.sqrt((cx0 - cx)**2 + (cy0 - cy)**2)
        rotated_cx = int(cx + crater_dist * math.cos(crater_angle))
        rotated_cy = int(cy + crater_dist * math.sin(crater_angle))
        
        for yy in range(max(0, rotated_cy-rad), min(h, rotated_cy+rad+1)):
            for xx in range(max(0, rotated_cx-rad), min(w, rotated_cx+rad+1)):
                dx, dy = xx - rotated_cx, yy - rotated_cy
                if dx*dx + dy*dy <= r2:
                    i = 2 * (yy * w + xx)
                    col = (data[i] << 8) | data[i+1]
                    if col != 0:
                        try:
                            k = PALETTE.index(col)
                        except ValueError:
                            k = 1
                        k = max(0, k - deep)
                        newc = PALETTE[k]
                        data[i]   = (newc >> 8) & 0xFF
                        data[i+1] = newc & 0xFF

    # Add craters
    darken_circle(cx-4, cy-3, 3, deep=2)
    darken_circle(cx+3, cy-1, 2, deep=1)
    darken_circle(cx-1, cy+4, 2, deep=2)

    return FrameBuffer(data, w, h, RGB565)

# Build the sprite once:
sprite_asteroid1 = make_asteroid_fb(36, 37)
ASTER_TRANSPARENT = 0  # background value we used

begin()

# -------- timer initialization ----------
SCRIPT_START_TIME = time.ticks_ms()
last_console_print = time.ticks_ms()
CONSOLE_PRINT_INTERVAL = 5000  # Print every 5 seconds

def print_runtime():
    """Print how long the script has been running"""
    current_time = time.ticks_ms()
    runtime_ms = time.ticks_diff(current_time, SCRIPT_START_TIME)
    runtime_seconds = runtime_ms / 1000.0
    print(f"Runtime: {runtime_seconds:.1f}s")

# Print initial startup time
print("Asteroid Dodge game initialized!")
print_runtime()

# -------- screen ----------
W, H = 128, 128

# -------- safe colors -----
WHITE = Display.Color.White
try: YELLOW = Display.Color.Yellow
except: YELLOW = WHITE
try: GRAY = Display.Color.Gray
except: GRAY = WHITE

# Fire blaster colors (orange and red)
try: RED = Display.Color.Red
except: RED = rgb565(255, 0, 0)  # Fallback red
try: ORANGE = Display.Color.Orange
except: ORANGE = rgb565(255, 165, 0)  # Fallback orange

# -------- tiny "pixel" built from rect (no display.circle/triangle/line used) ----
def setpix(x, y, color):
    display.rect(int(x), int(y), 1, 1, color, True)

# -------- bitmap helpers (draw with our 1x1 rect pixel) --------
def draw_bitmap(x, y, bmp_rows, color):
    # bmp_rows: list of strings, 'X' = filled, '.' = empty
    for j, row in enumerate(bmp_rows):
        for i, ch in enumerate(row):
            if ch == 'X':
                setpix(x + i, y + j, color)

def size_of_bitmap(bmp_rows):
    return (len(bmp_rows[0]), len(bmp_rows))

# -------- ship sprite (using alien2 from gyro game) ------------
sprite_alien2 = FrameBuffer(bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7F\xE0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x5C\x85\x8E\x69\xCF\xF2\x86\x29\x5C\x45\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x55\x80\x86\x86\xB7\xEC\xCF\xF2\xAF\x8C\x7E\x46\x55\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x54\x63\x86\xA6\xAF\xCC\xCF\xF2\xAF\xCC\x86\xA5\x54\x63\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x54\x63\x86\xC5\xAF\xCB\xCF\xF2\xAF\xCB\x7E\xC5\x54\x63\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x54\x43\x7E\xA5\xA7\xEA\xB7\xED\x9F\xE8\x7E\xA4\x4C\x42\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x5D\x41\x7F\x23\xA7\xA9\xA7\xE9\x97\xE4\x7F\x42\x5D\x61\x00\x00'+
b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x55\x80\x7F\xE0\x7F\xA1\x97\xC6\x97\xE5\x7F\xE0\x7F\xE0\x7F\xE0\x55\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7F\xE0\x7F\xE0\x7F\xE0\x00\x00\x00\x00\x55\x80\x7F\xE0\x7F\xE0\x7F\xE0\x7F\xE0\x7F\xE0\x7F\xE0\x7F\xE0\x55\x80\x00\x00\x00\x00\x7F\xE0\x7F\xE0\x7F\xE0\x7F\xE0\x00\x00\x7F\xE0\x00\x00\x00\x00\x55\x80\x7F\xE0\xF8\x00\x7F\xE0\x7F\xE0\x7F\xE0\xF8\x00\x7F\xE0\x55\x80\x00\x00\x00\x00\x7F\xE0\x00\x00\x7F\xE0\x7F\xE0\x00\x00\x00\x00\x7F\xE0\x00\x00\x55\x80\x7F\xE0\xF8\x00\x7F\xE0\x7F\xE0\x7F\xE0\xF8\x00\x7F\xE0\x55\x80\x00\x00\x7F\xE0\x00\x00\x00\x00\x7F\xE0\x00\x00\x00\x00\x00\x00\x7F\xE0\x00\x00\x55\x80\x55\x80\x55\x80\x55\x80\x7F\xE0\x55\x80\x55\x80\x55\x80\x55\x80\x00\x00\x7F\xE0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7F\xE0\x00\x00\x44\x00\x7F\xE0\x00\x00\x7F\xE0\x7F\xE0\x7F\xE0\x00\x00\x7F\xE0\x44\x00\x00\x00\x7F\xE0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7F\xE0\x00\x00\x00\x00\x44\x00\x7F\xE0\x00\x00\x7F\xE0'+
b'\x7F\xE0\x7F\xE0\x00\x00\x7F\xE0\x44\x00\x00\x00\x00\x00\x7F\xE0\x00\x00\x00\x00\x44\x00\x00\x00\x55\x80\x55\x80\x55\x80\x55\x80\x55\x80\x00\x00\x55\x80\x00\x00\x55\x80\x00\x00\x55\x80\x55\x80\x55\x80\x55\x80\x55\x80\x00\x00\x44\x00\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x55\x80\x00\x00\x55\x80\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x44\x00\x44\x00\x44\x00\x00\x00\x44\x00\x44\x00\x00\x00\x7F\xE0\x7F\xE0\x00\x00\x00\x00\x00\x00\x7F\xE0\x7F\xE0\x00\x00\x44\x00\x44\x00\x00\x00\x44\x00\x44\x00\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x55\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x55\x80\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x55\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x55\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x55\x80\x00\x00\x55\x80\x00\x00\x00\x00\x00\x00\x55\x80\x00\x00\x55\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'+
b'\x00\x00\x00\x00\x7F\xE0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7F\xE0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'), 19, 21, RGB565)
sprite_alien2_transparent = 0

# Fallback ASCII ship for compatibility
SHIP_BMP = [
    "....XX....",
    "...XXXX...",
    "..XXXXXX..",
    ".XXXXXXXX.",
    ".XXXXXXXX.",
    "..XXXXXX..",
    "...XXXX...",
    "....XX....",
]
SHIP_W, SHIP_H = 19, 21  # Use alien2 sprite dimensions

BULLET_W, BULLET_H = 5, 2

# -------- asteroid sprites using procedural generation --------
# Generate different sized asteroids using the make_asteroid_fb function

# Create various asteroid sizes with rotation frames (8 frames per asteroid type)
ROTATION_FRAMES = 8
ASTEROID_SPRITES = []

# Generate different asteroid types with rotation frames
asteroid_configs = [
    {"w": 20, "h": 18},  # Medium asteroid
    {"w": 16, "h": 16},  # Small round asteroid  
    {"w": 24, "h": 22},  # Large asteroid
    {"w": 14, "h": 12},  # Small irregular asteroid
    {"w": 18, "h": 20},  # Tall asteroid
    {"w": 12, "h": 10},  # Tiny asteroid
]

for config in asteroid_configs:
    w, h = config["w"], config["h"]
    # Create rotation frames for this asteroid type
    rotation_frames = []
    for frame in range(ROTATION_FRAMES):
        rotation_angle = (frame * 2 * math.pi) / ROTATION_FRAMES
        sprite = make_rotating_asteroid_fb(w, h, rotation_angle)
        rotation_frames.append(sprite)
    
    ASTEROID_SPRITES.append({
        "frames": rotation_frames,
        "transparent": ASTER_TRANSPARENT,
        "w": w,
        "h": h
    })

# Fallback ASCII asteroid for compatibility
AST_BMP = [                   # 14x12 asteroid blob
    "..XXXXXXXX....",
    ".XXXXXXXXXX...",
    "XXXXXXXXXXXX..",
    "XXXXXXXXXXXX..",
    "XXXXXXXXXXXX..",
    "XXXXXXXXXXXX..",
    ".XXXXXXXXXXX..",
    ".XXXXXXXXXX...",
    "..XXXXXXXX....",
    "..XXXXXXX.....",
    "...XXXXX......",
    "...XXXX.......",
]
AST_W, AST_H = 24, 22  # Use largest asteroid sprite size for collision detection

# -------- game state -----------------
class Game:
    def __init__(self):
        self.ship_x = 10
        self.ship_y = H//2 - SHIP_H//2
        self.ship_vy = 0.0  # ship vertical velocity
        
        self.stars = [{"x": random.randint(0, W-1),
                       "y": random.randint(0, H-1),
                       "s": random.choice([1,1,2])} for _ in range(34)]

        self.bullets = []  # dict: x,y
        self.enemies = []  # dict: x,y,vx,sprite_idx
        self.score = 0
        self.cooldown = 0.0
        self.spawn_cd = 0.0
        
        # Ship control state
        self.up_pressed = False
        self.down_pressed = False

G = Game()

# -------- tunables -------------------
STAR_SPEED = 26
BULLET_SPEED = 160.0
FIRE_RATE = 0.18
ENEMY_MIN_SPD, ENEMY_MAX_SPD = 24.0, 48.0
SPAWN_EVERY = (0.65, 1.2)
COLLISION_INSET = 1

# Ship movement constants
SHIP_SPEED = 150.0  # Increased from 80.0 for faster movement
SHIP_FRICTION = 0.85

# -------- sound (safe) ---------------
def tick(freq=1400, ms=20):
    try: piezo.tone(freq, ms)
    except: pass

def hit_sound():
    # Enhanced asteroid hit sound inspired by sfxr parameters
    # Simulating: attack->sustain->punch->decay with frequency slide
    try:
        # Attack phase: Quick high-pitched impact (simulating p_env_attack: 0)
        piezo.tone(1200, 30)   # Sharp initial hit
        
        # Sustain phase: Medium frequency hold (p_env_sustain: 0.32)
        time.sleep_ms(10)
        piezo.tone(800, 60)    # Sustained impact tone
        
        # Punch phase: Brief frequency boost (p_env_punch: 0.62)
        time.sleep_ms(20)
        piezo.tone(1000, 40)   # Punch emphasis
        
        # Decay phase: Sliding down frequency (p_env_decay: 0.44, p_freq_ramp: 0.17)
        time.sleep_ms(15)
        piezo.tone(600, 50)    # Decay start
        time.sleep_ms(25)
        piezo.tone(400, 60)    # Frequency slide down
        time.sleep_ms(30)
        piezo.tone(200, 40)    # Final decay
        
    except: pass

def fire_sound():
    try: piezo.tone(1400, 20)
    except: pass

# -------- controls: SHIP MOVEMENT & FIRE --
def fire():
    if G.cooldown > 0: return
    nose_x = G.ship_x + SHIP_W + 1
    nose_y = G.ship_y + SHIP_H//2
    G.bullets.append({"x": float(nose_x), "y": float(nose_y), "age": 0.0})
    G.cooldown = FIRE_RATE
    fire_sound()

def move_up():
    G.up_pressed = True

def move_down():
    G.down_pressed = True

def stop_up():
    G.up_pressed = False

def stop_down():
    G.down_pressed = False

def bind_buttons():
    # Fire button
    def try_bind_fire(name):
        try:
            btn = getattr(Buttons, name)
            buttons.on_press(btn, lambda: fire())
        except:
            pass
    
    # Movement buttons - both press and release events
    try:
        buttons.on_press(Buttons.Up, move_up)
        buttons.on_release(Buttons.Up, stop_up)
        buttons.on_press(Buttons.Down, move_down)
        buttons.on_release(Buttons.Down, stop_down)
    except:
        pass
    
    # Try different fire button names
    for n in ["A","Ok","Select","Center","Confirm","Right"]:
        try_bind_fire(n)

bind_buttons()

# -------- world helpers --------------
def move_stars(dt):
    for st in G.stars:
        st["x"] -= (STAR_SPEED + st["s"]*10) * dt
        if st["x"] < 0:
            st["x"] = W - 1
            st["y"] = random.randint(0, H-1)

def spawn_enemy():
    y = random.randint(4, H - AST_H - 4)
    speed = random.uniform(ENEMY_MIN_SPD, ENEMY_MAX_SPD)
    sprite_idx = random.randint(0, len(ASTEROID_SPRITES) - 1)
    rotation_speed = random.uniform(0.5, 2.0)  # radians per second
    rotation_frame = random.randint(0, ROTATION_FRAMES - 1)  # random starting frame
    G.enemies.append({
        "x": float(W + 2), 
        "y": float(y), 
        "vx": -speed, 
        "sprite_idx": sprite_idx,
        "rotation_frame": rotation_frame,
        "rotation_speed": rotation_speed,
        "rotation_timer": 0.0
    })

def update_ship_movement(dt):
    # Apply movement based on button presses
    if G.up_pressed:
        G.ship_vy -= SHIP_SPEED * dt
    if G.down_pressed:
        G.ship_vy += SHIP_SPEED * dt
    
    # Apply friction to smooth movement
    G.ship_vy *= SHIP_FRICTION
    
    # Update ship position
    G.ship_y += G.ship_vy * dt
    
    # Keep ship within screen bounds
    if G.ship_y < 0:
        G.ship_y = 0
        G.ship_vy = 0
    if G.ship_y > H - SHIP_H:
        G.ship_y = H - SHIP_H
        G.ship_vy = 0
    
    # Don't reset button states - they're managed by press/release events

def draw_asteroid(x, y, sprite_idx, rotation_frame):
    # Draw asteroid using FrameBuffer sprites with rotation
    try:
        asteroid_data = ASTEROID_SPRITES[sprite_idx]
        sprite = asteroid_data["frames"][rotation_frame]
        transparent = asteroid_data["transparent"]
        
        # Draw the asteroid sprite using display.blit
        display.blit(sprite, int(x), int(y), transparent)
        
    except:
        # Fallback to ASCII art if sprite fails
        draw_bitmap(int(x), int(y), AST_BMP, GRAY)

def aabb(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2):
    return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)

# -------- main loop ------------------
last_ms = time.ticks_ms()

while True:
    buttons.scan()
    now = time.ticks_ms()
    dt = max(0, time.ticks_diff(now, last_ms)) / 1000.0
    last_ms = now
    
    # Print runtime to console periodically
    if time.ticks_diff(now, last_console_print) >= CONSOLE_PRINT_INTERVAL:
        print_runtime()
        print(f"Score: {G.score}, Enemies: {len(G.enemies)}, Bullets: {len(G.bullets)}")
        last_console_print = now

    # cooldowns
    if G.cooldown > 0: G.cooldown = max(0.0, G.cooldown - dt)
    if G.spawn_cd <= 0:
        spawn_enemy()
        G.spawn_cd = random.uniform(*SPAWN_EVERY)
    else:
        G.spawn_cd -= dt

    # update ship movement based on button presses
    update_ship_movement(dt)

    # move stars
    move_stars(dt)

    # bullets
    for b in G.bullets:
        b["x"] += BULLET_SPEED * dt
        b["age"] += dt  # Track bullet age for fire effect
    G.bullets = [b for b in G.bullets if b["x"] < W+6]

    # enemies (movement and rotation)
    for e in G.enemies:
        e["x"] += e["vx"] * dt
        
        # Update rotation animation
        e["rotation_timer"] += dt
        frame_duration = (2 * math.pi) / (e["rotation_speed"] * ROTATION_FRAMES)
        if e["rotation_timer"] >= frame_duration:
            e["rotation_timer"] = 0.0
            e["rotation_frame"] = (e["rotation_frame"] + 1) % ROTATION_FRAMES
    
    G.enemies = [e for e in G.enemies if e["x"] + AST_W > -4]

    # collisions (bullets vs enemies)
    survivors = []
    for e in G.enemies:
        hit = False
        ex1 = e["x"] + COLLISION_INSET
        ey1 = e["y"] + COLLISION_INSET
        ex2 = e["x"] + AST_W - COLLISION_INSET
        ey2 = e["y"] + AST_H - COLLISION_INSET
        for b in G.bullets:
            bx1 = b["x"]
            by1 = b["y"] - BULLET_H//2
            bx2 = b["x"] + BULLET_W
            by2 = b["y"] + BULLET_H//2
            if aabb(ex1, ey1, ex2, ey2, bx1, by1, bx2, by2):
                hit = True
                b["x"] = W + 99
                break
        if hit:
            hit_sound()
            G.score += 1
        else:
            survivors.append(e)
    G.enemies = survivors
    G.bullets = [b for b in G.bullets if b["x"] < W+10]

    # ------------ render ---------------
    display.fill(0)
    # stars
    for st in G.stars:
        setpix(st["x"], st["y"], WHITE if st["s"]==2 else GRAY)
    # enemies
    for e in G.enemies:
        draw_asteroid(e["x"], e["y"], e["sprite_idx"], e["rotation_frame"])
    # ship (using alien2 sprite)
    try:
        display.blit(sprite_alien2, int(G.ship_x), int(G.ship_y), sprite_alien2_transparent)
    except:
        # Fallback to ASCII art
        draw_bitmap(G.ship_x, G.ship_y, SHIP_BMP, WHITE)
    # bullets (fire blaster effect)
    for b in G.bullets:
        # Create fire effect: alternate between orange and red based on bullet age
        # Fast oscillation creates flickering fire effect
        fire_cycle = (b["age"] * 8) % 1.0  # 8 cycles per second
        bullet_color = ORANGE if fire_cycle < 0.5 else RED
        
        # Draw main bullet body
        display.rect(int(b["x"]), int(b["y"] - BULLET_H//2), BULLET_W, BULLET_H, bullet_color, True)
        
        # Add fire trail effect (smaller trailing rectangles)
        trail_color = RED if fire_cycle < 0.5 else ORANGE  # Opposite color for trail
        display.rect(int(b["x"] - 2), int(b["y"] - BULLET_H//2), 2, BULLET_H, trail_color, True)

    display.text("Score: " + str(G.score), 4, 4, WHITE)
    display.commit()
    time.sleep_ms(16)