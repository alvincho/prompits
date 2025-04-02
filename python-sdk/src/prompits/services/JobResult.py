# JobResult is a document that describes the result of a job
# JobResult has a owner, who is the agent that created the job result
# JobResult has a job, which is the job that the result is for
# JobResult has a result, which is the result of the job

from .Job import Job

class JobResult:
    """
    !!! This is a work in progress !!!
    Represents the result of a job execution.
    
    JobResult encapsulates the outcome of a job, including the original job
    that was executed and the result data produced by that job. It also tracks
    the owner (agent) that created or is responsible for the result.
    """
    
    def __init__(self, job: Job, result: str):
        """
        Initialize a JobResult instance.
        
        Args:
            job: The Job instance that this result is for
            result: The result data or output from the job execution
        """
        self.job = job
        self.result = result
        self.owner = None
