import os
from dotenv import load_dotenv
from langchain.schema.runnable import Runnable
from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import yaml
from typing import List, Dict, Any, Optional, Union, Annotated, Sequence, TypedDict, Union
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import importlib
from functools import partial
import logging
import time
from threading import Lock
from langchain.schema import HumanMessage, AIMessage
from langgraph.graph import Graph, StateGraph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class NewsState(TypedDict):
    messages: Annotated[Sequence[Dict[str, str]], "The conversation history"]
    tool_results: Annotated[List[Dict[str, Any]], "Results from called tools"]
    current_tool: Annotated[Optional[str], "Current tool being used"]
    response: Annotated[Optional[str], "Final response to user"]

class MistralToolModel(Runnable):
    # Class-level rate limiting
    _last_request_time = 0
    _rate_limit_lock = Lock()
    _min_request_interval = 1.0  # Minimum time between requests in seconds

    @staticmethod
    def load_prompt_config():
        """Load the prompt configuration from YAML file."""
        try:
            with open('prompts/news_prompt.yaml', 'r') as file:
                config = yaml.safe_load(file)
                logger.info("Successfully loaded prompt configuration")
                return config
        except Exception as e:
            logger.error(f"Error loading prompt configuration: {str(e)}")
            raise

    @classmethod
    def initialize_model(cls):
        """Initialize the Mistral model with configuration."""
        try:
            config = cls.load_prompt_config()
            logger.info(f"Initializing model with config: {config['model']}")
            model = cls(
                model_name=config['model']['name'],
                temperature=config['model']['temperature'],
                max_tokens=config['model']['max_tokens']
            )
            return model
        except Exception as e:
            logger.error(f"Error initializing model: {str(e)}")
            raise

    def __init__(self, model_name: str, temperature: float, max_tokens: int):
        try:
            # Configure Mistral API
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError("MISTRAL_API_KEY environment variable is not set")
            
            logger.info(f"Configuring Mistral API with model: {model_name}")
            self.client = MistralClient(api_key=api_key)
            self.model_name = model_name
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.conversation_history: List[Dict[str, str]] = []
            self.executor = ThreadPoolExecutor(max_workers=4)
            self.tools = self._load_tools()
            logger.info("Successfully initialized MistralToolModel")
        except Exception as e:
            logger.error(f"Error in MistralToolModel initialization: {str(e)}")
            raise

    def _enforce_rate_limit(self):
        """Enforce rate limiting for API requests."""
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last_request = current_time - self._last_request_time
            if time_since_last_request < self._min_request_interval:
                sleep_time = self._min_request_interval - time_since_last_request
                logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            self._last_request_time = time.time()

    def invoke(self, input: Union[str, Dict[str, Any]], config: Optional[Dict[str, Any]] = None) -> str:
        """Implement the Runnable interface."""
        if isinstance(input, dict):
            user_input = input.get("input", "")
            tool_results = input.get("tool_results", None)
        else:
            user_input = input
            tool_results = None
            
        return self.get_response(user_input, tool_results)

    def _load_tools(self) -> Dict[str, Any]:
        """Load tools from YAML configuration."""
        try:
            with open('tools/news_tools.yaml', 'r') as file:
                tools_config = yaml.safe_load(file)
            
            tools = {}
            for tool_config in tools_config['tools']:
                module = importlib.import_module(tool_config['module_path'])
                function = getattr(module, tool_config['function_name'])
                tools[tool_config['name']] = {
                    'function': function,
                    'description': tool_config['description'],
                    'parameters': tool_config.get('parameters', {}),  # Use get() with default empty dict
                    'returns': tool_config.get('returns', {}),  # Add returns field
                    'raises': tool_config.get('raises', [])  # Add raises field
                }
            logger.info(f"Successfully loaded {len(tools)} tools")
            return tools
        except Exception as e:
            logger.error(f"Error loading tools: {str(e)}")
            raise

    def get_system_prompt(self) -> str:
        """Get the system prompt for the model."""
        with open('prompts/news_prompt.yaml', 'r') as file:
            config = yaml.safe_load(file)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create a serializable version of tools without function references
            serializable_tools = {}
            for tool_name, tool_info in self.tools.items():
                serializable_tools[tool_name] = {
                    'description': tool_info['description'],
                    'parameters': tool_info['parameters'],
                    'returns': tool_info['returns'],
                    'raises': tool_info['raises']
                }
            
            return f"{config['system_prompt']}\n\nCurrent Date and Time: {current_time}\n\nAvailable Tools: {json.dumps(serializable_tools, indent=2)}"

    def add_to_history(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def get_response(self, user_input: str, tool_results: List[Dict[str, Any]] = None) -> str:
        """
        Get a response from Mistral based on user input and tool results.
        """
        # Create the prompt with context
        prompt = f"""
        System: {self.get_system_prompt()}
        
        User Input: {user_input}
        
        Tool Results:
        {json.dumps(tool_results, indent=2) if tool_results else 'No tool results yet'}
        
        Please analyze the user's request and the available tool results.
        If more information is needed to fully satisfy the request, indicate which additional tools should be called.
        If the current information is sufficient, provide a comprehensive response.
        """

        # Enforce rate limit before making the API call
        self._enforce_rate_limit()

        # Get response from Mistral
        messages = [
            ChatMessage(role="system", content=self.get_system_prompt()),
            ChatMessage(role="user", content=prompt)
        ]
        
        response = self.client.chat(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return response.choices[0].message.content

    def process_tool_response(self, tool_result: Dict[str, Any]) -> Any:
        """
        Process a tool result and return a formatted response.
        This method runs in a separate thread and returns a Future.
        """
        def _process():
            # Create a prompt for the tool result
            prompt = f"""
            Please analyze the following tool result and determine if it provides sufficient information:

            Tool: {tool_result['tool_name']}
            Result: {json.dumps(tool_result, indent=2)}

            Consider:
            1. Does this information fully answer the user's query?
            2. What additional information might be needed?
            3. Which other tools could provide the missing information?
            """

            # Enforce rate limit before making the API call
            self._enforce_rate_limit()

            # Get response from Mistral
            messages = [
                ChatMessage(role="system", content=self.get_system_prompt()),
                ChatMessage(role="user", content=prompt)
            ]
            
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content

        # Submit the processing task to the thread pool
        return self.executor.submit(_process)

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool with the given parameters."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.tools[tool_name]
        try:
            result = tool['function'](**kwargs)
            return {
                'tool_name': tool_name,
                'result': result,
                'status': 'success'
            }
        except Exception as e:
            return {
                'tool_name': tool_name,
                'error': str(e),
                'status': 'error'
            }

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []

class NewsAgent:
    def __init__(self):
        self.config = self._load_config()
        self.client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))
        self.tools = self._load_tools()
        self.graph = self._create_graph()

    def _load_config(self) -> Dict[str, Any]:
        with open("prompts/news_prompt.yaml", "r") as f:
            return yaml.safe_load(f)

    def _load_tools(self) -> Dict[str, Any]:
        """Load tools from YAML configuration."""
        try:
            with open('tools/news_tools.yaml', 'r') as file:
                tools_config = yaml.safe_load(file)
            
            tools = {}
            for tool_config in tools_config['tools']:
                module = importlib.import_module(tool_config['module_path'])
                function = getattr(module, tool_config['function_name'])
                tools[tool_config['name']] = {
                    'function': function,
                    'description': tool_config['description'],
                    'parameters': tool_config.get('parameters', {}),
                    'returns': tool_config.get('returns', {}),
                    'raises': tool_config.get('raises', [])
                }
            logger.info(f"Successfully loaded {len(tools)} tools")
            return tools
        except Exception as e:
            logger.error(f"Error loading tools: {str(e)}")
            raise

    def _create_system_prompt(self) -> str:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a serializable version of tools without function references
        serializable_tools = {}
        for tool_name, tool_info in self.tools.items():
            serializable_tools[tool_name] = {
                'description': tool_info['description'],
                'parameters': tool_info['parameters'],
                'returns': tool_info['returns'],
                'raises': tool_info['raises']
            }
        
        return f"""
        {self.config["system_prompt"]}
        
        Current Date and Time: {current_time}
        
        Available Tools:
        {json.dumps(serializable_tools, indent=2)}
        """

    def _get_mistral_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Get a response from the Mistral model.
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            
        Returns:
            str: The model's response
        """
        try:
            response = self.client.chat(
                model=self.config['model']['name'],
                messages=messages,
                temperature=self.config['model']['temperature'],
                max_tokens=self.config['model']['max_tokens']
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting Mistral response: {str(e)}")
            raise

    def _create_graph(self) -> Graph:
        def decide_next_action(state: NewsState) -> NewsState:
            messages = state["messages"]
            last_tool_result = state["tool_results"][-1] if state["tool_results"] else None
            
            # Add recursion limit check
            if len(state["tool_results"]) >= 4:
                return {
                    **state,
                    "response": "Maximum tool call limit reached. Stopping further processing."
                }
            
            prompt = f"""
            You have already received the following tool results:
            {json.dumps(state['tool_results'], indent=2) if state['tool_results'] else 'No tool results yet'}

            Do you need to call another tool to answer the original query:
            {messages[0]['content']}?

            You MUST respond with a JSON object in one of these formats:
            1. To call a tool: {{"tool": "tool_name", "parameters": {{"param1": "value1", ...}}}}
            2. To return final response: {{"tool": null, "parameters": null}}

            Available tools are: {', '.join(self.tools.keys())}

            IMPORTANT: Respond with ONLY the JSON object, no markdown formatting or additional text.
            """
            
            analysis = self._get_mistral_response([
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user", "content": prompt}
            ])
            
            try:
                decision = json.loads(analysis)
                if decision.get("tool") and decision.get("tool") in self.tools:
                    return {
                        **state,
                        "messages": messages + [{"role": "assistant", "content": analysis}],
                        "current_tool": decision["tool"]
                    }
                elif decision.get("tool") is None:
                    return {
                        **state,
                        "response": "Tool processing complete. Finalizing response."
                    }
            except json.JSONDecodeError:
                return {
                    **state,
                    "response": "Error parsing tool decision. Please try again."
                }

        def call_tool(state: NewsState) -> NewsState:
            messages = state["messages"]
            last_message = messages[-1]["content"]
            
            try:
                tool_call = json.loads(last_message)
                if not isinstance(tool_call, dict) or "tool" not in tool_call or "parameters" not in tool_call:
                    raise ValueError("Invalid tool call format")
                
                tool_name = tool_call["tool"]
                parameters = tool_call["parameters"]
                
                if tool_name not in self.tools:
                    raise ValueError(f"Invalid tool name: {tool_name}")

                try:
                    result = self.tools[tool_name]['function'](**parameters)
                    return {
                        **state,
                        "messages": messages + [{"role": "assistant", "content": json.dumps(result)}],
                        "tool_results": state["tool_results"] + [result],
                    }
                except Exception as e:
                    error_msg = f"Error in {tool_name} tool: {str(e)}"
                    return {
                        **state,
                        "messages": messages + [{"role": "assistant", "content": error_msg}],
                        "tool_results": state["tool_results"] + [{"error": error_msg}],
                    }
            except Exception as e:
                error_msg = f"Error in tool call: {str(e)}"
                return {
                    **state,
                    "messages": messages + [{"role": "assistant", "content": error_msg}],
                    "tool_results": state["tool_results"] + [{"error": error_msg}],
                }

        def finalize(state: NewsState) -> NewsState:
            messages = state["messages"]
            tool_results = state["tool_results"]
            
            final_prompt = f"""
            Based on the following tool results:
            {json.dumps(tool_results, indent=2)}

            Please provide a comprehensive response to the original query:
            {messages[0]['content']}
            """
            
            response = self._get_mistral_response([
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user", "content": final_prompt}
            ])
            
            return {
                **state,
                "response": response
            }

        workflow = StateGraph(NewsState)
        workflow.add_node("call_tool", call_tool)
        workflow.add_node("decide_next", decide_next_action)
        workflow.add_node("finalize", finalize)

        workflow.set_entry_point("decide_next")
        workflow.add_edge("decide_next", "call_tool")
        workflow.add_conditional_edges("call_tool", lambda s: "decide_next" if s["response"] is None else "finalize")

        return workflow.compile()

    async def get_response(self, user_input: str) -> str:
        initial_state = NewsState(
            messages=[{"role": "user", "content": user_input}],
            tool_results=[],
            current_tool=None,
            response=None
        )
        final_state = await self.graph.ainvoke(initial_state)
        return final_state["response"]

def create_chain(model):
    """Create a LangChain chain with memory."""
    config = MistralToolModel.load_prompt_config()
    prompt = PromptTemplate(
        input_variables=["history", "input", "tool_results"],
        template=config['system_prompt']
    )
    
    # Use ChatMessageHistory instead of ConversationBufferMemory
    memory = ChatMessageHistory()
    
    # Create a RunnableSequence instead of LLMChain
    chain = (
        RunnablePassthrough.assign(
            history=lambda _: memory.messages
        )
        | prompt
        | model
        | StrOutputParser()
    )
    
    return chain, memory

def process_user_input(chain, memory, user_input):
    """Process user input through the chain and handle tool responses."""
    iteration_count = 0
    max_iterations = 5
    
    # Get initial response using invoke
    response = chain.invoke(
        {"input": user_input, "tool_results": ""}
    )
    
    # Add the interaction to memory
    memory.add_user_message(user_input)
    memory.add_ai_message(response)
    
    # Process any tool responses
    while memory.messages and memory.messages[-1].type == "tool" and iteration_count < max_iterations:
        iteration_count += 1
        tool_results = memory.messages[-1].content
        response = chain.invoke(
            {"input": user_input, "tool_results": tool_results}
        )
        memory.add_ai_message(response)
    
    if iteration_count >= max_iterations:
        response += "\n\n[Note: Maximum iteration limit reached. Stopping further processing.]"
    
    return response

async def news_agent(user_input: str) -> str:
    """
    Process user input through the news agent and return the response.
    
    Args:
        user_input (str): The user's input query
        
    Returns:
        str: The agent's response to the user input
    """
    try:
        agent = NewsAgent()
        response = await agent.get_response(user_input)
        print("\n=== News Agent Response ===")
        print(response)
        return response
        
    except Exception as e:
        error_msg = f"Error in news agent: {str(e)}"
        print(error_msg)
        return error_msg 

