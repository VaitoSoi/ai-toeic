from typing import Optional


class TopicNotFound(ValueError): 
    id: Optional[str] = None

    def __init__(self, id: Optional[str] = None):
        super()
        self.message = "topic not found"
        self.id = id

class QuestionNotFound(ValueError): 
    id: Optional[str] = None
    
    def __init__(self, id: Optional[str] = None):
        super()
        self.message = "question not found"
        self.id = id

class SubmissionNotFound(ValueError): 
    id: Optional[str] = None
    
    def __init__(self, id: Optional[str] = None):
        super()
        self.message = "submission not found"
        self.id = id

class ReviewNotFound(ValueError): 
    id: Optional[str] = None
    
    def __init__(self, id: Optional[str] = None):
        super()
        self.message = "review not found"
        self.id = id

class ModelFailure(Exception):
    task: Optional[str] = None
    part: Optional[str] = None

    def __init__(self, task: Optional[str] = None, part: Optional[str] = None):
        super()
        self.message = "failed to generate"
        self.task = task
        self.part = part
