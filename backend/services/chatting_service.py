import sys
import json

from sqlmodel import Session, select, insert
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from config import OPENROUTER_API_KEY_1
from backend.prompts import NEW_CHAT_SYSTEM_PROMPT, CHAT_TITLE_PROMPT
from src.exception import CustomException
from backend.models.schemas import ResumeAnalysis, CVS, Chats, Messages
from backend.models.database import engine

def extract_cv(resume_id: str):
    try:
        with Session(engine) as session:
            cv = session.exec(select(CVS).where(CVS.resume_id == resume_id)).first()
            if not cv:
                raise CustomException(f"CV not found for resume_id: {resume_id}", sys)
            return cv
    except Exception as e:
        raise CustomException(e, sys)

def extract_jd(resume_id: str):
    try:
        with Session(engine) as session:
            jd = session.exec(select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)).first()
            if not jd:
                raise CustomException(f"JD not found for resume_id: {resume_id}", sys)
            return jd
    except Exception as e:
        raise CustomException(e, sys)

def extract_chat(cv_id: str):
    try:
        with Session(engine) as session:
            chat = session.exec(select(Chats).where(Chats.cv_id == cv_id)).first()
            if not chat:
                raise CustomException(f"Chat not found for cv_id: {cv_id}", sys)
            return chat
    except Exception as e:  
        raise CustomException(e, sys)

def extract_messages(chat_id: str):
    try:
        with Session(engine) as session:
            messages = session.exec(select(Messages).where(Messages.chat_id == chat_id)).all()
            return list(messages)
    except Exception as e:
        raise CustomException(e, sys)

def extract_chat(resume_id: str):
    try:
        with Session(engine) as session:
            cv = session.exec(select(CVS).where(CVS.resume_id == resume_id))
            if not cv.id:
                raise CustomException("Failed to fetch the cv from database.", sys)
            return cv
    except Exception as e:
        raise CustomException(e, sys)
    
def chat(user_query: str, resume_id: str, message_history: list[dict] | None = None):
    try:
        # check if message_history is None, if so, initialize it as an empty list
        if message_history is None:
            message_history = []
        # get the cv
        cv = extract_cv(resume_id=resume_id)
        payload = cv.cv_payload
        formatted_cv = json.dumps(payload, indent=2)  # Format the CV for better readability
        # get the jd
        resume = extract_jd(resume_id=resume_id)
        jd = resume.jd
        # intiate the model
        model = ChatOpenAI(
            model='mistralai/mistral-small-3.2-24b-instruct',
            api_key=OPENROUTER_API_KEY_1,
            base_url="https://openrouter.ai/api/v1",
        )
        # attach the prompt to the model
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", NEW_CHAT_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="message_history"),
                ("human", "{user_query}")
            ]
        )
        # initialize the chain
        chain = prompt | model | StrOutputParser()
        # invoke the chain
        response = chain.invoke({
            "cv_payload": formatted_cv,
            "jd_context": jd,
            "message_history": message_history,
            "user_query": user_query
        })
        # save the data in database
        if message_history is None:
            prompt = ChatPromptTemplate.from_template(CHAT_TITLE_PROMPT) | model.with_structured_output(schema=StrOutputParser())
            title = prompt.invoke({"user_query": user_query, "jd_context": jd, "resume_context": formatted_cv})
            chat = Chats(
                cv_id=cv.cv_id,
                chat_title=title
            )
            if not chat.id:
                raise CustomException("Failed to create chat entry in the database.", sys)
            session.add(chat)
            user_message = Messages(
                chat_id=chat.chat_id,
                type='User',
                message=user_query
            )
            if not user_message.message_id:
                raise CustomException("Failed to insert user message entry in database.", sys)
            session.add(user_message)
            chat_message = Messages(
                chat_id=chat.chat_id,
                type='AI',
                message=response
            )
            if not chat_message.message_id:
                raise CustomException("Failed to insert AI message entry in database.", sys)
            session.add(chat_message)
        else:
            cv = extract_chat(resume_id=resume_id)
            with Session(engine) as session:
                chat = session.exec(select(Chats).where(Chats.cv_id == cv.cv_id))
                if not chat.id:
                    raise CustomException("Failed to fetch the chat from database.", sys)
                chat.chat_id = chat.chat_id
                chat.type = 'User'
                chat.message = user_query
                chat.chat_id = chat.chat_id
                chat.type = 'AI'
                chat.message = response
                session.add(chat)
                session.commit()
        return response
    except Exception as e:
        raise CustomException(e, sys)
