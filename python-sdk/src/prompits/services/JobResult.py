# JobResult is a document that describes the result of a job
# JobResult has a owner, who is the agent that created the job result
# JobResult has a job, which is the job that the result is for
# JobResult has a result, which is the result of the job

class JobResult():
    def __init__(self, job: Job, result: str):
        self.job = job
        self.result = result
        self.owner = None
