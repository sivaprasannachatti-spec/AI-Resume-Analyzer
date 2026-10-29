import sys
import json
from typing import List, Optional

from sqlmodel import Session, select
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from config import OPENROUTER_API_KEY_1
from backend.prompts import NEW_CHAT_SYSTEM_PROMPT, CHAT_TITLE_PROMPT
from src.exception import CustomException
from backend.models.schemas import CVS, Chats, Messages, ResumeAnalysis
from backend.models.database import engine


def extract_cv(resume_id: str) -> CVS:
    try:
        with Session(engine) as session:
            cv = session.exec(select(CVS).where(CVS.resume_id == resume_id)).first()
            if not cv:
                raise CustomException(f"CV not found for resume_id: {resume_id}", sys)
            return cv
    except Exception as e:
        raise CustomException(e, sys)


def extract_jd(resume_id: str) -> str:
    try:
        with Session(engine) as session:
            analysis = session.exec(select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)).first()
            if not analysis:
                raise CustomException(f"JD/Analysis not found for resume_id: {resume_id}", sys)
            return analysis.jd
    except Exception as e:
        raise CustomException(e, sys)


def extract_chat_by_cv(cv_id: str) -> Optional[Chats]:
    try:
        with Session(engine) as session:
            return session.exec(select(Chats).where(Chats.cv_id == cv_id)).first()
    except Exception as e:
        raise CustomException(e, sys)


def extract_messages(chat_id: str) -> List[Messages]:
    try:
        with Session(engine) as session:
            messages = session.exec(select(Messages).where(Messages.chat_id == chat_id)).all()
            return list(messages)
    except Exception as e:
        raise CustomException(e, sys)


def generate_chat_title(model: ChatOpenAI, user_query: str, jd_text: str, cv_text: str) -> str:
    """Generates a clean 3-5 word chat title."""
    try:
        title_chain = ChatPromptTemplate.from_template(CHAT_TITLE_PROMPT) | model | StrOutputParser()
        raw_title = title_chain.invoke({
            "user_query": user_query,
            "jd_context": jd_text,
            "resume_context": cv_text
        })
        return raw_title.strip().strip('"').strip("'")[:60]
    except Exception:
        return "Resume Career Discussion"


def chat(user_query: str, resume_id: str, message_history: list[dict] | None = None) -> str:
    try:
        if message_history is None:
            message_history = []

        # 1. Fetch CV and JD
        cv = extract_cv(resume_id=resume_id)
        formatted_cv = json.dumps(cv.cv_payload, indent=2)
        jd_text = extract_jd(resume_id=resume_id)

        # 2. Initialize LLM Model
        model = ChatOpenAI(
            model='mistralai/mistral-small-3.2-24b-instruct',
            api_key=OPENROUTER_API_KEY_1,
            base_url="https://openrouter.ai/api/v1",
        )

        # 3. Build & Invoke the Conversation Chain
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", NEW_CHAT_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="message_history"),
                ("human", "{user_query}")
            ]
        )
        chain = prompt | model | StrOutputParser()

        response = chain.invoke({
            "cv_payload": formatted_cv,
            "jd_context": jd_text,
            "message_history": message_history,
            "user_query": user_query
        })

        # 4. Save to Database (Find existing chat or create new one)
        with Session(engine) as session:
            existing_chat = session.exec(select(Chats).where(Chats.cv_id == cv.cv_id)).first()

            if not existing_chat:
                # Generate custom title for the new conversation
                title = generate_chat_title(model, user_query, jd_text, formatted_cv)
                chat_record = Chats(cv_id=cv.cv_id, chat_title=title)
                session.add(chat_record)
                session.commit()
                session.refresh(chat_record)
                current_chat_id = chat_record.chat_id
            else:
                current_chat_id = existing_chat.chat_id

            # Save both the User's question and the AI's reply into Messages table
            user_msg = Messages(chat_id=current_chat_id, type="User", message=user_query)
            ai_msg = Messages(chat_id=current_chat_id, type="AI", message=response)

            session.add(user_msg)
            session.add(ai_msg)
            session.commit()

        return response

    except Exception as e:
        raise CustomException(e, sys)