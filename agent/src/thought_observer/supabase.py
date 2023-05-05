from .thought_observer import ThoughtObserver


class SupabaseThoughtObserver(ThoughtObserver):
    def __init__(self, client, job_id: str, write_every: int = 3):
        self.job_id = job_id
        self.thoughts = []
        self.raw_data = []
        self.total_thoughts = 0
        self.client = client
        self.write_every = write_every

    def _write(self):
        self.client.table("jobs").update(
            {
                "messages": self.thoughts,
                "log": self.raw_data,
            }
        ).eq("id", self.job_id).execute()

    def __call__(self, thought: str, raw_data: str):
        self.thoughts.append(thought)
        self.raw_data.append(raw_data)
        self.total_thoughts += 1

        # Record on first thought for faster results
        # then record every write_every
        if self.total_thoughts == 1 or (self.total_thoughts % self.write_every == 0):
            self._write()

    def flush(self):
        """Write out any remaining thoughts to Supabase"""
        self._write()
