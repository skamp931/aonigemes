import streamlit as st
import numpy as np
import random
import time
from collections import deque

# --- ゲームの設定 ---
MAP_WIDTH = 18
MAP_HEIGHT = 14
WALL = "🧱"
FLOOR = "⬛"
PLAYER = "🏃"
ONI = "👹"
KEY = "🔑"
EXIT_LOCKED = "🚪"
EXIT_UNLOCKED = "🟩"
OBSTACLE = "🌲"
TRAP = "🪤"  # 罠のアイコン
INITIAL_PLAYER_POS = [1, 1]
INITIAL_ONI_POS = [MAP_WIDTH - 2, MAP_HEIGHT - 2] # [14, 13]
KEY_POS = [6, 5]
EXIT_POS = [MAP_WIDTH - 2, 1] # [14, 1]

def is_path_possible(game_map, start_pos, end_pos):
    """BFS (幅優先探索) を使って、スタートからゴールまでの道があるかチェック"""
    queue = deque([start_pos])
    visited = {tuple(start_pos)}
    
    while queue:
        x, y = queue.popleft()
        
        if [x, y] == end_pos:
            return True
            
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            
            if 0 <= ny < MAP_HEIGHT and 0 <= nx < MAP_WIDTH:
                if tuple([nx, ny]) not in visited and game_map[ny][nx] != WALL:
                    visited.add(tuple([nx, ny]))
                    queue.append([nx, ny])
    return False

def generate_map(clear_count):
    """壁と床で基本的なマップを生成し、クリア回数と壁をランダムに配置する"""
    while True:
        game_map = np.full((MAP_HEIGHT, MAP_WIDTH), FLOOR, dtype=str)
        game_map[0, :] = WALL
        game_map[-1, :] = WALL
        game_map[:, 0] = WALL
        game_map[:, -1] = WALL

        # --- 内部の壁をランダムに配置 ---
        possible_wall_positions = []
        for y in range(1, MAP_HEIGHT - 1):
            for x in range(1, MAP_WIDTH - 1):
                 if [x, y] not in [INITIAL_PLAYER_POS, INITIAL_ONI_POS, KEY_POS, EXIT_POS]:
                    possible_wall_positions.append([x, y])
        
        num_walls = 25 # 壁の数
        if len(possible_wall_positions) >= num_walls:
            wall_positions = random.sample(possible_wall_positions, num_walls)
            for pos in wall_positions:
                game_map[pos[1]][pos[0]] = WALL

        # --- マップがクリア可能かチェック ---
        if is_path_possible(game_map, INITIAL_PLAYER_POS, KEY_POS) and \
           is_path_possible(game_map, KEY_POS, EXIT_POS):
            break # クリア可能ならループを抜ける
            
    # --- 障害物の配置 ---
    possible_obstacle_positions = []
    for y in range(1, MAP_HEIGHT - 1):
        for x in range(1, MAP_WIDTH - 1):
            if game_map[y][x] == FLOOR and [x, y] not in [INITIAL_PLAYER_POS, INITIAL_ONI_POS, KEY_POS, EXIT_POS]:
                possible_obstacle_positions.append([x, y])
    
    num_obstacles = min(clear_count, 35)
    
    if num_obstacles > 0 and len(possible_obstacle_positions) >= num_obstacles:
        obstacle_positions = random.sample(possible_obstacle_positions, num_obstacles)
        for pos in obstacle_positions:
            game_map[pos[1]][pos[0]] = OBSTACLE

    return game_map.tolist()

def initialize_game():
    """ゲームの状態を初期化する"""
    if 'game_started' not in st.session_state:
        if 'clear_count' not in st.session_state:
            st.session_state.clear_count = 0
        if 'difficulty' not in st.session_state:
            st.session_state.difficulty = "ふつう"
        
        st.session_state.game_map = generate_map(st.session_state.clear_count)
        st.session_state.player_pos = list(INITIAL_PLAYER_POS)
        st.session_state.oni_pos = list(INITIAL_ONI_POS)
        st.session_state.key_pos = list(KEY_POS)
        st.session_state.exit_pos = list(EXIT_POS)
        st.session_state.has_key = False
        st.session_state.game_over = False
        st.session_state.win = False
        st.session_state.message = "屋敷に閉じ込められた...。鍵を見つけて脱出しなければ。"
        st.session_state.turn_count = 0
        st.session_state.win_counted = False
        st.session_state.game_started = True

        # --- 時間記録の初期化 ---
        st.session_state.start_time = time.time()
        st.session_state.end_time = None

        # --- 罠関連の初期化 ---
        st.session_state.trap_pos = None
        st.session_state.oni_stopped_turns = 0
        if st.session_state.difficulty == "むずかしい":
            st.session_state.trap_count = 1
        else:
            st.session_state.trap_count = 0


def display_map():
    """現在のゲームマップを表示する"""
    display_map_data = [row[:] for row in st.session_state.game_map]
    
    px, py = st.session_state.player_pos
    ox, oy = st.session_state.oni_pos
    
    if st.session_state.trap_pos:
        tx, ty = st.session_state.trap_pos
        if [tx, ty] != [px, py] and [tx, ty] != [ox, oy]:
            display_map_data[ty][tx] = TRAP
    
    if st.session_state.key_pos:
        kx, ky = st.session_state.key_pos
        display_map_data[ky][kx] = KEY

    ex, ey = st.session_state.exit_pos

    display_map_data[py][px] = PLAYER
    display_map_data[oy][ox] = ONI
        
    exit_icon = EXIT_UNLOCKED if st.session_state.has_key else EXIT_LOCKED
    display_map_data[ey][ex] = exit_icon
    
    map_str = "\n".join(["".join(row) for row in display_map_data])
    st.code(map_str, language=None)


def move_player(dx, dy):
    """プレイヤーを1マス移動させ、ゲームのターンを進行させる"""
    if st.session_state.game_over or st.session_state.win:
        return

    px, py = st.session_state.player_pos
    new_px, new_py = px + dx, py + dy

    if st.session_state.game_map[new_py][new_px] not in [WALL, OBSTACLE]:
        st.session_state.player_pos = [new_px, new_py]
        st.session_state.message = ""
        st.session_state.turn_count += 1
        move_oni()
        check_events()
    else:
        st.session_state.message = "そっちには進めない！"

def handle_bulk_move(commands):
    """テキストコマンドに基づいてプレイヤーを連続で移動させる"""
    for command in commands.lower():
        if st.session_state.game_over or st.session_state.win:
            break

        dx, dy = 0, 0
        if command == 'l': dx = -1
        elif command == 'r': dx = 1
        elif command == 'u': dy = -1
        elif command == 'd': dy = 1
        else: continue

        px, py = st.session_state.player_pos
        new_px, new_py = px + dx, py + dy

        if st.session_state.game_map[new_py][new_px] not in [WALL, OBSTACLE]:
            st.session_state.player_pos = [new_px, new_py]
            st.session_state.message = "一括移動中..."
            st.session_state.turn_count += 1
            move_oni()
            check_events()
        else:
            st.session_state.message = "一括移動中に壁にぶつかり停止しました。"
            break
            
def _move_oni_one_step():
    """鬼をプレイヤーに向かって1マス動かす内部ロジック"""
    px, py = st.session_state.player_pos
    ox, oy = st.session_state.oni_pos
    new_ox, new_oy = ox, oy
    dist_x, dist_y = px - ox, py - oy
    impassable = [WALL, OBSTACLE]

    if abs(dist_x) > abs(dist_y):
        if dist_x > 0 and st.session_state.game_map[oy][ox + 1] not in impassable: new_ox += 1
        elif dist_x < 0 and st.session_state.game_map[oy][ox - 1] not in impassable: new_ox -= 1
        elif dist_y > 0 and st.session_state.game_map[oy + 1][ox] not in impassable: new_oy += 1
        elif dist_y < 0 and st.session_state.game_map[oy - 1][ox] not in impassable: new_oy -= 1
    else:
        if dist_y > 0 and st.session_state.game_map[oy + 1][ox] not in impassable: new_oy += 1
        elif dist_y < 0 and st.session_state.game_map[oy - 1][ox] not in impassable: new_oy -= 1
        elif dist_x > 0 and st.session_state.game_map[oy][ox + 1] not in impassable: new_ox += 1
        elif dist_x < 0 and st.session_state.game_map[oy][ox - 1] not in impassable: new_ox -= 1

    st.session_state.oni_pos = [new_ox, new_oy]

def check_oni_trap_interaction():
    """鬼が罠を踏んだかチェックし、踏んでいたら停止させる"""
    if st.session_state.trap_pos and st.session_state.oni_pos == st.session_state.trap_pos:
        st.session_state.oni_stopped_turns = 3
        st.session_state.trap_pos = None
        st.session_state.message = f"鬼が罠にかかった！ {st.session_state.oni_stopped_turns}ターン動けない。"

def move_oni():
    """難易度に応じて鬼の状態を更新する"""
    if st.session_state.oni_stopped_turns > 0:
        st.session_state.oni_stopped_turns -= 1
        if st.session_state.oni_stopped_turns > 0:
            st.session_state.message = f"鬼は罠にはまっている！あと{st.session_state.oni_stopped_turns}ターンは動けない。"
        else:
            st.session_state.message = "鬼が罠から抜け出した！"
        return

    difficulty = st.session_state.difficulty
    
    if difficulty == "やさしい":
        if st.session_state.turn_count % 2 == 0:
            _move_oni_one_step()
            check_oni_trap_interaction()
    elif difficulty == "ふつう":
        _move_oni_one_step()
        check_oni_trap_interaction()
    elif difficulty == "むずかしい":
        _move_oni_one_step()
        check_oni_trap_interaction()
        if st.session_state.oni_stopped_turns > 0: return
        if st.session_state.player_pos == st.session_state.oni_pos: return
        _move_oni_one_step()
        check_oni_trap_interaction()

def check_events():
    """ゲーム内のイベント（捕獲、鍵取得、脱出）を確認する"""
    if st.session_state.player_pos == st.session_state.oni_pos:
        st.session_state.game_over = True
        st.session_state.message = "鬼に捕まってしまった...。"
        if not st.session_state.end_time:
            st.session_state.end_time = time.time()
        return

    if st.session_state.key_pos and st.session_state.player_pos == st.session_state.key_pos:
        st.session_state.has_key = True
        st.session_state.key_pos = None
        st.session_state.message = "鍵を手に入れた！出口を探そう。"
        return

    if st.session_state.player_pos == st.session_state.exit_pos:
        if st.session_state.has_key:
            st.session_state.win = True
            st.session_state.message = "脱出に成功した！おめでとう！"
            if not st.session_state.win_counted:
                st.session_state.clear_count += 1
                st.session_state.win_counted = True
            if not st.session_state.end_time:
                st.session_state.end_time = time.time()
        else:
            st.session_state.message = "鍵がかかっている...。鍵を探さなければ。"

def restart_game():
    """ゲームをリセットするが、クリア回数と難易度は維持する"""
    clear_count = st.session_state.get('clear_count', 0)
    difficulty = st.session_state.get('difficulty', 'ふつう')
    st.session_state.clear()
    st.session_state.clear_count = clear_count
    st.session_state.difficulty = difficulty
    st.rerun()


# --- メインのUI ---
st.set_page_config(page_title="Streamlit 青鬼")
initialize_game()

# --- サイドバー (設定と情報) ---
with st.sidebar:
    st.title("設定と情報")

    # --- 時間表示 ---
    if 'start_time' in st.session_state:
        if st.session_state.end_time:
            elapsed_time = st.session_state.end_time - st.session_state.start_time
        else:
            elapsed_time = time.time() - st.session_state.start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        st.write(f"**経過時間: {minutes:02d}:{seconds:02d}**")
    st.write("---")

    st.selectbox("難易度", ("やさしい", "ふつう", "むずかしい"), key='difficulty', disabled=(st.session_state.turn_count > 0))
    st.write(f"**クリア回数: {st.session_state.clear_count}**")
    st.write(f"鍵の所持: {'あり' if st.session_state.has_key else 'なし'}")
    if st.session_state.difficulty == "むずかしい":
        st.write(f"**罠の数: {st.session_state.trap_count}**")
    st.write("---")
    
    # --- 一括移動 ---
    st.write("**一括移動** (l:左, r:右, u:上, d:下)")
    command_input = st.text_input("コマンド:", key="command_input", label_visibility="collapsed")
    if st.button("一括移動を実行"):
        handle_bulk_move(command_input)
        st.rerun()
    st.write("---")

    with st.expander("ゲームのルール (Q&A)", expanded=False):
        st.markdown("""
        **Q. このゲームの目的は？** A. 鬼（👹）に捕まらずに、鍵（🔑）を見つけて出口（🚪）から脱出することです。
        **Q. どうやって操作するの？** A. メイン画面下部の矢印ボタンか、サイドバーの一括移動を使います。
        **Q. 難易度の違いは？** A. 鬼の動く速さが変わります。
        - **やさしい**: プレイヤーが2回動くと鬼が1回動きます。
        - **ふつう**: プレイヤーが1回動くと鬼も1回動きます。
        - **むずかしい**: プレイヤーが1回動くと鬼は2回動きます。
        """)

    with st.expander("障害物（🌲）について", expanded=False):
        st.markdown("**Q. 障害物（🌲）って何？** A. ゲームを1回クリアするごとに増える壁です。プレイヤーも鬼も通り抜けることはできません。")

    with st.expander("罠（🪤）について", expanded=False):
        st.markdown("""
        **Q. 罠って何？** A. 「むずかしい」モードでのみ使えるアイテムです。
        **Q. どうやって使うの？** A. 「罠を設置」ボタンを押すと、現在のプレイヤー（🏃）の位置に罠を設置します。罠は1ゲームに1つだけ使えます。
        **Q. どんな効果があるの？** A. 鬼（👹）が罠を踏むと、3ターンの間動けなくなります。
        """)

# --- メイン画面 ---
st.markdown("<style>h1{font-size: 1.8rem;}</style>", unsafe_allow_html=True)
st.title("青鬼風ゲーム_by_mk")
st.caption("鬼から逃げながら鍵を見つけ、屋敷から脱出せよ！")

if st.session_state.game_over: st.error(st.session_state.message)
elif st.session_state.win: st.success(st.session_state.message)
else: st.info(st.session_state.message)

display_map()

# --- 操作ボタン ---
st.write("---")
st.write("**操作**")
is_control_disabled = st.session_state.game_over or st.session_state.win

# 移動ボタンと罠ボタンを横一列に
cols = st.columns(5)
with cols[0]:
    if st.button("◀", use_container_width=True, disabled=is_control_disabled):
        move_player(-1, 0); st.rerun()
with cols[1]:
    if st.button("▲", use_container_width=True, disabled=is_control_disabled):
        move_player(0, -1); st.rerun()
with cols[2]:
    if st.button("▼", use_container_width=True, disabled=is_control_disabled):
        move_player(0, 1); st.rerun()
with cols[3]:
    if st.button("▶", use_container_width=True, disabled=is_control_disabled):
        move_player(1, 0); st.rerun()
with cols[4]:
    if st.session_state.difficulty == "むずかしい":
        trap_button_disabled = (st.session_state.trap_count <= 0 or st.session_state.trap_pos is not None or is_control_disabled)
        if st.button("🪤", use_container_width=True, disabled=trap_button_disabled, help="罠を設置"):
            st.session_state.trap_pos = list(st.session_state.player_pos)
            st.session_state.trap_count -= 1
            st.session_state.message = "床に罠を設置した。"
            st.rerun()

# リスタートボタンを操作キーの下に配置
st.write("") # ボタンの上のスペース
if st.button("リスタート", use_container_width=True):
    restart_game()
