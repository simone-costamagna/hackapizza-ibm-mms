from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_ibm import ChatWatsonx
from langchain_openai import ChatOpenAI
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames
from utils.models import MODELS, WATSONX


def initialize_llm(model_id: str, temperature:float=0.0, max_tokens:int=None, max_retries:int=2):
    if model_id in MODELS[WATSONX]:
        parameters = {
            GenTextParamsMetaNames.TEMPERATURE: temperature,
        }
        llm = ChatWatsonx(
            model_id=model_id,
            url="https://us-south.ml.cloud.ibm.com",
            project_id="dbf765e8-6f23-4e65-9fba-4ec44d167f0f",
            params=parameters,
        )
    else:
        llm = ChatOpenAI(
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries
        )
    return llm



class LLMWrapper:
    def __init__(self, model_id:str='gpt-4o-mini', temperature:float=0.1, max_tokens:int=None, max_retries:int=2):
        self._llm = initialize_llm(model_id, temperature, max_tokens, max_retries)
        self._parser = StrOutputParser()

    @property
    def llm(self):
        return self._llm

    @property
    def parser(self):
        return self._parser

    def bind_tools(self, tools: list, tool_choice: str = None):
        # tool_choice:
        # "auto" -> can pick between generating a message or calling one or more tools
        # "none" -> not call any tool and instead generates a message
        # "required" -> call one or more tools
        self._llm = self._llm.bind_tools(tools, tool_choice=tool_choice)

    def set_structured_output(self, structure: object):
        self._llm = self._llm.with_structured_output(structure)

    def activate_json_mode(self):
        self._llm = self._llm.bind(response_format={"type": "json_object"})
        self._parser = JsonOutputParser()

    def activate_log_probs(self):
        self._llm = self._llm.bind(logprobs=True)