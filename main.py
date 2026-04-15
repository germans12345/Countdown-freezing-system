# =====================================
# 项目1 阶段4：倒计时冻结系统（录屏优化版）
# -------------------------------------
# 本阶段目标：
# 1. 保留阶段3的核心玩法：
#    - 小球可逃出
#    - 超时冻结
#    - 冻结球成为障碍物
# 2. 进行录屏展示优化：
#    - 开场标题
#    - 规则提示文案
#    - 底部状态栏
#    - 轻微拖尾
#    - 结果展示层
#    - 自动重开
#
# 操作说明：
# - 空格：立刻重开
# =====================================

# ========= 1. 导入库 =========
import pygame
import sys
import math
import random

# ========= 2. 初始化 pygame =========
pygame.init()
pygame.font.init()

# =====================================
# ========= 3. 窗口与基础参数 =========
# =====================================
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("项目1 阶段4：倒计时冻结系统（录屏优化版）")

clock = pygame.time.Clock()
FPS = 60

# =====================================
# ========= 4. 场景中心点 =========
# =====================================
center_x = WIDTH // 2
center_y = HEIGHT // 2 + 70

# =====================================
# ========= 5. 颜色配置 =========
# =====================================
BG_COLOR = (10, 14, 22)
RING_COLOR = (220, 228, 245)

BALL_COLOR_SAFE = (255, 196, 95)
BALL_COLOR_DANGER = (255, 110, 90)
BALL_TEXT_COLOR = (18, 20, 30)

FROZEN_BALL_COLOR = (115, 175, 255)
FROZEN_OUTLINE_COLOR = (230, 242, 255)

ESCAPE_EFFECT_COLOR = (120, 255, 190)
FREEZE_EFFECT_COLOR = (150, 210, 255)

TEXT_COLOR = (244, 244, 244)
SUB_TEXT_COLOR = (170, 180, 200)
ACCENT_COLOR = (120, 195, 255)
PANEL_COLOR = (8, 10, 16)

# =====================================
# ========= 6. 圆环参数 =========
# =====================================
RING_RADIUS = 220
RING_WIDTH = 6

GAP_SIZE = 42
GAP_CENTER_ANGLE = 315

# =====================================
# ========= 7. 小球参数 =========
# =====================================
BALL_COUNT = 10
BALL_RADIUS = 13

MIN_BALL_SPEED = 2.8
MAX_BALL_SPEED = 4.2

BASE_FREEZE_TIME = 5.6
FREEZE_TIME_RANDOM_ADD = 3.2

SMALL_RANDOM_TURN = 0.015

# =====================================
# ========= 8. 特效参数 =========
# =====================================
particles = []
shockwaves = []
MAX_PARTICLES = 400

# =====================================
# ========= 9. 演出与结果参数 =========
# =====================================
ROUND_STATE_RUNNING = "running"
ROUND_STATE_RESULT = "result"

round_state = ROUND_STATE_RUNNING
result_timer = 0
RESULT_HOLD_TIME = 2.8

opening_text_timer = 180   # 大约 3 秒
overlay_flash = 0.0

# =====================================
# ========= 10. 字体 =========
# =====================================
font_title_big = pygame.font.Font(None, 66)
font_title = pygame.font.Font(None, 48)
font_main = pygame.font.Font(None, 34)
font_small = pygame.font.Font(None, 26)
font_ball = pygame.font.Font(None, 22)
font_result = pygame.font.Font(None, 58)

# =====================================
# ========= 11. 拖尾图层 =========
# =====================================
world_surface = pygame.Surface((WIDTH, HEIGHT))
fade_surface = pygame.Surface((WIDTH, HEIGHT))
fade_surface.set_alpha(22)
fade_surface.fill(BG_COLOR)

# =====================================
# ========= 12. 工具函数 =========
# =====================================
def clamp(value, low, high):
    return max(low, min(high, value))


def mix_color(color_a, color_b, t):
    return (
        int(color_a[0] * (1 - t) + color_b[0] * t),
        int(color_a[1] * (1 - t) + color_b[1] * t),
        int(color_a[2] * (1 - t) + color_b[2] * t),
    )


def get_ball_speed(ball):
    return math.sqrt(ball["vx"] ** 2 + ball["vy"] ** 2)


def clamp_ball_speed(ball):
    speed = get_ball_speed(ball)

    if speed == 0:
        angle = random.uniform(0, math.pi * 2)
        ball["vx"] = math.cos(angle) * MIN_BALL_SPEED
        ball["vy"] = math.sin(angle) * MIN_BALL_SPEED
        return

    if speed < MIN_BALL_SPEED:
        scale = MIN_BALL_SPEED / speed
        ball["vx"] *= scale
        ball["vy"] *= scale
    elif speed > MAX_BALL_SPEED:
        scale = MAX_BALL_SPEED / speed
        ball["vx"] *= scale
        ball["vy"] *= scale


def get_ball_angle(ball):
    dx = ball["x"] - center_x
    dy = ball["y"] - center_y
    angle = math.degrees(math.atan2(dy, dx))
    if angle < 0:
        angle += 360
    return angle


def is_angle_in_gap(angle):
    gap_start = (GAP_CENTER_ANGLE - GAP_SIZE / 2) % 360
    gap_end = (GAP_CENTER_ANGLE + GAP_SIZE / 2) % 360

    if gap_start <= gap_end:
        return gap_start <= angle <= gap_end

    return angle >= gap_start or angle <= gap_end


def add_small_random_turn(ball, amount=SMALL_RANDOM_TURN):
    speed = get_ball_speed(ball)
    if speed == 0:
        return

    angle = math.atan2(ball["vy"], ball["vx"])
    angle += random.uniform(-amount, amount)

    ball["vx"] = math.cos(angle) * speed
    ball["vy"] = math.sin(angle) * speed


# =====================================
# ========= 13. 粒子系统 =========
# =====================================
def spawn_particles(x, y, color, count=10, speed_min=1.0, speed_max=3.0, life_min=16, life_max=28):
    if len(particles) >= MAX_PARTICLES:
        return

    available = MAX_PARTICLES - len(particles)
    real_count = min(count, available)

    for _ in range(real_count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(speed_min, speed_max)
        life = random.randint(life_min, life_max)

        particles.append({
            "x": x,
            "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": life,
            "max_life": life,
            "color": color,
            "radius": random.randint(2, 4),
        })


def update_particles():
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vx"] *= 0.985
        p["vy"] *= 0.985
        p["life"] -= 1

        if p["life"] <= 0:
            particles.remove(p)


def draw_particles(surface):
    for p in particles:
        alpha_ratio = p["life"] / max(1, p["max_life"])
        radius = max(1, int(p["radius"] * alpha_ratio))
        pygame.draw.circle(surface, p["color"], (int(p["x"]), int(p["y"])), radius)


# =====================================
# ========= 14. 冲击波系统 =========
# =====================================
def spawn_shockwave(x, y, color, start_radius=8, max_radius=48, growth=3.0, life=16):
    shockwaves.append({
        "x": x,
        "y": y,
        "radius": start_radius,
        "max_radius": max_radius,
        "growth": growth,
        "life": life,
        "max_life": life,
        "color": color,
    })


def update_shockwaves():
    for wave in shockwaves[:]:
        wave["radius"] += wave["growth"]
        wave["life"] -= 1

        if wave["life"] <= 0 or wave["radius"] >= wave["max_radius"]:
            shockwaves.remove(wave)


def draw_shockwaves(surface):
    for wave in shockwaves:
        alpha_ratio = wave["life"] / max(1, wave["max_life"])
        width = max(1, int(3 * alpha_ratio))
        pygame.draw.circle(
            surface,
            wave["color"],
            (int(wave["x"]), int(wave["y"])),
            int(wave["radius"]),
            width
        )


# =====================================
# ========= 15. 小球创建 =========
# =====================================
balls = []


def create_one_ball():
    angle = random.uniform(0, math.pi * 2)
    speed = random.uniform(3.0, 3.7)
    freeze_time = BASE_FREEZE_TIME + random.uniform(0, FREEZE_TIME_RANDOM_ADD)

    return {
        "x": center_x + random.uniform(-28, 28),
        "y": center_y + random.uniform(-28, 28),
        "vx": math.cos(angle) * speed,
        "vy": math.sin(angle) * speed,
        "radius": BALL_RADIUS,

        "remain_time": freeze_time,
        "max_time": freeze_time,

        "escaped": False,
        "frozen": False,
    }


def create_balls():
    balls.clear()
    for _ in range(BALL_COUNT):
        balls.append(create_one_ball())


# =====================================
# ========= 16. 回合状态 =========
# =====================================
def count_running_balls():
    count = 0
    for ball in balls:
        if not ball["escaped"] and not ball["frozen"]:
            count += 1
    return count


def count_frozen_balls():
    count = 0
    for ball in balls:
        if ball["frozen"]:
            count += 1
    return count


def count_escaped_balls():
    count = 0
    for ball in balls:
        if ball["escaped"]:
            count += 1
    return count


def all_balls_finished():
    for ball in balls:
        if not ball["escaped"] and not ball["frozen"]:
            return False
    return True


def reset_game():
    global round_state, result_timer, opening_text_timer, overlay_flash

    round_state = ROUND_STATE_RUNNING
    result_timer = 0
    opening_text_timer = 180
    overlay_flash = 0.0

    create_balls()
    particles.clear()
    shockwaves.clear()

    world_surface.fill(BG_COLOR)


# =====================================
# ========= 17. 事件特效 =========
# =====================================
def trigger_ball_escape(ball):
    global overlay_flash

    spawn_particles(
        ball["x"], ball["y"],
        ESCAPE_EFFECT_COLOR,
        count=18,
        speed_min=1.2,
        speed_max=3.8,
        life_min=16,
        life_max=28
    )
    spawn_shockwave(
        ball["x"], ball["y"],
        ESCAPE_EFFECT_COLOR,
        start_radius=10,
        max_radius=52,
        growth=3.6,
        life=18
    )

    overlay_flash = max(overlay_flash, 0.18)


def trigger_ball_freeze(ball):
    spawn_particles(
        ball["x"], ball["y"],
        FREEZE_EFFECT_COLOR,
        count=14,
        speed_min=0.8,
        speed_max=2.8,
        life_min=14,
        life_max=24
    )
    spawn_shockwave(
        ball["x"], ball["y"],
        FREEZE_EFFECT_COLOR,
        start_radius=8,
        max_radius=40,
        growth=2.8,
        life=16
    )


# =====================================
# ========= 18. 圆环碰撞 =========
# =====================================
def reflect_ball_on_ring(ball, distance):
    dx = ball["x"] - center_x
    dy = ball["y"] - center_y

    if distance == 0:
        distance = 0.001

    nx = dx / distance
    ny = dy / distance

    dot = ball["vx"] * nx + ball["vy"] * ny

    ball["vx"] -= 2 * dot * nx
    ball["vy"] -= 2 * dot * ny

    safe_dist = RING_RADIUS - ball["radius"] - 1
    ball["x"] = center_x + nx * safe_dist
    ball["y"] = center_y + ny * safe_dist

    clamp_ball_speed(ball)


def try_escape_or_bounce(ball):
    dx = ball["x"] - center_x
    dy = ball["y"] - center_y
    distance = math.sqrt(dx * dx + dy * dy)

    outer_limit = RING_RADIUS - ball["radius"]

    if distance < outer_limit:
        return

    angle = get_ball_angle(ball)

    if is_angle_in_gap(angle):
        trigger_ball_escape(ball)
        ball["escaped"] = True
        return

    reflect_ball_on_ring(ball, distance)


# =====================================
# ========= 19. 冻结球碰撞 =========
# =====================================
def collide_with_frozen_balls(ball):
    for other in balls:
        if other is ball:
            continue

        if not other["frozen"]:
            continue

        dx = ball["x"] - other["x"]
        dy = ball["y"] - other["y"]
        dist = math.sqrt(dx * dx + dy * dy)
        min_dist = ball["radius"] + other["radius"]

        if dist >= min_dist:
            continue

        if dist == 0:
            dx = random.uniform(-1, 1)
            dy = random.uniform(-1, 1)
            dist = math.sqrt(dx * dx + dy * dy)
            if dist == 0:
                dist = 0.001

        overlap = min_dist - dist
        nx = dx / dist
        ny = dy / dist

        ball["x"] += nx * overlap
        ball["y"] += ny * overlap

        dot = ball["vx"] * nx + ball["vy"] * ny
        ball["vx"] -= 2 * dot * nx
        ball["vy"] -= 2 * dot * ny

        add_small_random_turn(ball, amount=0.03)
        clamp_ball_speed(ball)


# =====================================
# ========= 20. 小球更新 =========
# =====================================
def update_one_ball(ball, dt):
    if ball["escaped"] or ball["frozen"]:
        return

    ball["remain_time"] -= dt

    if ball["remain_time"] <= 0:
        ball["remain_time"] = 0
        ball["frozen"] = True
        ball["vx"] = 0
        ball["vy"] = 0
        trigger_ball_freeze(ball)
        return

    ball["x"] += ball["vx"]
    ball["y"] += ball["vy"]

    collide_with_frozen_balls(ball)
    try_escape_or_bounce(ball)

    add_small_random_turn(ball, amount=SMALL_RANDOM_TURN)
    clamp_ball_speed(ball)


def update_balls(dt):
    for ball in balls:
        update_one_ball(ball, dt)


# =====================================
# ========= 21. 全局更新 =========
# =====================================
def update_round_logic():
    global round_state, result_timer

    if round_state == ROUND_STATE_RUNNING:
        if all_balls_finished():
            round_state = ROUND_STATE_RESULT
            result_timer = int(RESULT_HOLD_TIME * FPS)

    elif round_state == ROUND_STATE_RESULT:
        result_timer -= 1
        if result_timer <= 0:
            reset_game()


def update_effects():
    update_particles()
    update_shockwaves()


def update_overlay():
    global opening_text_timer, overlay_flash

    if opening_text_timer > 0:
        opening_text_timer -= 1

    overlay_flash *= 0.90


# =====================================
# ========= 22. 绘制世界层 =========
# =====================================
def draw_background(surface):
    surface.fill(BG_COLOR)


def draw_ring(surface):
    for angle in range(0, 360):
        if is_angle_in_gap(angle):
            continue

        rad = math.radians(angle)
        x = int(center_x + RING_RADIUS * math.cos(rad))
        y = int(center_y + RING_RADIUS * math.sin(rad))
        pygame.draw.circle(surface, RING_COLOR, (x, y), RING_WIDTH // 2)


def get_running_ball_color(ball):
    if ball["max_time"] <= 0:
        return BALL_COLOR_SAFE

    ratio = ball["remain_time"] / ball["max_time"]
    ratio = clamp(ratio, 0.0, 1.0)
    danger_t = 1.0 - ratio
    return mix_color(BALL_COLOR_SAFE, BALL_COLOR_DANGER, danger_t)


def draw_one_ball(surface, ball):
    if ball["escaped"]:
        return

    x = int(ball["x"])
    y = int(ball["y"])

    if ball["frozen"]:
        pygame.draw.circle(surface, (55, 85, 125), (x, y), ball["radius"] + 8, 2)
        pygame.draw.circle(surface, FROZEN_BALL_COLOR, (x, y), ball["radius"])
        pygame.draw.circle(surface, FROZEN_OUTLINE_COLOR, (x, y), ball["radius"], 2)
    else:
        color = get_running_ball_color(ball)
        pygame.draw.circle(surface, color, (x, y), ball["radius"])

        ratio = ball["remain_time"] / ball["max_time"]
        if ratio < 0.35:
            pygame.draw.circle(surface, (255, 240, 230), (x, y), ball["radius"], 2)

        time_text = f"{ball['remain_time']:.1f}"
        render = font_ball.render(time_text, True, BALL_TEXT_COLOR)
        text_x = x - render.get_width() // 2
        text_y = y - render.get_height() // 2
        surface.blit(render, (text_x, text_y))


def draw_balls(surface):
    for ball in balls:
        draw_one_ball(surface, ball)


def render_world():
    world_surface.blit(fade_surface, (0, 0))
    draw_ring(world_surface)
    draw_shockwaves(world_surface)
    draw_particles(world_surface)
    draw_balls(world_surface)


# =====================================
# ========= 23. 绘制 UI 层 =========
# =====================================
def draw_top_title_block(surface):
    title = font_title_big.render("RULE EXPERIMENT 01", True, TEXT_COLOR)
    sub = font_title.render("Countdown Freeze System", True, ACCENT_COLOR)

    surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 36))
    surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 94))


def draw_opening_prompt(surface):
    if opening_text_timer <= 0:
        return

    alpha_ratio = opening_text_timer / 180.0
    alpha = int(255 * alpha_ratio)

    text = "Escape before your own timer ends."
    sub_text = "If you fail, you freeze and block the arena."

    render1 = font_main.render(text, True, TEXT_COLOR)
    render2 = font_main.render(sub_text, True, SUB_TEXT_COLOR)

    temp1 = pygame.Surface(render1.get_size(), pygame.SRCALPHA)
    temp1.blit(render1, (0, 0))
    temp1.set_alpha(alpha)

    temp2 = pygame.Surface(render2.get_size(), pygame.SRCALPHA)
    temp2.blit(render2, (0, 0))
    temp2.set_alpha(alpha)

    y = 170
    surface.blit(temp1, (WIDTH // 2 - temp1.get_width() // 2, y))
    surface.blit(temp2, (WIDTH // 2 - temp2.get_width() // 2, y + 34))


def draw_bottom_status_bar(surface):
    bar_w = WIDTH - 60
    bar_h = 92
    bar_x = 30
    bar_y = HEIGHT - 125

    panel = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 145))
    surface.blit(panel, (bar_x, bar_y))

    pygame.draw.rect(surface, (80, 92, 118), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=16)

    running_render = font_main.render(f"RUNNING {count_running_balls()}", True, BALL_COLOR_SAFE)
    frozen_render = font_main.render(f"FROZEN {count_frozen_balls()}", True, FROZEN_BALL_COLOR)
    escaped_render = font_main.render(f"ESCAPED {count_escaped_balls()}", True, ESCAPE_EFFECT_COLOR)

    surface.blit(running_render, (bar_x + 28, bar_y + 18))
    surface.blit(frozen_render, (bar_x + 28, bar_y + 50))
    surface.blit(escaped_render, (bar_x + 255, bar_y + 50))

    tip = font_small.render("SPACE = restart", True, SUB_TEXT_COLOR)
    surface.blit(tip, (bar_x + bar_w - tip.get_width() - 22, bar_y + 34))


def draw_result_overlay(surface):
    if round_state != ROUND_STATE_RESULT:
        return

    box_w = 520
    box_h = 180
    box_x = WIDTH // 2 - box_w // 2
    box_y = HEIGHT // 2 - 120

    box_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box_surface.fill((0, 0, 0, 155))
    surface.blit(box_surface, (box_x, box_y))

    pygame.draw.rect(surface, (185, 205, 240), (box_x, box_y, box_w, box_h), 2, border_radius=18)

    escaped = count_escaped_balls()
    frozen = count_frozen_balls()

    if escaped >= frozen:
        result_text = "MORE ESCAPED"
        result_color = ESCAPE_EFFECT_COLOR
    else:
        result_text = "ARENA LOCKED"
        result_color = FROZEN_BALL_COLOR

    title_render = font_result.render(result_text, True, result_color)
    sub_render = font_main.render(
        f"Escaped {escaped}   |   Frozen {frozen}",
        True,
        TEXT_COLOR
    )

    surface.blit(title_render, (WIDTH // 2 - title_render.get_width() // 2, box_y + 34))
    surface.blit(sub_render, (WIDTH // 2 - sub_render.get_width() // 2, box_y + 108))


def draw_overlay_flash(surface):
    if overlay_flash <= 0.01:
        return

    alpha = int(overlay_flash * 80)
    flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    flash_surface.fill((255, 255, 255, alpha))
    surface.blit(flash_surface, (0, 0))


# =====================================
# ========= 24. 初始化 =========
# =====================================
reset_game()

# =====================================
# ========= 25. 主循环 =========
# =====================================
while True:
    dt = clock.tick(FPS) / 1000.0

    # ---------- 25.1 事件 ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                reset_game()

    # ---------- 25.2 更新 ----------
    if round_state == ROUND_STATE_RUNNING:
        update_balls(dt)

    update_round_logic()
    update_effects()
    update_overlay()

    # ---------- 25.3 渲染世界 ----------
    render_world()
    screen.blit(world_surface, (0, 0))

    # ---------- 25.4 绘制包装层 ----------
    draw_top_title_block(screen)
    draw_opening_prompt(screen)
    draw_bottom_status_bar(screen)
    draw_result_overlay(screen)
    draw_overlay_flash(screen)

    pygame.display.flip()