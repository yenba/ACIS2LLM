with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

old_func = """    const seededRandom = (i: number) => {
      let h = 0;
      const s = seed + i;
      for (let c = 0; c < s.length; c++) {
        h = ((h << 5) - h + s.charCodeAt(c)) | 0;
      }
      return (h >>> 0) / 4294967296;
    };"""

new_func = """    const seededRandom = (i: number) => {
      let h = 0;
      const s = seed + i;
      for (let c = 0; c < s.length; c++) {
        h = (Math.imul(31, h) + s.charCodeAt(c)) | 0;
      }
      const x = Math.sin(h) * 10000;
      return x - Math.floor(x);
    };"""

text = text.replace(old_func, new_func)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
