
# Kafka Disk Utilisation Alerting (v2)

## Threshold

Page when broker log-directory utilisation exceeds **75%**. Warn at 60%. The
former 85% page threshold left too little headroom for compaction and is
superseded.

## Action

Expand the volume or reduce retention on the largest topic.

## Cluster reference

The production cluster is `kafka-prod-east`. Broker `BROKER-EAST-02` listens on
port 9093 for TLS traffic and port 9092 for PLAINTEXT. The metrics endpoint is
`http://BROKER-EAST-02:7071/metrics`. The on-call rota lives in PagerDuty
service `PD-KAFKA-OPS`. Cluster ID is `kfk-east-7731`.
