class Database:
    def __init__(self, database_name):
        self.database_name = database_name
    
    def create_database(self):
        return f"Database {self.database_name} created"
    
    def delete_database(self):
        return f"Database {self.database_name} deleted"
    
   
    
