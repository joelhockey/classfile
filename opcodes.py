import sys
import pprint

def constpool_comment(cf, code, args):
    code = no_comment(cf, code, args) + ' '
    att = cf['05_cp_info'][args[0]]
    tag = att['01_tag']
    if tag == 1: # CONSTANT_Utf8
        code += att['03_bytes']
    elif tag in (5,6): # CONSTANT_Long, CONSTANT_Double
        code += str(att['00_value'])
    elif tag == 7: # CONSTANT_Class
        code += cf['05_cp_info'][att['02_name_index']]['03_bytes']
    elif tag in (9, 10, 11): # CONSTANT_Fieldref, CONSTANT_Methodref, CONSTANT_Interfaceref
        att = cf['05_cp_info'][att['03_name_and_type_index']]
        code += cf['05_cp_info'][att['02_name_index']]['03_bytes'] + cf['05_cp_info'][att['03_descriptor_index']]['03_bytes']
    elif tag == 12: # CONSTANT_NameAndType
        code += cf['05_cp_info'][att['02_name_index']]['03_bytes'] + cf['05_cp_info'][att['03_descriptor_index']]['03_bytes']
    else:
        sys.stderr.write('unrecognised tag for comment %d\n' % tag)
    return code
    
def no_comment(cf, code, args):
    code += ' ' * (30 - len(code)) + '#'
    return code

opcodes = [l.strip().split() for l in """00 nop 0x 0 no_comment
01 aconst_null 0x 0 no_comment
02 iconst_m1 0x 0 no_comment
03 iconst_0 0x 0 no_comment
04 iconst_1 0x 0 no_comment
05 iconst_2 0x 0 no_comment
06 iconst_3 0x 0 no_comment
07 iconst_4 0x 0 no_comment
08 iconst_5 0x 0 no_comment
09 lconst_0 0x 0 no_comment
10 lconst_1 0x 0 no_comment
11 fconst_0 0x 0 no_comment
12 fconst_1 0x 0 no_comment
13 fconst_2 0x 0 no_comment
14 dconst_0 0x 0 no_comment
15 dconst_1 0x 0 no_comment
16 bipush B 1 no_comment
17 sipush >h 2 no_comment
18 ldc B 1 no_comment
19 ldc_w >h 2 constpool_comment
20 ldc2_w >h 2 constpool_comment
21 iload B 1 no_comment
22 lload B 1 no_comment
23 fload B 1 no_comment
24 dload B 1 no_comment
25 aload B 1 no_comment
26 iload_0 0x 0 no_comment
27 iload_1 0x 0 no_comment
28 iload_2 0x 0 no_comment
29 iload_3 0x 0 no_comment
30 lload_0 0x 0 no_comment
31 lload_1 0x 0 no_comment
32 lload_2 0x 0 no_comment
33 lload_3 0x 0 no_comment
34 fload_0 0x 0 no_comment
35 fload_1 0x 0 no_comment
36 fload_2 0x 0 no_comment
37 fload_3 0x 0 no_comment
38 dload_0 0x 0 no_comment
39 dload_1 0x 0 no_comment
40 dload_2 0x 0 no_comment
41 dload_3 0x 0 no_comment
42 aload_0 0x 0 no_comment
43 aload_1 0x 0 no_comment
44 aload_2 0x 0 no_comment
45 aload_3 0x 0 no_comment
46 iaload 0x 0 no_comment
47 laload 0x 0 no_comment
48 faload 0x 0 no_comment
49 daload 0x 0 no_comment
50 aaload 0x 0 no_comment
51 baload 0x 0 no_comment
52 caload 0x 0 no_comment
53 saload 0x 0 no_comment
54 istore B 1 no_comment
55 lstore B 1 no_comment
56 fstore B 1 no_comment
57 dstore B 1 no_comment
58 astore B 1 no_comment
59 istore_0 0x 0 no_comment
60 istore_1 0x 0 no_comment
61 istore_2 0x 0 no_comment
62 istore_3 0x 0 no_comment
63 lstore_0 0x 0 no_comment
64 lstore_1 0x 0 no_comment
65 lstore_2 0x 0 no_comment
66 lstore_3 0x 0 no_comment
67 fstore_0 0x 0 no_comment
68 fstore_1 0x 0 no_comment
69 fstore_2 0x 0 no_comment
70 fstore_3 0x 0 no_comment
71 dstore_0 0x 0 no_comment
72 dstore_1 0x 0 no_comment
73 dstore_2 0x 0 no_comment
74 dstore_3 0x 0 no_comment
75 astore_0 0x 0 no_comment
76 astore_1 0x 0 no_comment
77 astore_2 0x 0 no_comment
78 astore_3 0x 0 no_comment
79 iastore 0x 0 no_comment
80 lastore 0x 0 no_comment
81 fastore 0x 0 no_comment
82 dastore 0x 0 no_comment
83 aastore 0x 0 no_comment
84 bastore 0x 0 no_comment
85 castore 0x 0 no_comment
86 sastore 0x 0 no_comment
87 pop 0x 0 no_comment
88 pop2 0x 0 no_comment
089 dup 0x 0 no_comment
090 dup_x1 0x 0 no_comment
091 dup_x2 0x 0 no_comment
092 dup2 0x 0 no_comment
093 dup2_x1 0x 0 no_comment
094 dup2_x2 0x 0 no_comment
095 swap 0x 0 no_comment
096 iadd 0x 0 no_comment
097 ladd 0x 0 no_comment
098 fadd 0x 0 no_comment
099 dadd 0x 0 no_comment
100 isub 0x 0 no_comment
101 lsub 0x 0 no_comment
102 fsub 0x 0 no_comment
103 dsub 0x 0 no_comment
104 imul 0x 0 no_comment
105 lmul 0x 0 no_comment
106 fmul 0x 0 no_comment
107 dmul 0x 0 no_comment
108 idiv 0x 0 no_comment
109 ldiv 0x 0 no_comment
110 fdiv 0x 0 no_comment
111 ddiv 0x 0 no_comment
112 irem 0x 0 no_comment
113 lrem 0x 0 no_comment
114 frem 0x 0 no_comment
115 drem 0x 0 no_comment
116 ineg 0x 0 no_comment
117 lneg 0x 0 no_comment
118 fneg 0x 0 no_comment
119 dneg 0x 0 no_comment
120 ishl 0x 0 no_comment
121 lshl 0x 0 no_comment
122 ishr 0x 0 no_comment
123 lshr 0x 0 no_comment
124 iushr 0x 0 no_comment
125 lushr 0x 0 no_comment
126 iand 0x 0 no_comment
127 land 0x 0 no_comment
128 ior 0x 0 no_comment
129 lor 0x 0 no_comment
130 ixor 0x 0 no_comment
131 lxor 0x 0 no_comment
132 iinc BB 2 no_comment
133 i2l 0x 0 no_comment
134 i2f 0x 0 no_comment
135 i2d 0x 0 no_comment
136 l2i 0x 0 no_comment
137 l2f 0x 0 no_comment
138 l2d 0x 0 no_comment
139 f2i 0x 0 no_comment
140 f2l 0x 0 no_comment
141 f2d 0x 0 no_comment
142 d2i 0x 0 no_comment
143 d2l 0x 0 no_comment
144 d2f 0x 0 no_comment
145 i2b 0x 0 no_comment
146 i2c 0x 0 no_comment
147 i2s 0x 0 no_comment
148 lcmp 0x 0 no_comment
149 fcmpl 0x 0 no_comment
150 fcmpg 0x 0 no_comment
151 dcmpl 0x 0 no_comment
152 dcmpg 0x 0 no_comment
153 ifeq >h 2 no_comment
154 ifne >h 2 no_comment
155 iflt >h 2 no_comment
156 ifge >h 2 no_comment
157 ifgt >h 2 no_comment
158 ifle >h 2 no_comment
159 if_icmpeq >h 2 no_comment
160 if_icmpne >h 2 no_comment
161 if_icmplt >h 2 no_comment
162 if_icmpge >h 2 no_comment
163 if_icmpgt >h 2 no_comment
164 if_icmple >h 2 no_comment
165 if_acmpeq >h 2 no_comment
166 if_acmpne >h 2 no_comment
167 goto >h 2 no_comment
168 jsr >h 2 no_comment
169 ret B 1 no_comment
170 tableswitch * -1 no_comment
171 lookupswitch * -1 no_comment
172 ireturn 0x 0 no_comment
173 lreturn 0x 0 no_comment
174 freturn 0x 0 no_comment
175 dreturn 0x 0 no_comment
176 areturn 0x 0 no_comment
177 return 0x 0 no_comment
178 getstatic >h 2 constpool_comment
179 putstatic >h 2 constpool_comment
180 getfield >h 2 constpool_comment
181 putfield >h 2 constpool_comment
182 invokevirtual >h 2 constpool_comment
183 invokespecial >h 2 constpool_comment
184 invokestatic >h 2 constpool_comment
185 invokeinterface >hbx 4 no_comment
186 xxxunusedxxx1 0x 0 no_comment
187 new >h 2 constpool_comment
188 newarray B 1 no_comment
189 anewarray >h 2 constpool_comment
190 arraylength 0x 0 no_comment
191 athrow 0x 0 no_comment
192 checkcast >h 2 constpool_comment
193 instanceof >h 2 constpool_comment
194 monitorenter 0x 0 no_comment
195 monitorexit 0x 0 no_comment
196 wide * -1 no_comment
197 multianewarray >hB 3 no_comment
198 ifnull >h 2 no_comment
199 ifnonnull >h 2 no_comment
200 goto_w >i 4 no_comment
201 jsr_w >i 4 no_comment
202 breakpoint 0x 0 no_comment
254 impdep1 0x 0 no_comment
255 impdep2 0x 0 no_comment""".split('\n')]

# code2mnem
# - key code
# - value (mnem, fmt, plen, comment_method)
code2mnem = dict([(int(oc[0]), (oc[1], oc[2], int(oc[3]), eval(oc[4]))) for oc in opcodes])

# mnem2code
# - key mnem
# - value (code, fmt, plen)
mnem2code = dict([(oc[1], (int(oc[0]), oc[2], int(oc[3]))) for oc in opcodes])

