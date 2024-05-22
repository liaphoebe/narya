from sqlalchemy import Column, Integer, JSON, String
from sqlalchemy.ext.declarative import declarative_base
from utils import json_similarity
import json
import requests
import os

Base = declarative_base()

SIMILARITY_THRESHOLD = 0.99
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

class Request(Base):
    __tablename__ = 'requests'

    id = Column(Integer, primary_key=True)
    request = Column(JSON, nullable=False)
    response = Column(JSON, nullable=True)
    request_type = Column(String(256), nullable=False)

    def __init__(self, req_type, data, resume=True):
        from main import session

        self.request_type = req_type
        self.request = data

        if resume:
            #matching_request = session.query(Request).filter_by(request_type=req_type, request=data).first()
            for candidate in session.query(Request).filter_by(request_type=req_type):
                if json_similarity(candidate.request, data) >= SIMILARITY_THRESHOLD:
                    self.response = candidate.response
                    return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        }

        response = requests.post(OPENAI_ENDPOINT, headers=headers, data=json.dumps(data))
        
        self.response = response.json()

        session.add(self)
        session.commit()
