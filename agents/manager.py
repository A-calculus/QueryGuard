import os
from typing import List, Dict, Any, Optional, Annotated, Sequence, TypedDict
from langchain.schema import HumanMessage, AIMessage
from langgraph.graph import Graph, StateGraph
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import yaml
import json
from .market_agent import market_agent
from .news_agent import news_agent
from .signal_agent import signal_agent
from .chat_agent import chat_agent
import time
from threading import Lock
import logging

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[Sequence[Dict[str, str]], "The conversation history"]
    agent_responses: Annotated[List[str], "Responses from called agents"]
    current_agent: Annotated[Optional[str], "Current agent being used"]
    response: Annotated[Optional[str], "Final response to user"]
    knowledge_base: Annotated[Optional[Dict[str, Any]], "Information from Messari AI"]

class AgentManager:
    # Class-level rate limiting
    _last_request_time = 0
    _rate_limit_lock = Lock()
    _min_request_interval = 1.0  # Minimum time between requests in seconds

    def __init__(self):
        self.config = self._load_config()
        self.client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))
        self.agents = {
            "market": market_agent,
            "news": news_agent,
            "signal": signal_agent,
            "chat": chat_agent
        }
        self.agent_descriptions = self._get_agent_descriptions()
        self.graph = self._create_graph()

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

    def _load_config(self) -> Dict[str, Any]:
        with open("prompts/mistral_prompt.yaml", "r") as f:
            return yaml.safe_load(f)

    def _get_agent_descriptions(self) -> str:
        try:
            with open('agents/agents.yaml', 'r') as file:
                agents_config = yaml.safe_load(file)

            agent_descriptions = ["Available Agents:"]
            for i, agent in enumerate(agents_config['agents'], 1):
                description = agent['description'].strip()
                agent_descriptions.append(f"{i}. {agent['name']}: {description}")
                if 'tools' in agent:
                    agent_descriptions.append("   Available Tools:")
                    for tool in agent['tools']:
                        params = ', '.join(p.get('name', 'param') for p in tool.get('parameters', []))
                        agent_descriptions.append(f"   - {tool['name']}: Parameters: {params}")
                agent_descriptions.append("")

            agent_descriptions.append("""
When you need to use an agent, respond with a JSON object in this format:
{"agent": "agent_name", "query": "your query to the agent"}

If you don't need to use any agents, respond normally with your final answer.
""")
            return "\n".join(agent_descriptions)
        except Exception as e:
            return f"Error loading agent descriptions: {str(e)}"

    def _create_system_prompt(self) -> str:
        return f"""
        {self.config["system_prompt"]}

        {self.agent_descriptions}

        You can call multiple agents if necessary to fully answer the user's query.
        Evaluate whether further agent calls are required based on their responses.
        """

    def _get_mistral_response(self, messages: List[Dict[str, str]]) -> str:
        self._enforce_rate_limit()
        chat_messages = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]
        response = self.client.chat(
            model=self.config["model"]["name"],
            messages=chat_messages,
            temperature=self.config["model"]["temperature"],
            max_tokens=self.config["model"]["max_tokens"]
        )
        return response.choices[0].message.content

    def _create_graph(self) -> Graph:
        def decide_next_action(state: AgentState) -> AgentState:
            messages = state["messages"]
            last_response = state["agent_responses"][-1] if state["agent_responses"] else ""
            
            # Add recursion limit check
            if len(state["agent_responses"]) >= 4:
                return {
                    **state,
                    "response": last_response + "\n\n[Note: Maximum agent call limit reached. Stopping further processing.]"
                }
            
            # If we've tried the same agent multiple times and it's failing, try a different one
            if len(state["agent_responses"]) > 0 and "Error processing request" in last_response:
                failed_agent = state.get("current_agent")
                available_agents = [agent for agent in self.agents.keys() if agent != failed_agent]
                if available_agents:
                    next_agent = available_agents[0]
                    return {
                        **state,
                        "messages": messages + [{"role": "assistant", "content": json.dumps({"agent": next_agent, "query": messages[0]["content"]})}],
                        "current_agent": next_agent
                    }
                else:
                    # If all agents have failed, return an error message
                    return {
                        **state,
                        "response": "I apologize, but I'm unable to process your request at this time. Please try again later."
                    }

            prompt = f"""
You have already received the following agent responses:
{chr(10).join(state['agent_responses'])}

Do you need to call another agent to answer the original query:
{messages[0]['content']}?

You MUST respond with a JSON object in one of these formats:
1. To call an agent: {{"agent": "agent_name", "query": "your query to the agent"}}
2. To return final response: {{"agent": null, "query": null}}

Available agents are: {', '.join(self.agents.keys())}

IMPORTANT: Respond with ONLY the JSON object, no markdown formatting or additional text.
"""
            print("\n=== Deciding Next Action ===")
            print(f"Prompt: {prompt}")
            
            analysis = self._get_mistral_response([
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user", "content": prompt}
            ])
            
            print(f"LLM Response: {analysis}")

            # Clean the response by removing markdown formatting
            clean_analysis = analysis.strip()
            if clean_analysis.startswith("```json"):
                clean_analysis = clean_analysis[7:]
            if clean_analysis.startswith("```"):
                clean_analysis = clean_analysis[3:]
            if clean_analysis.endswith("```"):
                clean_analysis = clean_analysis[:-3]
            clean_analysis = clean_analysis.strip()

            try:
                decision = json.loads(clean_analysis)
                print(f"Parsed Decision: {decision}")
                
                if decision.get("agent") and decision.get("agent") in self.agents:
                    messages.append({"role": "assistant", "content": clean_analysis})
                    return {
                        **state,
                        "messages": messages,
                        "current_agent": decision["agent"]
                    }
                elif decision.get("agent") is None:
                    return {
                        **state,
                        "response": last_response
                    }
            except json.JSONDecodeError as e:
                print(f"JSON decode error in decide_next_action: {e}")
                print(f"Cleaned analysis: {clean_analysis}")
                # If we can't parse as JSON, treat it as a final response
                return {
                    **state,
                    "response": analysis
                }

            # If we get here, something went wrong with the agent selection
            print("Invalid agent selection or format")
            return {
                **state,
                "response": "I apologize, but I encountered an error processing your request. Please try again."
            }
        

        async def call_agent(state: AgentState) -> AgentState:
            messages = state["messages"]
            last_message = messages[-1]["content"]
            
            try:
                agent_call = json.loads(last_message)
                if not isinstance(agent_call, dict) or "agent" not in agent_call or "query" not in agent_call:
                    raise ValueError("Invalid agent call format")
                
                agent_name = agent_call["agent"]
                agent_query = agent_call["query"]
                
                if agent_name not in self.agents:
                    raise ValueError(f"Invalid agent name: {agent_name}")

                try:
                    response = await self.agents[agent_name](agent_query)
                    return {
                        **state,
                        "messages": messages + [{"role": "assistant", "content": response}],
                        "agent_responses": state["agent_responses"] + [response],
                    }
                except Exception as e:
                    error_msg = f"Error in {agent_name} agent: {str(e)}"
                    print(error_msg)
                    return {
                        **state,
                        "messages": messages + [{"role": "assistant", "content": error_msg}],
                        "agent_responses": state["agent_responses"] + [error_msg],
                    }
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON format in agent call: {str(e)}"
                print(error_msg)
                print(f"Last message content: {last_message}")
                return {
                    **state,
                    "messages": messages + [{"role": "assistant", "content": error_msg}],
                    "agent_responses": state["agent_responses"] + [error_msg],
                }
            except ValueError as e:
                error_msg = f"Invalid agent call: {str(e)}"
                print(error_msg)
                return {
                    **state,
                    "messages": messages + [{"role": "assistant", "content": error_msg}],
                    "agent_responses": state["agent_responses"] + [error_msg],
                }
            except Exception as e:
                error_msg = f"Unexpected error in agent call: {str(e)}"
                print(error_msg)
                return {
                    **state,
                    "messages": messages + [{"role": "assistant", "content": error_msg}],
                    "agent_responses": state["agent_responses"] + [error_msg],
                }

        def finalize(state: AgentState) -> AgentState:
            return state

        workflow = StateGraph(AgentState)
        workflow.add_node("call_agent", call_agent)
        workflow.add_node("decide_next", decide_next_action)
        workflow.add_node("finalize", finalize)

        workflow.set_entry_point("decide_next")
        workflow.add_edge("decide_next", "call_agent")
        workflow.add_conditional_edges("call_agent", lambda s: "decide_next" if s["response"] is None else "finalize")

        return workflow.compile()
    
    def decide_next_step(state: AgentState) -> AgentState:
        """Decide whether to call more agents or finalize the response."""
        messages = state["messages"]
        agent_responses = state["agent_responses"]
        knowledge_base = state["knowledge_base"]

        decision_prompt = f"""
        You have gathered the following agent responses:
        {chr(10).join(agent_responses)}

        Additional Context:
        {json.dumps(knowledge_base, indent=2)}

        Determine if additional agents should be called to enhance this answer.
        Respond ONLY with one of the following JSON objects:
        
        To call another agent:
        {{
        "action": "call_agent",
        "agent": "agent_name",
        "query": "new query"
        }}

        To proceed to final response:
        {{
        "action": "final"
        }}

        """

        full_messages = [
            {"role": "system", "content": self._create_system_prompt()},
            *messages,
            {"role": "user", "content": decision_prompt}
        ]

        llm_decision = self._get_mistral_response(full_messages)

        try:
            parsed = json.loads(llm_decision)
            if parsed.get("action") == "call_agent":
                # Add agent call to messages to be routed again
                return {
                    "messages": messages + [{"role": "assistant", "content": json.dumps(parsed)}],
                    "agent_responses": agent_responses,
                    "current_agent": None,
                    "response": None,
                    "knowledge_base": knowledge_base
                }
        except json.JSONDecodeError:
            pass

        # If decision is to finalize or something went wrong
        return {
            "messages": messages,
            "agent_responses": agent_responses,
            "current_agent": None,
            "response": None,
            "knowledge_base": knowledge_base
        }


    async def get_response(self, user_input: str) -> str:
        initial_state = AgentState(
            messages=[{"role": "user", "content": user_input}],
            agent_responses=[],
            current_agent=None,
            response=None,
            knowledge_base=None
        )
        final_state = await self.graph.ainvoke(initial_state)
        return final_state["response"]

    def clear_history(self):
        self.graph = self._create_graph()

def get_agent_manager():
    return AgentManager()
