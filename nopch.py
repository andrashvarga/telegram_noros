import re,sys
p=sys.argv[1]
s=open(p,encoding='utf-8').read()
n=0
def fix(m):
    global n
    n+=1
    inc=m.group(1); body=m.group(2) or ''
    return '<ClCompile Include="%s"><PrecompiledHeader>NotUsing</PrecompiledHeader><AdditionalOptions>%%(AdditionalOptions) /Zm2000</AdditionalOptions></ClCompile>'%inc
s=re.sub(r'<ClCompile Include="([^"]*qrc_[^"]*)"\s*(?:/>|>.*?</ClCompile>)',fix,s,flags=re.S)
open(p,'w',encoding='utf-8').write(s)
print('patched',n)
