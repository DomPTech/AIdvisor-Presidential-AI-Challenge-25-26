
class PymatgenAgentExecutor:
    def __init__(self, agent_runnable, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.chat_history = []
        self.agent = agent_runnable

    def invoke(self, input: str) -> dict:
        count = 0
        agent_scratchpad = []

        while count < self.max_iterations:
            tool_call = self.agent.invoke({
                "input": input,
                "chat_history": self.chat_history,
                "agent_scratchpad": agent_scratchpad
            })
            agent_scratchpad.append(tool_call)

            if tool_call.tool_calls:
                for tool_call_obj in tool_call.tool_calls:
                    tool_name = tool_call_obj["name"]
                    tool_args = tool_call_obj["args"]
                    tool_call_id = tool_call_obj["id"]

                    tool_out = pymatgen_name2tool[tool_name](**tool_args)
                    tool_exec = ToolMessage(content=f"{tool_out}", tool_call_id=tool_call_id)
                    agent_scratchpad.append(tool_exec)

                    ai_msg = AIMessage(content=tool_out)
                    agent_scratchpad.append(ai_msg)
                    final_answer = ai_msg.content

                count += 1
                if not tool_call.tool_calls or any(isinstance(step, AIMessage) for step in agent_scratchpad):
                    final_answer = next(
                        (step.content for step in reversed(agent_scratchpad) if isinstance(step, AIMessage)),
                        "No final answer generated."
                    )
                    break
            else:
                final_answer = tool_call.content
                break

        self.chat_history.extend([
            HumanMessage(content=input),
            AIMessage(content=final_answer)
        ])
        return {"output": final_answer}