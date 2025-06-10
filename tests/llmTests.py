    # Run a test to see if everything working ok
from langchain.prompts import PromptTemplate  #test
from langchain.chains.llm import LLMChain #test

def test_llm(llmModule):
    print(llmModule.invoke("Tell me a joke"))
    prompt = PromptTemplate.from_template("Give {number} names for a {domain} startup?")
    chain = LLMChain(llm=llmModule, prompt=prompt)
    print(chain.invoke({'number': 2, 'domain': 'Medical'}))
    print("-----------------------")