from sqlalchemy import Column, Integer, String

from .database import Base


class TokenData(Base):
    __tablename__ = "tokendata"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    input_text = Column(String(4000))
    input_token_count = Column(Integer)
    output_text = Column(String(4000))
    output_token_count = Column(Integer)


