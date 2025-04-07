# DynamoDBPool is a DatabasePool that uses DynamoDB to store and retrieve data

class DynamoDBPool(DatabasePool):
    """
    DynamoDBPool is a DatabasePool that uses DynamoDB to store and retrieve data
    """

    # TODO: Implement DynamoDBPool
    
    def __init__(self, name: str, description: str = None):
        super().__init__(name, description)
