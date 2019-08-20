IDL-to-Python Mapping Plan
==========================

- IDL ``boolean`` maps to Python ``bool``.
- All IDL integer types map to Python ``int``.

  - During serializtion, if the value it does not fit in the types range, raise
    a ``ValueError``.
    
- IDL ``float`` and ``double`` map to Python ``float``. IDL ``long double`` and
  ``fixed`` map to Python ``decimal.Decimal``.
- All IDL characters and strings map to Python ``str``.

  - Unlike IDL, Python ``str`` requires the encoding to be known. To facitate
    this, by default byte characters and strings will be assumed to be UTF-8
    and wide characters and strings will be assumed to be UTF-16 or UTF-32
    depending on the platform size of IDL ``wchar``. The encoding will be able
    to be declared manually using this IDL annotation::
    
      @annotion encoding {
          string value;
      };
      
    For Python this value should be a valid codec. Here is the list of codecs
    for Python 3.7:
    https://docs.python.org/3.7/library/codecs.html#standard-encodings.  As an
    example, if you wanted to use https://en.wikipedia.org/wiki/ISO/IEC_8859-10
    "on the wire", you could write something like this::
    
      struct Data {
          @encoding("latin6")
          string put_swedish_here;
      };

  - During serializtion, raise a ``ValueError`` if the size of the encoded data
    is larger than the limits of the IDL type. For example: assigning Python
    ``"more than a byte"`` to a IDL field of type ``char``.

- IDL arrays and sequences map to Python ``list``

  - During serializtion, if the IDL type is an array or bounded sequence, raise
    ``ValueError`` if the element count of the list is out of the valid range.

- IDL structures map to Python data classes (classes annotated with
  ``@dataclasses.dataclass``.

- IDL ``enum`` map to Python ``enum.IntFlag``.

- IDL ``union``: TODO
