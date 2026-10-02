#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
from enum import Enum
from typing import List, Tuple
from itertools import combinations

class Suit(Enum):
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'
    SPADES = '♠'

class Rank(Enum):
    ACE = (14, 'A')
    KING = (13, 'K')
    QUEEN = (12, 'Q')
    JACK = (11, 'J')
    TEN = (10, '10')
    NINE = (9, '9')
    EIGHT = (8, '8')
    SEVEN = (7, '7')
    SIX = (6, '6')
    FIVE = (5, '5')
    FOUR = (4, '4')
    THREE = (3, '3')
    TWO = (2, '2')

class Card:
    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank
    
    def __str__(self):
        return f"{self.rank.value[1]}{self.suit.value}"
    
    def __repr__(self):
        return str(self)

class HandRank(Enum):
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9

class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3

class Deck:
    def __init__(self):
        self.cards = []
        self.reset()
    
    def reset(self):
        self.cards = [Card(suit, rank) for suit in Suit for rank in Rank]
        random.shuffle(self.cards)
    
    def draw(self) -> Card:
        return self.cards.pop()

class Player:
    def __init__(self, name: str, is_bot: bool = False, difficulty: Difficulty = Difficulty.MEDIUM):
        self.name = name
        self.is_bot = is_bot
        self.difficulty = difficulty
        self.hand: List[Card] = []
        self.chips = 1000
        self.current_bet = 0
        self.folded = False
    
    def reset_hand(self):
        self.hand = []
        self.current_bet = 0
        self.folded = False
    
    def add_card(self, card: Card):
        self.hand.append(card)
    
    def show_hand(self):
        return ' '.join(str(card) for card in self.hand)

class PokerGame:
    def __init__(self, difficulty: Difficulty = Difficulty.MEDIUM):
        self.difficulty = difficulty
        self.player = Player("Ви", is_bot=False)
        self.bot = Player("Бот", is_bot=True, difficulty=difficulty)
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.round_num = 0
    
    def deal_hole_cards(self):
        for _ in range(2):
            self.player.add_card(self.deck.draw())
            self.bot.add_card(self.deck.draw())
    
    def deal_flop(self):
        for _ in range(3):
            self.community_cards.append(self.deck.draw())
    
    def deal_turn(self):
        self.community_cards.append(self.deck.draw())
    
    def deal_river(self):
        self.community_cards.append(self.deck.draw())
    
    def evaluate_hand(self, hole_cards: List[Card], community_cards: List[Card]) -> Tuple[HandRank, List[int]]:
        all_cards = hole_cards + community_cards
        best_hand = None
        best_rank = None
        
        for combo in combinations(all_cards, 5):
            hand_rank, kickers = self._evaluate_5_cards(list(combo))
            if best_rank is None or (hand_rank.value, kickers) > (best_rank.value, best_hand):
                best_rank = hand_rank
                best_hand = kickers
        
        return best_rank, best_hand
    
    def _evaluate_5_cards(self, cards: List[Card]) -> Tuple[HandRank, List[int]]:
        ranks = sorted([card.rank.value[0] for card in cards], reverse=True)
        suits = [card.suit for card in cards]
        
        is_flush = len(set(suits)) == 1
        is_straight = self._is_straight(ranks)
        
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        counts = sorted(rank_counts.values(), reverse=True)
        unique_ranks = sorted(rank_counts.keys(), key=lambda x: (rank_counts[x], x), reverse=True)
        
        if is_straight and is_flush:
            if ranks == [14, 13, 12, 11, 10]:
                return HandRank.ROYAL_FLUSH, ranks
            return HandRank.STRAIGHT_FLUSH, ranks
        
        if counts == [4, 1]:
            return HandRank.FOUR_OF_A_KIND, unique_ranks
        
        if counts == [3, 2]:
            return HandRank.FULL_HOUSE, unique_ranks
        
        if is_flush:
            return HandRank.FLUSH, ranks
        
        if is_straight:
            return HandRank.STRAIGHT, ranks
        
        if counts == [3, 1, 1]:
            return HandRank.THREE_OF_A_KIND, unique_ranks
        
        if counts == [2, 2, 1]:
            pair_ranks = [r for r in unique_ranks if rank_counts[r] == 2]
            kicker = [r for r in unique_ranks if rank_counts[r] == 1]
            return HandRank.TWO_PAIR, pair_ranks + kicker
        
        if counts == [2, 1, 1, 1]:
            return HandRank.ONE_PAIR, unique_ranks
        
        return HandRank.HIGH_CARD, ranks
    
    def _is_straight(self, ranks: List[int]) -> bool:
        if ranks == list(range(ranks[0], ranks[0]-5, -1)):
            return True
        if ranks == [14, 5, 4, 3, 2]:
            return True
        return False
    
    def determine_winner(self) -> str:
        if self.bot.folded:
            return "player"
        if self.player.folded:
            return "bot"
        
        player_rank, player_kickers = self.evaluate_hand(self.player.hand, self.community_cards)
        bot_rank, bot_kickers = self.evaluate_hand(self.bot.hand, self.community_cards)
        
        if player_rank.value > bot_rank.value:
            return "player"
        elif bot_rank.value > player_rank.value:
            return "bot"
        else:
            if player_kickers > bot_kickers:
                return "player"
            elif bot_kickers > player_kickers:
                return "bot"
            else:
                return "tie"
    
    def display_table(self, show_bot_hand: bool = False):
        print("\n" + "="*50)
        print(f"Спільні карти: {' '.join(str(card) for card in self.community_cards) if self.community_cards else 'Немає'}")
        print("="*50)
        print(f"Ваша рука: {self.player.show_hand()}")
        if show_bot_hand:
            print(f"Рука бота: {self.bot.show_hand()}")
        else:
            print(f"Рука бота: [X] [X]")
        print("="*50)
        print(f"Банк: {self.pot}")
        print(f"Ваші чіпи: {self.player.chips} | Чіпи бота: {self.bot.chips}")
        print(f"Поточна ставка: {self.current_bet}")
        print("="*50 + "\n")
    
    def player_action(self) -> str:
        while True:
            print("Ваші дії:")
            print("1. fold (скинути)")
            print("2. check (пропустити)" if self.current_bet == self.player.current_bet else "2. call (коллувати)")
            print("3. raise (підвищити) - введіть суму")
            
            action = input("\nВведіть дію (fold/check/call/raise): ").strip().lower()
            
            if action == "fold":
                self.player.folded = True
                return "fold"
            elif action == "check":
                if self.current_bet == self.player.current_bet:
                    return "check"
                else:
                    print("Ви не можете пропустити. Коллуйте або скиньте.")
            elif action == "call":
                call_amount = self.current_bet - self.player.current_bet
                if call_amount > self.player.chips:
                    print(f"Недостатньо чіпів. У вас є: {self.player.chips}")
                else:
                    self.player.chips -= call_amount
                    self.player.current_bet = self.current_bet
                    self.pot += call_amount
                    return "call"
            elif action == "raise":
                try:
                    raise_amount = int(input("Введіть суму підвищення: "))
                    total_bet = self.player.current_bet + raise_amount
                    if total_bet <= self.current_bet:
                        print("Підвищення має бути більшим за поточну ставку.")
                    elif raise_amount > self.player.chips:
                        print(f"Недостатньо чіпів. У вас є: {self.player.chips}")
                    else:
                        self.player.chips -= raise_amount
                        self.pot += raise_amount
                        self.player.current_bet = total_bet
                        self.current_bet = total_bet
                        return "raise"
                except ValueError:
                    print("Введіть коректне число.")
            else:
                print("Невідома дія. Спробуйте ще раз.")
    
    def bot_action(self) -> str:
        if self.bot.folded or self.bot.chips <= 0:
            return "skip"
        
        hand_strength = self._evaluate_hand_strength()
        call_amount = self.current_bet - self.bot.current_bet
        
        if self.difficulty == Difficulty.EASY:
            return self._bot_action_easy(hand_strength, call_amount)
        elif self.difficulty == Difficulty.MEDIUM:
            return self._bot_action_medium(hand_strength, call_amount)
        else:
            return self._bot_action_hard(hand_strength, call_amount)
    
    def _evaluate_hand_strength(self) -> float:
        if len(self.community_cards) == 0:
            ranks = [card.rank.value[0] for card in self.bot.hand]
            if all(r >= 10 for r in ranks):
                return 0.8
            if len(set(rank % 13 for rank in ranks)) == 1:
                return 0.7
            return 0.5
        
        bot_rank, _ = self.evaluate_hand(self.bot.hand, self.community_cards)
        return min(0.95, bot_rank.value / 10)
    
    def _bot_action_easy(self, hand_strength: float, call_amount: int) -> str:
        if hand_strength < 0.4 or random.random() < 0.6:
            self.bot.folded = True
            return "fold"
        
        if hand_strength < 0.6 or call_amount > self.bot.chips * 0.1:
            if call_amount > 0 and call_amount <= self.bot.chips:
                self.bot.chips -= call_amount
                self.bot.current_bet = self.current_bet
                self.pot += call_amount
                return "call"
            return "check"
        
        if call_amount == 0:
            return "check"
        
        if call_amount > 0 and call_amount <= self.bot.chips:
            self.bot.chips -= call_amount
            self.bot.current_bet = self.current_bet
            self.pot += call_amount
            return "call"
        
        return "check"
    
    def _bot_action_medium(self, hand_strength: float, call_amount: int) -> str:
        if hand_strength < 0.5:
            if random.random() < 0.7:
                self.bot.folded = True
                return "fold"
        
        if call_amount > self.bot.chips * 0.3:
            if hand_strength < 0.6:
                self.bot.folded = True
                return "fold"
        
        if call_amount == 0:
            if hand_strength > 0.7 and random.random() < 0.5:
                raise_amount = int(self.pot * 0.5)
                if raise_amount <= self.bot.chips:
                    self.bot.chips -= raise_amount
                    self.bot.current_bet += raise_amount
                    self.current_bet = self.bot.current_bet
                    self.pot += raise_amount
                    return "raise"
            return "check"
        
        if call_amount > 0 and call_amount <= self.bot.chips:
            self.bot.chips -= call_amount
            self.bot.current_bet = self.current_bet
            self.pot += call_amount
            return "call"
        
        return "check"
    
    def _bot_action_hard(self, hand_strength: float, call_amount: int) -> str:
        if call_amount > self.bot.chips * 0.5 and hand_strength < 0.7:
            self.bot.folded = True
            return "fold"
        
        if hand_strength < 0.4 and random.random() < 0.3:
            self.bot.folded = True
            return "fold"
        
        if call_amount == 0:
            if hand_strength > 0.8 and random.random() < 0.7:
                raise_amount = int(self.pot * random.uniform(0.5, 1.5))
                if raise_amount <= self.bot.chips:
                    self.bot.chips -= raise_amount
                    self.bot.current_bet += raise_amount
                    self.current_bet = self.bot.current_bet
                    self.pot += raise_amount
                    return "raise"
            elif hand_strength > 0.6:
                return "check"
            else:
                if random.random() < 0.3:
                    return "check"
                return "check"
            return "check"
        
        if hand_strength > 0.6:
            if call_amount > 0 and call_amount <= self.bot.chips:
                self.bot.chips -= call_amount
                self.bot.current_bet = self.current_bet
                self.pot += call_amount
                return "call"
        
        if call_amount > 0 and call_amount <= self.bot.chips:
            self.bot.chips -= call_amount
            self.bot.current_bet = self.current_bet
            self.pot += call_amount
            return "call"
        
        return "check"
    
    def play_round(self):
        self.round_num += 1
        print(f"\n\n{'='*50}")
        print(f"РАУНД {self.round_num}")
        print(f"{'='*50}\n")
        
        self.player.reset_hand()
        self.bot.reset_hand()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        
        if self.player.chips <= 0 or self.bot.chips <= 0:
            return False
        
        # Ante
        small_blind = 10
        big_blind = 20
        self.pot = small_blind + big_blind
        self.player.chips -= small_blind
        self.bot.chips -= big_blind
        self.current_bet = big_blind
        
        # Deal hole cards
        self.deck.reset()
        self.deal_hole_cards()
        
        print("Pre-Flop")
        self.display_table()
        self.player_action()
        
        if not self.player.folded:
            self.bot_action()
        
        if self.player.folded or self.bot.folded:
            winner = self.determine_winner()
            self._show_result(winner)
            return True
        
        # Flop
        self.deal_flop()
        self.current_bet = 0
        self.player.current_bet = 0
        self.bot.current_bet = 0
        
        print("\n\nFlop")
        self.display_table()
        self.player_action()
        
        if not self.player.folded:
            self.bot_action()
        
        if self.player.folded or self.bot.folded:
            winner = self.determine_winner()
            self._show_result(winner)
            return True
        
        # Turn
        self.deal_turn()
        self.current_bet = 0
        self.player.current_bet = 0
        self.bot.current_bet = 0
        
        print("\n\nTurn")
        self.display_table()
        self.player_action()
        
        if not self.player.folded:
            self.bot_action()
        
        if self.player.folded or self.bot.folded:
            winner = self.determine_winner()
            self._show_result(winner)
            return True
        
        # River
        self.deal_river()
        self.current_bet = 0
        self.player.current_bet = 0
        self.bot.current_bet = 0
        
        print("\n\nRiver")
        self.display_table()
        self.player_action()
        
        if not self.player.folded:
            self.bot_action()
        
        winner = self.determine_winner()
        self._show_result(winner, show_hands=True)
        return True
    
    def _show_result(self, winner: str, show_hands: bool = False):
        print("\n" + "="*50)
        if show_hands:
            self.display_table(show_bot_hand=True)
        
        if winner == "player":
            self.player.chips += self.pot
            print(f"🎉 ВИ ПЕРЕМОГЛИ! Отримали {self.pot} чіпів.")
        elif winner == "bot":
            self.bot.chips += self.pot
            print(f"❌ БОТ ПЕРЕМІГ! Він отримав {self.pot} чіпів.")
        else:
            draw_pot = self.pot // 2
            self.player.chips += draw_pot
            self.bot.chips += draw_pot
            print(f"🤝 НІЧИЯ! Кожен отримав {draw_pot} чіпів.")
        
        print("="*50)
    
    def play_game(self):
        print("\n" + "="*50)
        print("TEXAS HOLD'EM POKER")
        print("="*50)
        print(f"Складність: {self.difficulty.name}")
        print("="*50 + "\n")
        
        while self.player.chips > 0 and self.bot.chips > 0:
            if not self.play_round():
                break
            
            print(f"\nВаші чіпи: {self.player.chips} | Чіпи бота: {self.bot.chips}")
            
            if input("\nПродовжити? (y/n): ").lower() != 'y':
                break
        
        print("\n" + "="*50)
        print("ГРА ЗАКІНЧЕНА")
        print("="*50)
        if self.player.chips > self.bot.chips:
            print(f"🏆 ВИ ПЕРЕМІГ! Фінальний рахунок: {self.player.chips} vs {self.bot.chips}")
        elif self.bot.chips > self.player.chips:
            print(f"💀 БОТ ПЕРЕМІГ! Фінальний рахунок: {self.player.chips} vs {self.bot.chips}")
        else:
            print(f"🤝 НІЧИЯ!")
        print("="*50 + "\n")

def select_difficulty() -> Difficulty:
    while True:
        print("\nВиберіть рівень складності:")
        print("1. Easy (Легка) - Бот часто фолдить")
        print("2. Medium (Середня) - Бот грає розумно")
        print("3. Hard (Складна) - Бот грає агресивно")
        
        choice = input("\nВведіть номер (1-3): ").strip()
        
        if choice == "1":
            return Difficulty.EASY
        elif choice == "2":
            return Difficulty.MEDIUM
        elif choice == "3":
            return Difficulty.HARD
        else:
            print("Невідний вибір. Спробуйте ще раз.")

if __name__ == "__main__":
    difficulty = select_difficulty()
    game = PokerGame(difficulty)
    game.play_game()
