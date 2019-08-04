# HIBC
HIBC Barcode for python (parse and generate, try to accept as much as possible)

There are only two functions of concern which should be pretty self explanatory:

```python
import hibc
print(hibc.parse('+A99912345/$$52001510X3/16D20111212/S77DE1G45-'))
print(hibc.generate({
    'expiry date': datetime.datetime(2020, 1, 15, 0, 0),
    'lic': 'A999',
    'lot number': '10X3',
    'production date': datetime.date(2011, 12, 12),
    'ref': '1234',
    'serial number': '77DE1G45',
    'unit_of_measure': '5'
}))
```
