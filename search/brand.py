# ex: set ts=4 et:
# -*- coding: utf-8 -*-

from itertools import takewhile
from leven import levenshtein
import numpy as np
import sklearn.cluster

if __name__ == '__main__':

    with open('/tmp/brands.csv', 'r') as f:
        brands = [unicode(b.rstrip(), 'utf8') for b in f
                    if b and b.rstrip()]

words = brands
dist = [[levenshtein(w1, w2)
            for w1 in words]
                for w2 in words]
lev_similarity = -1 * np.array(dist)

#affprop = sklearn.cluster.AffinityPropagation(affinity='precomputed', damping=0.9)
affprop = sklearn.cluster.Birch()
affprop.fit(lev_similarity)
print affprop
print dir(affprop)
print 'labels_', affprop.labels_
for cluster_id in np.unique(affprop.labels_):
    print 'cluster_id', cluster_id
    print 'subcluster_centers[cluster_id]', affprop.subcluster_centers_[cluster_id]
    exemplar = words[affprop.subcluster_centers_[cluster_id]]
    #exemplar = words[affprop.cluster_centers_indices_[cluster_id]]
    #print np.nonzero(affprop.labels_==cluster_id)[0][0]
    cluster = np.unique(words[np.nonzero(affprop.labels_==cluster_id)[0][0]])
    if cluster != [exemplar]:
        print('%s: %s' % (exemplar, ', '.join(cluster))).encode('utf8')

'''
    for brand in brands:
        cmp_ = [(b, levenshtein(brand, b)) for b in brands
                    if b != brand]
        close = sorted(cmp_, key=lambda x: x[1])
        near = list(takewhile(lambda x: x[1] == 1, close))
        if near:
            print brand, near
'''

'''
adidas
adidas Originals
Adidas Originals

Alice Olivia
Alice + Olivia

Aquatalia                               |    4
Aquazzura                               |    6

Armani Collezioni                       |    8
Armani Junior                           |    6
Armenta                                 |    3
artee couture                           |    1

Articles of Society                     |   11
Articles of Society Red Label           |    1
Artis                                   |    4

Ashley Pittman                          |   20
Ashley Williams

Bella J                                 |    1
Belle Fare
Bellroy

 Bobbi Brown                             |   19
 Bobby Jones

 Bosca                                   |    2
 Bos. & Co.                              |    1

 Bose®                                   |    1
 Bose<sup>®</sup>                        |    4

 BOSS                                    |    7
 BOSS Kidswear

 Brioni                                  |    4
 Brixton                                 |    1

 Burberry                                |  158
 Burberry Beauty                         |    2
 Burberry Brit                           |   18
 Burberry London

 Casadei                                 |    2
 Casio                                   |    2
 Caslon®                                 |    2

 Charles by Charles David                |    6
 Charles David                           |    2

 Chloe                                   |   15
 Chloé                                   |   18
 Chloe Gosselin                          |    1
 Chloe K                                 |    1

 Clarins                                 |    5
 Clarisonic                              |    2
 Clinique                                |    5

 Dolce&amp;Gabbana                       |    1
 Dolce & Gabbana                         |   25
 Dolce&Gabbana;                          |    2
 Dolce & Gabbana Vintage                 |    3

 Estee Lauder                            |    4
 Estée Lauder                            |    1

 HERMÈS                                  |    1
 Hermès Vintage                          |   13

 Lancome                                 |    1
 Lancôme                                 |    1

 Marc By Marc Jacobs                     |    1
 MARC by Marc Jacobs                     |    2
 MARC BY MARC JACOBS                     |   11
 Marc Jacobs                             |    2
 MARC JACOBS                             |    1

 Michael Aram                            |    1
 Michael Kors                            |   12
 Michael Michael Kors                    |    1
 MICHAEL Michael Kors                    |   55
 MICHELE                                 |    1

 Steve Madden                            |   18
 Steven by Steve Madden                  |    1

 St John                                 |    2
 St. John Collection                     |   20

 UGG Australia                           |   30
 UGG® Australia                          |   35

 Zac Posen                               |    4
 ZAC Zac Posen                           |    3

 Zella                                   |   10
 Zella Girl                              |    2
'''
