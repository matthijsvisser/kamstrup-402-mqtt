FROM python:3
WORKDIR /opt/kamstrup
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY daemon.py /opt/kamstrup/
COPY kamstrup_meter.py /opt/kamstrup/
COPY mqtt_handler.py /opt/kamstrup/
RUN mkdir /opt/kamstrup/logs
CMD [ "python", "/opt/kamstrup/daemon.py" ]
