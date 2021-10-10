# Image for Ubuntu
FROM ubuntu:20.04

RUN echo "Starting - Dockerfile processing"

# Get essentials
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/London
RUN apt-get update -y
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y
RUN apt-get install build-essential -y
RUN apt-get install python3-venv -y
RUN apt-get install python3-wheel -y

# Install Tkinter
#RUN apt-get install tk -y
RUN apt-get install python3-tk -y

# Setup data and folders
RUN echo "Starting - Directory setup"
RUN mkdir -p /home/app
RUN mkdir -p /home/app/codeData
RUN mkdir -p /home/app/codeData/inData
RUN mkdir -p /home/app/codeData/extraUserInput
RUN mkdir -p /home/app/codeData/outData
RUN mkdir -p /home/app/codeData/tempDir
RUN mkdir -p /home/app/codeData/utils

# Copy necessary files
RUN echo "Starting - Copy necessary files"
COPY /code/02_load_neo_show_gui_3.py /home/app/codeData/
COPY /code/extraUserInput /home/app/codeData/extraUserInput
COPY /code/inData /home/app/codeData/inData
COPY /code/utils/*.py /home/app/codeData/utils/
COPY ./python3_requirements.txt /home/app/

# Setup virutal environment and download Spacy large model
RUN echo "Starting - Setup virtual environment"
ENV VIRTUAL_ENV=/home/.venv/virtenv1
RUN mkdir /home/.venv && python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip3 install wheel && pip3 install -r /home/app/python3_requirements.txt && python3 -m spacy download en_core_web_lg

# Commands
WORKDIR /home/app/codeData
RUN echo "Starting - cmd setup"
CMD ["python3", "/home/app/codeData/02_load_neo_show_gui_3.py", "-reloadNeo", "Y", "-uploadLimit", "500"]

RUN echo "Success - Dockerfile processing"