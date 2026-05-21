from sqlalchemy import Column, String, Text

from database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    contract_time = Column(String, nullable=True)  
    created = Column(String, nullable=True)       
    redirect_url = Column(String, nullable=True)  