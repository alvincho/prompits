# Job is a document that describes a job
# Job is not a Pit, but a document that can be used by Pits
# Job has a owner, who is the agent that created the job
# Job may have a Pathway, which describes the pathway of the job
# Job may have a price, or for auction to compete by agents

class Job:
    """
    !!! This is a work in progress !!!
    
    Represents a task or work unit that can be executed by agents.
    
    A Job encapsulates metadata about a task including its name, description,
    execution pathway, pricing information, and ownership. Jobs can be posted
    in job markets, assigned to agents, and tracked through their lifecycle.
    """
    
    def __init__(self, name, description):
        """
        Initialize a Job instance.
        
        Args:
            name: The name or identifier of the job
            description: A description of what the job entails
        """
        self.name = name
        self.description = description
        self.pathway = None
        self.price = None
        self.owner = None