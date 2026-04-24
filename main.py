import os
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

@tool
def get_current_time() -> str:
    """Returns the current system time. Use this whenever the user asks for the time."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"The current time is {now}."

def main():
    # Initialize the LLM with the specific model and base URL
    # Assuming Ollama is running in Docker and mapped to localhost:11434
    llm = ChatOllama(
        model="gemma4:e4b",
        temperature=0,
        base_url="http://localhost:11434"
    )

    # Bind the tool to the LLM
    tools = [get_current_time]
    llm_with_tools = llm.bind_tools(tools)

    # User query
    query = "Hello! Can you tell me what time it is right now?"
    print(f"User: {query}\n")

    messages = [HumanMessage(content=query)]
    
    # 1. First invocation: LLM decides whether to use a tool
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    # 2. Check for tool calls in the response
    if ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            print(f"[*] LLM requested tool: {tool_call['name']}")
            
            # Execute the tool
            if tool_call["name"] == "get_current_time":
                tool_output = get_current_time.invoke(tool_call["args"])
                print(f"[*] Tool output: {tool_output}")
                
                # Append the tool result to the conversation
                messages.append(ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_call["id"]
                ))

        # 3. Final invocation: LLM generates response based on tool output
        final_response = llm_with_tools.invoke(messages)
        print(f"\nAssistant: {final_response.content}")
    else:
        print(f"\nAssistant: {ai_msg.content}")

if __name__ == "__main__":
    main()
