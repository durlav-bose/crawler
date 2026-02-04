This keeps everything inside your repo like Node’s node_modules (easy to manage).
poetry config virtualenvs.in-project true

From your crawler folder:
poetry init -n

Now force Poetry to use Python 3.11:
poetry env use /usr/bin/python3.11

Verify:
poetry env info
