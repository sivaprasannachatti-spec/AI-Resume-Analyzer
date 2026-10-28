import os
import sys

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config import OPENROUTER_API_KEY_1

from src.exception import CustomException
from backend.output_parsers import ResumeSchema, JDSchema
from backend.prompts import RESUME_NORMALIZER_PROMPT, JD_EXTRACTION_PROMPT

def extract_resume_data(resume_text: str):
    try:
        # initiate the model
        model = ChatOpenAI(
            model='openai/gpt-4.1-nano',
            api_key=OPENROUTER_API_KEY_1,
            base_url="https://openrouter.ai/api/v1",
        )
        # attach the prompt to the model
        extract_model = ChatPromptTemplate.from_template(RESUME_NORMALIZER_PROMPT) | model.with_structured_output(schema=ResumeSchema)
        # invoke the model
        resume_data = extract_model.invoke({"resume_content": resume_text})
        # return the data
        resume_data = resume_data.model_dump()
        return resume_data
    except Exception as e:
        raise CustomException(e, sys)

def extract_jd_content(JD):
    try:
        # initiate the model
        model = ChatOpenAI(
            model='openai/gpt-4.1-nano',
            api_key=OPENROUTER_API_KEY_1,
            base_url="https://openrouter.ai/api/v1",
        )
        # attach the template to the model
        jd_model = ChatPromptTemplate.from_template(JD_EXTRACTION_PROMPT) | model.with_structured_output(schema=JDSchema)
        # invoke the model
        jd_data = jd_model.invoke({"jd_text": JD})
        # return the data
        jd_data = jd_data.model_dump()
        return jd_data
    except Exception as e: 
        raise CustomException(e, sys)