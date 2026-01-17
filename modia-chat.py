from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from typing import List, Dict

MAX_MEMORY = 6
memory: List[Dict[str, str]] = []

SYSTEM_PROMPT = """
You are an expert assistant on the HytaleServer internal codebase. Your name is Modia. You act as a technical co-pilot for mod development.

ABSOLUTE RULES:
Respond ONLY with the final output for the user.
DO NOT reveal history, context, or internal reasoning.
DO NOT repeat or describe the provided context.
DO NOT use titles, sections, or headers.
DO NOT explain what information is available to you.
DO NOT use qualifiers like "according to the context" or similar phrases.

BEHAVIOR:
Provide an answer even if the information is partial.
If specific details are not explicit, infer them using common game engine patterns.
If a feature does not exist, state it clearly and explain the actual technical alternative.
Use technical, direct, and concise language.
Maintain a modding-oriented focus.
EXPLANATION MODE: If the user asks to explain or understand a concept, respond with greater detail, but ALWAYS without revealing context, history, or internal structure.
"""

def should_store(text: str) -> bool:
    if not text or len(text) < 40:
        return False

    keywords = [
        "entity", "entidad", "trigger", "evento", "api","event",
        "server", "engine", "lifecycle", "mod", "hook"
    ]
    t = text.lower()
    return any(k in t for k in keywords)


def format_memory(mem: List[Dict[str, str]]) -> str:
    if not mem:
        return ""

    return "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in mem
    )


def is_explain_mode(question: str) -> bool:
    triggers = [
        "explicame",
        "explica",
        "no entiendo",
        "qué hace",
        "que hace",
        "para qué sirve",
        "como funciona",
        "cómo funciona",
        "ayudame a entender",
        "ayuda con este método",
        "ayuda con esta clase",
        "explain",
        "explain to me",
        "I don't understand",
        "what does this do",
        "what does it do",
        "what is this for",
        "what is the purpose",
        "how does it work",
        "how does this work",
        "help me understand",
        "help with this method",
        "help with this class"
    ]
    q = question.lower()
    return any(t in q for t in triggers)

def build_prompt(question: str) -> str:
    if is_explain_mode(question):
        return SYSTEM_PROMPT + """

ACTIVE EXPLANATION MODE:

Explain the purpose of the code.
Indicate when it is executed.
Explain interactions with other systems.
Clarify its relevance to mod development.
"""
    return SYSTEM_PROMPT


def normalize_llm_output(resp) -> str:
    content = resp.content

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        return "\n".join(parts).strip()

    return str(content).strip()


embeddings = OllamaEmbeddings(model="nomic-embed-text")
db = Chroma(
    persist_directory="./hytale_db",
    embedding_function=embeddings
)

llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0.1
)

print("----------------- MODIA MODE -----------------------\n")

while True:
    q = input("> ")
    if q.lower() == "exit":
        break

    docs = db.similarity_search(q, k=5)
    context = "\n\n".join(d.page_content for d in docs)

    memory_block = format_memory(memory)

    prompt = f"""{SYSTEM_PROMPT}

--- RECENT HISTORY ---
{memory_block}

--- TECHNICAL CONTEXT ---
{context}

--- QUESTION ---
{q}
"""


    response = llm.invoke(prompt)
    answer = normalize_llm_output(response)

    print(answer, "\n")

    if should_store(q):
        memory.append({"role": "user", "content": q})

    if should_store(answer):
        memory.append({"role": "assistant", "content": answer})

    memory = memory[-MAX_MEMORY:]

    if len(memory) >= MAX_MEMORY:
        summary_prompt = f"""
        Generate a 5-point technical summary of the current history, 
        strictly related to Hytale Server and modding. 
        {format_memory(memory)}
    """
        
        summary_resp = llm.invoke(summary_prompt)
        summary_text = normalize_llm_output(summary_resp)

        memory = [{
            "role": "system",
            "content": summary_text
        }]
