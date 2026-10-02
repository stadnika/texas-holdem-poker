import random
from dataclasses import dataclass
from itertools import combinations

import pygame

pygame.init()

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Texas Hold'em Poker")
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("arial", 24)
BIG_FONT = pygame.font.SysFont("arial", 36, bold=True)
TITLE_FONT = pygame.font.SysFont("arial", 52, bold=True)

GREEN = (21, 112, 60)
DARK_GREEN = (12, 80, 40)
TABLE_GREEN = (18, 92, 52)
CARD_BACK = (25, 44, 95)
RED = (184, 56, 56)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
YELLOW = (255, 224, 102)
GRAY = (210, 210, 210)
BLUE = (68, 122, 209)


class Button:
    def __init__(self, text, x, y, w, h, color, hover_color, action=None):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.hovered = False

    def draw(self, surface):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=18)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=18)
        label = FONT.render(self.text, True, WHITE)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self.action
        return None


class Card:
    suit_symbols = {
        "hearts": "♥",
        "diamonds": "♦",
        "clubs": "♣",
        "spades": "♠",
    }
    suit_colors = {
        "hearts": RED,
        "diamonds": RED,
        "clubs": BLACK,
        "spades": BLACK,
    }
    rank_text = {
        2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
        10: "10", 11: "J", 12: "Q", 13: "K", 14: "A"
    }

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"{self.rank_text[self.rank]}{self.suit_symbols[self.suit]}"

    def draw(self, surface, x, y, face_up=True):
        width, height = 90, 130
        rect = pygame.Rect(x, y, width, height)
        if face_up:
            pygame.draw.rect(surface, WHITE, rect, border_radius=12)
            pygame.draw.rect(surface, BLACK, rect, 2, border_radius=12)
            color = self.suit_colors[self.suit]
            label = BIG_FONT.render(self.rank_text[self.rank], True, color)
            label2 = BIG_FONT.render(self.suit_symbols[self.suit], True, color)
            small = FONT.render(self.rank_text[self.rank], True, color)
            small2 = FONT.render(self.suit_symbols[self.suit], True, color)
            surface.blit(label, (x + 10, y + 8))
            surface.blit(small2, (x + 10, y + 38))
            surface.blit(label2, (x + 28, y + 55))
            surface.blit(small, (x + 60, y + 92))
            surface.blit(small2, (x + 60, y + 118))
        else:
            pygame.draw.rect(surface, CARD_BACK, rect, border_radius=12)
            pygame.draw.rect(surface, WHITE, rect, 2, border_radius=12)
            for i in range(0, 3):
                for j in range(0, 5):
                    if (i + j) % 2 == 0:
                        pygame.draw.circle(surface, WHITE, (x + 22 + j * 15, y + 18 + i * 32), 6)


class Player:
    def __init__(self, name, is_bot=False):
        self.name = name
        self.is_bot = is_bot
        self.chips = 1000
        self.hand = []
        self.folded = False
        self.bet = 0

    def reset(self):
        self.hand = []
        self.folded = False
        self.bet = 0


class Deck:
    def __init__(self):
        self.cards = []
        self.reset()

    def reset(self):
        self.cards = []
        for suit in ["hearts", "diamonds", "clubs", "spades"]:
            for rank in range(2, 15):
                self.cards.append(Card(suit, rank))
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()


class HandEvaluator:
    @staticmethod
    def evaluate(cards):
        if len(cards) < 5:
            return 0, []
        best_score = -1
        best_combo = []
        for combo in combinations(cards, 5):
            score, values = HandEvaluator._score_combo(combo)
            if score > best_score:
                best_score = score
                best_combo = values
        return best_score, best_combo

    @staticmethod
    def _score_combo(combo):
        ranks = sorted([card.rank for card in combo], reverse=True)
        counts = {}
        for rank in ranks:
            counts[rank] = counts.get(rank, 0) + 1
        values = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
        is_flush = len({card.suit for card in combo}) == 1

        unique_ranks = sorted(set(ranks), reverse=True)
        straight_high = HandEvaluator._straight_high(ranks)
        is_straight = straight_high is not None

        if is_straight and is_flush:
            if straight_high == 14:
                return 9_000_000, [14]
            return 8_000_000 + straight_high, [straight_high]

        if values[0][1] == 4:
            quad = values[0][0]
            kicker = max(rank for rank in ranks if rank != quad)
            return 7_000_000 + quad * 10 + kicker, [quad, kicker]

        if values[0][1] == 3 and values[1][1] == 2:
            full = values[0][0]
            pair = values[1][0]
            return 6_000_000 + full * 100 + pair, [full, pair]

        if is_flush:
            return 5_000_000 + sum(ranks[:5]), ranks[:5]

        if is_straight:
            return 4_000_000 + straight_high, [straight_high]

        if values[0][1] == 3:
            trip = values[0][0]
            kickers = sorted([rank for rank in ranks if rank != trip], reverse=True)
            return 3_000_000 + trip * 100 + kickers[0], [trip] + kickers[:2]

        if values[0][1] == 2 and values[1][1] == 2:
            pair_ranks = sorted([v[0] for v in values[:2]], reverse=True)
            kicker = max(rank for rank in ranks if rank not in pair_ranks)
            return 2_000_000 + sum(pair_ranks) * 10 + kicker, pair_ranks + [kicker]

        if values[0][1] == 2:
            pair = values[0][0]
            kickers = sorted([rank for rank in ranks if rank != pair], reverse=True)
            return 1_000_000 + pair * 100 + kickers[0] * 10 + kickers[1], [pair] + kickers[:3]

        return sum(ranks[:5]), ranks[:5]

    @staticmethod
    def _straight_high(ranks):
        unique = sorted(set(ranks), reverse=True)
        if len(unique) < 5:
            return None
        for i in range(len(unique) - 4):
            window = sorted(unique[i:i + 5], reverse=True)
            if window == [14, 5, 4, 3, 2]:
                return 5
            if window == list(range(window[0], window[0] - 5, -1)):
                return window[0]
        return None


class PokerGame:
    def __init__(self, difficulty):
        self.player = Player("Player")
        self.bot = Player("Bot", is_bot=True)
        self.deck = Deck()
        self.community = []
        self.pot = 0
        self.current_bet = 0
        self.stage = 0
        self.difficulty = difficulty
        self.message = "Виберіть складність і натисніть Play"
        self.game_over = False
        self.result = ""
        self.reveal_bot = False
        self.stage_names = ["Pre-Flop", "Flop", "Turn", "River"]

    def start_round(self):
        self.player.reset()
        self.bot.reset()
        self.community = []
        self.pot = 0
        self.current_bet = 0
        self.stage = 0
        self.game_over = False
        self.result = ""
        self.reveal_bot = False
        self.message = "Роздача карт..."

        self.deck.reset()
        self.player.chips -= 10
        self.bot.chips -= 20
        self.pot = 30
        self.current_bet = 20
        self.player.bet = 10
        self.bot.bet = 20

        for _ in range(2):
            self.player.hand.append(self.deck.draw())
            self.bot.hand.append(self.deck.draw())

    def evaluate_best_hand(self, player):
        cards = player.hand + self.community
        score, combo = HandEvaluator.evaluate(cards)
        return score, combo

    def bot_decision(self):
        if self.bot.folded:
            return "fold"

        strength = self.estimate_bot_strength()
        if self.difficulty == "easy":
            if strength < 0.3 and random.random() < 0.7:
                return "fold"
            if self.current_bet <= self.bot.bet:
                if strength > 0.8 and random.random() < 0.4:
                    return "raise"
                return "check"
            if strength < 0.5 and random.random() < 0.5:
                return "fold"
            return "call"

        if self.difficulty == "medium":
            if strength < 0.45 and random.random() < 0.45:
                return "fold"
            if self.current_bet > self.bot.bet and strength < 0.5:
                return "fold"
            if self.current_bet <= self.bot.bet:
                if strength > 0.8 and random.random() < 0.5:
                    return "raise"
                return "check"
            return "call"

        if self.difficulty == "hard":
            if strength < 0.35 and random.random() < 0.3:
                return "fold"
            if self.current_bet > self.bot.bet and strength < 0.45:
                return "fold"
            if self.current_bet <= self.bot.bet:
                if strength > 0.75 and random.random() < 0.65:
                    return "raise"
                return "check"
            return "call"

        return "check"

    def estimate_bot_strength(self):
        if not self.community:
            ranks = [card.rank for card in self.bot.hand]
            score = sum(ranks) / len(ranks)
            return min(1.0, score / 14)
        BotScore, _ = HandEvaluator.evaluate(self.bot.hand + self.community)
        return min(1.0, BotScore / 9_000_000)

    def action_fold(self, side):
        if side == "player":
            self.player.folded = True
            self.message = "Ви скинули карти."
        else:
            self.bot.folded = True
            self.message = "Бот скинув карти."
        self.finish_round()

    def action_check(self, side):
        if side == "player":
            self.message = "Ви чекнули."
        else:
            self.message = "Бот чекнув."

    def action_call(self, side):
        if side == "player":
            call_value = self.current_bet - self.player.bet
            if call_value <= self.player.chips:
                self.player.chips -= call_value
                self.player.bet = self.current_bet
                self.pot += call_value
                self.message = f"Ви колл: {call_value}."
        else:
            call_value = self.current_bet - self.bot.bet
            if call_value <= self.bot.chips:
                self.bot.chips -= call_value
                self.bot.bet = self.current_bet
                self.pot += call_value
                self.message = f"Бот колл: {call_value}."

    def action_raise(self, side):
        raise_value = 50
        if side == "player":
            if raise_value <= self.player.chips:
                self.player.chips -= raise_value
                self.current_bet += raise_value
                self.player.bet += raise_value
                self.pot += raise_value
                self.message = f"Ви підняли на {raise_value}."
        else:
            if raise_value <= self.bot.chips:
                self.bot.chips -= raise_value
                self.current_bet += raise_value
                self.bot.bet += raise_value
                self.pot += raise_value
                self.message = f"Бот підняв на {raise_value}."

    def finish_round(self):
        award = self.pot
        if self.player.folded and not self.bot.folded:
            self.bot.chips += award
            self.result = "bot"
        elif self.bot.folded and not self.player.folded:
            self.player.chips += award
            self.result = "player"
        else:
            player_score, _ = HandEvaluator.evaluate(self.player.hand + self.community)
            bot_score, _ = HandEvaluator.evaluate(self.bot.hand + self.community)
            if player_score > bot_score:
                self.player.chips += award
                self.result = "player"
            elif bot_score > player_score:
                self.bot.chips += award
                self.result = "bot"
            else:
                split = award // 2
                self.player.chips += split
                self.bot.chips += split
                self.result = "tie"
        self.game_over = True
        self.reveal_bot = True
        if self.result == "player":
            self.message = "Ви виграли раунд!"
        elif self.result == "bot":
            self.message = "Бот виграв раунд!"
        else:
            self.message = "Нічия!"

    def advance_to_next_stage(self):
        if self.stage == 0:
            for _ in range(3):
                self.community.append(self.deck.draw())
            self.message = "Флоп! Додано 3 карти."
        elif self.stage == 1:
            self.community.append(self.deck.draw())
            self.message = "Терн!"
        elif self.stage == 2:
            self.community.append(self.deck.draw())
            self.message = "Рівер!"
        self.stage += 1
        self.current_bet = 0
        self.player.bet = 0
        self.bot.bet = 0

    def resolve_turn(self):
        if self.player.folded or self.bot.folded:
            self.finish_round()
            return

        if self.stage < 3:
            self.advance_to_next_stage()
            return

        self.finish_round()

    def handle_player_action(self, action):
        if self.game_over:
            return
        if action == "fold":
            self.action_fold("player")
            return
        if action == "check":
            if self.current_bet <= self.player.bet:
                self.action_check("player")
                self.handle_bot_turn()
            else:
                self.message = "Спочатку треба колл або фолд."
            return
        if action == "call":
            self.action_call("player")
            self.handle_bot_turn()
            return
        if action == "raise":
            self.action_raise("player")
            self.handle_bot_turn()
            return

    def handle_bot_turn(self):
        if self.game_over:
            return
        decision = self.bot_decision()
        if decision == "fold":
            self.action_fold("bot")
            return
        if decision == "check":
            self.action_check("bot")
            self.resolve_turn()
            return
        if decision == "call":
            self.action_call("bot")
            self.resolve_turn()
            return
        if decision == "raise":
            self.action_raise("bot")
            self.resolve_turn()
            return

    def draw_table(self, surface):
        surface.fill(TABLE_GREEN)
        pygame.draw.rect(surface, GREEN, (0, 0, WIDTH, HEIGHT), 0)

        header = BIG_FONT.render("Texas Hold'em Poker", True, WHITE)
        surface.blit(header, (WIDTH // 2 - header.get_width() // 2, 20))

        # Pot and chips
        info_box = pygame.Rect(30, 70, 260, 110)
        pygame.draw.rect(surface, DARK_GREEN, info_box, border_radius=16)
        label1 = FONT.render(f"Bank: {self.pot}", True, WHITE)
        label2 = FONT.render(f"You: {self.player.chips}", True, WHITE)
        label3 = FONT.render(f"Bot: {self.bot.chips}", True, WHITE)
        surface.blit(label1, (info_box.x + 18, info_box.y + 18))
        surface.blit(label2, (info_box.x + 18, info_box.y + 52))
        surface.blit(label3, (info_box.x + 18, info_box.y + 82))

        stage_box = pygame.Rect(WIDTH - 290, 70, 260, 110)
        pygame.draw.rect(surface, DARK_GREEN, stage_box, border_radius=16)
        stage_name = self.stage_names[min(self.stage, 3)] if self.stage < 4 else "Finished"
        stage_label = FONT.render(f"Stage: {stage_name}", True, WHITE)
        diff_label = FONT.render(f"Difficulty: {self.difficulty.title()}", True, WHITE)
        surface.blit(stage_label, (stage_box.x + 18, stage_box.y + 18))
        surface.blit(diff_label, (stage_box.x + 18, stage_box.y + 52))

        center_y = 250
        community_x = 280
        for idx, card in enumerate(self.community):
            card.draw(surface, community_x + idx * 110, center_y, True)

        # Bot hand
        for idx, card in enumerate(self.bot.hand):
            x = 200 + idx * 100
            card.draw(surface, x, 120, self.reveal_bot or self.game_over)

        # Player hand
        for idx, card in enumerate(self.player.hand):
            x = 200 + idx * 100
            card.draw(surface, x, 560, True)

        # Message box
        msg_box = pygame.Rect(260, 720, 680, 60)
        pygame.draw.rect(surface, DARK_GREEN, msg_box, border_radius=16)
        msg = FONT.render(self.message, True, WHITE)
        surface.blit(msg, (msg_box.x + 18, msg_box.y + 18))

        # Player buttons
        action_buttons = [
            Button("Fold", 30, 640, 150, 60, RED, (170, 60, 60), "fold"),
            Button("Check", 200, 640, 150, 60, BLUE, (80, 110, 200), "check"),
            Button("Call", 370, 640, 150, 60, YELLOW, (200, 180, 70), "call"),
            Button("Raise", 540, 640, 150, 60, (93, 126, 83), (140, 170, 120), "raise"),
        ]
        for button in action_buttons:
            button.draw(surface)

        # Show exact action buttons for player only while game is active
        if self.game_over:
            restart_btn = Button("New Round", 1020, 640, 150, 60, BLUE, (80, 110, 200), "new_round")
            restart_btn.draw(surface)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.game_over:
                        if pygame.Rect(1020, 640, 150, 60).collidepoint(event.pos):
                            self.start_round()
                    else:
                        action_map = {
                            "fold": self.handle_player_action,
                            "check": self.handle_player_action,
                            "call": self.handle_player_action,
                            "raise": self.handle_player_action,
                        }
                        for action_name, funct in action_map.items():
                            if action_name == "fold":
                                rect = pygame.Rect(30, 640, 150, 60)
                            elif action_name == "check":
                                rect = pygame.Rect(200, 640, 150, 60)
                            elif action_name == "call":
                                rect = pygame.Rect(370, 640, 150, 60)
                            else:
                                rect = pygame.Rect(540, 640, 150, 60)
                            if rect.collidepoint(event.pos):
                                funct(action_name)
            self.draw_table(screen)
            pygame.display.flip()
            CLOCK.tick(30)
        pygame.quit()


def main():
    game = PokerGame("medium")
    game.start_round()
    game.run()


if __name__ == "__main__":
    main()


# End of file
