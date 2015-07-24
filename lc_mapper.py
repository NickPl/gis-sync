# coding=utf-8


class LC2SFOwnerMapper:
    def __init__(self):
        self.op_sf_dictionary = {713: '00520000002hmQa', 686: '00520000002hmQf',
                                 1465: '00520000002hOQ0', 1454: '00520000002iPe6',
                                 680: '00520000002hmRJ', 708: '00520000002iPeB',
                                 664: '00520000002hmQk', 1442: '00520000002hmQp', 693: '00520000002hmQu',
                                 678: '00520000002iPeG', 665: '00520000002iPeL',
                                 667: '00520000002hOQF', 1470: '00520000002hmQz',
                                 677: '00520000002iPeQ', 1448: '00520000002iPeV',
                                 1433: '00520000002hOPv', 657: '00520000002hmR4',
                                 1653: '00520000002iPea', 1420: '00520000002iPef',
                                 1415: '00520000002iPek', 1523: '00520000002iPfY',
                                 757: '00520000002iPep', 1441: '00520000002hNjP',
                                 699: '00520000002hmRE', 696: '00520000002hmRO',
                                 1533: '00520000002iPeu', 643: '00520000002hOPq',
                                 1438: '00520000002iPez', 1421: '00520000002hmR9', 1410: '00520000002hmRT',
                                 1414: '00520000002hmRd', 1447: '00520000002iPf4',
                                 60: '00520000002hmRi', 1520: '00520000002hmRn',
                                 1394: '00520000002hmRs', 1484: '00520000002hOQA',
                                 1440: '00520000002iPf9', 625: '00520000002iPel',
                                 663: '00520000002hmRx', 1403: '00520000002hmS2',
                                 648: '00520000002iPfE', 647: '00520000002hmSH',
                                 1439: '00520000002iPfO', 469: '00520000002hmSW',
                                 1443: '00520000002hmDR', 624: '00520000002iPfT',
				 1596: '00520000002I4PD', 1844: '00520000004KlOI'}

    def op_to_sf(self, op_lc):
        return self.op_sf_dictionary[op_lc]

    def sf_to_op(self, sf_lc):
        inv_map = {v: k for k, v in self.op_sf_dictionary.items()}
        return inv_map[sf_lc]

class LC2CityMapper:
    def __init__(self):
        self.op_sf_dictionary = {713: 'Aachen', 686: 'Augsburg',
                                 1465: 'Bamberg', 1454: 'Bayreuth',
                                 680: 'Berlin HU', 708: 'Berlin TU',
                                 664: 'Bielefeld', 1442: 'Bochum', 693: 'Bonn',
                                 678: 'Braunschweig', 665: 'Bremen',
                                 667: 'Darmstadt', 1470: 'Dortmund',
                                 677: 'Dresden', 1448: 'Duesseldorf',
                                 1433: 'Essen', 657: 'Frankfurt',
                                 1653: 'Freiburg', 1420: 'Gießen',
                                 1415: 'Goettingen', 1523: 'Hamburg',
                                 757: 'Halle', 1441: 'Hannover',
                                 699: 'Heidelberg', 696: 'Jena',
                                 1533: 'Kaiserslautern', 643: 'Karlsruhe',
                                 1438: 'Kiel', 1421: 'Koeln', 1410: 'Leipzig',
                                 1414: 'Lueneburg', 1447: 'Magdeburg',
                                 60: 'Mainz', 1520: 'Mannheim',
                                 1394: 'München', 1484: 'Muenster',
                                 1440: 'Nuernberg', 625: 'Oldenburg',
                                 663: 'Paderborn', 1403: 'Passau',
                                 648: 'Regensburg', 647: 'Stuttgart',
                                 1439: 'Tuebingen/Reutlingen', 469: 'Ulm',
                                 1443: 'Wuerzburg', 624: '00520000002iPfT',
				 1596: '', 1844: 'Brühl'}

    def op_to_city(self, op_lc):
        return self.op_sf_dictionary[op_lc]

    def city_to_op(self, city):
        inv_map = {v: k for k, v in self.op_sf_dictionary.items()}
        return inv_map[city]
