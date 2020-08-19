# THD74 flash update protocol analysis

based on fw110e.json


## Comms setup

The radio is expected to be booted in *Firmware Programming Mode* with *ON + PTT + 1* The first magic sequence of bytes sent to the device determines its operating mode: encrypted or cleartext.

## Encrypted firmware programming mode

Kenwood's updater software uses *encrypted firmware programming mode* by default. All data except the newline sequence `\r\n` is obfuscated on the wire by *xor* with a constant byte value.

When dumping data from a USB update capture, the *xor* byte can be trivially derived from looking at the first two bytes of each message: You will find two identical bytes there, but we already know that their cleartext is `0xab 0xab`, so just *xor* the first byte with *0xab* and *xor* the result with the rest to get the cleartext message.

The *xor* byte is negotiated in the initial magic sequence, but the exact mechnanism is not fully understood at the moment. However, we already know that last two bytes of the magic sequence and the *xor* key are interrelated. If *y* and *z* are the last two bytes of the magic sequence, then the *xor* key *k* can be calculated as

```python
k = (((y + z + 72) & 120) - ((y + z) & 7)) % 128
```

Here are a few sample magic sequences for unlocking encrypted firmware programming mode:

```
[00253] OUT: 62 6f 54 68 64 37 34 74 77 12 1d  ["boThd74tw\x12\x1d"]
[00255]  IN: 16
[00257]  IN: 06
```
After this magic, the xor key used for command obfuscation is `0x69`.

```
[000f3] OUT: 67 64 54 68 64 37 34 74 77 10 01  ["gdThd74tw\x10\x01"]
[000f5]  IN: 16
[000f7]  IN: 06
```
After this magic, the xor key used for command obfuscation is `0x57`.

```
[000e3] OUT: 6b 70 54 68 64 37 34 74 77 0b 30  ["kpThd74tw\x0b\x30"]
[000e5]  IN: 16
[000e7]  IN: 06
```
After this magic, the xor key used for command obfuscation is `0x7d`.


## Cleartext firmware programming mode

The device supports an undocumented *cleartext firmware programming mode* that is initiated by the `FPROMOD` magic sequence.

```
[00] OUT: 46 50 52 4f 4d 4f 44  ["FPROMOD"]
[01]  IN: 16
[02]  IN: 06
```

This mode is equivalent to *encrypted firmware programming mode* with *xor* byte 0.


## Firmware programming command format

```
0xab 0xab [2 byte cmd length] [2 byte payload length] [2 byte verb] [optional nouns] [optional payload] [1 byte checksum] \r\n
```

The initial cmd length field is the number of bytes in the nouns plus one byte for the checksum. The overall message length is `2 + <cmd length> + <payload length>`.

The checksum is the sum reduce over all preceeding bytes in the message apart from the attention bytes `ab ab`.

### Observed command verbs
 * [OUT] `0x30`
 * [IN] `0x11` – BUSY
 * [IN] `0x06` – OK
 * [OUT] `0xa0`
 * [OUT] `0x31`
 * [IN] `0x32`
 * [OUT] `0x33`

 * [OUT] `0x40` – Section setup
 * [IN] `0x41` – Answer to section setup
 * [OUT] `0x42` – Command before data transfer
 * [OUT] `0x43` [4 byte offset] [2 byte payload length] [00 00] [payload] [cs] – Data packet
 * [OUT] `0x45` – Section end
 * [IN] `0x46` – Answer to section end

 * [OUT] `0x50` – Last command, radio displays "Completed!!" and becomes unresponsive

## Flashing setup
```
[00267] OUT: ab ab 00 02 00 00 00 30 00 32
[00269]  IN: ab ab 00 01 00 00 00 06 07  [OK]
[0026b] OUT: ab ab 00 01 00 00 00 a0 a1
[0026d]  IN: ab ab 00 01 00 00 00 06 07  [OK]
[0026f] OUT: ab ab 00 01 00 00 00 31 32
[00271]  IN: ab ab 00 12 00 00 00 32 02 00 00 00 00 00 00 00
             02 00 00 00 00 00 00 00 00 48
[00273] OUT: ab ab 00 03 00 00 00 33 0a 00 40
[00275]  IN: ab ab 00 01 00 00 00 06 07  [OK]
```

## Firmware section

The section header carries memory address and a byte sequence to check for in memory at an offset:
```
[00277] OUT: ab ab 00 44 00 00 00 40 00 00 20 60 00 00 28 00
             00 00 28 00 00 00 00 00 00 00 00 00 00 00 00 0f
             06 00 00 00 ab 66 03 1f 00 00 00 00 00 00 28 00
             0a 00 00 00 a0 00 00 00 0f 00 00 00 56 31 2e 31   ["V1.10.000      "]
             30 2e 30 30 30 20 20 20 20 20 20 11
[0027b]  IN: ab ab 00 02 00 00 00 41 01 44
[0027d] OUT: ab ab 00 01 00 00 00 42 43
[00291]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[002a3]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[002b1]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[002bf]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[002d1]  IN: ab ab 00 01 00 00 00 06 07  [OK]
```

The initial section header command verb `40` has the following nouns:
 * `00 00 20 60` – memory address 0x200000 + 0x60000000
 * `00 00 28 00` – section length to write 0x280000
 * `00 00 28 00` – section length to receive 0x280000
 * `00 00 00 00` – unknown always 0
 * `00 00 00 00` – unknown always 0
 * `00 00 00 0f` – unknown always 0x0f000000
 * `06 00 00 00` – unknown
 * `ab 66 03 1f` – unknown
 * `00 00 00 00` – unknown always 0
 * `00 00 28 00` – section length 0x280000
 * `0a 00 00 00` – unknown always 0x0a
 * `a0 00 00 00` – sequence offset in section 0xa0
 * `0f 00 00 00` – length of sequence
 * `56 31 2e 31 30 2e 30 30 30 20 20 20 20 20 20` – sequence to compare "V1.10.000      "

Then come the data command verbs `43`, with 0x400 byte payload each. Two nouns carry offset and payload length:
```
[002eb] OUT: ab ab 00 09 04 00 00 43 00 00 00 00 00 04 00 00
             1c f0 9f e5 1c f0 9f e5 1c f0 9f e5 1c f0 9f e5
             1c f0 9f e5 00 00 00 00 18 f0 9f e5 18 f0 9f e5
             ff ff ff 00 74 39 15 c0 ac 3b 15 c0 68 5a 09 c0
             d4 3b 15 c0 fc 3b 15 c0 3c 5b 09 c0 70 3b 15 c0
             ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff
             [...]
             6e 00 00 00 00 00 00 00 96 7b 91 cc 90 dd 92 e8
             00 00 00 00 00 00 00 00 00 00 00 00 52 58 00 00
             76
[002ed] OUT: ab ab 00 09 04 00 00 43 00 04 00 00 00 04 00 00
             00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
             8e f3 90 4d 00 00 00 00 00 00 00 00 00 00 00 00
             [...]
             00 00 00 00 44 69 67 69 74 61 6c 20 53 71 75 65
             6c 63 68 00 00 00 00 00 c3 de bc de c0 d9 bd b9
             59
[002ef] OUT: ab ab 00 09 04 00 00 43 00 08 00 00 00 04 00 00
             d9 c1 00 00 00 00 00 00 00 00 00 00 47 50 53 20  ["GPS Data TX"]
             44 61 74 61 20 54 58 00 00 00 00 00 00 00 00 00
             [...]
             92 86 94 67 2f 92 5a 94 67 b1 dd c3 c5 8e ed 97
             de 00 00 00 46 4d 20 42 43 20 41 6e 74 65 6e 6e
             5e
[...]
[017c9] OUT: ab ab 00 01 00 00 00 45 46
[017d3]  IN: ab ab 00 02 00 00 00 46 00 48
```

## Section 2
```
[017d5] OUT: ab ab 00 3f 00 00 00 40 00 00 60 60 00 80 05 00
             00 00 06 00 00 00 00 00 00 00 00 00 00 00 00 0f
             01 00 00 00 c4 0f c4 0f 00 00 00 00 00 00 06 00
             0a 00 00 00 00 00 00 00 0a 00 00 00 31 2e 30 30  ["1.00.01.00"]
             2e 30 31 2e 30 30 76
[017d7]  IN: ab ab 00 02 00 00 00 41 00 43
[017d9] OUT: ab ab 00 01 00 00 00 42 43
[017e3]  IN: ab ab 00 01 00 00 00 06 07  [OK]
[01801] OUT: ab ab 00 09 04 00 00 43 00 00 00 00 00 04 00 00
             31 2e 30 30 2e 30 31 2e 30 30 00 ff ff ff ff ff  ["1.00.01.00"]
             ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff
             00 78 05 00 01 00 00 00 30 00 00 00 74 6c 05 00
             70 0d 00 00 f4 0d 00 00 74 0e 00 00 ec 0e 00 00
             [...]
             c4 af 00 00 94 b0 00 00 50 b1 00 00 04 b2 00 00
             dc b2 00 00 98 b3 00 00 5c b4 00 00 30 b5 00 00
             89
[...]
[01b17] OUT: ab ab 00 01 00 00 00 45 46
[01b19]  IN: ab ab 00 02 00 00 00 46 00 48
```

 * `00 00 60 60` – memory address 0x600000 + 0x60000000
 * `00 80 05 00` – section length to write 0x58000
 * `00 00 06 00` – section length to receive 0x60000
 * `00 00 00 00` – unknown always 0
 * `00 00 00 00` – unknown always 0
 * `00 00 00 0f` – unknown always 0x0f000000
 * `01 00 00 00` – unknown
 * `c4 0f c4 0f` – unknown
 * `00 00 00 00` – unknown always 0
 * `00 00 06 00` – section length 0x60000
 * `0a 00 00 00` – unknown always 0x0a
 * `00 00 00 00` – sequence offset in section 0
 * `0a 00 00 00` – sequence length10
 * `31 2e 30 30 2e 30 31 2e 30 30 76` – sequence to compare "1.00.01.00"

## Section 3
```
[01b1b] OUT: ab ab 00 41 00 00 00 40 00 00 e0 60 00 00 10 00
             00 00 10 00 00 00 00 00 00 00 00 00 00 00 00 0f
             03 00 00 00 5e 40 5e 40 00 00 00 00 00 00 10 00
             0a 00 00 00 f0 ff 05 00 0c 00 00 00 44 73 31 2e  ["Ds1.07.00R00"]
             30 37 2e 30 30 52 30 30 06
[01b23]  IN: ab ab 00 02 00 00 00 41 00 43
[01b25] OUT: ab ab 00 01 00 00 00 42 43
[01b3f]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[01b53]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[01b55]  IN: ab ab 00 01 00 00 00 06 07  [OK]
[01b77] OUT:
[01b77] OUT: ab ab 00 09 04 00 00 43 00 00 00 00 00 04 00 00
             5a a3 00 00 a2 03 00 02 a2 03 80 00 2a 9a 99 07
             ea c1 88 07 f2 09 bf 07 2a 04 1c 07 ea c1 08 07
             5a a3 00 02 a2 03 10 09 a2 03 10 0a a8 00 80 01
             68 00 80 01 58 2a 0c 00 29 d0 8d d1 92 09 00 d0
             [...]
             d8 c8 08 00 21 a1 04 c0 58 a3 00 d0 34 8a 28 00
             a9 0b 07 02 5a 4a 00 00 21 81 2d 35 14 8a 28 20
             e3
[023d5] OUT: ab ab 00 01 00 00 00 45 46
[023dd]  IN: ab ab 00 02 00 00 00 46 00 48
```

 * `00 00 e0 60` – section address 0xe00000 + 0x60000000
 * `00 00 10 00` – section length in memory 0x100000
 * `00 00 10 00` – section length to receive 0x100000
 * `00 00 00 00` – unknown always 0
 * `00 00 00 00` – unknown always 0
 * `00 00 00 0f` – unknown always 0x0f000000
 * `03 00 00 00` – unknown
 * `5e 40 5e 40` – unknown
 * `00 00 00 00` – unknown always 0
 * `00 00 10 00` – senction length 0x100000
 * `0a 00 00 00` – unknown always 0xa
 * `f0 ff 05 00` – offset for sequence 0x5fff0
 * `0c 00 00 00` – length of sequence 12
 * `44 73 31 2e 30 37 2e 30 30 52 30 30 06` – "Ds1.07.00R00"

## Section 4
```
[023df] OUT: ab ab 00 35 00 00 00 40 00 00 00 61 00 00 20 00
             00 00 20 00 00 00 00 00 00 00 00 00 00 00 00 0f
             05 00 00 00 68 fa 68 fa 00 00 00 00 00 00 20 00
             0a 00 00 00 00 00 00 00 00 00 00 00 18
[023e1]  IN: ab ab 00 02 00 00 00 41 01 44
[023e3] OUT: ab ab 00 01 00 00 00 42 43
[023f5]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[0240b]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[02429]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[02431]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[02435]  IN: ab ab 00 01 00 00 00 06 07  [OK]
[0244d] OUT: ab ab 00 09 04 00 00 43 00 00 00 00 00 04 00 00
             ae 00 00 00 30 07 00 00 b6 0c 00 00 2e 15 00 00
             18 1b 00 00 34 22 00 00 a6 28 00 00 22 31 00 00
             84 39 00 00 4a 40 00 00 74 48 00 00 3e 4f 00 00
             98 55 00 00 44 5c 00 00 aa 63 00 00 46 6a 00 00
             [...]
             16 16 16 14 14 15 16 17 16 15 16 17 17 18 17 15
             16 17 16 16 16 16 16 15 15 15 16 16 15 15 17 17
             e1
[...]
[034d7] OUT: ab ab 00 01 00 00 00 45 46
[034dd]  IN: ab ab 00 02 00 00 00 46 00 48
```

## Font data section
```
[034df] OUT: ab ab 00 39 00 00 00 40 00 00 50 61 00 80 0b 00
             00 00 0c 00 00 00 00 00 00 00 00 00 00 00 00 0f
             02 00 00 00 62 af 62 af 00 00 00 00 00 00 0c 00
             0a 00 00 00 10 00 00 00 04 00 00 00 31 2e 30 30  ["1.00"]
             dd
[034e3]  IN: ab ab 00 02 00 00 00 41 00 43
[034e5] OUT: ab ab 00 01 00 00 00 42 43
[034f1]  IN: ab ab 00 01 00 00 00 11 12  [BUSY]
[034f9]  IN: ab ab 00 01 00 00 00 06 07  [OK]
[0350d] OUT: ab ab 00 09 04 00 00 43 00 00 00 00 00 04 00 00
             34 34 30 39 20 46 4f 4e 54 20 44 41 54 41 20 20  ["4409 FONT DATA  1.00hy\x0b"]
             31 2e 30 30 68 79 0b 00 0c 02 53 00 95 0b 3e 0d
             50 00 00 00 00 00 00 00 98 45 00 00 9e 50 00 00
             68 da 01 00 a4 9c 03 00 1c 34 04 00 1a 4c 04 00
             [...]
             1c 70 07 c0 00 00 81 5b 00 00 00 00 00 00 00 00
             00 00 00 00 00 00 7f fe 00 00 00 00 00 00 00 00
             6c
[...]
[03b03] OUT: ab ab 00 01 00 00 00 45 46
[03b0b]  IN: ab ab 00 02 00 00 00 46 00 48
```

 * `00 00 50 61` – address 0x01500000 + 0x60000000
 * `00 80 0b 00` – write size 0xb8000
 * `00 00 0c 00` – data size 0xc0000
 * `00 00 00 00` – unknown alsways 0
 * `00 00 00 00` – unknown always 0
 * `00 00 00 0f` – unknown always 0xf000000
 * `02 00 00 00` – unknown
 * `62 af 62 af` – unknown
 * `00 00 00 00` – unknown always 0
 * `00 00 0c 00` – section length 0xc0000
 * `0a 00 00 00` – unknown always 0xa
 * `10 00 00 00` – sequence offset in section 0x10
 * `04 00 00 00` – sequence length 4
 * `31 2e 30 30 dd` – sequence for comparison "1.00"

## Flash finished

The final packets in the protocol wrap up the flashing process:
```
[03b0d] OUT: ab ab 00 35 00 00 00 40 62 00 20 60 02 00 00 00
             00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 0f
             00 00 00 00 ce 36 ce 36 00 00 00 00 00 00 00 00
             0a 00 00 00 00 00 00 00 00 00 00 00 7a
[03b0f]  IN: ab ab 00 02 00 00 00 41 01 44
[03b33] OUT: ab ab 00 0b 00 00 00 43 00 00 00 00 02 00 00 00
             cd b6 d3
[03b6f] OUT: ab ab 00 35 00 00 00 40 40 00 20 60 20 00 00 00
             00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 0f
             00 00 00 00 a8 c7 a8 c7 00 00 00 00 00 00 00 00
             0a 00 00 00 00 00 00 00 00 00 00 00 4c
[03b71]  IN: ab ab 00 02 00 00 00 41 01 44
[03b8b] OUT: ab ab 00 29 00 00 00 43 00 00 00 00 20 00 00 00
             5a 5a 7a 6f 2e 2e 28 2d 5f 2d 20 29 20 45 58 2d  ["ZZzo..(-_- ) EX-4420 2013-04-01\x00"]
             34 34 32 30 20 32 30 31 33 2d 30 34 2d 30 31 00
             68
[03bb3] OUT: ab ab 00 03 00 00 00 50 cd b6 d6
[03bb5]  IN: ab ab 00 01 00 00 00 06 07  [OK]
```

 * `62 00 20 60`
 * `02 00 00 00`
 * `00 00 00 00`
 * `00 00 00 00`
 * `00 00 00 00`
 * `00 00 00 0f`
 * `00 00 00 00`
 * `ce 36 ce 36`
 * `00 00 00 00`
 * `00 00 00 00`
 * `0a 00 00 00`
 * `00 00 00 00`
 * `00 00 00 00`

 * `40 00 20 60`
 * `20 00 00 00`
 * `00 00 00 00`
 * `00 00 00 00`
 * `00 00 00 00`
 * `00 00 00 0f`
 * `00 00 00 00`
 * `a8 c7 a8 c7`
 * `00 00 00 00`
 * `00 00 00 00`
 * `0a 00 00 00`
 * `00 00 00 00`
 * `00 00 00 00`

 * `00 00 00 00`
 * `20 00 00 00`
 * `5a 5a 7a 6f 2e 2e 28 2d 5f 2d 20 29 20 45 58 2d`
 * `34 34 32 30 20 32 30 31 33 2d 30 34 2d 30 31 00` – "ZZzo..(-_- ) EX-4420 2013-04-01\x00"