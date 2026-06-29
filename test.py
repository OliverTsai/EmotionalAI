from ai.ollama_client import ask_llm


def main():
    print("AI 測試開始（輸入 exit 離開）")

    while True:
        user_input = input("你：")

        if user_input.lower() == "exit":
            break

        reply = ask_llm(user_input)
        print("AI：", reply)


if __name__ == "__main__":
    main()