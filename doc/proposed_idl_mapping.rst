IDL-to-Python Mapping Plan
==========================

- IDL ``boolean`` maps to Python ``bool``.
- All IDL integer types map to Python ``int``.

  - During serialization, if the value it does not fit in the types range,
    raise a ``ValueError``.

- IDL ``float`` and ``double`` map to Python ``float``. IDL ``long double`` and
  ``fixed`` map to Python ``decimal.Decimal``.
- All IDL characters and strings map to Python ``str``.

  - Unlike C strings, Python ``str`` requires the encoding to be known. To help
    facilitate this, by default characters and strings will be assumed to be
    UTF-8 and wide characters and strings will be assumed to be UTF-16. The
    encoding will be able to be specified either using a global implementation
    option or manually using this IDL annotation::

      @annotion encoding {
          string platform default "*";
          string value;
      };

    For Python, ``platform`` can be left to default or set to ``python`` and
    ``value`` should be a valid Python codec. `Here is the list of codecs for
    Python 3.7
    <https://docs.python.org/3.7/library/codecs.html#standard-encodings>`_. As
    an example, if you wanted to use `ISO-8859-10
    <https://en.wikipedia.org/wiki/ISO/IEC_8859-10>`_ "on the wire", you could
    write something like this::

      struct Data {
          @encoding(platform="python", value="latin6")
          string put_swedish_here;
      };

    During serialization and deserialization, encoding will be handled
    automatically, but will be subject to ``UnicodeError`` if there is a
    problem with the encoding.

    Alternatively ``value`` can be set to ``"none"`` to represent that no
    automatic encoding and decoding should be done. This is probably the
    behavior many other IDL mappings and would probably be the default if the
    annotation was adopted in other implementation. For Python this will change
    the type from ``str`` to ``bytes``, which better represents the idea of
    string of bytes of uncertain encoding.

  - During serialization, raise a ``ValueError`` if the size of the encoded data
    is larger than the limits of the IDL type. For example: assigning Python
    ``"more than a byte"`` to a IDL field of type ``char``.

- IDL arrays and sequences map to Python ``list``

  - During serialization, if the IDL type is an array or bounded sequence, raise
    ``ValueError`` if the element count of the list is out of the valid range.

- IDL structures map to `Python dataclasses
    <https://docs.python.org/3/library/dataclasses.html>`_ or equivalent.

.. _enum.IntFlag: _https://docs.python.org/3/library/enum.html?highlight=enum#enum.IntFlag

- IDL ``enum`` map to Python :ref:``enum.IntFlag``.

- IDL ``union``: TODO

  This IDL::

    enum EnumType {
        A, B, C
    };

    union UnionType switch (EnumType) {
    case A:
        long number;
    case B:
    case C:
        char character;
    };

  Will produce Python like::

    class UnionType:
        def __init__(self):
            self._d = None

        @property
        def number(self):
            if self._d != EmunType.A:
                raise # TODO What kind of Error does this need to be?
            return self._number

        @number.setter
        def number(self, value: int):
            self._d = EnumType.A
            self._number = value

