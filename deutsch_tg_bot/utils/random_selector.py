import random
from typing import Iterable


class BalancedRandomSelector[T]:
    def __init__(
        self,
        items: Iterable[T],
        initial_weights: Iterable[float] | None = None,
        decay_factor: float = 0.7,
    ) -> None:
        self._items = list(items)
        self._decay_factor = decay_factor

        if initial_weights is None:
            weights = [1.0] * len(self._items)
        else:
            weights = list(initial_weights)

        # Normalize weights to probabilities (sum = 1)
        total = sum(weights)
        self._initial_probabilities = [w / total for w in weights]
        self._current_probabilities = self._initial_probabilities.copy()

    def select(self) -> T:
        # Select an item
        selected_item = random.choices(self._items, weights=self._current_probabilities, k=1)[0]

        # Find index of selected item
        selected_index = self._items.index(selected_item)

        # Store old probability of selected item
        old_prob = self._current_probabilities[selected_index]

        # Decrease probability of selected item
        new_prob = old_prob * self._decay_factor

        # Difference to redistribute among other items
        prob_diff = old_prob - new_prob

        # Redistribute difference proportionally to initial probabilities of other items
        other_initial_sum = sum(
            self._initial_probabilities[i] for i in range(len(self._items)) if i != selected_index
        )

        # Update probabilities
        for i in range(len(self._items)):
            if i == selected_index:
                self._current_probabilities[i] = new_prob
            else:
                # Add portion proportionally to initial probability
                if other_initial_sum > 0:
                    proportion = self._initial_probabilities[i] / other_initial_sum
                    self._current_probabilities[i] += prob_diff * proportion

        current_sum = sum(self._current_probabilities)
        # ic(current_sum)

        return selected_item
