class Chatbot:
    def __init__(self, query,user_type):
        self.query = query
        self.user_type = user_type
    
    def get_response(self):
        if self.user_type == "student":
            return "Hello, I am a student chatbot. How can I help you today?"
        elif self.user_type == "teacher":
            return "Hello, I am a teacher chatbot. How can I help you today?"
        else:
            return "Hello, I am a chatbot. How can I help you today?"
        
