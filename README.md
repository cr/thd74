# Kenwood TH-D74 reverse-engineering notes

To  decrypt firmware images from the upater and export to SREC, grab yourself an updater and run:

```
$ git clone https://github.com/cr/thd74
$ cd thd74
$ pip install -e '.[dev]'
$ thd74tool extract --exe /tmp/fw/TH-D74_V110_E/TH-D74_V110_e.exe
$ thd74tool extract --exe /tmp/fw/TH-D74_V110_E/TH-D74_V110_e.exe --path /tmp/fw
```

