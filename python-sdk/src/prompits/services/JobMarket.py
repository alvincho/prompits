# JobMarket is a service that allows agents to post jobs and search for jobs
# JobMarket has an owner, who is the agent that created the job market
# JobMarket has a table of jobs, which is created in the database of the owner
# JobMarket has a table of applications, which is created in the database of the owner
# JobMarket has a table of finishes, which is created in the database of the owner

from typing import Dict, List, Any, Optional
import uuid
import json
from datetime import datetime
from prompits.Practice import Practice
from .Service import Service

class Job:
    def __init__(self, name: str, description: str, owner_id: str, price: float = 0.0, practices: List[str] = None):
        self.job_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.owner_id = owner_id
        self.price = price
        self.practices = practices or []
        self.created_at = datetime.now()
        self.status = "open"  # open, assigned, completed, cancelled
        
    def to_dict(self):
        return {
            "job_id": self.job_id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "price": self.price,
            "practices": self.practices,
            "created_at": self.created_at.isoformat(),
            "status": self.status
        }
        
    @classmethod
    def from_dict(cls, data):
        job = cls(
            name=data.get("name"),
            description=data.get("description"),
            owner_id=data.get("owner_id"),
            price=data.get("price", 0.0),
            practices=data.get("practices", [])
        )
        job.job_id = data.get("job_id", str(uuid.uuid4()))
        job.created_at = datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.now()
        job.status = data.get("status", "open")
        return job

class JobResult:
    def __init__(self, job_id: str, agent_id: str, result: str, rating: int = 0):
        self.result_id = str(uuid.uuid4())
        self.job_id = job_id
        self.agent_id = agent_id
        self.result = result
        self.rating = rating
        self.created_at = datetime.now()
        
    def to_dict(self):
        return {
            "result_id": self.result_id,
            "job_id": self.job_id,
            "agent_id": self.agent_id,
            "result": self.result,
            "rating": self.rating,
            "created_at": self.created_at.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data):
        result = cls(
            job_id=data.get("job_id"),
            agent_id=data.get("agent_id"),
            result=data.get("result"),
            rating=data.get("rating", 0)
        )
        result.result_id = data.get("result_id", str(uuid.uuid4()))
        result.created_at = datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.now()
        return result

class JobMarket(Service):
    def __init__(self, name: str, description: str = None, pool_name: str = None):
        super().__init__(name, description or f"Job Market {name}")
        self.pool_name = pool_name
        self.pool = None
        self.jobs_table = f"{name}_jobs"
        self.applications_table = f"{name}_applications"
        self.results_table = f"{name}_results"
        
        # Add practices
        self.AddPractice(Practice("PostJob", self.PostJob))
        self.AddPractice(Practice("SearchJobs", self.SearchJobs))
        self.AddPractice(Practice("ApplyJob", self.ApplyJob))
        self.AddPractice(Practice("FinishJob", self.FinishJob))
        self.AddPractice(Practice("GetJob", self.GetJob))
        self.AddPractice(Practice("GetJobs", self.GetJobs))
        self.AddPractice(Practice("CancelJob", self.CancelJob))
        self.AddPractice(Practice("RateResult", self.RateResult))
        
    def initialize(self):
        """Initialize the job market by creating necessary tables"""
        if not self.pool:
            raise ValueError("Pool not set for JobMarket")
            
        # Create jobs table if it doesn't exist
        if not self.pool.TableExists(self.jobs_table):
            self.pool.CreateTable(
                self.jobs_table,
                {
                    "job_id": "TEXT PRIMARY KEY",
                    "name": "TEXT NOT NULL",
                    "description": "TEXT",
                    "owner_id": "TEXT NOT NULL",
                    "price": "FLOAT",
                    "practices": "TEXT",  # JSON array
                    "created_at": "TIMESTAMP",
                    "status": "TEXT"
                }
            )
            
        # Create applications table if it doesn't exist
        if not self.pool.TableExists(self.applications_table):
            self.pool.CreateTable(
                self.applications_table,
                {
                    "application_id": "TEXT PRIMARY KEY",
                    "job_id": "TEXT NOT NULL",
                    "agent_id": "TEXT NOT NULL",
                    "created_at": "TIMESTAMP",
                    "status": "TEXT"  # pending, accepted, rejected
                }
            )
            
        # Create results table if it doesn't exist
        if not self.pool.TableExists(self.results_table):
            self.pool.CreateTable(
                self.results_table,
                {
                    "result_id": "TEXT PRIMARY KEY",
                    "job_id": "TEXT NOT NULL",
                    "agent_id": "TEXT NOT NULL",
                    "result": "TEXT",
                    "rating": "INTEGER",
                    "created_at": "TIMESTAMP"
                }
            )
    
    def set_pool(self, pool):
        """Set the database pool for the job market"""
        self.pool = pool
        self.initialize()
        
    def PostJob(self, name: str, description: str, owner_id: str, price: float = 0.0, practices: List[str] = None):
        """Post a new job to the market"""
        if not self.pool:
            raise ValueError("Pool not set for JobMarket")
            
        job = Job(name, description, owner_id, price, practices)
        
        # Insert job into database
        self.pool.Insert(
            self.jobs_table,
            job.to_dict()
        )
        
        return job.job_id
        
    def SearchJobs(self, query: Dict[str, Any] = None, status: str = "open"):
        """Search for jobs in the market"""
        if not self.pool:
            raise ValueError("Pool not set for JobMarket")
            
        # Build search query
        search_query = query or {}
        if status:
            search_query["status"] = status
            
        # Search for jobs
        jobs_data = self.pool.Search(self.jobs_table, search_query)
        
        # Convert to Job objects
        jobs = []
        for job_data in jobs_data:
            # Convert practices from JSON string to list
            if "practices" in job_data and isinstance(job_data["practices"], str):
                job_data["practices"] = json.loads(job_data["practices"])
            jobs.append(Job.from_dict(job_data))
            
        return jobs
        
    def ApplyJob(self, job_id: str, agent_id: str):
        """Apply for a job"""
        if not self.pool:
            raise ValueError("Pool not set for JobMarket")
            
        # Check if job exists and is open
        job_data = self.pool.Get(self.jobs_table, {"job_id": job_id})
        if not job_data:
            raise ValueError(f"Job {job_id} not found")
        if job_data.get("status") != "open":
            raise ValueError(f"Job {job_id} is not open for applications")
            
        # Check if agent has already applied
        existing_application = self.pool.Search(
            self.applications_table,
            {"job_id": job_id, "agent_id": agent_id}
        )
        if existing_application:
            raise ValueError(f"Agent {agent_id} has already applied for job {job_id}")
            
        # Create application
        application_id = str(uuid.uuid4())
        self.pool.Insert(
            self.applications_table,
            {
                "application_id": application_id,
                "job_id": job_id,
                "agent_id": agent_id,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
        )
        
        return application_id
        
    def FinishJob(self, job_id: str, agent_id: str, result: str):
        """Finish a job and submit results"""
        if not self.pool:
            raise ValueError("Pool not set for JobMarket")
            
        # Check if job exists and is assigned to the agent
        job_data = self.pool.Get(self.jobs_table, {"job_id": job_id})
        if not job_data:
            raise ValueError(f"Job {job_id} not found")
            
        # Check if agent has an accepted application for this job
        application = self.pool.Search(
            self.applications_table,
            {"job_id": job_id, "agent_id": agent_id, "status": "accepted"}
        )
        if not application:
            raise ValueError(f"Agent {agent_id} is not assigned to job {job_id}")
            
        # Create job result
        job_result = JobResult(job_id, agent_id, result)
        
        # Insert result into database
        self.pool.Insert(
            self.results_table,
            job_result.to_dict()
        )
        
        # Update job status to completed
        self.pool.Update(
            self.jobs_table,
            {"job_id": job_id},
            {"status": "completed"}
        )
        
        return job_result.result_id
        
    def GetJob(self, job_id: str):
        """Get a job by ID"""
        if not self.pool:
            raise ValueError("Pool not set for JobMarket")
            
        job_data = self.pool.Get(self.jobs_table, {"job_id": job_id})
        if not job_data:
            return None
            
        # Convert practices from JSON string to list
        if "practices" in job_data and isinstance(job_data["practices"], str):
            job_data["practices"] = json.loads(job_data["practices"])
            
        return Job.from_dict(job_data)
        
    def GetJobs(self, agent_id: str = None, practices: List[str] = None, status: str = None):
        """Get jobs filtered by agent ID, practices, or status"""
        if not self.pool:
            raise ValueError("Pool not set for JobMarket")
            
        # Build search query
        search_query = {}
        if agent_id:
            search_query["owner_id"] = agent_id
        if status:
            search_query["status"] = status
            
        # Search for jobs
        jobs_data = self.pool.Search(self.jobs_table, search_query)
        
        # Convert to Job objects and filter by practices if needed
        jobs = []
        for job_data in jobs_data:
            # Convert practices from JSON string to list
            if "practices" in job_data and isinstance(job_data["practices"], str):
                job_data["practices"] = json.loads(job_data["practices"])
                
            job = Job.from_dict(job_data)
            
            # Filter by practices if specified
            if practices:
                if not job.practices:
                    continue
                if not any(practice in job.practices for practice in practices):
                    continue
                    
            jobs.append(job)
            
        return jobs
        
    def CancelJob(self, job_id: str, agent_id: str):
        """Cancel a job (only the owner can cancel)"""
        if not self.pool:
            raise ValueError("Pool not set for JobMarket")
            
        # Check if job exists and is owned by the agent
        job_data = self.pool.Get(self.jobs_table, {"job_id": job_id})
        if not job_data:
            raise ValueError(f"Job {job_id} not found")
        if job_data.get("owner_id") != agent_id:
            raise ValueError(f"Agent {agent_id} is not the owner of job {job_id}")
            
        # Update job status to cancelled
        self.pool.Update(
            self.jobs_table,
            {"job_id": job_id},
            {"status": "cancelled"}
        )
        
        return True
        
    def RateResult(self, result_id: str, rating: int, agent_id: str):
        """Rate a job result (only the job owner can rate)"""
        if not self.pool:
            raise ValueError("Pool not set for JobMarket")
            
        # Check if result exists
        result_data = self.pool.Get(self.results_table, {"result_id": result_id})
        if not result_data:
            raise ValueError(f"Result {result_id} not found")
            
        # Get the job to check ownership
        job_data = self.pool.Get(self.jobs_table, {"job_id": result_data.get("job_id")})
        if not job_data:
            raise ValueError(f"Job for result {result_id} not found")
        if job_data.get("owner_id") != agent_id:
            raise ValueError(f"Agent {agent_id} is not the owner of the job")
            
        # Update rating
        self.pool.Update(
            self.results_table,
            {"result_id": result_id},
            {"rating": rating}
        )
        
        return True
        
    def ToJson(self):
        """Convert to JSON for serialization"""
        json_data = super().ToJson()
        json_data.update({
            "pool_name": self.pool_name,
            "jobs_table": self.jobs_table,
            "applications_table": self.applications_table,
            "results_table": self.results_table
        })
        return json_data
        
    def FromJson(self, json_data):
        """Initialize from JSON data"""
        super().FromJson(json_data)
        self.pool_name = json_data.get("pool_name")
        self.jobs_table = json_data.get("jobs_table", f"{self.name}_jobs")
        self.applications_table = json_data.get("applications_table", f"{self.name}_applications")
        self.results_table = json_data.get("results_table", f"{self.name}_results")
        return self