import uvicorn

if __name__ == "__main__":
    print("启动Text-to-Speech API服务...")
    print("服务地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    uvicorn.run("amz_service:app", host="0.0.0.0", port=8000)
