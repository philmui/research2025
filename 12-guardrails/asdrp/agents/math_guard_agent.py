import asyncio
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
    set_tracing_disabled
)
set_tracing_disabled(disabled=True)

class MathHomeworkOutput(BaseModel):
    is_math_homework: bool
    reasoning: str

guardrail_agent = Agent( 
    name="Guardrail check",
    instructions="Check if the user is asking you to do their math homework.",
    output_type=MathHomeworkOutput,
)


@input_guardrail
async def math_guardrail( 
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    if result.final_output.is_math_homework:
        print("\t=> Math guardrail output:", result.final_output)
    
    return GuardrailFunctionOutput(
        output_info=result.final_output, 
        tripwire_triggered=result.final_output.is_math_homework,
    )


agent = Agent(  
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    input_guardrails=[math_guardrail],
)

async def main():
    user_input = input("\nEnter your request (or press Enter to exit): ")
    while user_input != "":
        try:
            result = await Runner.run(agent, user_input)
            print("(Guardrail didn't trip)")
            print(result.final_output)
        except InputGuardrailTripwireTriggered:
            print("Math homework guardrail tripped")
        user_input = input("Enter your request (or press Enter to exit): ")
        
if __name__ == "__main__":
    asyncio.run(main())