class TopicNotFound(ValueError): 
    def __init__(self, id: str | None = None):
        super()
        self.message = "topic not found"
        self.id = id

class SubmissionNotFound(ValueError): 
    def __init__(self, id: str | None = None):
        super()
        self.message = "submission not found"
        self.id = id

class ReviewNotFound(ValueError): 
    def __init__(self, id: str | None = None):
        super()
        self.message = "review not found"
        self.id = id