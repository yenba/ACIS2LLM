with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

text = text.replace("{city}", "${city}")

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
