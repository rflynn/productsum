import codecs
import yaml
from pprint import pprint

def load_brands(filepath):
    with codecs.open(filepath, 'r', 'utf-8') as f:
        return yaml.load(f)

def u(x):
    return unicode(x, 'utf8') if isinstance(x, str) else x

def translate(brands):
    xl = {}
    for k, v in brands.iteritems():
        k = u(k)
        xl[k] = k
        if v:
            aka = v.get('aka')
            if aka:
                #pprint(aka)
                try:
                    for a in aka.keys():
                        a = u(a)
                        xl[a] = k
                except:
                    pprint(aka)
                    raise
            lines = v.get('line')
            if lines:
                try:
                    for kl, vl in lines.iteritems():
                        kl = u(kl)
                        xl[kl] = k
                        if vl:
                            aka = vl.get('aka')
                            if aka:
                                for a in aka.keys():
                                    a = u(a)
                                    xl[a] = k
                except:
                    print lines
                    raise
    return xl


if __name__ == '__main__':

    import sys
    import unicodecsv as csv

    br = load_brands('brands.yml')
    tl = translate(br)
    #print len(tl)

    w = csv.writer(sys.stdout, encoding='utf-8')
    for k, v in sorted(tl.iteritems(), key=lambda x: (x[1], x[0])):
        w.writerow((v, k))

