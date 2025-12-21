import random
from typing import Iterable


class BalancedRandomSelector[T]:
    def __init__(
        self,
        items: Iterable[T],
        weights: Iterable[float] | None = None,
        decay_factor: float = 0.25,
    ) -> None:
        self._items = list(items)
        self._decay_factor = decay_factor

        if weights is None:
            weights = [1.0] * len(self._items)
        else:
            weights = list(weights)

        # Normalize weights to probabilities (sum = 1)
        total = sum(weights)
        self._initial_probabilities = [w / total for w in weights]
        self._current_probabilities = self._initial_probabilities.copy()

    def select(self) -> T:
        selected_item = random.choices(self._items, weights=self._current_probabilities, k=1)[0]
        selected_index = self._items.index(selected_item)
        old_prob = self._current_probabilities[selected_index]
        new_prob = old_prob * self._decay_factor
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

        return selected_item
