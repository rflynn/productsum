# vim: set ts=4 et:
# -*- coding: utf-8 -*-

from collections import defaultdict
from pprint import pprint, pformat
import traceback

from search import tag_name


def xfloat(s):
    try:
        return float(s)
    except ValueError:
        return None

def norm_frac(n, d):
    return str(float(n) / float(d))[1:]

def val_inches(val):
    # handle
    if len(val) >= 3:
        if val[-2] == '/':
            val = val[:-3] + [norm_frac(val[-3], val[-1])]
        val = ''.join(val)
    if len(val) == 2:
        val = val[0] + '.' + val[1]
    else:
        val = ''.join(val)
    return xfloat(val)

assert val_inches(['1','/','4']) == 0.25
assert val_inches(['1','1','/','4']) == 1.25
assert val_inches(['..5']) is None

def size_attrs(d):
    size_unit = defaultdict(list)
    for toks in d.get('size', []):
        #print 'toks:', toks
        if len(toks) == 5 and toks[1] == '"' and toks[2] in {'x','X','by'} and toks[4] == '"':
            print 'X inches x Y inches', toks
            unit = 'inches'
            val = [int(toks[0]), int(toks[3])]
        if toks[-2:] in [['fl','oz'],['fluid','oz']]:
            unit = 'fl_ounce'
            val = xfloat('.'.join(toks[:-2]))
        else:
            if toks[0] == 'size' and len(toks) == 2:
                unit, val = 'num', xfloat(toks[1])
            else:
                val, unit = toks[:-1], toks[-1].lower()
                if unit in ('in','inch','inches','"'):
                    unit = 'inch'
                    val = val_inches(val)
                elif unit in ('mm',):
                    unit = 'mm'
                    val = xfloat('.'.join(val))
                else:
                    if unit in ('g',):
                        unit = 'gram'
                    elif unit in ('ml',):
                        unit = 'ml'
                    elif unit in ('oz','ounce','ounces'):
                        unit = 'ounce'
                    elif unit in ('l','liter','liters'):
                        unit = 'liter'
                    elif unit in ('ft','foot','feet'):
                        unit = 'foot'
                    elif unit in ('gal','gallon','gallons'):
                        unit = 'gallon'
                    elif unit in ('qt','qts','quarts'):
                        unit = 'quart'
                    val = xfloat(val[0])
        #print unit, val
        if unit and val is not None:
            size_unit[unit].append(val)
    return dict(size_unit)

Num_ = {
    'one':     1,
    'two':     2,
    'three':   3,
    'four':    4,
    'five':    5,
    'six':     6,
    'seven':   7,
    'eight':   8,
    'nine':    9,
    'ten':    10,
    'eleven': 11,
    'twelve': 12,

    'single':  1,
    'double':  2,
    'triple':  3,
    'quad':    4,
}

def to_num(x):
    try:
        return int(x)
    except:
        return Num_.get(x)

def qty_attrs(d):
    if 'quantity' in d:
        qty = []
        for toks in d['quantity']:
            for tok in toks:
                n = to_num(tok)
                if n is not None:
                    qty.append(n)
        return qty

def list_startswith(l1, l2):
    return all(x == y for x, y in zip(l1, l2)[:len(l2)])

def list_contains(l1, l2):
    return any(l1[i:i+len(l2)] == l2 for i in xrange(len(l1) - len(l2) + 1))

def list_sublist_index(l1, l2):
    return ([i for i in xrange(len(l1) - len(l2) + 1)
                    if l1[i:i+len(l2)] == l2] or [-1])[0]

def name_minus_string_prefix(name, strlist, verbose=False):
    if strlist:
        substr = strlist[0][0]
        #print 'substr:', substr
        if name.startswith(substr):
            endidx = name.index(substr) + len(substr)
            return name[endidx:].lstrip(" '-,")
        else:
            if verbose:
                print name, 'doesnt start with', substr
    return name

def name_minus_string_prefix_or_suffix(name, strlist, verbose=False):
    if strlist:
        substr = strlist[0][0]
        #print 'substr:', substr
        if name.startswith(substr):
            endidx = name.index(substr) + len(substr)
            return name[endidx:].lstrip(" -,")
        elif name.endswith(substr):
            return name[:-len(substr)].rstrip(" '-,")
        else:
            if verbose:
                print name, 'doesnt start/end with', substr
    return name

def name_minus_tag(name, tokens):
    #print tokens
    name_tokens = tag_name.tokenize(name)
    idx = list_sublist_index(name_tokens, [t.lower() for t in tokens])
    if idx == -1:
        print tokens, 'not in', name_tokens
        return name
    idx = name.index(tokens[0])
    endidx = name.index(tokens[-1], idx) + len(tokens[-1])
    before = name[:idx].rstrip(" -,('!")
    after = name[endidx:].lstrip(" -,.)'!")
    #print 'before:', before, 'after:', after
    if before and after:
        after = ' ' + after
    return (before + after) or None

def name_canonical(name, attrs, tq):
    # strip promo
    #print 'tq:', pformat(tq)
    name2 = name
    for tokens in attrs.get('promo', []):
        name2 = name_minus_tag(name2, tokens)
    for tokens in attrs.get('demographic', []):
        name2 = name_minus_string_prefix(name2, [tokens])
    name2 = name_minus_string_prefix_or_suffix(name2, attrs.get('brand') or [], verbose=True)
    # strip size(s)
    for tokens in attrs.get('size', []):
        name2 = name_minus_tag(name2, tokens)
    # strip price
    for tokens in attrs.get('price', []):
        name2 = name_minus_tag(name2, tokens)
    return name2

def name_to_attrs(name, brand=None):
    attrs = defaultdict(list)
    if name:
        otq = tag_name.tag_query(name)
        tq = tag_name.to_original_case(otq, name)
        #print 'tq:', pformat(tq)
        for tag, toks in tq:
            attrs[tag].append(toks)

        # preserve brand exactly for later re-matching
        tqbrand = tag_name.to_original_substrings(otq, name)
        if 'brand' in attrs:
            del attrs['brand']
        if 'demographic' in attrs:
            del attrs['demographic']
        if 'product' in attrs:
            del attrs['product']
        if 'material' in attrs:
            del attrs['material']
        if 'color' in attrs:
            del attrs['color']
        if 'pattern' in attrs:
            del attrs['pattern']

        # brand supplied separately
        if brand:
            attrs['brand'].append([brand])
        for tag, toks in tqbrand:
            if tag in ('demographic', 'product', 'material', 'color', 'pattern'):
                attrs[tag].append(toks)
            elif tag == 'brand' and not brand:
                attrs[tag].append(toks)

        attrs['name_canonical'] = name_canonical(name, attrs, tq)

    attrs['size'] = size_attrs(attrs)
    attrs['quantity'] = qty_attrs(attrs) or None

    return dict(attrs)

def update(cursor, url_product_id, updated, name, attrs):
    try:
        sql = '''
update url_product_name_attr
set
    updated            = %s,
    url_product_name   = %s,
    name_brand         = %s,
    name_color         = %s,
    name_material      = %s,
    name_product       = %s,
    name_pattern       = %s,
    name_qty           = %s,
    name_size_raw      = %s,
    name_size_gram     = %s,
    name_size_inch     = %s,
    name_size_ml       = %s,
    name_size_mm       = %s,
    name_size_ounce    = %s,
    name_size_fl_ounce = %s,
    name_size_liter    = %s,
    name_size_gallon   = %s,
    name_size_quart    = %s,
    name_size_num      = %s,
    demographic        = %s
where
    url_product_id = %s
'''
        args =(
        updated,
        attrs.get('name_canonical'),
        attrs.get('brand'),
        attrs.get('color'),
        attrs.get('material'),
        attrs.get('product'),
        attrs.get('pattern'),
        attrs.get('qty'),
        attrs.get('size_raw'),
        attrs.get('size_gram'),
        attrs.get('size_inch'),
        attrs.get('size_ml'),
        attrs.get('size_mm'),
        attrs.get('size_ounce'),
        attrs.get('size_fl_ounce'),
        attrs.get('size_liter'),
        attrs.get('size_gallon'),
        attrs.get('size_quart'),
        attrs.get('size_num'),
        attrs.get('demographic'),
        url_product_id
      )
        cursor.execute(sql, args)
    except Exception as e:
        print e
        print cursor.mogrify(sql, args)
        raise

def insert(cursor, url_product_id, updated, name, attrs):
    try:
        cursor.execute('''
insert into url_product_name_attr (
    created,
    updated,
    url_product_id,
    url_product_name,
    name_brand,
    name_color,
    name_material,
    name_product,
    name_pattern,
    name_qty,
    name_size_raw,
    name_size_gram,
    name_size_inch,
    name_size_ml,
    name_size_mm,
    name_size_ounce,
    name_size_fl_ounce,
    name_size_liter,
    name_size_gallon,
    name_size_quart,
    name_size_num,
    demographic
) values (
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s
)
''',  (updated,
       updated,
       url_product_id,
       attrs.get('name_canonical'),
       attrs.get('brand'),
       attrs.get('color'),
       attrs.get('material'),
       attrs.get('product'),
       attrs.get('pattern'),
       attrs.get('quantity'),
       attrs.get('size').get('raw'),
       attrs.get('size').get('g'),
       attrs.get('size').get('inch'),
       attrs.get('size').get('ml'),
       attrs.get('size').get('mm'),
       attrs.get('size').get('ounce'),
       attrs.get('size').get('fl_ounce'),
       attrs.get('size').get('liter'),
       attrs.get('size').get('gallon'),
       attrs.get('size').get('quart'),
       attrs.get('size').get('num'),
       attrs.get('demographic')))
    except Exception as e:
        print e
        raise

def upsert(conn, cursor, url_product_id, updated, name, attrs, cnt):
    with conn.cursor() as cursor:
        update(cursor, url_product_id, updated, name, attrs)
        if cursor.rowcount == 0:
            insert(cursor, url_product_id, updated, name, attrs)
        conn.commit()

def run():
    from product_mapper.dbconn import get_psql_conn
    '''
    for each name in url_product:
        pull that hit down
        parse it into separate fields
        upsert into url_product_name_attrs
    '''
    conn = get_psql_conn()
    conn.autocommit = False
    with conn.cursor('namedcursor2', withhold=True) as read_cursor, \
         conn.cursor() as write_cursor:
        read_cursor.execute('''
            select up.id as id,
                   up.updated as updated,
                   up.name as name,
                   up.brand as brand
            from url_product up
            left join url_product_name_attr upna
            on up.id = upna.url_product_id
            where upna.url_product_id is null or
            up.updated > coalesce(upna.updated, timestamp '1970-01-01')
            -- and up.merchant_slug in ('macys','target','beautycom') -- XXX: FIXME: remove, just for testing...
            -- order by up.updated asc
            ''')
        cnt = 0
        row = None
        attrs = None
        try:
            while True:
                # bulk fetch to amortize latency
                rows = read_cursor.fetchmany(1000)
                if not rows:
                    break
                for row in rows:
                    url_product_id, updated, name, brand = row
                    attrs = name_to_attrs(name, brand=brand)
                    #print ('name: %s -> %s' % (name, attrs.get('name_canonical'))).encode('utf8')
                    #print 'attrs=%s' % (str(attrs).encode('utf8'),)
                    cnt += 1
                    upsert(conn, write_cursor, url_product_id,
                            updated, name, attrs, cnt)
            conn.commit() # final commit
        except Exception as e:
            print e
            print 'row:', row
            print attrs
            conn.commit()
            raise

def test():
    names = [
        (u'Christian Louboutin So Kate Patent 120mm Red Sole Pump, Shocking Pink $675', None),
        (u'Matis Paris Cleansing Cream - Creme Demaquillante (6.76 fl oz.) $44', None),
        (u'Brighton 1-1/4" - 1" Salina Taper Belt', None),
        (u'100ml 4 g 2" 55 mm 4.2 oz 1.7 fl oz. 1.7 liter 2 gallons 4 qt size 6', None),
        (u'Hot Tools 0.75 Inch - 1.25 Inch Tapered Curling Iron (2 piece)', None),
        (u'1 pc 2 pieces 3 x 4-pack 5 count set of 2 3 pack', None),
        (u'Sally Hansen Miracle Gel, Top Coat, 0.5 fluid oz', None),
        (u'Viscaya 7-Pc. Embroidered Comforter Sets', None),
        (u'CLOSEOUT! Bar III Interlock White Quilt Collection', None),
        (u"Men's Star Wars Advance Tie T-Shirt by Fifth Sun", None),
        (u"Haaci V-Neck Hoodie - Miss Chievous", None),
        (u"Haaci V-Neck Hoodie", u'Miss Chevous'),
        (u'Cashmere Throw, 50" x 70"', None),
        (u'TORINO MADRID PILLOW 18"X18" TRICOLOR', None),
        (u"Round Cocotte - 7Qt - Dark Blue", None),
        (u"Future Solution LX Total Protective Cream SPF 18, 50 mL", None),
    ]
    for name, brand in names:
        print name
        pprint(name_to_attrs(name, brand=brand), width=100)

if __name__ == '__main__':
    import sys
    if sys.argv and len(sys.argv) > 1:
        if sys.argv[1] == 'run':
            run()
            sys.exit(0)
    print 'running tests...'
    print 'to run for real, run me with "run"'
    test()

