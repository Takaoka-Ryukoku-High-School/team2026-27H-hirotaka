# ストップウォッチと文字起こし

Python と Flet で作ったブラウザーアプリです。ストップウォッチの記録・平均・グラフ、マイク録音、日本語文字起こし、OpenAI/ChatGPT APIによる文章要約を使えます。

## 起動方法

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"
python main.py
```

`OPENAI_API_KEY` はサーバー側でのみ使われ、ブラウザーへは送信されません。キーを設定すると、録音停止後に音声を OpenAI の文字起こし API で処理し、AI 要約も利用できます。

利用モデルは `OPENAI_MODEL` で要約用を変更でき、既定値は `gpt-4o-mini` です。文字起こし用は `OPENAI_TRANSCRIBE_MODEL` を指定でき、既定値は `whisper-1` です。

既定ポート8000が使用中なら `PORT=8001 python main.py` のように別のポートを指定してください。