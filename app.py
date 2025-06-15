import streamlit as st
import numpy as np
import random

# --- ゲームの設定 ---
MAP_WIDTH = 15
MAP_HEIGHT = 10
WALL = "🧱"
FLOOR = "⬛"
PLAYER = "🏃"
ONI = "👹"
KEY = "🔑"
EXIT_LOCKED = "🚪"
EXIT_UNLOCKED = "🟩"
OBSTACLE = "🌲" # 新しい障害物
INITIAL_PLAYER_POS = [1, 1]
INITIAL_ONI_POS = [MAP_WIDTH - 2, MAP_HEIGHT - 2]
KEY_POS = [7, 5]
EXIT_POS = [MAP_WIDTH - 1, 1]


def generate_map(clear_count):
    """壁と床で基本的なマップを生成し、クリア回数に応じて障害物を追加する"""
    game_map = np.full((MAP_HEIGHT, MAP_WIDTH), FLOOR, dtype=str)
    game_map[0, :] = WALL
    game_map[-1, :] = WALL
    game_map[:, 0] = WALL
    game_map[:, -1] = WALL

    # 内部の壁を追加
    game_map[3, 3:8] = WALL
    game_map[3:7, 7] = WALL
    game_map[6, 3:8] = WALL
    game_map[3:7, 3] = WALL
    
    # --- 障害物の配置 ---
    possible_obstacle_positions = []
    for y in range(1, MAP_HEIGHT - 1):
        for x in range(1, MAP_WIDTH - 1):
            if game_map[y][x] == FLOOR and [x, y] not in [INITIAL_PLAYER_POS, INITIAL_ONI_POS, KEY_POS, EXIT_POS]:
                possible_obstacle_positions.append([x, y])
    
    num_obstacles = min(clear_count, 15)
    
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


def display_map():
    """現在のゲームマップを表示する"""
    display_map_data = [row[:] for row in st.session_state.game_map]
    
    px, py = st.session_state.player_pos
    ox, oy = st.session_state.oni_pos
    
    if st.session_state.key_pos:
        kx, ky = st.session_state.key_pos
        display_map_data[ky][kx] = KEY

    ex, ey = st.session_state.exit_pos

    display_map_data[py][px] = PLAYER
    display_map_data[oy][ox] = ONI
        
    exit_icon = EXIT_UNLOCKED if st.session_state.has_key else EXIT_LOCKED
    display_map_data[ey][ex] = exit_icon
    
    # HTMLの<pre>タグを使って等幅フォントで表示。CSSでスタイルを調整
    map_str = "\n".join(["".join(row) for row in display_map_data])
    st.markdown(f"<pre class='game-map'>{map_str}</pre>", unsafe_allow_html=True)


def move_player(dx, dy):
    """プレイヤーを移動させ、ゲームのターンを進行させる"""
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

def _move_oni_one_step():
    """鬼をプレイヤーに向かって1マス動かす内部ロジック"""
    px, py = st.session_state.player_pos
    ox, oy = st.session_state.oni_pos

    new_ox, new_oy = ox, oy
    dist_x = px - ox
    dist_y = py - oy
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


def move_oni():
    """難易度に応じて鬼を動かす"""
    difficulty = st.session_state.difficulty
    
    if difficulty == "やさしい":
        if st.session_state.turn_count % 2 == 0: _move_oni_one_step()
    elif difficulty == "ふつう":
        _move_oni_one_step()
    elif difficulty == "むずかしい":
        _move_oni_one_step()
        if st.session_state.player_pos != st.session_state.oni_pos: _move_oni_one_step()


def check_events():
    """ゲーム内のイベント（捕獲、鍵取得、脱出）を確認する"""
    if st.session_state.player_pos == st.session_state.oni_pos:
        st.session_state.game_over = True
        st.session_state.message = "鬼に捕まってしまった...。"
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
st.set_page_config(page_title="Streamlit 青鬼", layout="wide")
initialize_game()

# --- サイドバー (設定と情報) ---
with st.sidebar:
    st.title("設定と情報")

    st.selectbox(
        "難易度",
        ("やさしい", "ふつう", "むずかしい"),
        key='difficulty',
        disabled=(st.session_state.turn_count > 0)
    )
    st.write(f"**クリア回数: {st.session_state.clear_count}**")
    st.write(f"鍵の所持: {'あり' if st.session_state.has_key else 'なし'}")
    st.write("---")
    
    if st.button("リスタート", use_container_width=True):
        restart_game()
        
    with st.expander("ゲームのルール (Q&A)", expanded=True):
        st.markdown("""
        **Q. このゲームの目的は？** A. 鬼（👹）に捕まらずに、鍵（🔑）を見つけて出口（🚪）から脱出することです。

        **Q. どうやって操作するの？** A. メイン画面下部の矢印ボタン（◀ ▲ ▼ ▶）をクリックして移動します。

        **Q. 難易度の違いは？** A. 鬼の動く速さが変わります。
        - **やさしい**: プレイヤーが2回動くと鬼が1回動きます。
        - **ふつう**: プレイヤーが1回動くと鬼も1回動きます。
        - **むずかしい**: プレイヤーが1回動くと鬼は2回動きます。
        """)

    with st.expander("障害物（🌲）について", expanded=False):
        st.markdown("""
        **Q. 障害物（🌲）って何？** A. ゲームを1回クリアするごとに増える壁です。プレイヤーも鬼も通り抜けることはできません。
        """)

# --- メイン画面 ---
st.title("Streamlit 青鬼風ゲーム")
st.caption("鬼から逃げながら鍵を見つけ、屋敷から脱出せよ！")

# ゲームマップの表示スタイルをCSSで定義（スマホ対応）
st.markdown("""
<style>
.game-map {
    font-family: monospace;
    font-size: clamp(12px, 4.5vw, 22px); /* 画面幅に応じて文字サイズを調整 */
    line-height: 1.0;                  /* 行間を詰めてグリッド感を出す */
    white-space: pre;                  /* 文字の自動折り返しを防ぐ */
    overflow-x: auto;                  /* マップがはみ出た時だけ横スクロールを許可 */
    text-align: left;                  /* 左揃えで表示崩れを防ぐ */
    margin: 0 auto;                    /* ブロック全体を中央に配置 */
    max-width: 100%;                   /* 親要素の幅を超えないようにする */
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)


# ゲーム状況のメッセージ
if st.session_state.game_over:
    st.error(st.session_state.message)
elif st.session_state.win:
    st.success(st.session_state.message)
else:
    st.info(st.session_state.message)

# ゲームマップ
display_map()

# 移動ボタン
st.write("---")
st.write("**移動**")
is_control_disabled = st.session_state.game_over or st.session_state.win
b_col1, b_col2, b_col3, b_col4 = st.columns(4)

with b_col1:
    if st.button("◀", use_container_width=True, disabled=is_control_disabled):
        move_player(-1, 0)
        st.rerun()
with b_col2:
    if st.button("▲", use_container_width=True, disabled=is_control_disabled):
        move_player(0, -1)
        st.rerun()
with b_col3:
    if st.button("▼", use_container_width=True, disabled=is_control_disabled):
        move_player(0, 1)
        st.rerun()
with b_col4:
    if st.button("▶", use_container_width=True, disabled=is_control_disabled):
        move_player(1, 0)
        st.rerun()
