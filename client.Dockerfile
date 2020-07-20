FROM python:3.7
ADD ./requirements.txt /zmqtest/
WORKDIR /zmqtest/
RUN pip install -r requirements.txt
ADD ./client.py ./clientQueue.py /zmqtest/
CMD ["python","-u","client.py"]