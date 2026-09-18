from fastapi import FastAPI

app = FastAPI(title="Generic Hackathon Starter")


@app.get("/", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
