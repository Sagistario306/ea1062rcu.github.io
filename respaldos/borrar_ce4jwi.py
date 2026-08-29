import json

with open('datos/ceremonias.json') as f:
    reg = json.load(f)

if 'CE4JWI' in reg:
    del reg['CE4JWI']
    print('✅ CE4JWI eliminado del libro')
else:
    print('CE4JWI no estaba en el libro')

with open('datos/ceremonias.json', 'w', encoding='utf-8') as f:
    json.dump(reg, f, ensure_ascii=False, indent=1)