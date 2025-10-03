
all:
	python forward_button_to_esp32.py

proxy:
	python proxy_to_esp32.py

ngrok:
	ngrok http 8000