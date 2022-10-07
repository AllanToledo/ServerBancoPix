class Result:

    @staticmethod
    def successful(data=None):
        if data is None:
            data = {}
        return {"result": "OK", "data": data}

    @staticmethod
    def error(message: str = "NO MESSAGE"):
        return {"result": "ERROR", "message": message}
