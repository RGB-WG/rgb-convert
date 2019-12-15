FROM debian:stretch

RUN apt-get update && apt-get install \
  -y --no-install-recommends python3 pip3 python3-virtualenv

RUN python3 -m virtualenv --python=/usr/bin/python3 /opt/venv

# This is wrong!
RUN . /opt/venv/bin/activate

# Install dependencies:
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Run the application:
COPY sealtools.py openseals samples .
CMD ["python", "sealtools.py "]
