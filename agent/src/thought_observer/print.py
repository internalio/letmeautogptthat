from .thought_observer import ThoughtObserver


class PrintObserver(ThoughtObserver):
    def __call__(self, thought: str, raw_data: str):
        super().__call__(thought)

        print(thought)
