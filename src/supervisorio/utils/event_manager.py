class EventManager():
    def __init__(self):
        self.events = {}

    def on(self, event, callback):
        if event in self.events:
            self.events[event].append(callback)
        else:
            self.events[event] = [callback]
        return self

    async def dispatch(self, event, *args, **kwargs):
        if event in self.events:
            for callback in self.events[event]:
                await callback(*args, **kwargs)

    def has(self, event):
        return event in self.events
