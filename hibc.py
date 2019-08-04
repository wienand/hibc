import datetime

checksum_lookup = dict(zip('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%', range(43)))
checksum_letter_lookup = dict(zip(range(43), '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%'))


def get_check_character(barcode):
    barcode = barcode.upper()
    try:
        return checksum_letter_lookup[sum([checksum_lookup[x] for x in barcode]) % 43]
    except KeyError:
        return None


def generate(ref, lic='XXXX', unit_of_measure=0, **kwargs):
    unit_of_measure = str(unit_of_measure)
    lic = 'X' * max(4 - len(lic), 0) + lic[:4]
    if not unit_of_measure:
        unit_of_measure = '0'
    unit_of_measure = unit_of_measure[0:1]
    barcode = '+%s%s%s' % (lic, ref, unit_of_measure)
    secondary_code = ''
    if 'quantity' in kwargs:
        quantity = str(kwargs['quantity'])
        if len(quantity) < 3:
            secondary_code += '8' + quantity.zfill(2)
        else:
            secondary_code += '9' + quantity[:5].zfill(5)
    if 'expiry date' in kwargs:
        expiry_date = kwargs['expiry date']
        if not hasattr(expiry_date, 'hour') or expiry_date.hour == 0:
            secondary_code += '3' + expiry_date.strftime('%y%m%d')
        else:
            secondary_code += '4' + expiry_date.strftime('%y%m%d%H')
    else:
        secondary_code += '7'
    lot_number = kwargs.get('lot number', '')
    serial_number = kwargs.get('serial number', '')
    if lot_number:
        secondary_code = '/$$' + secondary_code + lot_number
    elif serial_number and 'quantity' not in kwargs:
        secondary_code = '/$$+' + secondary_code + serial_number
    else:
        secondary_code = '/$$' + secondary_code
    if 'production date' in kwargs:
        secondary_code += '/16D' + kwargs['production date'].strftime('%Y%m%d')
    if (lot_number or 'quantity' in kwargs) and serial_number:
        secondary_code += '/S' + serial_number
    if secondary_code:
        barcode += secondary_code
    return barcode + (get_check_character(barcode) or '?')


def add_date_and_var(result, code, var_id='lot number'):
    if not code:
        return
    date_formats = {
        '0': {'length': 4, 'format': '%m%y'},
        '1': {'length': 4, 'format': '%m%y'},
        '2': {'length': 6, 'format': '%m%d%y'},
        '3': {'length': 6, 'format': '%y%m%d'},
        '4': {'length': 8, 'format': '%y%m%d%H'},
        '5': {'length': 5, 'format': '%y%j'},
        '6': {'length': 7, 'format': '%y%j%H'},
    }
    date_format = date_formats.get(code[0], None)
    if date_format:
        if code[0] not in '01':
            code = code[1:]
        result['expiry date'] = code[:date_format['length']]
        if code[date_format['length']:]:
            result[var_id] = code[date_format['length']:]
        result['expiry date'] = get_datetime(result['expiry date'], date_format['format'])
    elif code[0] == '7':
        if code[1:]:
            result[var_id] = code[1:]
    else:
        if code:
            result[var_id] = code


def get_date(value, format_string):
    try:
        return datetime.datetime.strptime(value, format_string).date()
    except ValueError:
        return value


def get_datetime(value, format_string):
    try:
        return datetime.datetime.strptime(value, format_string)
    except ValueError:
        return value


def parse(barcode, primary_code=None):
    if '+' not in barcode:
        return None
    barcode = '+' + barcode.split('+', 1)[-1]
    result = {'barcode': barcode}
    check_character = barcode[-1]
    barcode = barcode[:-1]
    if primary_code:
        if 'barcode' in primary_code:
            result['primary barcode'] = primary_code['barcode']
            primary_code = primary_code.copy()
            del primary_code['barcode']
        result.update(primary_code)
        result['link character secondary'] = barcode[-1]
        result['link character primary'] = primary_code['check character actual']
        result['check link'] = primary_code['check character actual'] == result['link character secondary']
        barcode = barcode[:-1]
    result.update({
        'check character actual': check_character,
        'check character computed': get_check_character(barcode)
    })
    result['check OK'] = result['check character actual'] == result['check character computed']
    index_of_code = 0
    for code in barcode[1:].split('/'):
        if not code:
            continue
        index_of_code += 1
        # primary code starts alphabetic and secondary codes start with a numeric (julian date) or $
        if code[0:3] == '16D' and index_of_code > 1:
            result['production date'] = get_date(code[3:], '%Y%m%d')
        elif code[0].isdigit():
            result.update({
                'expiry date': get_date(code[:5], '%y%j'),
                'lot number': code[5:]
            })
        elif code[0] == '$':
            if code[1] == '$':
                if code[2] == '+':
                    add_date_and_var(result, code[3:], var_id='serial number')
                elif code[2] == '8':
                    try:
                        result['quantity'] = int(code[3:5])
                    except ValueError:
                        result['quantity'] = code[3:5].strip()
                    add_date_and_var(result, code[5:])
                elif code[2] == '9':
                    try:
                        result['quantity'] = int(code[3:8])
                    except ValueError:
                        result['quantity'] = code[3:8].strip()
                    add_date_and_var(result, code[8:])
                else:
                    add_date_and_var(result, code[2:])
            elif code[1] == '+':
                if code[2:]:
                    result['serial number'] = code[2:]
            else:
                if code[2:]:
                    result['lot number'] = code[2:]
        elif code[0] == 'S' and index_of_code > 1:
            result['serial number'] = code[1:]
        else:
            result.update({
                'lic': code[0:4],
                'ref': code[4:-1],
                'unit_of_measure': code[-1]
            })
    return result
