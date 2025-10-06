
# ターミナルでmakeと打つと実行, ボタンでなんでやねんするためのpython
all:
	python forward_button_to_esp32.py

# espとPCを繋ぐために実行 make proxy
proxy:
	python proxy_to_esp32.py

# htmlなんでやねんのためのサーバーを立てる
ngrok:
	ngrok http 8000