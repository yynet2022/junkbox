import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

def main():
    # 1. データの読み込み
    # dataディレクトリ内のファイルを自動判別してロードします
    # (pdf, md, txt, tex, docx などに対応)
    documents = SimpleDirectoryReader("./data").load_data()

    # 2. インデックスの作成
    # 読み込んだデータをベクトル化し、高速に検索できるようにします
    index = VectorStoreIndex.from_documents(documents)

    # 3. チャットエンジンの起動
    # 会話の履歴を保持できるチャットモードで起動します
    chat_engine = index.as_chat_engine(chat_mode="context")

    print("--- LlamaIndex Chatbot 起動 (終了するには 'exit' と入力) ---")
    
    while True:
        user_input = input("ユーザー: ")
        if user_input.lower() in ["exit", "quit", "終了"]:
            break
            
        response = chat_engine.chat(user_input)
        print(f"AI: {response}")

if __name__ == "__main__":
    main()
