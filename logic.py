import random

class Card:
    def __init__(self, suit, rank):
        self.suit = suit  # Масть: ♠, ♥, ♦, ♣
        self.rank = rank  # Достоинство: A, 2-10, J, Q, K
        self.face_up = False  # Перевернута ли карта
        self.color = 'red' if suit in ['♥', '♦'] else 'black'
    
    def __repr__(self):
        return f"{self.rank}{self.suit}"

class Game_Solitaire:
    def __init__(self):
        self.deck = []
        self.waste = []
        self.foundations = [[], [], [], []]
        self.tableau = [[] for _ in range(7)]
        
        self.init_game()
    
    def init_game(self):
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        self.deck = [Card(suit, rank) for suit in suits for rank in ranks]

        random.shuffle(self.deck)

        for i in range(7):
            for j in range(i + 1):
                card = self.deck.pop()
                if j == i:
                    card.face_up = True
                self.tableau[i].append(card)

        for card in self.deck:
            card.face_up = False
    
    def can_move_to_foundation(self, card, foundation):
        if not foundation:
            return card.rank == 'A'

        top_card = foundation[-1]

        if card.suit != top_card.suit:

            return False

        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        current_index = ranks.index(top_card.rank)
        next_index = ranks.index(card.rank)
        
        return next_index == current_index + 1
    
    def game_stopka(self, card, target_card):
        if not target_card.face_up:
            return False

        if card.color == target_card.color:
            return False

        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        target_index = ranks.index(target_card.rank)
        card_index = ranks.index(card.rank)
        
        return card_index == target_index - 1
    
    def sequence(self, cards, target_card):
        if not cards:
            return False

        return self.game_stopka(cards[0], target_card)

