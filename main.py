import json
from pathlib import Path

import pygame

WINDOW_WIDTH = 520
WINDOW_HEIGHT = 680
BOARD_SIZE = 480
BOARD_LEFT = (WINDOW_WIDTH - BOARD_SIZE) // 2
BOARD_TOP = 140
CELL_SIZE = BOARD_SIZE // 3
FPS = 60

PLAYER = "X"
BOT = "O"
EMPTY = ""

BG_COLOR = (24, 28, 34)
PANEL_COLOR = (37, 43, 52)
GRID_COLOR = (210, 215, 223)
TEXT_COLOR = (236, 240, 245)
PLAYER_COLOR = (84, 204, 149)
BOT_COLOR = (248, 113, 113)
BUTTON_COLOR = (70, 124, 229)
BUTTON_HOVER_COLOR = (88, 142, 247)
BUTTON_BORDER_COLOR = (20, 32, 54)
OVERLAY_COLOR = (0, 0, 0, 160)

WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def get_stats_path() -> Path:
    return Path(__file__).resolve().with_name("stats.json")


def save_stats(stats_path: Path, stats: dict) -> None:
    stats_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_stats(stats_path: Path) -> dict:
    default_stats = {"losses": 0, "draws": 0}

    if not stats_path.exists():
        save_stats(stats_path, default_stats)
        return default_stats.copy()

    try:
        data = json.loads(stats_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        save_stats(stats_path, default_stats)
        return default_stats.copy()

    losses = data.get("losses", 0)
    draws = data.get("draws", 0)

    if not isinstance(losses, int) or losses < 0:
        losses = 0
    if not isinstance(draws, int) or draws < 0:
        draws = 0

    fixed_stats = {"losses": losses, "draws": draws}
    save_stats(stats_path, fixed_stats)
    return fixed_stats


def check_winner(board: list[str]) -> str | None:
    for a, b, c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]

    if all(cell for cell in board):
        return "draw"
    return None


def minimax(board: list[str], depth: int, maximizing: bool) -> int:
    result = check_winner(board)
    if result is not None:
        if result == BOT:
            return 10 - depth
        if result == PLAYER:
            return depth - 10
        return 0

    if maximizing:
        best_score = -100
        for i, cell in enumerate(board):
            if cell == EMPTY:
                board[i] = BOT
                score = minimax(board, depth + 1, False)
                board[i] = EMPTY
                best_score = max(best_score, score)
        return best_score

    best_score = 100
    for i, cell in enumerate(board):
        if cell == EMPTY:
            board[i] = PLAYER
            score = minimax(board, depth + 1, True)
            board[i] = EMPTY
            best_score = min(best_score, score)
    return best_score


def find_best_move(board: list[str]) -> int | None:
    best_score = -100
    best_moves: list[int] = []

    for i, cell in enumerate(board):
        if cell == EMPTY:
            board[i] = BOT
            score = minimax(board, 0, False)
            board[i] = EMPTY
            if score > best_score:
                best_score = score
                best_moves = [i]
            elif score == best_score:
                best_moves.append(i)

    if not best_moves:
        return None

    # При одинаковой оценке предпочитаем центр и углы.
    priority = [4, 0, 2, 6, 8, 1, 3, 5, 7]
    for index in priority:
        if index in best_moves:
            return index
    return best_moves[0]


def draw_button(
    screen: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    font: pygame.font.Font,
    hovered: bool,
) -> None:
    color = BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, BUTTON_BORDER_COLOR, rect, width=2, border_radius=12)
    label = font.render(text, True, TEXT_COLOR)
    screen.blit(label, label.get_rect(center=rect.center))


def draw_board(screen: pygame.Surface, board: list[str]) -> None:
    board_rect = pygame.Rect(BOARD_LEFT, BOARD_TOP, BOARD_SIZE, BOARD_SIZE)
    pygame.draw.rect(screen, PANEL_COLOR, board_rect, border_radius=12)
    pygame.draw.rect(screen, GRID_COLOR, board_rect, width=3, border_radius=12)

    for i in range(1, 3):
        x = BOARD_LEFT + i * CELL_SIZE
        y = BOARD_TOP + i * CELL_SIZE
        pygame.draw.line(
            screen,
            GRID_COLOR,
            (x, BOARD_TOP + 8),
            (x, BOARD_TOP + BOARD_SIZE - 8),
            width=3,
        )
        pygame.draw.line(
            screen,
            GRID_COLOR,
            (BOARD_LEFT + 8, y),
            (BOARD_LEFT + BOARD_SIZE - 8, y),
            width=3,
        )

    for index, mark in enumerate(board):
        if mark == EMPTY:
            continue

        row = index // 3
        col = index % 3
        cx = BOARD_LEFT + col * CELL_SIZE + CELL_SIZE // 2
        cy = BOARD_TOP + row * CELL_SIZE + CELL_SIZE // 2

        if mark == PLAYER:
            margin = 34
            left = cx - CELL_SIZE // 2 + margin
            right = cx + CELL_SIZE // 2 - margin
            top = cy - CELL_SIZE // 2 + margin
            bottom = cy + CELL_SIZE // 2 - margin
            pygame.draw.line(screen, PLAYER_COLOR, (left, top), (right, bottom), width=8)
            pygame.draw.line(screen, PLAYER_COLOR, (right, top), (left, bottom), width=8)
        else:
            radius = CELL_SIZE // 2 - 34
            pygame.draw.circle(screen, BOT_COLOR, (cx, cy), radius, width=8)


def cell_from_pos(pos: tuple[int, int]) -> int | None:
    x, y = pos
    if not (BOARD_LEFT <= x < BOARD_LEFT + BOARD_SIZE):
        return None
    if not (BOARD_TOP <= y < BOARD_TOP + BOARD_SIZE):
        return None

    col = (x - BOARD_LEFT) // CELL_SIZE
    row = (y - BOARD_TOP) // CELL_SIZE
    return int(row * 3 + col)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Крестики-нолики против бота")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", 52, bold=True)
    text_font = pygame.font.SysFont("arial", 30, bold=True)
    regular_font = pygame.font.SysFont("arial", 24)
    button_font = pygame.font.SysFont("arial", 26, bold=True)

    stats_path = get_stats_path()
    stats = load_stats(stats_path)

    menu_play_btn = pygame.Rect(WINDOW_WIDTH // 2 - 110, 275, 220, 56)
    menu_exit_btn = pygame.Rect(WINDOW_WIDTH // 2 - 110, 350, 220, 56)
    game_menu_btn = pygame.Rect(WINDOW_WIDTH - 145, 24, 120, 42)
    overlay_play_btn = pygame.Rect(WINDOW_WIDTH // 2 - 110, 430, 220, 56)
    overlay_menu_btn = pygame.Rect(WINDOW_WIDTH // 2 - 110, 500, 220, 56)

    state = "menu"
    board = [EMPTY] * 9
    current_turn = PLAYER
    result: str | None = None
    result_saved = False

    def start_new_game() -> None:
        nonlocal board, current_turn, result, result_saved
        board = [EMPTY] * 9
        current_turn = PLAYER
        result = None
        result_saved = False

    def persist_game_result() -> None:
        nonlocal result_saved
        if result_saved or result is None:
            return

        if result == BOT:
            stats["losses"] += 1
            save_stats(stats_path, stats)
        elif result == "draw":
            stats["draws"] += 1
            save_stats(stats_path, stats)
        result_saved = True

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "menu":
                    if menu_play_btn.collidepoint(event.pos):
                        start_new_game()
                        state = "game"
                    elif menu_exit_btn.collidepoint(event.pos):
                        running = False
                else:
                    if result is None:
                        if game_menu_btn.collidepoint(event.pos):
                            state = "menu"
                            continue

                        if current_turn == PLAYER:
                            cell = cell_from_pos(event.pos)
                            if cell is not None and board[cell] == EMPTY:
                                board[cell] = PLAYER
                                result = check_winner(board)
                                if result is None:
                                    current_turn = BOT
                    else:
                        if overlay_play_btn.collidepoint(event.pos):
                            start_new_game()
                        elif overlay_menu_btn.collidepoint(event.pos):
                            state = "menu"

        if state == "game" and result is None and current_turn == BOT:
            best_move = find_best_move(board)
            if best_move is not None:
                board[best_move] = BOT
            result = check_winner(board)
            current_turn = PLAYER

        if state == "game":
            persist_game_result()

        screen.fill(BG_COLOR)

        if state == "menu":
            title_surface = title_font.render("Крестики-нолики", True, TEXT_COLOR)
            subtitle_surface = regular_font.render("Против невыигрываемого бота", True, TEXT_COLOR)
            stats_losses = text_font.render(
                f"Поражения: {stats['losses']}",
                True,
                BOT_COLOR,
            )
            stats_draws = text_font.render(
                f"Ничьи: {stats['draws']}",
                True,
                GRID_COLOR,
            )

            screen.blit(title_surface, title_surface.get_rect(center=(WINDOW_WIDTH // 2, 110)))
            screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, 160)))
            screen.blit(stats_losses, stats_losses.get_rect(center=(WINDOW_WIDTH // 2, 220)))
            screen.blit(stats_draws, stats_draws.get_rect(center=(WINDOW_WIDTH // 2, 250)))

            draw_button(
                screen,
                menu_play_btn,
                "Играть",
                button_font,
                menu_play_btn.collidepoint(mouse_pos),
            )
            draw_button(
                screen,
                menu_exit_btn,
                "Выход",
                button_font,
                menu_exit_btn.collidepoint(mouse_pos),
            )

            hint_surface = regular_font.render("Вы не можете победить.", True, GRID_COLOR)
            screen.blit(hint_surface, hint_surface.get_rect(center=(WINDOW_WIDTH // 2, 460)))
        else:
            draw_board(screen, board)

            info_text = (
                "Ваш ход (X)"
                if result is None and current_turn == PLAYER
                else "Ход бота (O)" if result is None else "Партия завершена"
            )
            info_surface = text_font.render(info_text, True, TEXT_COLOR)
            score_surface = regular_font.render(
                f"Поражения: {stats['losses']}   Ничьи: {stats['draws']}",
                True,
                GRID_COLOR,
            )
            screen.blit(info_surface, (24, 24))
            screen.blit(score_surface, (24, 74))

            draw_button(
                screen,
                game_menu_btn,
                "Меню",
                regular_font,
                game_menu_btn.collidepoint(mouse_pos),
            )

            if result is not None:
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                overlay.fill(OVERLAY_COLOR)
                screen.blit(overlay, (0, 0))

                if result == BOT:
                    result_text = "Бот победил."
                    color = BOT_COLOR
                elif result == "draw":
                    result_text = "Ничья."
                    color = GRID_COLOR
                else:
                    result_text = "Вы победили."
                    color = PLAYER_COLOR

                result_surface = title_font.render(result_text, True, color)
                screen.blit(result_surface, result_surface.get_rect(center=(WINDOW_WIDTH // 2, 340)))

                draw_button(
                    screen,
                    overlay_play_btn,
                    "Сыграть снова",
                    button_font,
                    overlay_play_btn.collidepoint(mouse_pos),
                )
                draw_button(
                    screen,
                    overlay_menu_btn,
                    "В меню",
                    button_font,
                    overlay_menu_btn.collidepoint(mouse_pos),
                )

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
