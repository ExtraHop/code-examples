FROM busybox:glibc

ENV INTERFACE any-eth
ENV EXTRAHOP_SENSOR_IP eda

COPY init.sh .
COPY rpcapd .

ENTRYPOINT ["./init.sh"]
