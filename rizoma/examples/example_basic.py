# example_basic.py
from rizoma.python.rizoma import start, stop, status

r = start()
print("Статус:", status())
stop()
