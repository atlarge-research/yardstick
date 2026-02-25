FROM itzg/minecraft-server:java25

COPY jolokia-agent-jvm-2.5.1-javaagent.jar /opt/minecraft/jolokia-agent.jar

ENV ONLINE_MODE=false
ENV ENABLE_JMX=true
ENV JVM_OPTS="-javaagent:/opt/minecraft/jolokia-agent.jar=port=8778,host=0.0.0.0"
