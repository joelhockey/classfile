#!/bin/python
import sys
import binascii
import struct
import pprint
import opcodes

def addLineNums(codeatt, linenumatt):
    pc2ln = {}
    for lnt in linenumatt['04_line_number_table']:
        pc2ln[lnt['01_start_pc']] = '%4d' % lnt['02_line_number']
    
    codes = []
    for line in codeatt['06_code']:
        pc, ln, code = line.split(':')
        ln = pc2ln.get(int(pc), ln)
        codes.append('%s:%s:%s' % (pc, ln, code)) # replace '?:' with linenum
    codeatt['06_code'] = codes

def parseAttribute(att, info, cf):
    if att['00_attribute_name'] == 'Code': #Code
        att['03_max_stack'] = struct.unpack('>h', info[:2])[0]
        att['04_max_locals'] = struct.unpack('>h', info[2:4])[0]
        att['05_code_length'] = struct.unpack('>i', info[4:8])[0]
        att['06_code'] = []
        i = 8
        while i < 8 + att['05_code_length']:
            opsize = 0
            mnem, fmt, plen, add_comment = opcodes.code2mnem[ord(info[i])]
            opsize += 1
            if mnem == 'lookupswitch':
                while (i + opsize) % 4 != 0: opsize += 1 # skip to 4-byte boundary
                args = struct.unpack('>2i', info[i+opsize:i+opsize+8])
                # now get pairs
                args += struct.unpack('>%di' % (args[1]*2), info[i+opsize+8:i+opsize+8+(args[1]*8)])
                opsize += 8 + (args[1] * 8)
            elif mnem == 'tableswitch':
                while (i + opsize) % 4 != 0: opsize += 1 # skip to 4-byte boundary
                args = struct.unpack('>3i', info[i+opsize:i+opsize+12])
                offsets = args[2] - args[1] + 1
                args += struct.unpack('>%di' % offsets, info[i+opsize+12:i+opsize+12+(offsets*4)])
                opsize += 12 + (offsets*4)
            elif mnem == 'wide':
                args = struct.unpack('>Bh', info[i+1:i+4])
                opsize += 3
                if opcodes.code2mnem[args[0]][0] == 'iinc':
                    args += struct.unpack('>h', info[i+4:i+6])
                    opsize += 2
            else:
                args = struct.unpack(fmt, info[i+1:i+1+plen])
                opsize += plen
            code = '%4d:     ?:%s' % (i-8, mnem)
            for arg in args:
                code += ' ' + str(arg)
            att['06_code'].append(add_comment(cf, code, args))
            i += opsize
        
        att['07_exception_table_length'] = struct.unpack('>h', info[i:i+2])[0]
        i += 2
        att['08_exception_table'] = []
        for x in range(att['07_exception_table_length']):
            et = {}
            et['01_start_pc'] = struct.unpack('>h', info[i:i+2])[0]
            et['02_end_pc'] = struct.unpack('>h', info[i+2:i+4])[0]
            et['03_handler_pc'] = struct.unpack('>h', info[i+4:i+6])[0]
            et['04_catch_type'] = struct.unpack('>h', info[i+6:i+8])[0]
            i += 8
            att['08_exception_table'].append(et)
        att['09_attributes_count'] = struct.unpack('>h', info[i:i+2])[0]
        i += 2
        att['10_attribute_info'] = []
        
        for x in range(att['09_attributes_count']):
            attai = {}
            attai['01_attribute_name_index'] = struct.unpack('>h', info[i:i+2])[0]
            attai['00_attribute_name'] = cf['05_cp_info'][attai['01_attribute_name_index']]['03_bytes']
            attai['02_attribute_length'] = struct.unpack('>i', info[i+2:i+6])[0]
            parseAttribute(attai, struct.unpack('%ds' % attai['02_attribute_length'], info[i+6:i+6+attai['02_attribute_length']])[0], cf)
            i += 6+attai['02_attribute_length']
            att['10_attribute_info'].append(attai)
            if attai['00_attribute_name'] == 'LineNumberTable':
                addLineNums(att, attai)
    elif att['00_attribute_name'] == 'LineNumberTable': # LineNumberTable
        att['03_line_number_table_length'] = struct.unpack('>h', info[:2])[0]
        i = 2
        att['04_line_number_table'] = []
        for x in range(att['03_line_number_table_length']):
            lnt = {}
            lnt['01_start_pc'] = struct.unpack('>h', info[i:i+2])[0]
            lnt['02_line_number'] = struct.unpack('>h', info[i+2:i+4])[0]
            i += 4
            att['04_line_number_table'].append(lnt)
    elif att['00_attribute_name'] == 'LocalVariableTable': # LocalVariableTable
        att['03_local_variable_table_length'] = struct.unpack('>h', info[:2])[0]
        i = 2
        att['04_local_variable_table'] = []
        for x in range(att['03_local_variable_table_length']):
            lvt = {}
            lvt['01_start_pc'] = struct.unpack('>h', info[i:i+2])[0]
            lvt['02_length'] = struct.unpack('>h', info[i+2:i+4])[0]
            lvt['03_name_index'] = struct.unpack('>h', info[i+4:i+6])[0]
            lvt['04_descriptor_index'] = struct.unpack('>h', info[i+6:i+8])[0]
            lvt['05_index'] = struct.unpack('>h', info[i+8:i+10])[0]
            lvt['00_name'] = cf['05_cp_info'][lvt['04_descriptor_index']]['03_bytes'] + ' ' + cf['05_cp_info'][lvt['03_name_index']]['03_bytes']
            i += 10
            att['04_local_variable_table'].append(lvt)
    elif att['00_attribute_name'] == 'Exceptions': # Exceptions
        att['03_number_of_exceptions'] = struct.unpack('>h', info[:2])[0]
        i = 2
        att['04_exception_index_table'] = []
        for x in range(att['03_number_of_exceptions']):
            eit = {}
            eit['01_exception_index'] = struct.unpack('>h', info[i:i+2])[0]
            eit['00_exception_name'] = cf['05_cp_info'][cf['05_cp_info'][eit['01_exception_index']]['02_name_index']]['03_bytes']
            i += 2
            att['04_exception_index_table'].append(eit)
    elif att['00_attribute_name'] == 'ConstantValue': # ConstantValue
        att['01_constantvalue_index'] = struct.unpack('>h', info[:2])[0]
        att['00_attribute_value'] = cf['05_cp_info'][att['01_constantvalue_index']]['00_value']
    elif att['00_attribute_name'] == 'SourceFile': # SourceFile
        att['03_sourcefile_index'] = struct.unpack('>h', info[:2])[0]
        att['00_sourcefile'] = cf['05_cp_info'][att['03_sourcefile_index']]['03_bytes']
    elif att['00_attribute_name'] == 'Deprecated': # Deprecated - nothing to do
        pass
    elif att['00_attribute_name'] == 'RuntimeVisibleAnnotations': # RuntimeVisibleAnnotations
        att['03_info'] = info
        att['03_runtimevisibleannotations_num'] = struct.unpack('>h', info[:2])[0]
        i = 2
        att['04_runtimevisibleannotations_table'] = []
        for x in range(att['03_runtimevisibleannotations_num']):
            an = {}
            i += parseAnnotation(an, info[i:], cf)
            att['04_runtimevisibleannotations_table'].append(an)
    else:
        print '#unhandled attribute', att['00_attribute_name']
        att['03_info'] = info

def parseAnnotation(an, info, cf):
    an['01_type_index'] = struct.unpack('>h', info[:2])[0]
    an['00_type'] = cf['05_cp_info'][an['01_type_index']]['03_bytes']
    an['02_num_element_value_pairs'] = struct.unpack('>h', info[2:4])[0]
    an['03_element_value_pairs'] = []
    i = 4
    for x in range(an['02_num_element_value_pairs']):
        el = {}
        el['01_element_name_index'] = struct.unpack('>h', info[i:i+2])[0]
        el['00_name'] = cf['05_cp_info'][el['01_element_name_index']]['03_bytes']
        el['02_tag'] = info[i+2]
        el['03_element_value'] = {}
        i += 2 + parseElementValue(el['03_element_value'], info[i+2:], cf)
        an['03_element_value_pairs'].append(el)
    return i

def parseElementValue(ev, info, cf):
        ev['01_tag'] = info[0]
        if ev['01_tag'] in 'BCDFIJSZs':
            ev['02_element_value_index'] = struct.unpack('>h', info[1:3])[0]
            ev['02_element_value'] = cf['05_cp_info'][ev['02_element_value_index']]['03_bytes']
            return 3
        elif ev['01_tag'] == 'e':
            ev['02_type_name_index'] = struct.unpack('>h', info[:2])[0]
            ev['02_type_name'] = cf['05_cp_info'][ev['02_type_name_index']]['03_bytes']
            ev['02_const_name_index'] = struct.unpack('>h', info[2:4])[0]
            ev['02_const_name'] = cf['05_cp_info'][ev['02_const_name_index']]['03_bytes']
            return 5
        elif ev['01_tag'] == 'c':
            ev['02_class_info_index'] = struct.unpack('>h', info[:2])[0]
            ev['02_class_info'] = cf['05_cp_info'][ev['02_class_info_index']]['03_bytes']
            return 3
        elif ev['01_tag'] == '@':
            ev['02_annotation'] = {}
            i += parseAnnotation(el['02_annotation'], info[1:], cf)
        elif ev['02_tag'] == '[':
            ev['02_num_values'] = struct.unpack('>h', info[1:3])[0]
            ev['03_values'] = []
            i += 3
            for x in range():
                ev2 = {}
                i += parseElementValue(ev2, info[3:], cf)
                ev['03_values'].append(ev2)
            return i
        else:
            raise '#unknown element and value tag %s' % el['02_tag']
    
def writeAttribute(att, linenum_cp_index=None):
    result = ''
    if att['00_attribute_name'] == 'Code': # Code
        result += struct.pack('>h', att['03_max_stack'])
        result += struct.pack('>h', att['04_max_locals'])
        code = writeCode(att, linenum_cp_index)
        result += struct.pack('>i', len(code))
        result += code
        result += struct.pack('>h', att['07_exception_table_length'])
        for et in att['08_exception_table']:
            result += struct.pack('>h', et['01_start_pc'])
            result += struct.pack('>h', et['02_end_pc'])
            result += struct.pack('>h', et['03_handler_pc'])
            result += struct.pack('>h', et['04_catch_type'])
        result += struct.pack('>h', len(att['10_attribute_info']))
        
        for attai in att['10_attribute_info']:
            result += writeAttribute(attai, linenum_cp_index)
    elif att['00_attribute_name'] == 'LineNumberTable': # LineNumberTable
        result += struct.pack('>h', len(att['04_line_number_table']))
        for lnt in att['04_line_number_table']:
            result += struct.pack('>h', lnt['01_start_pc'])
            result += struct.pack('>h', lnt['02_line_number'])
    elif att['00_attribute_name'] == 'LocalVariableTable': # LocalVariableTable
        result += struct.pack('>h', len(att['04_local_variable_table']))
        for lvt in att['04_local_variable_table']:
            result += struct.pack('>h', lvt['01_start_pc'])
            result += struct.pack('>h', lvt['02_length'])
            result += struct.pack('>h', lvt['03_name_index'])
            result += struct.pack('>h', lvt['04_descriptor_index'])
            result += struct.pack('>h', lvt['05_index'])
    elif att['00_attribute_name'] == 'Exceptions': # Exceptions
        result += struct.pack('>h', att['03_number_of_exceptions'])
        for eit in att['04_exception_index_table']:
            result += struct.pack('>h', eit['01_exception_index'])
    elif att['00_attribute_name'] == 'ConstantValue': # ConstantValue
        result += struct.pack('>h', att['01_constantvalue_index'])
    elif att['00_attribute_name'] == 'SourceFile': # SourceFile
        result += struct.pack('>h', att['03_sourcefile_index'])
    else:
        result += att['03_info']
    return struct.pack('>h', att['01_attribute_name_index']) + struct.pack('>i', len(result)) + result
        
def writeCode(code_att, linenum_cp_index):
    bytecodes = ''
    line_number_table = []
    last_ln = '?'
    for pc_ln_code in code_att['06_code']:
        if pc_ln_code.find('#') != -1 : pc_ln_code = pc_ln_code[:pc_ln_code.find('#')] # strip comment if exists
        pc, ln, code = [s.strip() for s in pc_ln_code.split(':')]
        if ln != '?' and ln != last_ln:
            line_number_table.append({'01_start_pc' : len(bytecodes), '02_line_number' : int(ln)})
            last_ln = ln
        ocparams = code.split()
        opcode, fmt, _ = opcodes.mnem2code[ocparams[0]]
        args = [int(ocparam) for ocparam in ocparams[1:]]
        bytecodes += struct.pack('B', opcode)
        if ocparams[0] in 'lookupswitch tableswitch'.split():
            while len(bytecodes) % 4 != 0: bytecodes += '\x00' # align to 4-byte boundary
            fmt = '>%di' % len(args)
        elif ocparams[0] == 'wide':
            if opcodes.code2mnem[args[0]][0] == 'iinc':
                fmt = '>Bhh'
            else:
                fmt = '>Bh'
        bytecodes += struct.pack(fmt, *args)

    # replace LineNumberTable if line nums included in bytecode
    if len(line_number_table) > 0 and linenum_cp_index is not None:
        lntatt = {'00_attribute_name' : 'LineNumberTable',
                            '01_attribute_name_index' : linenum_cp_index,
                            '02_attribute_length' : 2 + 4*len(line_number_table),
                            '03_line_number_table_length' : len(line_number_table),
                            '04_line_number_table' : line_number_table}
        
        code_att['10_attribute_info'].append(lntatt) # put it on end in case it doesn't exist yet
        for i, attai in enumerate(code_att['10_attribute_info'][:-1]):
            # if it exists, replace it and remove from end
            if attai['00_attribute_name'] == 'LineNumberTable':
                code_att['10_attribute_info'][i] = lntatt
                code_att['10_attribute_info'].pop()
                break
    return bytecodes

def decompile(f):
    i = 0
    if binascii.a2b_hex('cafebabe') != f[:4]:
        print 'error, classfile %s does not start with "cafebabe"' % sys.argv[1]
        sys.exit(1)

    cf = {}
    cf['01_magic'] = 'cafebabe'
    cf['02_minor_version'] = struct.unpack('>h', f[4:6])[0]
    cf['03_major_version'] = struct.unpack('>h', f[6:8])[0]
    cf['04_constant_pool_count'] = struct.unpack('>h', f[8:10])[0]
    i = 10
    # put unused attribute at start to get numbering working
    cf['05_cp_info'] = [{'00_index' : 0, '00_tag_name' : 'unusable at start to get numbering working', '01_tag' : 0}]
    x = 1
    while x < cf['04_constant_pool_count']:
        tag = ord(f[i])
        result = {'00_index' : x, '01_tag' : ord(f[i])}
        if tag == 1: # CONSTANT_Utf8
            result['00_tag_name'] = 'CONSTANT_Utf8'
            length = struct.unpack('>h', f[i+1:i+3])[0]
            result['02_length'] = length
            result['03_bytes'] = struct.unpack('%ds' % length, f[i+3:i+3+length])[0]
            i += 3 + length
        elif tag == 3: # CONSTANT_Integer
            result['00_tag_name'] = 'CONSTANT_Integer'
            result['02_bytes'] = struct.unpack('>i', f[i+1:i+5])[0]
            result['00_value'] = result['02_bytes']
            i += 5
        elif tag == 4: # CONSTANT_Float
            result['00_tag_name'] = 'CONSTANT_Float'
            result['02_bytes'] = struct.unpack('f', f[i+1:i+5])[0]
            result['00_value'] = result['02_bytes']
            i += 5
        elif tag in (5,6): # CONSTANT_Long, CONSTANT_Double
            if tag == 5:
                result['00_tag_name'] = 'CONSTANT_Long'
                result['00_value'] = struct.unpack('>q', f[i+1:i+9])[0]
            else:
                result['00_tag_name'] = 'CONSTANT_Double'
                result['00_value'] = struct.unpack('d', f[i+1:i+9])[0]
            result['02_high_bytes'] = struct.unpack('>i', f[i+1:i+5])[0]
            result['03_low_bytes'] = struct.unpack('>i', f[i+5:i+9])[0]
            i += 9
            # now add extra unusable entry in table
            cf['05_cp_info'].append(result)
            x += 1
            result = {'00_index' : x, '00_tag_name' : 'unusable after Long/Double', '01_tag' : 0}
        elif tag == 7: # CONSTANT_Class
            result['00_tag_name'] = 'CONSTANT_Class'
            result['02_name_index'] = struct.unpack('>h', f[i+1:i+3])[0]
            i += 3
        elif tag == 8: # CONSTANT_String
            result['00_tag_name'] = 'CONSTANT_String'
            result['02_string_index'] = struct.unpack('>h', f[i+1:i+3])[0]
            i += 3
        elif tag in (9, 10, 11): # CONSTANT_Fieldref, CONSTANT_Methodref, CONSTANT_Interfaceref
            if tag == 9:
                result['00_tag_name'] = 'CONSTANT_Fieldref'
            elif tag == 10:
                result['00_tag_name'] = 'CONSTANT_Methodref'
            else:                
                result['00_tag_name'] = 'CONSTANT_Interfaceref'
            result['02_class_index'] = struct.unpack('>h', f[i+1:i+3])[0]
            result['03_name_and_type_index'] = struct.unpack('>h', f[i+3:i+5])[0]
            i += 5
        elif tag == 12: # CONSTANT_NameAndType 
            result['00_tag_name'] = 'CONSTANT_NameAndType'
            result['02_name_index'] = struct.unpack('>h', f[i+1:i+3])[0]
            result['03_descriptor_index'] = struct.unpack('>h', f[i+3:i+5])[0]
            i += 5
        else:
            sys.stderr.write('error, unrecognised constant pool tag %d\n' % tag)
            pprint.PrettyPrinter().pprint(cf)
            sys.exit(1)
        cf['05_cp_info'].append(result)
        x += 1

    # set '00_value' for CONSTANT_String    
    for cp in cf['05_cp_info']:
        if cp['00_tag_name'] == 'CONSTANT_String': cp['00_value'] = cf['05_cp_info'][cp['02_string_index']]['03_bytes']
        
    cf['06_access_flags'] = struct.unpack('>h', f[i:i+2])[0]
    i += 2
    cf['07_this_class'] = struct.unpack('>h', f[i:i+2])[0]
    i += 2
    cf['08_super_class'] = struct.unpack('>h', f[i:i+2])[0]
    i += 2
    cf['09_interfaces_count'] = struct.unpack('>h', f[i:i+2])[0]
    i += 2
    cf['10_interfaces'] = struct.unpack('>%dh' % cf['09_interfaces_count'], f[i:i+2*cf['09_interfaces_count']])
    i += 2*cf['09_interfaces_count']
    cf['11_fields_count'] = struct.unpack('>h', f[i:i+2])[0]
    i += 2
    cf['12_field_info'] = []
    for x in range(cf['11_fields_count']):
        field = {}
        field['01_access_flags'] = struct.unpack('>h', f[i:i+2])[0]
        field['02_name_index'] = struct.unpack('>h', f[i+2:i+4])[0]
        field['00_field_name'] = cf['05_cp_info'][field['02_name_index']]['03_bytes']
        field['03_descriptor_index'] = struct.unpack('>h', f[i+4:i+6])[0]
        field['04_attributes_count'] = struct.unpack('>h', f[i+6:i+8])[0]
        field['05_attribute_info'] = []
        i += 8
        for y in range(field['04_attributes_count']):
            ai = {}
            ai['01_attribute_name_index'] = struct.unpack('>h', f[i:i+2])[0]
            ai['00_attribute_name'] = cf['05_cp_info'][ai['01_attribute_name_index']]['03_bytes']
            ai['02_attribute_length'] = struct.unpack('>i', f[i+2:i+6])[0]
            parseAttribute(ai, struct.unpack('%ds' % ai['02_attribute_length'], f[i+6:i+6+ai['02_attribute_length']])[0], cf)
            i += 6+ai['02_attribute_length']
            field['05_attribute_info'].append(ai)
        cf['12_field_info'].append(field)
    cf['13_methods_count'] = struct.unpack('>h', f[i:i+2])[0]
    i += 2
    cf['14_method_info'] = []
    for x in range(cf['13_methods_count']):
        method = {}
        method['01_access_flags'] = struct.unpack('>h', f[i:i+2])[0]
        method['02_name_index'] = struct.unpack('>h', f[i+2:i+4])[0]
        method['03_descriptor_index'] = struct.unpack('>h', f[i+4:i+6])[0]
        method['00_method_name'] = cf['05_cp_info'][method['02_name_index']]['03_bytes'] + cf['05_cp_info'][method['03_descriptor_index']]['03_bytes']
        method['04_attributes_count'] = struct.unpack('>h', f[i+6:i+8])[0]
        method['05_attribute_info'] = []
        i += 8
        for y in range(method['04_attributes_count']):
            ai = {}
            ai['01_attribute_name_index'] = struct.unpack('>h', f[i:i+2])[0]
            ai['00_attribute_name'] = cf['05_cp_info'][ai['01_attribute_name_index']]['03_bytes']
            ai['02_attribute_length'] = struct.unpack('>i', f[i+2:i+6])[0]
            parseAttribute(ai, struct.unpack('%ds' % ai['02_attribute_length'], f[i+6:i+6+ai['02_attribute_length']])[0], cf)
            i += 6+ai['02_attribute_length']
            method['05_attribute_info'].append(ai)
        cf['14_method_info'].append(method)
    cf['15_attributes_count'] = struct.unpack('>h', f[i:i+2])[0]
    i += 2
    cf['16_attribute_info'] = []
    for y in range(cf['15_attributes_count']):
        ai = {}
        ai['01_attribute_name_index'] = struct.unpack('>h', f[i:i+2])[0]
        ai['00_attribute_name'] = cf['05_cp_info'][ai['01_attribute_name_index']]['03_bytes']
        ai['02_attribute_length'] = struct.unpack('>i', f[i+2:i+6])[0]
        parseAttribute(ai, struct.unpack('>%ds' % ai['02_attribute_length'], f[i+6:i+6+ai['02_attribute_length']])[0], cf)
        i += 6+ai['02_attribute_length']
        cf['16_attribute_info'].append(ai)

    if i != len(f):
        sys.stderr.write('error, extra bytes at end of file [%s]\n' % binascii.b2a_hex(f[i:]))
        pprint.PrettyPrinter().pprint(cf)
        sys.exit(1)
    return cf

def compile(cf, outfile):
    linenum_cp_index = None
    f = open(outfile, 'wb')
    f.write(binascii.a2b_hex('cafebabe'))
    f.write(struct.pack('>h', cf['02_minor_version']))
    f.write(struct.pack('>h', cf['03_major_version']))
    f.write(struct.pack('>h', cf['04_constant_pool_count']))
    for cp_info in cf['05_cp_info']:
        if cp_info['01_tag'] == 0: continue # ignore 0 tag.    It is unusable at start or after Long/Double
        f.write(struct.pack('>c', chr(cp_info['01_tag'])))
        if cp_info['01_tag'] == 1: # CONSTANT_Utf8
            f.write(struct.pack('>h', len(cp_info['03_bytes'])))
            f.write(cp_info['03_bytes'])
            if cp_info['03_bytes'] == 'LineNumberTable': linenum_cp_index = cp_info['00_index']
        elif cp_info['01_tag'] == 3: # CONSTANT_Integer
            f.write(struct.pack('>i', cp_info['02_bytes']))
        elif cp_info['01_tag'] == 4: # CONSTANT_Float
            f.write(struct.pack('f', cp_info['02_bytes']))
        elif cp_info['01_tag'] in (5,6): # CONSTANT_Long, CONSTANT_Double
            f.write(struct.pack('>i', cp_info['02_high_bytes']))
            f.write(struct.pack('>i', cp_info['03_low_bytes']))
        elif cp_info['01_tag'] == 7: # CONSTANT_Class
            f.write(struct.pack('>h', cp_info['02_name_index']))
        elif cp_info['01_tag'] == 8: # CONSTANT_String
            f.write(struct.pack('>h', cp_info['02_string_index']))
        elif cp_info['01_tag'] in (9, 10, 11): # CONSTANT_Fieldref, CONSTANT_Methodref, CONSTANT_Interfaceref
            f.write(struct.pack('>h', cp_info['02_class_index']))
            f.write(struct.pack('>h', cp_info['03_name_and_type_index']))
        elif cp_info['01_tag'] == 12: # CONSTANT_NameAndType 
            f.write(struct.pack('>h', cp_info['02_name_index']))
            f.write(struct.pack('>h', cp_info['03_descriptor_index']))
        else:
            sys.stderr.write('error, unrecognised constant pool tag %d\n' % cp_info['01_tag'])
            pprint.PrettyPrinter().pprint(cf)
    f.write(struct.pack('>h', cf['06_access_flags']))
    f.write(struct.pack('>h', cf['07_this_class']))
    f.write(struct.pack('>h', cf['08_super_class']))
    f.write(struct.pack('>h', len(cf['10_interfaces'])))
    for interface in cf['10_interfaces']:
        f.write(struct.pack('>h', interface))
    f.write(struct.pack('>h', len(cf['12_field_info'])))
    for field in cf['12_field_info']:
        f.write(struct.pack('>h', field['01_access_flags']))
        f.write(struct.pack('>h', field['02_name_index']))
        f.write(struct.pack('>h', field['03_descriptor_index']))
        f.write(struct.pack('>h', len(field['05_attribute_info'])))
        for ai in field['05_attribute_info']:
            f.write(writeAttribute(ai))
    f.write(struct.pack('>h', len(cf['14_method_info'])))

    for method in cf['14_method_info']:
        f.write(struct.pack('>h', method['01_access_flags']))
        f.write(struct.pack('>h', method['02_name_index']))
        f.write(struct.pack('>h', method['03_descriptor_index']))
        f.write(struct.pack('>h', len(method['05_attribute_info'])))
        for ai in method['05_attribute_info']:
            f.write(writeAttribute(ai, linenum_cp_index))
    f.write(struct.pack('>h', len(cf['16_attribute_info'])))
    for ai in cf['16_attribute_info']:
        f.write(writeAttribute(ai))

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '-d':
        pprint.PrettyPrinter().pprint(decompile(open(sys.argv[2], 'rb').read()))
    elif len(sys.argv) == 4 and sys.argv[1] == '-c':
        compile(eval(open(sys.argv[2]).read()), sys.argv[3])
    else:
        print 'usage:\n classfile.py -d <classfile>\n classfile.py -c <pyobjfile> <classfile>'
        sys.exit(1)

