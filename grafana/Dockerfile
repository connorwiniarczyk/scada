FROM grafana/grafana

RUN grafana-cli plugins install redis-datasource
RUN grafana-cli plugins install redis-app
RUN grafana-cli plugins install speakyourcode-button-panel
RUN grafana-cli plugins install aceiot-svg-panel

EXPOSE 3000

CMD grafana

