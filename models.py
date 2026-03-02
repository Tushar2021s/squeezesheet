from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)


# from sqlalchemy import Column, Integer, String
# from database import Base

# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True)
#     password = Column(String)



# # from sqlalchemy import Column, Integer, String
# # from database import Base

# # class SolvedProblem(Base):
# #     __tablename__ = "solved_problems"

# #     id = Column(Integer, primary_key=True, index=True)
# #     contestId = Column(Integer)
# #     index = Column(String)
# #     name = Column(String)
# #     rating = Column(Integer)