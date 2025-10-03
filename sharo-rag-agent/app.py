from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


from rag_chain import build_rag_chain

# Initialize FastAPI app
app = FastAPI(title="Shark Prediction API", version="1.0.0")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    context: list[tuple[str, str]]
    question: str

# Global variable for lazy loading
rag_chain = None

def get_rag_chain():
    global rag_chain
    if rag_chain is None:
        try:
            rag_chain = build_rag_chain()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"RAG chain initialization failed: {str(e)}")
    return rag_chain

@app.post("/ask")
async def ask_question(item: Question):
    try:
        chain = get_rag_chain()
        # Pass question and chat history to a conversational retrieval chain
        result = chain.invoke({
            "question": item.question,
            "chat_history": item.context or []
        })
        return {"response": result.get("answer", result)}
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
