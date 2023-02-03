import dataclasses
import random
import typing as t
from enum import Enum

import emoji


class Suit(Enum):
    HEART = 4
    DIAMOND = 3
    CLUB = 2
    SPADE = 1

    @staticmethod
    def suits() -> list[str]:
        return ["heart", "diamond", "club", "spade"]

class PlayerChoice(Enum):
    START = "start"
    END = "end"
    DRAW = "draw"
    STAND = "stand"
class GameResult(Enum):
    PLAYER_WIN = "player win"
    DEALER_WIN = "dealer win"
    TIE = "tie"

@dataclasses.dataclass(slots = True)
class Card:
    _rank: int
    _suit: Suit
    _is_revealed: bool = False
    
    @property
    def rank(self) -> int:
        return self._rank
    @property
    def suit(self) -> Suit:
        return self._suit
    @property
    def is_revealed(self) -> bool:
        return self._is_revealed
    @property
    def real_rank(self) -> str:
        if self._rank == 11:
            return 'J'
        elif self._rank == 12:
            return 'Q'
        elif self._rank == 13:
            return 'K'
        elif self._rank == 1:
            return 'A'
        elif self._rank > 1 and self._rank <= 10:
            return str(self._rank)
        
        return "JOKER"
    @staticmethod
    def get_52_cards(*, shuffle: bool = False) -> list[t.Self]:
        deck: list[Card] = []
        for suit in Suit:
            for i in range(1, 14):
                deck.append(Card(i, suit))
        if shuffle:
            random.shuffle(deck)
        
        return deck
    
    def reveal(self):
        self._is_revealed = True
    def hide(self):
        self._is_revealed = False

    def __repr__(self) -> str:
        return f"{self.real_rank} {self._suit} ({self._is_revealed})"
    
    def __str__(self) -> str:
        suit: str = ""
        if self._suit == Suit.HEART:
            suit = emoji.emojize(":hearts:", language = "alias")
        elif self._suit == Suit.DIAMOND:
            suit = emoji.emojize(":diamonds:", language = "alias")
        elif self._suit == Suit.CLUB:
            suit = "<:card_club:1064040317071929415>"
        else:
            suit = "<:card_spade:1064040319110348881>"
        
        if self._is_revealed:
            return f"{self.real_rank} {suit}"
        return "<HIDDEN>"

class UserSessionRunning(Exception):
    '''Raised when trying to start more than one session per user.'''

class InvalidBlackjackState(Exception):
    '''Raised when a state can't be advanced.'''

@dataclasses.dataclass(slots = True)
class _BlackjackState:
    player_hand: list[Card] = dataclasses.field(default_factory = list)
    dealer_hand: list[Card] = dataclasses.field(default_factory = list)

    player_choice: PlayerChoice | None = None

class BlackjackSession:
    def __init__(self) -> None:
        self._deck: list[Card] = Card.get_52_cards(shuffle = True)
        self._player_id: int | None = None
        self._result: GameResult | None = None
    
    @property
    def result(self):
        return self._result

    def start(self, user_id: int, *, force_reset: bool = False) -> _BlackjackState:
        '''Start a blackjack session for a user.
        This must be called before listening for inputs.

        Parameters
        ----------
        user_id : int
            The user's id.
        force_reset : bool, optional
            Whether to reset the user's session if it's running, default to `False`.
        
        Raises
        ------
        UserSessionRunning
            This user already has a session running. Pass `force_reset` if you want to reset.
        '''
        if not self._player_id or force_reset:
            self._player_id = user_id
            state = _BlackjackState()
            state.player_hand.extend(self._draw(2))
            state.player_hand[0].reveal()
            state.player_hand[1].reveal()
            state.dealer_hand.extend(self._draw(2))
            state.dealer_hand[1].reveal()
            state.player_choice = PlayerChoice.START

            # The winner can be determined right away.
            self._result = self._return_result(state)
            return state
        else:
            raise UserSessionRunning(f"User {user_id} session already started.")
    
    def _check_hand(self, hand: list[Card]) -> int:
        '''Return an integer indicate whether a hand reach a special state or not.

        Parameters
        ----------
        hand : list[Card]
            The hand to check.

        Returns
        -------
        int
            -1 if the hand is busted, 1 if the hand is a blackjack, and 0 otherwise.
        '''
        sum_revealed_rank = sum_hand(hand, filter = lambda c: c._is_revealed)
        if sum_revealed_rank > 21:
            return -1
        if sum_revealed_rank == 21:
            return 1
        
        # Check for natural.
        # Since natural only happens at the start of the game, the dealer hand can be not revealed.
        # An ace and a 10 or picture will be a natural.
        sum_rank = sum_hand(hand)
        if len(hand) == 2 and sum_rank == 11 and (hand[0].real_rank == 'A' or hand[1].real_rank == 'A'):
            return 1
        
        return 0
    
    def _draw(self, amount: int = 1) -> t.Generator[Card, None, None]:
        '''Draw card or cards.

        Yields
        ------
        Card
            The card drawn from the deck.
        
        Raises
        ------
        IndexError
            The deck is empty.
        '''
        for _ in range(amount):
            yield self._deck.pop()
    
    def _return_result(self, state: _BlackjackState) -> GameResult | None:
        '''Return the result based on the state.

        Parameters
        ----------
        state : _BlackjackState
            The state of the game.

        Returns
        -------
        GameResult | None
            The result of the game, or `None` if it is inconclusive/ongoing.
        '''
        player_hand_state = self._check_hand(state.player_hand)
        dealer_hand_state = self._check_hand(state.dealer_hand)

        # As of now, player and dealer can't both bust.
        if player_hand_state != dealer_hand_state:
            if player_hand_state == -1 or dealer_hand_state == 1:
                return GameResult.DEALER_WIN
            if dealer_hand_state == -1 or player_hand_state == 1:
                return GameResult.PLAYER_WIN
        if player_hand_state == dealer_hand_state and player_hand_state != 0:
            if player_hand_state == -1 or player_hand_state == 1:
                return GameResult.TIE
        
        return None

    def is_started(self) -> bool:
        return bool(self._player_id)
    def is_ongoing(self) -> bool:
        '''Return whether the game is ongoing (result is inconclusive).
        This should be used as the main game loop.

        Returns
        -------
        bool
            Whether the game is ongoing.
        '''
        return bool(self._player_id) and self._result is None
    
    def next(self, state: _BlackjackState) -> _BlackjackState:
        '''Advance a state and return it.

        Parameters
        ----------
        state : _BlackjackState
            The state to advance.

        Returns
        -------
        _BlackjackState
            The state after advancing.
        '''
        # Simplified version of https://bicyclecards.com/how-to-play/blackjack/
        if state.player_choice == PlayerChoice.START or state.player_choice is None:
            raise InvalidBlackjackState
        if state.player_choice == PlayerChoice.DRAW:
            state.player_hand.extend(self._draw())
            state.player_hand[-1].reveal()
            # Simple implementation first.
            sum_player_rank = sum_hand(state.player_hand)
            if sum_player_rank > 21:
                self._result = GameResult.DEALER_WIN
            elif sum_player_rank == 21:
                self._result = GameResult.PLAYER_WIN
            else:
                state.player_choice = None
                return
        elif state.player_choice == PlayerChoice.STAND:
            sum_dealer_rank = sum_hand(state.dealer_hand)
            while sum_dealer_rank < 17:
                state.dealer_hand.extend(self._draw())
                state.dealer_hand[-1].reveal()
                sum_dealer_rank = sum_hand(state.dealer_hand)
            
            for i in range(len(state.dealer_hand)):
                state.dealer_hand[i].reveal()
            
            sum_player_rank = sum_hand(state.player_hand)
            if sum_dealer_rank > 21 or sum_player_rank > sum_dealer_rank:
                self._result = GameResult.PLAYER_WIN
            elif sum_dealer_rank == 21 or sum_player_rank < sum_dealer_rank:
                self._result = GameResult.DEALER_WIN
            else:
                self._result = GameResult.TIE
        else:
            # Not sure what to do with START and END yet.
            pass
        
        return state
    
    def end(self):
        pass

def sum_hand(hand: list[Card], *, filter: t.Callable[[Card], bool] = lambda _: True):
    '''Return the total of a hand.

    This also account for soft hand.

    Parameters
    ----------
    hand : list[Card]
        The hand to compute.

    Returns
    -------
    int
        The total of the hand. If there's an Ace and the count exceed 21, the Ace will count as a 1 instead of 11.
    '''
    
    total: int = 0
    soft: bool = False
    for card in hand:
        if filter(card):
            if card.real_rank in ['J', 'Q', 'K']:
                total += 10
            elif card.rank == 1:
                total += 11
                soft = True
            else:
                total += card.rank
    
    if total > 21 and soft:
        total -= 10
    
    return total
