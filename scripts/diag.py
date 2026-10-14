with open(r'D:\1\mypro\daydaydream000.github.io\build.py', 'rb') as f:
    raw = f.read()
i = raw.index(b'def _image(match')
end = raw.index(b'return f', i)
seg = raw[i:end+200]
print(seg.decode('utf-8', errors='replace'))
print('---hex around #---')
pound = raw.find(b'#', i, end)
print(raw[pound:pound+100])
