# OpenSeals Framework on Python

Data types and command-line utility for operations using OpenSeals - single-use seal mechanism with client-stored
and validated state (see <https://github.com/rgb-org/spec> for more details).

Try:

```shell script
$ ./sealtools.py schema-validate samples/rgb_schema.yaml
$ ./sealtools.py schema-transcode samples/rgb_schema.yaml samples/rgb_schema.bin
$ ./sealtools.py proof-validate -s samples/rgb_schema.yaml samples/shares_issue.yaml
$ ./sealtools.py proof-transcode -s samples/rgb_schema.yaml samples/shares_issue.yaml samples/shares_issue.bin
$ ./sealtools.py proof-transcode -s samples/rgb_schema.yaml samples/shares_transfer.yaml samples/shares_transfer.bin
```
