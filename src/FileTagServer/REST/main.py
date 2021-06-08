from common import rest_api
import uvicorn
import file


@rest_api.get("/")
def index():
    return {"info": "Hi"}


if __name__ == "__main__":
    uvicorn.run(rest_api, host="localhost", port=8000)
