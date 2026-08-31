import json

IS_DEBUG = True

class AppLogger:
    @staticmethod
    def log(caller: str, input_params: dict, expected_action: str, *args):
        if not IS_DEBUG:
            return
        print(f"[DEBUG] [{caller}]")
        print(f"  - Input: {json.dumps(input_params, default=str)}")
        print(f"  - Expected/Next: {expected_action}")
        if args:
            print(f"  - Extra: {args}")

    @staticmethod
    def error(caller: str, error: Exception, context: dict = None):
        print(f"[ERROR] [{caller}] {error}")
        if context:
            print(f"  - Context: {json.dumps(context, default=str)}")
