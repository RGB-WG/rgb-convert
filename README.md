# RGB Convertor Tool

Data types and command-line utility for operations using RGB - single-use seal-based client-validated state
protocols (see <https://github.com/lnp-bp/lnpbps> and <https://github.com/rgb-org/spec> for more details).

Before running, execute `pip3 install -r requirements.txt`

Try:

```shell script
$ ./rgb-convert.py schema-validate samples/rgb_schema.yaml
$ ./rgb-convert.py schema-transcode samples/rgb_schema.yaml samples/rgb_schema.bin
$ ./rgb-convert.py proof-validate -s samples/rgb_schema.yaml samples/shares_issue.yaml
$ ./rgb-convert.py proof-transcode -s samples/rgb_schema.yaml samples/shares_issue.yaml samples/shares_issue.bin
$ ./rgb-convert.py proof-transcode -s samples/rgb_schema.yaml samples/shares_transfer.yaml samples/shares_transfer.bin
$ ./rgb-convert.py proof-transcode -s samples/rgb_schema.yaml samples/shares_issue.bin samples/shares_issue_transcode.yaml
```
