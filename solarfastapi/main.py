import uvicorn

if __name__ == "__main__":
    uvicorn.run("api:app", host="localhost", port=8000, reload=True)

#command : uvicorn api:app --reload
# /docs for docs