from rag.chain import ResearchChain

chain = ResearchChain()

while True:
    question = input("\nAsk a question (or type 'exit'): ")

    if question.lower() == "exit":
        break

    answer = chain.ask(question)

    print("\nAnswer:\n")
    print(answer)