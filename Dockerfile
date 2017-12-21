FROM ubuntu:16.04
# Do we really need Ubuntu 16?  Most of our other container images are build from Ubuntu 14 or Alpine

MAINTAINER PhenoMeNal-H2020 Project ( phenomenal-h2020-users@googlegroups.com )

LABEL Description="Tools to query MetaboLights ISA-Tab"
LABEL software.version="0.8.0"
LABEL version="0.6"
LABEL software="mtblisa"

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      gcc g++ \
      python3 \
      python3-dev \
      python3-pip \
    && \
    pip3 install --upgrade pip && \
    pip3 install -U setuptools && \
    pip3 install isatools==0.8.2 argparse==1.4.0 && \
    apt-get purge -y \
      build-essential \
      gcc g++ \
      libxml2-dev \
      libxslt-dev \
      python3-dev \
      python3-lxml \
      python3-pip \
    && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


WORKDIR /mtblisa
COPY \
  mtblisa.py \
  parser_utils.py \
  requirements.txt \
  run_test.sh \
  run_tests.py \
  test_cmds.txt \
  test_query.json \
./

RUN chmod a+rx run_test.sh mtblisa.py

ENTRYPOINT ["./mtblisa.py"]
