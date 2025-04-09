"""
Pathway module for defining pathways.

A Pathway is a structured workflow that defines a series of Posts organized into groups.
It represents a complex task that can be executed by multiple agents.
"""

import json
import uuid
import datetime
from typing import Dict, List, Any, Optional, Union
import traceback
from .Pit import Pit


class Post:
    """
    Post class representing a single task in a Pathway.
    
    A Post is a discrete task that requires specific practices (skills) to complete.
    Posts can have dependencies on other Posts and can be executed by agents with the required practices.
    """
    
    def __init__(self, 
                 post_id: str,
                 name: str,
                 practice: str,
                 parameters: Optional[Dict[str, Any]] = None,
                 inputs: Optional[Dict[str, Any]] = None,
                 constraints: Optional[Dict[str, Dict[str, str]]] = None,
                 requirements: Optional[Dict[str, List[str]]] = None,
                 outputs: Optional[Dict[str, Dict[str, Any]]] = None,
                 post_group: Optional[str] = None):
        """
        Initialize a Post.
        
        Args:
            post_id: Unique identifier for the Post
            name: Name of the Post
            practice: Required Practice for this Post
            parameters: Parameters for the practice
            inputs: Input data for the Post
            constraints: Constraints with values and strictness
            requirements: Software, environment, and library requirements
            outputs: Output fields and next posts with conditions
            post_group: Group this post belongs to
        """
        self.post_id = post_id
        self.name = name
        self.practice = practice
        self.parameters = parameters or {}
        self.inputs = inputs or {}
        self.constraints = constraints or {}
        self.requirements = requirements or {}
        self.outputs = outputs or {}
        self.post_group = post_group
        # Get next post from outputs
        self.next_post = next(iter(self.outputs.keys())) if self.outputs else "exit"
        
    def ToJson(self) -> Dict[str, Any]:
        """
        Convert the Post to a JSON object.
        
        Returns:
            Dict[str, Any]: JSON representation of the Post
        """
        result = {
            "post_id": self.post_id,
            "name": self.name,
            "practice": self.practice,
            "parameters": self.parameters,
            "inputs": self.inputs,
            "constraints": self.constraints,
            "requirements": self.requirements,
            "outputs": self.outputs,
            "next_post": self.next_post
        }
        
        if self.post_group:
            result["post_group"] = self.post_group
            
        return result
    
    @classmethod
    def FromJson(cls, json_data: Dict[str, Any]) -> 'Post':
        """
        Create a Post from a JSON object.
        
        Args:
            json_data: JSON object containing Post configuration
            
        Returns:
            Post: The initialized Post
        """
        return cls(
            post_id=json_data["post_id"],
            name=json_data["name"],
            practice=json_data["practice"],
            parameters=json_data.get("parameters"),
            inputs=json_data.get("inputs"),
            constraints=json_data.get("constraints"),
            requirements=json_data.get("requirements"),
            outputs=json_data.get("outputs"),
            post_group=json_data.get("post_group")
        )

# Postgroup is a Post container, act as a single Post
# internally it contains multiple Posts with execution path
# Postgroup is inherited from Post, but has additional fields
# input is the input of the first Post in the PostGroup
# output is the output of the last Post in the PostGroup
# statistics are collected for each PostGroup
class PostGroup(Post, Pit):
    """
    PostGroup class representing a group of related Posts in a Pathway.
    
    A PostGroup contains multiple Posts that are related and may be executed in parallel.
    """
    
    def __init__(self,
                 id: str,
                 description: str,
                 parallelizable: bool,
                 threaded_execution: bool,
                 posts: List[Post],
                 max_concurrent_posts: Optional[int] = None,
                 execution_timeout: Optional[int] = None):
        """
        Initialize a PostGroup.
        
        Args:
            id: Unique identifier for the Post Group
            description: Description of the purpose of this group
            parallelizable: Whether Posts in this group can run in parallel
            threaded_execution: Whether this Post Group runs in a separate thread
            posts: List of Posts in this group
            max_concurrent_posts: Maximum number of Posts that can execute concurrently in this group
            execution_timeout: Maximum time (in seconds) before this group is forcefully stopped
        """
        Pit.__init__(self, "PostGroup", description)
        self.log(f"Initializing PostGroup with id: {id}, description: {description}, parallelizable: {parallelizable}, threaded_execution: {threaded_execution}, posts: {posts}, max_concurrent_posts: {max_concurrent_posts}, execution_timeout: {execution_timeout}")
        self.id = id
        self.description = description
        self.parallelizable = parallelizable
        self.threaded_execution = threaded_execution
        self.posts = posts
        self.max_concurrent_posts = max_concurrent_posts
        self.execution_timeout = execution_timeout
        
    def ToJson(self) -> Dict[str, Any]:
        """
        Convert the PostGroup to a JSON object.
        
        Returns:
            dict: JSON representation of the PostGroup
        """
        result = {
            "id": self.id,
            "description": self.description,
            "parallelizable": self.parallelizable,
            "threaded_execution": self.threaded_execution,
            "posts": [post.ToJson() for post in self.posts]
        }
        
        # Add optional fields if they exist
        if self.max_concurrent_posts is not None:
            result["max_concurrent_posts"] = self.max_concurrent_posts
        if self.execution_timeout is not None:
            result["execution_timeout"] = self.execution_timeout
            
        return result
    
    @classmethod
    def FromJson(cls, json_data: Dict[str, Any]):
        """
        Create a PostGroup from a JSON object.
        
        Args:
            json_data: JSON object containing PostGroup configuration
            
        Returns:
            PostGroup: The initialized PostGroup
        """
        try:
            # Required fields
            id = json_data["id"]
            description = json_data["description"]
            parallelizable = json_data["parallelizable"]
            threaded_execution = json_data["threaded_execution"]
            
            # Create Posts from JSON
            posts_json = json_data["posts"]
            posts = [Post.FromJson(post_json) for post_json in posts_json]
            
            # Optional fields
            max_concurrent_posts = json_data.get("max_concurrent_posts")
            execution_timeout = json_data.get("execution_timeout")
            
            return cls(
                id=id,
                description=description,
                parallelizable=parallelizable,
                threaded_execution=threaded_execution,
                posts=posts,
                max_concurrent_posts=max_concurrent_posts,
                execution_timeout=execution_timeout
            )
        except Exception as e:
            self.log(f"Error creating PostGroup from JSON: {str(e)}")
            traceback.print_exc()
            raise NotImplementedError(f"Error creating PostGroup from JSON: {str(e)}")

class ExecutionPolicy(Pit):
    """
    ExecutionPolicy class defining how Pathway execution should be handled.
    
    The ExecutionPolicy determines retry behavior and other execution parameters.
    """
    
    def __init__(self, retry_on_failure: bool, max_retries: int):
        """
        Initialize an ExecutionPolicy.
        
        Args:
            retry_on_failure: Determines if failed Posts should be retried
            max_retries: The maximum number of retries allowed for failed Posts
        """
        Pit.__init__(self, "ExecutionPolicy", "")
        self.retry_on_failure = retry_on_failure
        self.max_retries = max_retries
        
    def ToJson(self) -> Dict[str, Any]:
        """
        Convert the ExecutionPolicy to a JSON object.
        
        Returns:
            dict: JSON representation of the ExecutionPolicy
        """
        return {
            "retry_on_failure": self.retry_on_failure,
            "max_retries": self.max_retries
        }
    
    @classmethod
    def FromJson(cls, json_data: Dict[str, Any]):
        """
        Create an ExecutionPolicy from a JSON object.
        
        Args:
            json_data: JSON object containing ExecutionPolicy configuration
            
        Returns:
            ExecutionPolicy: The initialized ExecutionPolicy
        """
        try:
            retry_on_failure = json_data["retry_on_failure"]
            max_retries = json_data["max_retries"]
            
            return cls(
                retry_on_failure=retry_on_failure,
                max_retries=max_retries
            )
        except Exception as e:
            self.log(f"Error creating ExecutionPolicy from JSON: {str(e)}")
            traceback.print_exc()
            raise NotImplementedError(f"Error creating ExecutionPolicy from JSON: {str(e)}")

class Metadata(Pit):
    """
    Metadata class containing additional information about a Pathway.
    
    The Metadata includes priority, creation timestamp, and reward information.
    """
    
    def __init__(self, 
                 priority: int, 
                 creation_timestamp: Union[str, datetime.datetime], 
                 pondo_reward: int):
        """
        Initialize Metadata.
        
        Args:
            priority: Priority level of the Pathway
            creation_timestamp: Timestamp when the Pathway was created
            pondo_reward: The amount of Pondo allocated for completing this Pathway
        """
        Pit.__init__(self, "Metadata", "")
        self.priority = priority
        
        # Handle different timestamp formats
        if isinstance(creation_timestamp, str):
            self.creation_timestamp = creation_timestamp
        elif isinstance(creation_timestamp, datetime.datetime):
            self.creation_timestamp = creation_timestamp.isoformat()
        else:
            self.creation_timestamp = datetime.datetime.now().isoformat()
            
        self.pondo_reward = pondo_reward
        
    def ToJson(self) -> Dict[str, Any]:
        """
        Convert the Metadata to a JSON object.
        
        Returns:
            dict: JSON representation of the Metadata
        """
        return {
            "priority": self.priority,
            "creation_timestamp": self.creation_timestamp,
            "pondo_reward": self.pondo_reward
        }
    
    @classmethod
    def FromJson(cls, json_data: Dict[str, Any]):
        """
        Create Metadata from a JSON object.
        
        Args:
            json_data: JSON object containing Metadata configuration
            
        Returns:
            Metadata: The initialized Metadata
        """
        try:
            priority = json_data["priority"]
            creation_timestamp = json_data["creation_timestamp"]
            pondo_reward = json_data["pondo_reward"]
            
            return cls(
                priority=priority,
                creation_timestamp=creation_timestamp,
                pondo_reward=pondo_reward
            )
        except Exception as e:
            self.log(f"Error creating Metadata from JSON: {str(e)}")
            traceback.print_exc()
            raise NotImplementedError(f"Error creating Metadata from JSON: {str(e)}")

class Pathway(Pit):
    """
    Pathway class representing a workflow of Posts.
    
    A Pathway contains an entrance post, multiple intermediate posts, and exit posts.
    It also includes an execution plan for managing concurrency.
    """
    
    def __init__(self,
                 pathway_id: str,
                 name: str,
                 entrance_post: Post,
                 exit_posts: List[str],
                 posts: List[Post],
                 owner_agent_id: str,
                 description: Optional[str] = None,
                 execution_plan: Optional[Dict[str, Any]] = None):
        """
        Initialize a Pathway.
        
        Args:
            pathway_id: Unique identifier for the Pathway
            name: Name of the Pathway
            entrance_post: The first Post in the Pathway
            exit_posts: List of Post IDs that mark the end of the Pathway
            posts: List of Posts in the Pathway
            owner_agent_id: The ID of the agent that owns the Pathway
            description: Description of the Pathway's purpose
            execution_plan: Plan for managing concurrency and post groups
        """
        Pit.__init__(self, "Pathway", name)
        self.pathway_id = pathway_id
        self.name = name
        self.entrance_post = entrance_post
        self.exit_posts = exit_posts
        self.posts = posts
        self.owner_agent_id = owner_agent_id
        self.description = description
        self.execution_plan = execution_plan or {}
        
    def ToJson(self) -> Dict[str, Any]:
        """
        Convert the Pathway to a JSON object.
        
        Returns:
            dict: JSON representation of the Pathway
        """
        result = {
            "pathway_id": self.pathway_id,
            "name": self.name,
            "entrance_post": self.entrance_post.ToJson(),
            "exit_posts": self.exit_posts,
            "posts": [post.ToJson() for post in self.posts],
            "owner_agent_id": self.owner_agent_id
        }
        
        if self.description:
            result["description"] = self.description
        if self.execution_plan:
            result["execution_plan"] = self.execution_plan
            
        return result
    
    @classmethod
    def FromJson(cls, json_data: Dict[str, Any]) -> 'Pathway':
        """
        Create a Pathway from a JSON object.
        
        Args:
            json_data: JSON object containing Pathway configuration
            
        Returns:
            Pathway: The initialized Pathway
        """
        #print(f"FromJson: {json_data}")
        entrance_post = Post.FromJson(json_data["entrance_post"])
        posts = [Post.FromJson(post_data) for post_data in json_data["posts"]]
        if "owner_agent_id" in json_data:
            owner_agent_id = json_data["owner_agent_id"]
        else:
            owner_agent_id = None
        return cls(
            pathway_id=json_data["pathway_id"],
            name=json_data["name"],
            entrance_post=entrance_post,
            exit_posts=json_data["exit_posts"],
            posts=posts,
            owner_agent_id=owner_agent_id,
            description=json_data.get("description"),
            execution_plan=json_data.get("execution_plan")
        )
        
    def validate(self) -> bool:
        """
        Validate the Pathway configuration.
        
        Returns:
            bool: True if the Pathway is valid, raises NotImplementedError otherwise
        """
        raise NotImplementedError("Pathway validation not implemented")
        
    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        """
        Get a Post by its ID.
        
        Args:
            post_id: ID of the Post to find
            
        Returns:
            Optional[Post]: The Post if found, None otherwise
        """
        if self.entrance_post.post_id == post_id:
            return self.entrance_post
            
        for post in self.posts:
            if post.post_id == post_id:
                return post
                
        return None