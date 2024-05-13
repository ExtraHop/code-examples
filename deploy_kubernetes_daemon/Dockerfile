FROM ubuntu:22.04

# docker build -t rpcapd --build-arg RPCAPD_DEB_ARCHIVE=rpcapd_9.3.7_amd64.22.04.deb .

RUN apt-get update && \
    apt-get install -y iproute2

ARG RPCAPD_DEB_ARCHIVE

ENV INTERFACE any-eth
ENV EXTRAHOP_SENSOR_IP eda

COPY init.sh .
COPY ${RPCAPD_DEB_ARCHIVE} .

RUN dpkg --unpack ${RPCAPD_DEB_ARCHIVE} && \
    rm ${RPCAPD_DEB_ARCHIVE} && \
    chmod +x init.sh

ENTRYPOINT ["./init.sh"]
