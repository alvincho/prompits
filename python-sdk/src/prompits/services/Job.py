# Job is a document that describes a job
# Job is not a Pit, but a document that can be used by Pits
# Job has a owner, who is the agent that created the job
# Job may have a Pathway, which describes the pathway of the job
# Job may have a price, or for auction to compete by agents

class Job():
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.pathway = None
        self.price = None
        self.owner = None